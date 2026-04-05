# -*- coding: utf-8 -*-
"""
滞留时间监控服务

监控销售漏斗各阶段的滞留时间，超时触发告警。
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.sales.contracts import Contract
from app.models.sales.leads import Lead, Opportunity
from app.models.sales.quotes import Quote
from app.models.sales.sales_funnel import (
    AlertSeverityEnum,
    AlertStatusEnum,
    FunnelEntityTypeEnum,
    FunnelTransitionLog,
    StageDwellTimeAlert,
    StageDwellTimeConfig,
    SalesFunnelStage,
)

logger = logging.getLogger(__name__)


class DwellTimeMonitorService:
    """滞留时间监控服务"""

    def __init__(self, db: Session):
        self.db = db

    def check_all_entities(self) -> List[StageDwellTimeAlert]:
        """检查所有实体的滞留时间，返回新生成的告警列表"""
        new_alerts = []

        # 检查线索
        lead_alerts = self._check_leads()
        new_alerts.extend(lead_alerts)

        # 检查商机
        opp_alerts = self._check_opportunities()
        new_alerts.extend(opp_alerts)

        # 检查报价
        quote_alerts = self._check_quotes()
        new_alerts.extend(quote_alerts)

        # 检查合同
        contract_alerts = self._check_contracts()
        new_alerts.extend(contract_alerts)

        logger.info(f"滞留时间检查完成，新增告警 {len(new_alerts)} 条")
        return new_alerts

    def _check_leads(self) -> List[StageDwellTimeAlert]:
        """检查线索滞留时间"""
        alerts = []

        # 获取活跃线索（非转化、非丢失状态）
        active_leads = (
            self.db.query(Lead)
            .filter(Lead.status.notin_(["CONVERTED", "LOST"]))
            .all()
        )

        for lead in active_leads:
            alert = self._check_entity_dwell_time(
                entity_type=FunnelEntityTypeEnum.LEAD,
                entity_id=lead.id,
                current_stage=lead.status,
                entered_at=self._get_stage_enter_time(
                    FunnelEntityTypeEnum.LEAD, lead.id, lead.created_at
                ),
                amount=None,
                owner_id=lead.owner_id,
                owner_name=None,  # 简化处理
            )
            if alert:
                alerts.append(alert)

        return alerts

    def _check_opportunities(self) -> List[StageDwellTimeAlert]:
        """检查商机滞留时间"""
        alerts = []

        # 获取活跃商机
        active_opps = (
            self.db.query(Opportunity)
            .filter(Opportunity.stage.notin_(["WON", "LOST", "ON_HOLD"]))
            .all()
        )

        for opp in active_opps:
            alert = self._check_entity_dwell_time(
                entity_type=FunnelEntityTypeEnum.OPPORTUNITY,
                entity_id=opp.id,
                current_stage=opp.stage,
                entered_at=self._get_stage_enter_time(
                    FunnelEntityTypeEnum.OPPORTUNITY, opp.id, opp.created_at
                ),
                amount=opp.est_amount,
                owner_id=opp.owner_id,
                owner_name=None,
            )
            if alert:
                alerts.append(alert)

        return alerts

    def _check_quotes(self) -> List[StageDwellTimeAlert]:
        """检查报价滞留时间"""
        alerts = []

        # 获取活跃报价（草稿、待审批状态）
        active_quotes = (
            self.db.query(Quote)
            .filter(Quote.status.in_(["DRAFT", "SUBMITTED", "PENDING"]))
            .all()
        )

        for quote in active_quotes:
            alert = self._check_entity_dwell_time(
                entity_type=FunnelEntityTypeEnum.QUOTE,
                entity_id=quote.id,
                current_stage=quote.status,
                entered_at=self._get_stage_enter_time(
                    FunnelEntityTypeEnum.QUOTE, quote.id, quote.created_at
                ),
                amount=None,  # 报价金额需从版本获取
                owner_id=quote.created_by,
                owner_name=None,
            )
            if alert:
                alerts.append(alert)

        return alerts

    def _check_contracts(self) -> List[StageDwellTimeAlert]:
        """检查合同滞留时间"""
        alerts = []

        # 获取待处理合同
        active_contracts = (
            self.db.query(Contract)
            .filter(Contract.status.in_(["draft", "pending_approval", "approving"]))
            .all()
        )

        for contract in active_contracts:
            alert = self._check_entity_dwell_time(
                entity_type=FunnelEntityTypeEnum.CONTRACT,
                entity_id=contract.id,
                current_stage=contract.status,
                entered_at=self._get_stage_enter_time(
                    FunnelEntityTypeEnum.CONTRACT, contract.id, contract.created_at
                ),
                amount=contract.total_amount,
                owner_id=contract.sales_owner_id,
                owner_name=None,
            )
            if alert:
                alerts.append(alert)

        return alerts

    def _get_stage_enter_time(
        self,
        entity_type: FunnelEntityTypeEnum,
        entity_id: int,
        default_time: datetime,
    ) -> datetime:
        """获取进入当前阶段的时间"""
        # 查找最后一次状态变更记录
        last_log = (
            self.db.query(FunnelTransitionLog)
            .filter(
                FunnelTransitionLog.entity_type == entity_type.value,
                FunnelTransitionLog.entity_id == entity_id,
            )
            .order_by(FunnelTransitionLog.transitioned_at.desc())
            .first()
        )

        if last_log:
            return last_log.transitioned_at

        return default_time

    def _check_entity_dwell_time(
        self,
        entity_type: FunnelEntityTypeEnum,
        entity_id: int,
        current_stage: str,
        entered_at: datetime,
        amount: Optional[Any],
        owner_id: Optional[int],
        owner_name: Optional[str],
    ) -> Optional[StageDwellTimeAlert]:
        """检查单个实体的滞留时间"""
        # 获取阶段配置
        stage = (
            self.db.query(SalesFunnelStage)
            .filter(SalesFunnelStage.stage_code == current_stage)
            .first()
        )

        if not stage:
            return None

        # 获取滞留时间配置
        config = (
            self.db.query(StageDwellTimeConfig)
            .filter(StageDwellTimeConfig.stage_id == stage.id)
            .first()
        )

        if not config or not config.alert_enabled:
            return None

        # 计算滞留时间
        now = datetime.now()
        dwell_hours = int((now - entered_at).total_seconds() / 3600)

        # 检查是否已有未解决的告警
        existing_alert = (
            self.db.query(StageDwellTimeAlert)
            .filter(
                StageDwellTimeAlert.entity_type == entity_type.value,
                StageDwellTimeAlert.entity_id == entity_id,
                StageDwellTimeAlert.stage_id == stage.id,
                StageDwellTimeAlert.status.in_(
                    [AlertStatusEnum.ACTIVE, AlertStatusEnum.ACKNOWLEDGED]
                ),
            )
            .first()
        )

        # 确定告警严重程度和阈值
        severity = None
        threshold_hours = None

        if config.critical_hours and dwell_hours >= config.critical_hours:
            severity = AlertSeverityEnum.CRITICAL
            threshold_hours = config.critical_hours
        elif config.warning_hours and dwell_hours >= config.warning_hours:
            severity = AlertSeverityEnum.WARNING
            threshold_hours = config.warning_hours
        elif config.expected_hours and dwell_hours >= config.expected_hours:
            severity = AlertSeverityEnum.INFO
            threshold_hours = config.expected_hours

        if not severity:
            return None

        # 如果已有告警，检查是否需要升级
        if existing_alert:
            if self._should_escalate(existing_alert, severity):
                existing_alert.severity = severity.value
                existing_alert.dwell_hours = dwell_hours
                existing_alert.updated_at = now
                self.db.commit()
                logger.info(
                    f"滞留告警升级: {entity_type.value}:{entity_id} -> {severity.value}"
                )
            return None

        # 创建新告警
        alert = StageDwellTimeAlert(
            entity_type=entity_type.value,
            entity_id=entity_id,
            stage_id=stage.id,
            alert_code=self._generate_alert_code(),
            severity=severity.value,
            alert_message=self._generate_alert_message(
                entity_type, entity_id, current_stage, dwell_hours, threshold_hours
            ),
            entered_stage_at=entered_at,
            dwell_hours=dwell_hours,
            threshold_hours=threshold_hours,
            amount=amount,
            owner_id=owner_id,
            owner_name=owner_name,
            status=AlertStatusEnum.ACTIVE,
        )

        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        logger.info(
            f"创建滞留告警: {alert.alert_code} - "
            f"{entity_type.value}:{entity_id} 滞留 {dwell_hours} 小时"
        )

        return alert

    def _should_escalate(
        self, existing_alert: StageDwellTimeAlert, new_severity: AlertSeverityEnum
    ) -> bool:
        """判断是否需要升级告警"""
        severity_order = {
            AlertSeverityEnum.INFO.value: 1,
            AlertSeverityEnum.WARNING.value: 2,
            AlertSeverityEnum.CRITICAL.value: 3,
        }
        current_order = severity_order.get(existing_alert.severity, 0)
        new_order = severity_order.get(new_severity.value, 0)
        return new_order > current_order

    def _generate_alert_code(self) -> str:
        """生成告警编码"""
        today = datetime.now()
        prefix = f"DWL{today.strftime('%Y%m%d')}"

        last_alert = (
            self.db.query(StageDwellTimeAlert)
            .filter(StageDwellTimeAlert.alert_code.like(f"{prefix}%"))
            .order_by(StageDwellTimeAlert.alert_code.desc())
            .first()
        )

        if last_alert:
            seq = int(last_alert.alert_code[-4:]) + 1
        else:
            seq = 1

        return f"{prefix}{seq:04d}"

    def _generate_alert_message(
        self,
        entity_type: FunnelEntityTypeEnum,
        entity_id: int,
        stage: str,
        dwell_hours: int,
        threshold_hours: int,
    ) -> str:
        """生成告警消息"""
        entity_names = {
            FunnelEntityTypeEnum.LEAD: "线索",
            FunnelEntityTypeEnum.OPPORTUNITY: "商机",
            FunnelEntityTypeEnum.QUOTE: "报价",
            FunnelEntityTypeEnum.CONTRACT: "合同",
        }
        entity_name = entity_names.get(entity_type, "实体")

        return (
            f"{entity_name} #{entity_id} 在阶段 [{stage}] 已滞留 {dwell_hours} 小时，"
            f"超过阈值 {threshold_hours} 小时，请及时处理。"
        )

    # ==================== 告警管理 ====================

    def acknowledge_alert(
        self, alert_id: int, acknowledged_by: int
    ) -> Optional[StageDwellTimeAlert]:
        """确认告警"""
        alert = (
            self.db.query(StageDwellTimeAlert)
            .filter(StageDwellTimeAlert.id == alert_id)
            .first()
        )

        if not alert:
            return None

        alert.status = AlertStatusEnum.ACKNOWLEDGED
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.now()
        alert.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(alert)

        logger.info(f"告警已确认: {alert.alert_code} by user {acknowledged_by}")
        return alert

    def resolve_alert(
        self,
        alert_id: int,
        resolution_note: Optional[str] = None,
    ) -> Optional[StageDwellTimeAlert]:
        """解决告警"""
        alert = (
            self.db.query(StageDwellTimeAlert)
            .filter(StageDwellTimeAlert.id == alert_id)
            .first()
        )

        if not alert:
            return None

        alert.status = AlertStatusEnum.RESOLVED
        alert.resolved_at = datetime.now()
        alert.resolution_note = resolution_note
        alert.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(alert)

        logger.info(f"告警已解决: {alert.alert_code}")
        return alert

    def ignore_alert(
        self,
        alert_id: int,
        resolution_note: Optional[str] = None,
    ) -> Optional[StageDwellTimeAlert]:
        """忽略告警"""
        alert = (
            self.db.query(StageDwellTimeAlert)
            .filter(StageDwellTimeAlert.id == alert_id)
            .first()
        )

        if not alert:
            return None

        alert.status = AlertStatusEnum.IGNORED
        alert.resolved_at = datetime.now()
        alert.resolution_note = resolution_note
        alert.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(alert)

        logger.info(f"告警已忽略: {alert.alert_code}")
        return alert

    def auto_resolve_on_transition(
        self,
        entity_type: FunnelEntityTypeEnum,
        entity_id: int,
    ) -> int:
        """实体状态转换时自动解决相关告警"""
        resolved_count = (
            self.db.query(StageDwellTimeAlert)
            .filter(
                StageDwellTimeAlert.entity_type == entity_type.value,
                StageDwellTimeAlert.entity_id == entity_id,
                StageDwellTimeAlert.status.in_(
                    [AlertStatusEnum.ACTIVE, AlertStatusEnum.ACKNOWLEDGED]
                ),
            )
            .update(
                {
                    "status": AlertStatusEnum.RESOLVED,
                    "resolved_at": datetime.now(),
                    "resolution_note": "实体状态已变更，自动解决",
                    "updated_at": datetime.now(),
                }
            )
        )

        self.db.commit()

        if resolved_count > 0:
            logger.info(
                f"自动解决 {resolved_count} 条告警: "
                f"{entity_type.value}:{entity_id}"
            )

        return resolved_count

    # ==================== 查询方法 ====================

    def get_alerts(
        self,
        entity_type: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[StageDwellTimeAlert], int]:
        """
        获取告警列表（通用查询接口）

        Args:
            entity_type: 实体类型过滤
            severity: 严重程度过滤
            status: 状态过滤
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            告警列表和总数
        """
        query = self.db.query(StageDwellTimeAlert)

        if entity_type:
            query = query.filter(StageDwellTimeAlert.entity_type == entity_type)
        if severity:
            query = query.filter(StageDwellTimeAlert.severity == severity)
        if status:
            query = query.filter(StageDwellTimeAlert.status == status)

        total = query.count()
        alerts = (
            query.order_by(StageDwellTimeAlert.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return alerts, total

    def get_active_alerts(
        self,
        entity_type: Optional[FunnelEntityTypeEnum] = None,
        severity: Optional[AlertSeverityEnum] = None,
        owner_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[StageDwellTimeAlert], int]:
        """获取活跃告警列表"""
        query = self.db.query(StageDwellTimeAlert).filter(
            StageDwellTimeAlert.status.in_(
                [AlertStatusEnum.ACTIVE, AlertStatusEnum.ACKNOWLEDGED]
            )
        )

        if entity_type:
            query = query.filter(
                StageDwellTimeAlert.entity_type == entity_type.value
            )
        if severity:
            query = query.filter(StageDwellTimeAlert.severity == severity.value)
        if owner_id:
            query = query.filter(StageDwellTimeAlert.owner_id == owner_id)

        total = query.count()
        alerts = (
            query.order_by(
                StageDwellTimeAlert.severity.desc(),
                StageDwellTimeAlert.dwell_hours.desc(),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

        return alerts, total

    def get_alert_statistics(self) -> Dict[str, Any]:
        """获取告警统计"""
        # 按状态统计
        status_stats = (
            self.db.query(
                StageDwellTimeAlert.status,
                func.count(StageDwellTimeAlert.id),
            )
            .group_by(StageDwellTimeAlert.status)
            .all()
        )

        # 按严重程度统计（仅活跃告警）
        severity_stats = (
            self.db.query(
                StageDwellTimeAlert.severity,
                func.count(StageDwellTimeAlert.id),
            )
            .filter(
                StageDwellTimeAlert.status.in_(
                    [AlertStatusEnum.ACTIVE, AlertStatusEnum.ACKNOWLEDGED]
                )
            )
            .group_by(StageDwellTimeAlert.severity)
            .all()
        )

        # 按实体类型统计（仅活跃告警）
        entity_stats = (
            self.db.query(
                StageDwellTimeAlert.entity_type,
                func.count(StageDwellTimeAlert.id),
            )
            .filter(
                StageDwellTimeAlert.status.in_(
                    [AlertStatusEnum.ACTIVE, AlertStatusEnum.ACKNOWLEDGED]
                )
            )
            .group_by(StageDwellTimeAlert.entity_type)
            .all()
        )

        return {
            "by_status": {status: count for status, count in status_stats},
            "by_severity": {severity: count for severity, count in severity_stats},
            "by_entity_type": {
                entity_type: count for entity_type, count in entity_stats
            },
            "timestamp": datetime.now().isoformat(),
        }

    def get_owner_workload(self, owner_id: int) -> Dict[str, Any]:
        """获取负责人的告警工作量"""
        alerts = (
            self.db.query(StageDwellTimeAlert)
            .filter(
                StageDwellTimeAlert.owner_id == owner_id,
                StageDwellTimeAlert.status.in_(
                    [AlertStatusEnum.ACTIVE, AlertStatusEnum.ACKNOWLEDGED]
                ),
            )
            .all()
        )

        critical_count = sum(
            1 for a in alerts if a.severity == AlertSeverityEnum.CRITICAL.value
        )
        warning_count = sum(
            1 for a in alerts if a.severity == AlertSeverityEnum.WARNING.value
        )
        info_count = sum(
            1 for a in alerts if a.severity == AlertSeverityEnum.INFO.value
        )

        return {
            "owner_id": owner_id,
            "total_alerts": len(alerts),
            "critical": critical_count,
            "warning": warning_count,
            "info": info_count,
            "alerts": [
                {
                    "id": a.id,
                    "alert_code": a.alert_code,
                    "entity_type": a.entity_type,
                    "entity_id": a.entity_id,
                    "severity": a.severity,
                    "dwell_hours": a.dwell_hours,
                }
                for a in alerts
            ],
        }
