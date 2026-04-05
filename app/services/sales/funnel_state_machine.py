# -*- coding: utf-8 -*-
"""
销售漏斗统一状态机

提供 Lead/Opportunity/Quote/Contract 的统一状态管理和流转控制。
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy.orm import Session, joinedload

from app.models.sales.contracts import Contract
from app.models.sales.leads import Lead, Opportunity
from app.models.sales.quotes import Quote, QuoteVersion
from app.models.sales.sales_funnel import (
    FunnelEntityTypeEnum,
    FunnelTransitionLog,
    GateResultEnum,
    GateTypeEnum,
    SalesFunnelStage,
    StageGateResult,
)

from .gate_validators import GateValidatorFactory, ValidationResult

logger = logging.getLogger(__name__)


class FunnelStateMachine:
    """销售漏斗统一状态机

    管理销售漏斗中各实体的状态流转，确保状态转换符合业务规则。
    """

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _coerce_entity_type(
        entity_type: Union[FunnelEntityTypeEnum, str]
    ) -> FunnelEntityTypeEnum:
        """兼容枚举和值字符串两种输入。"""
        if isinstance(entity_type, FunnelEntityTypeEnum):
            return entity_type
        return FunnelEntityTypeEnum(str(entity_type).upper())

    # ==================== 状态查询 ====================

    def get_entity_stage(
        self, entity_type: Union[FunnelEntityTypeEnum, str], entity_id: int
    ) -> Optional[str]:
        """获取实体当前阶段"""
        entity_type = self._coerce_entity_type(entity_type)
        entity = self._get_entity(entity_type, entity_id)
        if not entity:
            return None

        if entity_type == FunnelEntityTypeEnum.LEAD:
            return entity.status
        elif entity_type == FunnelEntityTypeEnum.OPPORTUNITY:
            return entity.stage
        elif entity_type == FunnelEntityTypeEnum.QUOTE:
            # 报价阶段通过当前版本状态判断 - 使用预加载的关联对象
            if entity.current_version:
                return entity.current_version.status
            return "DRAFT"
        elif entity_type == FunnelEntityTypeEnum.CONTRACT:
            return entity.status

        return None

    def _get_entity(
        self, entity_type: Union[FunnelEntityTypeEnum, str], entity_id: int
    ) -> Optional[Any]:
        """获取实体对象 - 使用 eager loading 预加载常用关联"""
        entity_type = self._coerce_entity_type(entity_type)
        if entity_type == FunnelEntityTypeEnum.LEAD:
            return (
                self.db.query(Lead)
                .options(joinedload(Lead.assessment))
                .filter(Lead.id == entity_id)
                .first()
            )
        elif entity_type == FunnelEntityTypeEnum.OPPORTUNITY:
            return (
                self.db.query(Opportunity)
                .options(joinedload(Opportunity.assessment))
                .filter(Opportunity.id == entity_id)
                .first()
            )
        elif entity_type == FunnelEntityTypeEnum.QUOTE:
            return (
                self.db.query(Quote)
                .options(joinedload(Quote.current_version))
                .filter(Quote.id == entity_id)
                .first()
            )
        elif entity_type == FunnelEntityTypeEnum.CONTRACT:
            return self.db.query(Contract).filter(Contract.id == entity_id).first()
        return None

    def _get_entity_code(
        self, entity_type: Union[FunnelEntityTypeEnum, str], entity: Any
    ) -> Optional[str]:
        """获取实体编码"""
        entity_type = self._coerce_entity_type(entity_type)
        if entity_type == FunnelEntityTypeEnum.LEAD:
            return entity.lead_code
        elif entity_type == FunnelEntityTypeEnum.OPPORTUNITY:
            return entity.opp_code
        elif entity_type == FunnelEntityTypeEnum.QUOTE:
            return entity.quote_code
        elif entity_type == FunnelEntityTypeEnum.CONTRACT:
            return entity.contract_code
        return None

    # ==================== 状态转换 ====================

    def can_transition(
        self,
        entity_type: Union[FunnelEntityTypeEnum, str],
        entity_id: int,
        to_stage: str,
    ) -> Tuple[bool, List[str]]:
        """检查是否可以进行状态转换

        Returns:
            Tuple[bool, List[str]]: (是否可以转换, 原因列表)
        """
        entity_type = self._coerce_entity_type(entity_type)
        entity = self._get_entity(entity_type, entity_id)
        if not entity:
            return False, ["实体不存在"]

        current_stage = self.get_entity_stage(entity_type, entity_id)
        if not current_stage:
            return False, ["无法获取当前阶段"]

        # 获取阶段配置
        stage_config = (
            self.db.query(SalesFunnelStage)
            .filter(SalesFunnelStage.stage_code == current_stage)
            .first()
        )

        if not stage_config:
            # 没有配置时允许自由转换
            return True, []

        # 检查是否为终止状态
        if stage_config.is_terminal:
            return False, [f"当前阶段 {current_stage} 为终止状态，不允许转换"]

        # 检查目标阶段是否在允许列表中
        allowed_stages = stage_config.allowed_next_stages or []
        if to_stage not in allowed_stages:
            return False, [
                f"不允许从 {current_stage} 转换到 {to_stage}",
                f"允许的目标阶段: {', '.join(allowed_stages)}",
            ]

        # 检查是否需要通过阶段门
        if stage_config.required_gate:
            gate_type = GateTypeEnum(stage_config.required_gate)
            result, _ = GateValidatorFactory.validate_gate(
                gate_type=gate_type,
                entity_id=entity_id,
                db=self.db,
                save_result=False,
            )
            if not result.passed:
                return False, [
                    f"未通过阶段门 {stage_config.required_gate}",
                    *result.failed_rules,
                ]

        return True, []

    def transition(
        self,
        entity_type: Union[FunnelEntityTypeEnum, str],
        entity_id: int,
        to_stage: str,
        reason: Optional[str] = None,
        transitioned_by: Optional[int] = None,
        validate_gate: bool = True,
        extra_data: Optional[Dict] = None,
    ) -> Tuple[bool, Optional[FunnelTransitionLog], List[str]]:
        """执行状态转换

        Args:
            entity_type: 实体类型
            entity_id: 实体ID
            to_stage: 目标阶段
            reason: 转换原因
            transitioned_by: 操作人ID
            validate_gate: 是否验证阶段门
            extra_data: 额外数据

        Returns:
            Tuple[bool, FunnelTransitionLog, List[str]]: (是否成功, 转换日志, 消息列表)
        """
        entity_type = self._coerce_entity_type(entity_type)
        entity = self._get_entity(entity_type, entity_id)
        if not entity:
            return False, None, ["实体不存在"]

        from_stage = self.get_entity_stage(entity_type, entity_id)
        stage_config = (
            self.db.query(SalesFunnelStage)
            .filter(SalesFunnelStage.stage_code == from_stage)
            .first()
        )

        # 检查是否可以转换
        if validate_gate:
            can_trans, reasons = self.can_transition(entity_type, entity_id, to_stage)
            if not can_trans:
                return False, None, reasons

        # 计算滞留时间
        dwell_hours = self._calculate_dwell_hours(entity_type, entity)

        # 执行状态更新
        self._update_entity_stage(entity_type, entity, to_stage)

        # 执行阶段门验证并记录结果
        gate_result_id = None
        if validate_gate and stage_config and stage_config.required_gate:
            gate_type = GateTypeEnum(stage_config.required_gate)
            _, gate_result = GateValidatorFactory.validate_gate(
                gate_type=gate_type,
                entity_id=entity_id,
                db=self.db,
                validated_by=transitioned_by,
                save_result=True,
            )
            if gate_result:
                gate_result_id = gate_result.id

        # 记录转换日志
        log = FunnelTransitionLog(
            entity_type=entity_type.value,
            entity_id=entity_id,
            entity_code=self._get_entity_code(entity_type, entity),
            from_stage=from_stage,
            to_stage=to_stage,
            gate_type=stage_config.required_gate if stage_config else None,
            gate_result_id=gate_result_id,
            transition_reason=reason,
            transitioned_by=transitioned_by,
            transitioned_at=datetime.now(),
            dwell_hours=dwell_hours,
            extra_data=extra_data,
        )

        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        logger.info(
            f"漏斗状态转换: {entity_type.value}:{entity_id} "
            f"{from_stage} -> {to_stage}"
        )

        return True, log, [f"状态已从 {from_stage} 转换为 {to_stage}"]

    def _update_entity_stage(
        self,
        entity_type: Union[FunnelEntityTypeEnum, str],
        entity: Any,
        to_stage: str,
    ):
        """更新实体阶段状态"""
        entity_type = self._coerce_entity_type(entity_type)
        if entity_type == FunnelEntityTypeEnum.LEAD:
            entity.status = to_stage
        elif entity_type == FunnelEntityTypeEnum.OPPORTUNITY:
            entity.stage = to_stage
            entity.gate_status = "PASSED"
            entity.gate_passed_at = datetime.now()
        elif entity_type == FunnelEntityTypeEnum.QUOTE:
            # 报价状态通过版本更新
            if entity.current_version_id:
                version = (
                    self.db.query(QuoteVersion)
                    .filter(QuoteVersion.id == entity.current_version_id)
                    .first()
                )
                if version:
                    version.status = to_stage
        elif entity_type == FunnelEntityTypeEnum.CONTRACT:
            entity.status = to_stage

        entity.updated_at = datetime.now()
        self.db.commit()

    def _calculate_dwell_hours(
        self,
        entity_type: Union[FunnelEntityTypeEnum, str],
        entity: Any,
    ) -> int:
        """计算在当前阶段的滞留时间（小时）"""
        entity_type = self._coerce_entity_type(entity_type)
        # 查找最后一次状态变更记录
        last_log = (
            self.db.query(FunnelTransitionLog)
            .filter(
                FunnelTransitionLog.entity_type == entity_type.value,
                FunnelTransitionLog.entity_id == entity.id,
            )
            .order_by(FunnelTransitionLog.transitioned_at.desc())
            .first()
        )

        if last_log:
            start_time = last_log.transitioned_at
        else:
            start_time = entity.created_at

        if start_time:
            delta = datetime.now() - start_time
            return int(delta.total_seconds() / 3600)

        return 0

    # ==================== 跨实体转换 ====================

    def lead_to_opportunity(
        self,
        lead_id: int,
        opportunity_data: Dict,
        transitioned_by: Optional[int] = None,
    ) -> Tuple[bool, Optional[Opportunity], List[str]]:
        """线索转商机（G1 阶段门）

        Args:
            lead_id: 线索ID
            opportunity_data: 商机数据
            transitioned_by: 操作人ID

        Returns:
            Tuple[bool, Opportunity, List[str]]: (是否成功, 商机对象, 消息)
        """
        # G1 验证
        result, gate_result = GateValidatorFactory.validate_gate(
            gate_type=GateTypeEnum.G1,
            entity_id=lead_id,
            db=self.db,
            validated_by=transitioned_by,
            save_result=True,
        )

        if not result.passed:
            return False, None, [
                "G1 阶段门验证失败",
                *result.failed_rules,
            ]

        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return False, None, ["线索不存在"]

        from_stage = lead.status

        # 创建商机
        opportunity = Opportunity(
            opp_code=opportunity_data.get("opp_code") or f"OPP{datetime.now().strftime('%Y%m%d%H%M%S')}",
            lead_id=lead_id,
            customer_id=opportunity_data.get("customer_id"),
            opp_name=opportunity_data.get("opp_name") or f"商机-{lead.customer_name}",
            stage="DISCOVERY",
            owner_id=opportunity_data.get("owner_id") or lead.owner_id,
            est_amount=opportunity_data.get("est_amount"),
            expected_close_date=opportunity_data.get("expected_close_date"),
            gate_status="PASSED",
            gate_passed_at=datetime.now(),
        )

        self.db.add(opportunity)

        # 更新线索状态
        lead.status = "CONVERTED"

        # 记录转换日志
        log = FunnelTransitionLog(
            entity_type=FunnelEntityTypeEnum.LEAD.value,
            entity_id=lead_id,
            entity_code=lead.lead_code,
            from_stage=from_stage,
            to_stage="CONVERTED",
            gate_type="G1",
            gate_result_id=gate_result.id if gate_result else None,
            transition_reason="线索转商机",
            transitioned_by=transitioned_by,
            transitioned_at=datetime.now(),
            extra_data={"new_opportunity_code": opportunity.opp_code},
        )

        self.db.add(log)
        self.db.commit()
        self.db.refresh(opportunity)

        logger.info(f"线索转商机成功: {lead.lead_code} -> {opportunity.opp_code}")

        return True, opportunity, ["线索已成功转换为商机"]

    def opportunity_to_quote(
        self,
        opportunity_id: int,
        quote_data: Dict,
        transitioned_by: Optional[int] = None,
    ) -> Tuple[bool, Optional[Quote], List[str]]:
        """商机转报价（G2 阶段门）"""
        # G2 验证
        result, gate_result = GateValidatorFactory.validate_gate(
            gate_type=GateTypeEnum.G2,
            entity_id=opportunity_id,
            db=self.db,
            validated_by=transitioned_by,
            save_result=True,
        )

        if not result.passed:
            return False, None, [
                "G2 阶段门验证失败",
                *result.failed_rules,
            ]

        opportunity = (
            self.db.query(Opportunity)
            .filter(Opportunity.id == opportunity_id)
            .first()
        )
        if not opportunity:
            return False, None, ["商机不存在"]

        # 创建报价
        quote = Quote(
            quote_code=quote_data.get("quote_code") or f"QT{datetime.now().strftime('%Y%m%d%H%M%S')}",
            opportunity_id=opportunity_id,
            customer_id=opportunity.customer_id,
            quote_name=quote_data.get("quote_name") or f"报价-{opportunity.opp_name}",
            status="DRAFT",
            created_by=transitioned_by,
        )

        self.db.add(quote)
        self.db.commit()
        self.db.refresh(quote)

        # 记录转换日志
        log = FunnelTransitionLog(
            entity_type=FunnelEntityTypeEnum.OPPORTUNITY.value,
            entity_id=opportunity_id,
            entity_code=opportunity.opp_code,
            from_stage=opportunity.stage,
            to_stage="PROPOSAL",
            gate_type="G2",
            gate_result_id=gate_result.id if gate_result else None,
            transition_reason="商机转报价",
            transitioned_by=transitioned_by,
            transitioned_at=datetime.now(),
            extra_data={"new_quote_code": quote.quote_code},
        )

        self.db.add(log)

        # 更新商机阶段
        opportunity.stage = "PROPOSAL"
        opportunity.gate_status = "PASSED"
        opportunity.gate_passed_at = datetime.now()

        self.db.commit()

        logger.info(f"商机转报价成功: {opportunity.opp_code} -> {quote.quote_code}")

        return True, quote, ["商机已成功转换为报价"]

    def quote_to_contract(
        self,
        quote_id: int,
        contract_data: Dict,
        transitioned_by: Optional[int] = None,
    ) -> Tuple[bool, Optional[Contract], List[str]]:
        """报价转合同（G3 阶段门）"""
        # G3 验证
        result, gate_result = GateValidatorFactory.validate_gate(
            gate_type=GateTypeEnum.G3,
            entity_id=quote_id,
            db=self.db,
            validated_by=transitioned_by,
            save_result=True,
        )

        if not result.passed:
            return False, None, [
                "G3 阶段门验证失败",
                *result.failed_rules,
            ]

        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            return False, None, ["报价不存在"]

        # 获取报价版本金额
        current_version = None
        if quote.current_version_id:
            current_version = (
                self.db.query(QuoteVersion)
                .filter(QuoteVersion.id == quote.current_version_id)
                .first()
            )

        # 创建合同
        contract = Contract(
            contract_code=contract_data.get("contract_code") or f"CT{datetime.now().strftime('%Y%m%d%H%M%S')}",
            contract_name=contract_data.get("contract_name") or f"合同-{quote.quote_name}",
            contract_type=contract_data.get("contract_type") or "sales",
            opportunity_id=quote.opportunity_id,
            quote_id=quote.current_version_id,
            customer_id=quote.customer_id,
            total_amount=current_version.total_amount if current_version else 0,
            status="draft",
            sales_owner_id=transitioned_by,
        )

        self.db.add(contract)
        self.db.commit()
        self.db.refresh(contract)

        # 记录转换日志
        log = FunnelTransitionLog(
            entity_type=FunnelEntityTypeEnum.QUOTE.value,
            entity_id=quote_id,
            entity_code=quote.quote_code,
            from_stage=current_version.status if current_version else "DRAFT",
            to_stage="ACCEPTED",
            gate_type="G3",
            gate_result_id=gate_result.id if gate_result else None,
            transition_reason="报价转合同",
            transitioned_by=transitioned_by,
            transitioned_at=datetime.now(),
            extra_data={"new_contract_code": contract.contract_code},
        )

        self.db.add(log)

        # 更新报价状态
        if current_version:
            current_version.status = "ACCEPTED"

        self.db.commit()

        logger.info(f"报价转合同成功: {quote.quote_code} -> {contract.contract_code}")

        return True, contract, ["报价已成功转换为合同"]

    # ==================== 查询方法 ====================

    def get_transition_history(
        self,
        entity_type: Union[FunnelEntityTypeEnum, str],
        entity_id: int,
    ) -> List[FunnelTransitionLog]:
        """获取实体的状态转换历史"""
        entity_type = self._coerce_entity_type(entity_type)
        return (
            self.db.query(FunnelTransitionLog)
            .filter(
                FunnelTransitionLog.entity_type == entity_type.value,
                FunnelTransitionLog.entity_id == entity_id,
            )
            .order_by(FunnelTransitionLog.transitioned_at.desc())
            .all()
        )

    def get_funnel_summary(self) -> Dict[str, Any]:
        """获取漏斗汇总数据"""
        from sqlalchemy import func

        # 统计各阶段数量
        lead_stats = (
            self.db.query(Lead.status, func.count(Lead.id))
            .group_by(Lead.status)
            .all()
        )

        opp_stats = (
            self.db.query(Opportunity.stage, func.count(Opportunity.id))
            .group_by(Opportunity.stage)
            .all()
        )

        return {
            "leads": {status: count for status, count in lead_stats},
            "opportunities": {stage: count for stage, count in opp_stats},
            "timestamp": datetime.now().isoformat(),
        }
