# -*- coding: utf-8 -*-
"""
销售模块公共工具函数 - 阶段门验证函数
"""
from typing import List, Optional, Tuple

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.enums import (
    AssessmentDecisionEnum,
    AssessmentSourceTypeEnum,
    AssessmentStatusEnum,
)
from app.models.sales import (
    Contract,
    ContractDeliverable,
    Lead,
    Opportunity,
    OpportunityRequirement,
    Quote,
    QuoteItem,
    QuoteVersion,
)


def validate_g1_lead_to_opportunity(
    lead: Lead,
    requirement: Optional[OpportunityRequirement] = None,
    db: Optional[Session] = None
) -> Tuple[bool, List[str]]:
    """
    G1：线索 → 商机 验证
    需求模板必填：行业/产品对象/节拍/接口/现场约束/验收依据
    客户基本信息与联系人齐全
    可选：检查技术评估状态（如果已申请）
    """
    errors = []
    warnings = []

    # 检查客户基本信息
    if not lead.customer_name:
        errors.append("客户名称不能为空")
    if not lead.contact_name:
        errors.append("联系人不能为空")
    if not lead.contact_phone:
        errors.append("联系电话不能为空")

    # 检查需求模板必填项
    if requirement:
        if not requirement.product_object:
            errors.append("产品对象不能为空")
        if not requirement.ct_seconds:
            errors.append("节拍(秒)不能为空")
        if not requirement.interface_desc:
            errors.append("接口/通信协议不能为空")
        if not requirement.site_constraints:
            errors.append("现场约束不能为空")
        if not requirement.acceptance_criteria:
            errors.append("验收依据不能为空")
    else:
        errors.append("需求信息不能为空")

    # 可选：检查技术评估状态（如果已申请）
    if db and lead.assessment_id:
        from app.models.sales import TechnicalAssessment
        assessment = db.query(TechnicalAssessment).filter(TechnicalAssessment.id == lead.assessment_id).first()
        if assessment:
            if assessment.status != AssessmentStatusEnum.COMPLETED.value:
                warnings.append(f"技术评估状态为{assessment.status}，建议等待评估完成")
            elif assessment.decision == AssessmentDecisionEnum.NOT_RECOMMEND.value:
                warnings.append("技术评估建议为'不建议立项'，请谨慎考虑")

    # 检查未决事项（阻塞报价的）
    if db:
        from app.models.sales import OpenItem
        blocking_items = db.query(OpenItem).filter(
            and_(
                OpenItem.source_type == AssessmentSourceTypeEnum.LEAD.value,
                OpenItem.source_id == lead.id,
                OpenItem.blocks_quotation == True,
                OpenItem.status != 'CLOSED'
            )
        ).count()
        if blocking_items > 0:
            warnings.append(f"存在{blocking_items}个阻塞报价的未决事项，建议先解决")

    return len(errors) == 0, errors + warnings


def validate_g2_opportunity_to_quote(opportunity: Opportunity) -> Tuple[bool, List[str]]:
    """
    G2：商机 → 报价 验证
    预算范围、决策链、交付窗口、验收标准明确
    技术可行性初评通过
    """
    errors = []

    if not opportunity.budget_range:
        errors.append("预算范围不能为空")
    if not opportunity.decision_chain:
        errors.append("决策链不能为空")
    if not opportunity.delivery_window:
        errors.append("交付窗口不能为空")
    if not opportunity.acceptance_basis:
        errors.append("验收标准不能为空")

    # 技术可行性初评（简化：检查是否有评分）
    if opportunity.score is None or opportunity.score < 60:
        errors.append("技术可行性初评未通过（评分需≥60分）")

    return len(errors) == 0, errors


def validate_g3_quote_to_contract(
    quote: Quote,
    version: QuoteVersion,
    items: List[QuoteItem],
    db: Optional[Session] = None
) -> Tuple[bool, List[str], Optional[str]]:
    """
    G3：报价 → 合同 验证
    成本拆解齐备，毛利率低于阈值自动预警
    交期校验通过（关键物料交期 + 设计/装配/调试周期）
    风险条款与边界条款已补充
    """
    errors = []
    warnings = []

    # 检查成本拆解
    if not items or len(items) == 0:
        errors.append("报价明细不能为空")
    else:
        items_without_cost = [item for item in items if not item.cost or float(item.cost or 0) == 0]
        if items_without_cost:
            errors.append(f"有{len(items_without_cost)}个报价明细项未填写成本")

        total_cost = sum(float(item.cost or 0) * float(item.qty or 0) for item in items)
        if total_cost == 0:
            errors.append("成本拆解不完整，总成本不能为0")

    # 检查毛利率
    total_price = float(version.total_price or 0)
    total_cost = float(version.cost_total or 0)
    if total_price > 0:
        gross_margin = (total_price - total_cost) / total_price * 100
        margin_threshold = settings.SALES_GROSS_MARGIN_THRESHOLD
        margin_warning = settings.SALES_GROSS_MARGIN_WARNING

        if gross_margin < margin_threshold:
            errors.append(f"毛利率过低（{gross_margin:.2f}%），低于最低阈值{margin_threshold}%，需要审批")
        elif gross_margin < margin_warning:
            warnings.append(f"毛利率较低（{gross_margin:.2f}%），低于警告阈值{margin_warning}%，建议重新评估")

    # 检查交期
    if not version.lead_time_days or version.lead_time_days <= 0:
        errors.append("交期不能为空或必须大于0")
    else:
        min_lead_time = settings.SALES_MIN_LEAD_TIME_DAYS
        if version.lead_time_days < min_lead_time:
            warnings.append(f"交期较短（{version.lead_time_days}天），低于建议最小交期{min_lead_time}天，请确认关键物料交期和设计/装配/调试周期")

        if db is not None:
            from app.services.delivery_validation_service import (
                delivery_validation_service,
            )
            validation_result = delivery_validation_service.validate_delivery_date(
                db, quote, version, items
            )

            if validation_result["status"] == "WARNING":
                for warn in validation_result.get("warnings", []):
                    msg = warn.get("message", "")
                    if msg:
                        warnings.append(f"[交期校验] {msg}")

            for suggestion in validation_result.get("suggestions", []):
                warnings.append(f"[优化建议] {suggestion}")

    if not version.risk_terms:
        warnings.append("风险条款未补充，建议补充风险条款与边界条款")

    warning_msg = "; ".join(warnings) if warnings else None
    return len(errors) == 0, errors, warning_msg


def validate_g4_contract_to_project(
    contract: Contract,
    deliverables: List[ContractDeliverable],
    db: Optional[Session] = None
) -> Tuple[bool, List[str]]:
    """
    G4：合同 → 项目 验证
    付款节点与可交付物绑定
    SOW/验收标准/BOM初版/里程碑基线冻结
    """
    errors = []

    if not deliverables or len(deliverables) == 0:
        errors.append("合同交付物不能为空")
    else:
        required_deliverables = [d for d in deliverables if d.required_for_payment]
        if len(required_deliverables) == 0:
            errors.append("至少需要一个付款必需的交付物")

        incomplete_deliverables = [d for d in deliverables if not d.deliverable_name or len(d.deliverable_name.strip()) == 0]
        if incomplete_deliverables:
            errors.append(f"有{len(incomplete_deliverables)}个交付物名称不完整")

    if not contract.contract_amount or contract.contract_amount <= 0:
        errors.append("合同金额不能为空或必须大于0")

    if not contract.acceptance_summary:
        errors.append("验收摘要不能为空，请补充验收标准")

    if not contract.payment_terms_summary:
        errors.append("付款条款摘要不能为空，请补充付款节点信息")

    if contract.status != "SIGNED":
        errors.append("只有已签订的合同才能生成项目")

    if contract.project_id:
        errors.append("合同已关联项目，不能重复生成")

    if db is not None:
        freeze_checks = []

        from app.models.project import ProjectDocument
        sow_documents = db.query(ProjectDocument).filter(
            ProjectDocument.contract_id == contract.id,
            ProjectDocument.document_type == "SOW"
        ).count()

        if sow_documents == 0:
            freeze_checks.append("SOW文档未上传")
        else:
            freeze_checks.append(f"SOW文档已上传({sow_documents}份)")

        if contract.acceptance_summary:
            freeze_checks.append("验收标准已填写")
        else:
            freeze_checks.append("验收标准未确认")

        from app.models.material import BomHeader
        bom_count = db.query(BomHeader).filter(
            BomHeader.contract_id == contract.id,
            BomHeader.version == "1.0"
        ).count()

        if bom_count == 0:
            freeze_checks.append("BOM初版未创建")
        else:
            freeze_checks.append(f"BOM初版已创建({bom_count}个)")

        milestone_count = 0
        if hasattr(contract, 'deliverables') and contract.deliverables:
            from app.models.project import ProjectMilestone
            milestone_count = db.query(ProjectMilestone).filter(
                ProjectMilestone.contract_id == contract.id
            ).count()

        if milestone_count == 0:
            freeze_checks.append("里程碑基线未确定")
        else:
            freeze_checks.append(f"里程碑已设置({milestone_count}个)")

        missing_items = [item for item in freeze_checks if "未" in item]
        if missing_items:
            freeze_checks.append(f"警告：以下项目未完成 - {', '.join(missing_items)}")

    return len(errors) == 0, errors
