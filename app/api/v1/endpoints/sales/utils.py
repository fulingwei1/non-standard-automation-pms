# -*- coding: utf-8 -*-
"""
销售模块公共工具函数

包含编码生成、阶段门验证、公共辅助函数等
"""

import calendar
from typing import Optional, List, Tuple, Dict
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from fastapi import HTTPException
from app.models.user import User, UserRole, Role
from app.models.sales import (
    Lead, Opportunity, OpportunityRequirement, Quote, QuoteVersion, QuoteItem,
    Contract, ContractDeliverable, ContractAmendment, Invoice
)
from app.models.enums import (
    AssessmentSourceTypeEnum, AssessmentStatusEnum, AssessmentDecisionEnum
)
from app.core import security
from app.core.config import settings


def get_entity_creator_id(entity) -> Optional[int]:
    """Safely fetch created_by if the ORM model defines it."""
    return getattr(entity, "created_by", None)


def normalize_date_range(
    start_date_value: Optional[date],
    end_date_value: Optional[date],
) -> Tuple[date, date]:
    """Normalize and validate date range."""
    today = date.today()
    normalized_start = start_date_value or date(today.year, today.month, 1)

    if end_date_value:
        normalized_end = end_date_value
    else:
        if normalized_start.month == 12:
            normalized_end = date(normalized_start.year, 12, 31)
        else:
            normalized_end = date(normalized_start.year, normalized_start.month + 1, 1) - timedelta(days=1)

    if normalized_start > normalized_end:
        raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")

    return normalized_start, normalized_end


def get_user_role_code(db: Session, user: User) -> str:
    """获取用户的角色代码（返回第一个角色的代码）"""
    user_roles = db.query(UserRole).filter(UserRole.user_id == user.id).all()
    if user_roles and user_roles[0].role:
        return user_roles[0].role.role_code
    return "USER"


def get_user_role_name(db: Session, user: User) -> str:
    """获取用户的角色名称（返回第一个角色的名称）"""
    user_roles = db.query(UserRole).filter(UserRole.user_id == user.id).all()
    if user_roles and user_roles[0].role:
        return user_roles[0].role.role_name
    return "普通用户"


def get_visible_sales_users(
    db: Session,
    current_user: User,
    department_id: Optional[int],
    region_keyword: Optional[str],
) -> List[User]:
    """根据角色、部门和区域过滤可见的销售用户"""
    user_roles = db.query(UserRole).filter(UserRole.user_id == current_user.id).all()
    user_role_codes = [ur.role.role_code for ur in user_roles if ur.role]
    user_role_codes_lower = [rc.lower() for rc in user_role_codes]

    is_sales_director = 'SALES_DIR' in user_role_codes
    is_sales_manager = 'SALES_MANAGER' in user_role_codes

    query = db.query(User).filter(User.is_active == True)

    if is_sales_director:
        sales_role_codes = ['SALES', 'SALES_DIR', 'SALES_MANAGER', 'SA']
        sales_user_ids = (
            db.query(UserRole.user_id)
            .join(Role, Role.id == UserRole.role_id)
            .filter(Role.role_code.in_(sales_role_codes))
            .distinct()
            .all()
        )
        sales_user_ids = [uid for (uid,) in sales_user_ids]
        return query.filter(User.id.in_(sales_user_ids)).all()
    elif is_sales_manager:
        dept_id = getattr(current_user, 'department_id', None)
        if dept_id:
            return query.filter(User.department_id == dept_id).all()
        else:
            return [current_user]
    else:
        return [current_user]


def build_department_name_map(db: Session, users: List[User]) -> Dict[str, str]:
    """批量获取部门名称，减少数据库查询"""
    dept_names = {user.department for user in users if user.department}
    return {name: name for name in dept_names}


def shift_month(year: int, month: int, delta: int) -> Tuple[int, int]:
    """根据delta偏移月数"""
    total_months = year * 12 + (month - 1) + delta
    new_year = total_months // 12
    new_month = total_months % 12 + 1
    return new_year, new_month


def generate_trend_buckets(period: str, count: int) -> List[dict]:
    """根据周期生成统计区间"""
    today = date.today()
    buckets: List[dict] = []
    period = period.upper()

    if period == "QUARTER":
        period = "QUARTER"
    elif period == "YEAR":
        period = "YEAR"
    else:
        period = "MONTH"

    if period == "MONTH":
        for offset in range(count - 1, -1, -1):
            target_year, target_month = shift_month(today.year, today.month, -offset)
            start = date(target_year, target_month, 1)
            _, last_day = calendar.monthrange(target_year, target_month)
            end = date(target_year, target_month, last_day)
            label = f"{target_year}-{target_month:02d}"
            buckets.append({
                "label": label,
                "target_label": label,
                "start": start,
                "end": end,
            })
    elif period == "QUARTER":
        current_quarter = (today.month - 1) // 3 + 1
        for offset in range(count - 1, -1, -1):
            quarter_delta = -offset
            total_quarters = (today.year * 4 + (current_quarter - 1)) + quarter_delta
            target_year = total_quarters // 4
            target_quarter = total_quarters % 4 + 1
            start_month = (target_quarter - 1) * 3 + 1
            start = date(target_year, start_month, 1)
            end_month = start_month + 2
            _, last_day = calendar.monthrange(target_year, end_month)
            end = date(target_year, end_month, last_day)
            label = f"{target_year}-Q{target_quarter}"
            buckets.append({
                "label": label,
                "target_label": label,
                "start": start,
                "end": end,
            })
    else:  # YEAR
        for offset in range(count - 1, -1, -1):
            target_year = today.year - offset
            start = date(target_year, 1, 1)
            end = date(target_year, 12, 31)
            label = str(target_year)
            buckets.append({
                "label": label,
                "target_label": label,
                "start": start,
                "end": end,
            })

    return buckets


def calculate_growth(current: float, previous: Optional[float]) -> float:
    """计算增长率"""
    if previous is None or previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 2)


def get_previous_range(start_date_value: date, end_date_value: date) -> Tuple[date, date]:
    """根据当前区间计算上一对等区间"""
    delta_days = (end_date_value - start_date_value).days + 1
    prev_end = start_date_value - timedelta(days=1)
    prev_start = prev_end - timedelta(days=delta_days - 1)
    return prev_start, prev_end


# ==================== 阶段门验证函数 ====================


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
            from app.services.delivery_validation_service import delivery_validation_service
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


# ==================== 编码生成函数 ====================


def generate_lead_code(db: Session) -> str:
    """生成线索编码：L2507-001"""
    from app.utils.number_generator import generate_monthly_no
    from app.models.sales import Lead
    
    return generate_monthly_no(
        db=db,
        model_class=Lead,
        no_field='lead_code',
        prefix='L',
        separator='-',
        seq_length=3
    )


def generate_opportunity_code(db: Session) -> str:
    """生成商机编码：O2507-001"""
    from app.utils.number_generator import generate_monthly_no
    from app.models.sales import Opportunity
    
    return generate_monthly_no(
        db=db,
        model_class=Opportunity,
        no_field='opp_code',
        prefix='O',
        separator='-',
        seq_length=3
    )


def generate_quote_code(db: Session) -> str:
    """生成报价编码：Q2507-001"""
    from app.utils.number_generator import generate_monthly_no
    from app.models.sales import Quote
    
    return generate_monthly_no(
        db=db,
        model_class=Quote,
        no_field='quote_code',
        prefix='Q',
        separator='-',
        seq_length=3
    )


def generate_contract_code(db: Session) -> str:
    """生成合同编码：HT2507-001"""
    from app.utils.number_generator import generate_monthly_no
    from app.models.sales import Contract
    
    return generate_monthly_no(
        db=db,
        model_class=Contract,
        no_field='contract_code',
        prefix='HT',
        separator='-',
        seq_length=3
    )


def generate_amendment_no(db: Session, contract_code: str) -> str:
    """生成合同变更编号：{合同编码}-BG{序号}"""
    from app.models.sales import ContractAmendment
    
    prefix = f"{contract_code}-BG"
    count = db.query(ContractAmendment).filter(
        ContractAmendment.amendment_no.like(f"{prefix}%")
    ).count()
    seq = count + 1
    return f"{prefix}{seq:03d}"


def generate_invoice_code(db: Session) -> str:
    """生成发票编码：INV-yymmdd-xxx"""
    from app.utils.number_generator import generate_sequential_no
    from app.models.sales import Invoice
    
    return generate_sequential_no(
        db=db,
        model_class=Invoice,
        no_field='invoice_code',
        prefix='INV',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )
