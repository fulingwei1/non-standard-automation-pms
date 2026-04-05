# -*- coding: utf-8 -*-
"""
销售漏斗阶段门验证器

G1-G4 阶段门验证逻辑：
- G1: 线索转商机（Lead → Opportunity）
- G2: 商机转报价（Opportunity → Quote）
- G3: 报价转合同（Quote → Contract）
- G4: 合同转项目（Contract → Project）
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Type

from sqlalchemy.orm import Session, joinedload

from app.models.sales.contracts import Contract
from app.models.sales.leads import Lead, Opportunity
from app.models.sales.quotes import Quote, QuoteVersion
from app.models.sales.sales_funnel import (
    GateResultEnum,
    GateTypeEnum,
    StageGateConfig,
    StageGateResult,
)
from app.models.sales.technical_assessment import TechnicalAssessment

logger = logging.getLogger(__name__)


class ValidationResult:
    """验证结果"""

    def __init__(
        self,
        passed: bool,
        score: int = 0,
        threshold: int = 0,
        passed_rules: Optional[List[str]] = None,
        failed_rules: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        details: Optional[Dict] = None,
    ):
        self.passed = passed
        self.score = score
        self.threshold = threshold
        self.passed_rules = passed_rules or []
        self.failed_rules = failed_rules or []
        self.warnings = warnings or []
        self.details = details or {}

    def to_dict(self) -> Dict:
        return {
            "passed": self.passed,
            "score": self.score,
            "threshold": self.threshold,
            "passed_rules": self.passed_rules,
            "failed_rules": self.failed_rules,
            "warnings": self.warnings,
            "details": self.details,
        }


class BaseGateValidator(ABC):
    """阶段门验证器基类"""

    gate_type: GateTypeEnum = None

    def __init__(self, db: Session):
        self.db = db
        self.config = self._load_config()

    def _load_config(self) -> Optional[StageGateConfig]:
        """加载阶段门配置"""
        if not self.gate_type:
            return None

        return (
            self.db.query(StageGateConfig)
            .filter(StageGateConfig.gate_type == self.gate_type.value)
            .first()
        )

    @abstractmethod
    def validate(self, entity_id: int) -> ValidationResult:
        """执行验证"""
        pass

    def save_result(
        self,
        entity_type: str,
        entity_id: int,
        result: ValidationResult,
        validated_by: Optional[int] = None,
    ) -> StageGateResult:
        """保存验证结果"""
        gate_result = StageGateResult(
            entity_type=entity_type,
            entity_id=entity_id,
            gate_type=self.gate_type.value,
            result=GateResultEnum.PASSED if result.passed else GateResultEnum.FAILED,
            validation_details=result.details,
            passed_rules=result.passed_rules,
            failed_rules=result.failed_rules,
            warnings=result.warnings,
            score=result.score,
            threshold=result.threshold,
            validated_by=validated_by,
            validated_at=datetime.now(),
        )

        self.db.add(gate_result)
        self.db.commit()
        self.db.refresh(gate_result)

        logger.info(
            f"阶段门验证结果: {self.gate_type.value} - "
            f"{entity_type}:{entity_id} - "
            f"{'PASSED' if result.passed else 'FAILED'}"
        )

        return gate_result

    def waive_gate(
        self,
        gate_result_id: int,
        waived_by: int,
        waive_reason: str,
    ) -> Optional[StageGateResult]:
        """豁免阶段门"""
        gate_result = (
            self.db.query(StageGateResult)
            .filter(StageGateResult.id == gate_result_id)
            .first()
        )

        if not gate_result:
            return None

        # 检查是否允许豁免
        if self.config and not self.config.can_be_waived:
            raise ValueError(f"阶段门 {self.gate_type.value} 不允许豁免")

        gate_result.is_waived = True
        gate_result.waived_by = waived_by
        gate_result.waived_at = datetime.now()
        gate_result.waive_reason = waive_reason
        gate_result.result = GateResultEnum.WAIVED

        self.db.commit()
        self.db.refresh(gate_result)

        logger.info(f"阶段门豁免: {gate_result.id} by user {waived_by}")
        return gate_result


class G1Validator(BaseGateValidator):
    """G1 阶段门验证器：线索转商机

    验证条件：
    - 线索基本信息完整
    - 客户信息已录入
    - 需求摘要已填写
    - 技术可行性初步评估（如有）
    """

    gate_type = GateTypeEnum.G1

    def validate(self, lead_id: int) -> ValidationResult:
        """验证线索是否可以转换为商机"""
        # 使用 eager loading 预加载技术评估，避免 N+1 查询
        lead = (
            self.db.query(Lead)
            .options(joinedload(Lead.assessment))
            .filter(Lead.id == lead_id)
            .first()
        )

        if not lead:
            return ValidationResult(
                passed=False,
                failed_rules=["线索不存在"],
            )

        passed_rules = []
        failed_rules = []
        warnings = []
        details = {}
        score = 0
        max_score = 100

        # 规则 1: 客户名称（20分）
        if lead.customer_name:
            passed_rules.append("客户名称已填写")
            score += 20
        else:
            failed_rules.append("客户名称未填写")

        # 规则 2: 联系人信息（15分）
        if lead.contact_name and lead.contact_phone:
            passed_rules.append("联系人信息完整")
            score += 15
        elif lead.contact_name or lead.contact_phone:
            warnings.append("联系人信息不完整")
            score += 8
        else:
            failed_rules.append("联系人信息缺失")

        # 规则 3: 需求摘要（25分）
        if lead.demand_summary and len(lead.demand_summary) >= 50:
            passed_rules.append("需求摘要详细")
            score += 25
        elif lead.demand_summary:
            warnings.append("需求摘要过于简短")
            score += 15
        else:
            failed_rules.append("需求摘要未填写")

        # 规则 4: 行业信息（10分）
        if lead.industry:
            passed_rules.append("行业信息已填写")
            score += 10
        else:
            warnings.append("行业信息未填写")

        # 规则 5: 负责人已分配（10分）
        if lead.owner_id:
            passed_rules.append("负责人已分配")
            score += 10
        else:
            failed_rules.append("负责人未分配")

        # 规则 6: 技术评估（可选，20分）- 使用预加载的关联对象
        assessment = lead.assessment
        if assessment:
            if assessment.status == "COMPLETED":
                if assessment.decision in ["推荐立项", "有条件立项"]:
                    passed_rules.append("技术评估通过")
                    score += 20
                elif assessment.decision == "暂缓":
                    warnings.append("技术评估建议暂缓")
                    score += 10
                else:
                    failed_rules.append("技术评估不建议立项")
            else:
                warnings.append("技术评估未完成")
                score += 5
        else:
            warnings.append("未进行技术评估")

        # 计算通过阈值（默认60分）
        threshold = 60
        if self.config and self.config.validation_rules:
            threshold = self.config.validation_rules.get("pass_threshold", 60)

        details = {
            "lead_code": lead.lead_code,
            "customer_name": lead.customer_name,
            "industry": lead.industry,
            "has_assessment": bool(lead.assessment_id),
        }

        return ValidationResult(
            passed=score >= threshold and len(failed_rules) == 0,
            score=score,
            threshold=threshold,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            warnings=warnings,
            details=details,
        )


class G2Validator(BaseGateValidator):
    """G2 阶段门验证器：商机转报价

    验证条件：
    - 商机阶段已推进到 QUALIFICATION 以上
    - 预估金额已填写
    - 技术评估已完成且通过
    - 需求已确认
    """

    gate_type = GateTypeEnum.G2

    def validate(self, opportunity_id: int) -> ValidationResult:
        """验证商机是否可以转换为报价"""
        # 使用 eager loading 预加载技术评估，避免 N+1 查询
        opportunity = (
            self.db.query(Opportunity)
            .options(joinedload(Opportunity.assessment))
            .filter(Opportunity.id == opportunity_id)
            .first()
        )

        if not opportunity:
            return ValidationResult(
                passed=False,
                failed_rules=["商机不存在"],
            )

        passed_rules = []
        failed_rules = []
        warnings = []
        details = {}
        score = 0

        # 规则 1: 商机阶段检查（20分）
        valid_stages = ["QUALIFICATION", "PROPOSAL", "NEGOTIATION"]
        if opportunity.stage in valid_stages:
            passed_rules.append(f"商机阶段有效: {opportunity.stage}")
            score += 20
        else:
            failed_rules.append(f"商机阶段不满足要求: {opportunity.stage}")

        # 规则 2: 预估金额（20分）
        if opportunity.est_amount and float(opportunity.est_amount) > 0:
            passed_rules.append("预估金额已填写")
            score += 20
        else:
            failed_rules.append("预估金额未填写")

        # 规则 3: 客户关联（15分）
        if opportunity.customer_id:
            passed_rules.append("客户信息已关联")
            score += 15
        else:
            failed_rules.append("客户信息未关联")

        # 规则 4: 技术评估（25分）- 使用预加载的关联对象
        assessment = opportunity.assessment
        if assessment:
                if assessment.status == "COMPLETED":
                    if assessment.decision in ["推荐立项", "有条件立项"]:
                        passed_rules.append("技术评估通过")
                        score += 25
                        if assessment.decision == "有条件立项":
                            warnings.append("技术评估为有条件通过，请关注条件落实")
                    else:
                        failed_rules.append(f"技术评估结果: {assessment.decision}")
                else:
                    failed_rules.append("技术评估未完成")
        else:
            failed_rules.append("未进行技术评估")

        # 规则 5: 预计成交日期（10分）
        if opportunity.expected_close_date:
            passed_rules.append("预计成交日期已填写")
            score += 10
        else:
            warnings.append("预计成交日期未填写")

        # 规则 6: 负责人（10分）
        if opportunity.owner_id:
            passed_rules.append("负责人已分配")
            score += 10
        else:
            failed_rules.append("负责人未分配")

        threshold = 70
        if self.config and self.config.validation_rules:
            threshold = self.config.validation_rules.get("pass_threshold", 70)

        details = {
            "opp_code": opportunity.opp_code,
            "stage": opportunity.stage,
            "est_amount": str(opportunity.est_amount) if opportunity.est_amount else None,
            "has_assessment": bool(opportunity.assessment_id),
        }

        return ValidationResult(
            passed=score >= threshold and len(failed_rules) == 0,
            score=score,
            threshold=threshold,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            warnings=warnings,
            details=details,
        )


class G3Validator(BaseGateValidator):
    """G3 阶段门验证器：报价转合同

    验证条件：
    - 报价已审批通过
    - 报价版本有效
    - 成本核算完成
    - 毛利率符合要求
    """

    gate_type = GateTypeEnum.G3

    def validate(self, quote_id: int) -> ValidationResult:
        """验证报价是否可以转换为合同"""
        # 使用 eager loading 预加载当前版本，避免 N+1 查询
        quote = (
            self.db.query(Quote)
            .options(joinedload(Quote.current_version))
            .filter(Quote.id == quote_id)
            .first()
        )

        if not quote:
            return ValidationResult(
                passed=False,
                failed_rules=["报价不存在"],
            )

        # 使用预加载的关联对象
        current_version = quote.current_version

        passed_rules = []
        failed_rules = []
        warnings = []
        details = {}
        score = 0

        # 规则 1: 报价版本存在且有效（20分）
        if current_version:
            passed_rules.append("报价版本有效")
            score += 20
        else:
            failed_rules.append("报价无有效版本")

        # 规则 2: 报价状态检查（25分）
        if current_version and current_version.status == "APPROVED":
            passed_rules.append("报价已审批通过")
            score += 25
        elif current_version and current_version.status == "SUBMITTED":
            failed_rules.append("报价待审批")
        else:
            failed_rules.append("报价未提交审批")

        # 规则 3: 金额检查（15分）
        if current_version and current_version.total_amount:
            if float(current_version.total_amount) > 0:
                passed_rules.append("报价金额有效")
                score += 15
            else:
                failed_rules.append("报价金额无效")
        else:
            failed_rules.append("报价金额缺失")

        # 规则 4: 毛利率检查（20分）
        if current_version and current_version.margin_rate is not None:
            margin = float(current_version.margin_rate)
            min_margin = 15.0  # 最低毛利率要求
            if self.config and self.config.validation_rules:
                min_margin = self.config.validation_rules.get("min_margin_rate", 15.0)

            if margin >= min_margin:
                passed_rules.append(f"毛利率满足要求: {margin:.2f}%")
                score += 20
            elif margin >= min_margin * 0.8:
                warnings.append(f"毛利率接近下限: {margin:.2f}%")
                score += 10
            else:
                failed_rules.append(f"毛利率低于要求: {margin:.2f}% < {min_margin}%")
        else:
            warnings.append("毛利率未计算")

        # 规则 5: 客户确认（10分）
        if quote.customer_id:
            passed_rules.append("客户信息已关联")
            score += 10
        else:
            failed_rules.append("客户信息未关联")

        # 规则 6: 有效期检查（10分）
        if current_version and current_version.valid_until:
            if current_version.valid_until >= datetime.now().date():
                passed_rules.append("报价在有效期内")
                score += 10
            else:
                failed_rules.append("报价已过期")
        else:
            warnings.append("报价有效期未设置")

        threshold = 75
        if self.config and self.config.validation_rules:
            threshold = self.config.validation_rules.get("pass_threshold", 75)

        details = {
            "quote_code": quote.quote_code,
            "version_no": current_version.version_no if current_version else None,
            "status": current_version.status if current_version else None,
            "total_amount": str(current_version.total_amount)
            if current_version and current_version.total_amount
            else None,
            "margin_rate": str(current_version.margin_rate)
            if current_version and current_version.margin_rate
            else None,
        }

        return ValidationResult(
            passed=score >= threshold and len(failed_rules) == 0,
            score=score,
            threshold=threshold,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            warnings=warnings,
            details=details,
        )


class G4Validator(BaseGateValidator):
    """G4 阶段门验证器：合同转项目

    验证条件：
    - 合同已签署
    - 交付物清单完整
    - 付款条款明确
    - 项目信息准备就绪
    """

    gate_type = GateTypeEnum.G4

    def validate(self, contract_id: int) -> ValidationResult:
        """验证合同是否可以转换为项目"""
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()

        if not contract:
            return ValidationResult(
                passed=False,
                failed_rules=["合同不存在"],
            )

        passed_rules = []
        failed_rules = []
        warnings = []
        details = {}
        score = 0

        # 规则 1: 合同状态检查（25分）
        valid_statuses = ["signed", "executing", "SIGNED", "EXECUTING"]
        if contract.status in valid_statuses:
            passed_rules.append(f"合同状态有效: {contract.status}")
            score += 25
        else:
            failed_rules.append(f"合同状态不满足要求: {contract.status}")

        # 规则 2: 签订日期（15分）
        if contract.signing_date:
            passed_rules.append("签订日期已填写")
            score += 15
        else:
            failed_rules.append("签订日期未填写")

        # 规则 3: 合同金额（15分）
        if contract.total_amount and float(contract.total_amount) > 0:
            passed_rules.append("合同金额有效")
            score += 15
        else:
            failed_rules.append("合同金额无效")

        # 规则 4: 交付物清单（15分）
        if contract.deliverables and len(contract.deliverables) > 0:
            passed_rules.append(f"交付物清单已定义: {len(contract.deliverables)}项")
            score += 15
        else:
            warnings.append("交付物清单为空")
            score += 5

        # 规则 5: 付款条款（15分）
        if contract.payment_terms:
            passed_rules.append("付款条款已定义")
            score += 15
        else:
            warnings.append("付款条款未定义")

        # 规则 6: 客户信息（15分）
        if contract.customer_id:
            passed_rules.append("客户信息已关联")
            score += 15
        else:
            failed_rules.append("客户信息未关联")

        threshold = 80
        if self.config and self.config.validation_rules:
            threshold = self.config.validation_rules.get("pass_threshold", 80)

        details = {
            "contract_code": contract.contract_code,
            "status": contract.status,
            "total_amount": str(contract.total_amount)
            if contract.total_amount
            else None,
            "signing_date": str(contract.signing_date)
            if contract.signing_date
            else None,
            "deliverables_count": len(contract.deliverables)
            if contract.deliverables
            else 0,
        }

        return ValidationResult(
            passed=score >= threshold and len(failed_rules) == 0,
            score=score,
            threshold=threshold,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            warnings=warnings,
            details=details,
        )


class GateValidatorFactory:
    """阶段门验证器工厂"""

    _validators: Dict[GateTypeEnum, Type[BaseGateValidator]] = {
        GateTypeEnum.G1: G1Validator,
        GateTypeEnum.G2: G2Validator,
        GateTypeEnum.G3: G3Validator,
        GateTypeEnum.G4: G4Validator,
    }

    @classmethod
    def get_validator(cls, gate_type: GateTypeEnum, db: Session) -> BaseGateValidator:
        """获取验证器实例"""
        validator_class = cls._validators.get(gate_type)
        if not validator_class:
            raise ValueError(f"不支持的阶段门类型: {gate_type}")
        return validator_class(db)

    @classmethod
    def validate_gate(
        cls,
        gate_type: GateTypeEnum,
        entity_id: int,
        db: Session,
        validated_by: Optional[int] = None,
        save_result: bool = True,
    ) -> Tuple[ValidationResult, Optional[StageGateResult]]:
        """执行阶段门验证"""
        validator = cls.get_validator(gate_type, db)
        result = validator.validate(entity_id)

        gate_result = None
        if save_result:
            entity_type = {
                GateTypeEnum.G1: "LEAD",
                GateTypeEnum.G2: "OPPORTUNITY",
                GateTypeEnum.G3: "QUOTE",
                GateTypeEnum.G4: "CONTRACT",
            }[gate_type]

            gate_result = validator.save_result(
                entity_type=entity_type,
                entity_id=entity_id,
                result=result,
                validated_by=validated_by,
            )

        return result, gate_result
