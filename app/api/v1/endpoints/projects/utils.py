# -*- coding: utf-8 -*-
"""
项目模块公共工具函数

包含编码生成、序列化函数、阶段门校验等公共辅助函数
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from fastapi import HTTPException
from app.models.user import User
from app.models.project import (
    Project, Machine, ProjectStatusLog, ProjectPaymentPlan,
    ProjectTemplate, ProjectTemplateVersion
)
from app.models.business_support import InvoiceRequest
from app.core.config import settings


def _sync_invoice_request_receipt_status(db: Session, plan: ProjectPaymentPlan) -> None:
    """根据收款计划实收金额同步开票申请回款状态"""
    invoice_requests = db.query(InvoiceRequest).filter(
        InvoiceRequest.payment_plan_id == plan.id,
        InvoiceRequest.status == "APPROVED"
    ).all()
    if not invoice_requests:
        return

    planned_amount = plan.planned_amount or Decimal("0")
    actual_amount = plan.actual_amount or Decimal("0")

    if planned_amount and actual_amount >= planned_amount:
        receipt_status = "PAID"
    elif actual_amount > 0:
        receipt_status = "PARTIAL"
    else:
        receipt_status = "UNPAID"

    for invoice_request in invoice_requests:
        if invoice_request.receipt_status != receipt_status:
            invoice_request.receipt_status = receipt_status
            invoice_request.receipt_updated_at = datetime.utcnow()
            db.add(invoice_request)


def _serialize_project_status_log(log: ProjectStatusLog) -> Dict[str, Any]:
    """将ProjectStatusLog对象序列化为字典"""
    return {
        "id": log.id,
        "project_id": log.project_id,
        "old_stage": log.old_stage,
        "new_stage": log.new_stage,
        "old_status": log.old_status,
        "new_status": log.new_status,
        "old_health": log.old_health,
        "new_health": log.new_health,
        "change_type": log.change_type,
        "change_reason": log.change_reason,
        "changed_by": log.changed_by,
        "changed_at": log.changed_at.isoformat() if log.changed_at else None,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


def generate_review_no(db: Session) -> str:
    """生成复盘编号：REVIEW-YYYYMMDD-XXX"""
    from app.models.project_review import ProjectReview
    today = date.today().strftime("%Y%m%d")
    # 查询当天已有的复盘报告数量
    count = db.query(ProjectReview).filter(
        ProjectReview.review_no.like(f"REVIEW-{today}-%")
    ).count()
    seq = count + 1
    return f"REVIEW-{today}-{seq:03d}"


def _sync_to_erp_system(project, erp_order_no: Optional[str] = None) -> dict:
    """
    同步项目数据到ERP系统

    这是一个可扩展的ERP接口框架。实际使用时需要根据具体的ERP系统
    （如SAP、Oracle、金蝶、用友等）实现相应的API调用。

    Args:
        project: 项目对象
        erp_order_no: ERP订单号（可选）

    Returns:
        dict: 同步结果 {'success': bool, 'erp_order_no': str, 'error': str}
    """
    from app.core.config import settings

    # 检查是否配置了ERP接口
    erp_api_url = getattr(settings, 'ERP_API_URL', None)
    erp_api_key = getattr(settings, 'ERP_API_KEY', None)

    # 如果没有配置ERP接口，返回模拟成功
    if not erp_api_url:
        # 生成模拟ERP订单号
        generated_order_no = erp_order_no or f"ERP-{project.project_code}"
        return {
            'success': True,
            'erp_order_no': generated_order_no,
            'message': 'ERP接口未配置，使用模拟同步'
        }

    # 实际ERP集成逻辑（待实现）
    return {
        'success': True,
        'erp_order_no': erp_order_no or f"ERP-{project.project_code}",
        'message': 'ERP同步功能框架已就绪，请配置实际ERP接口'
    }


# ==================== 阶段门校验函数 ====================

def check_gate_s1_to_s2(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """G1: S1→S2 阶段门校验 - 基本信息完整、客户信息齐全"""
    missing = []

    # 基本信息检查
    if not project.project_name:
        missing.append("项目名称不能为空")
    if not project.customer_id:
        missing.append("客户信息不能为空")

    # 客户联系信息检查
    if not project.customer_name:
        missing.append("客户名称不能为空")
    if not project.customer_contact:
        missing.append("客户联系人不能为空")
    if not project.customer_phone:
        missing.append("客户联系电话不能为空")

    # 需求信息检查
    if not project.requirements:
        missing.append("需求采集表未填写")

    return (len(missing) == 0, missing)


def check_gate_s2_to_s3(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """G2: S2→S3 阶段门校验 - 需求规格书已确认、客户签字"""
    missing = []

    # 检查需求规格书文档
    from app.models.project import ProjectDocument
    spec_docs = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project.id,
        ProjectDocument.doc_type.in_(["REQUIREMENT", "SPECIFICATION"]),
        ProjectDocument.status == "APPROVED"
    ).count()

    if spec_docs == 0:
        missing.append("需求规格书未确认（请上传并确认需求规格书）")

    # 检查验收标准
    if not project.requirements or "验收标准" not in project.requirements:
        missing.append("验收标准未明确（请在需求中明确验收标准）")

    return (len(missing) == 0, missing)


def check_gate_s3_to_s4(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """
    G3: S3→S4 阶段门校验 - 立项评审通过、合同签订

    Issue 1.3: 细化校验条件
    """
    missing = []

    # 检查合同签订（如果配置了需要合同）
    from app.core.config import settings
    if getattr(settings, 'PROJECT_REQUIRE_CONTRACT', True):
        if not project.contract_id and not project.contract_no:
            missing.append("合同未签订（请关联合同或填写合同编号）")

        # 如果关联了合同，检查合同状态
        if project.contract_id:
            from app.models.sales import Contract
            contract = db.query(Contract).filter(Contract.id == project.contract_id).first()
            if contract and contract.status != "SIGNED":
                missing.append(f"合同状态为{contract.status}，需为已签订(SIGNED)")

    # 检查立项评审通过
    # 方式1：检查评审记录
    from app.models.technical_review import TechnicalReview
    approval_review = db.query(TechnicalReview).filter(
        TechnicalReview.project_id == project.id,
        TechnicalReview.review_type.in_(["PROPOSAL", "APPROVAL", "PROJECT_APPROVAL"]),
        TechnicalReview.status == "COMPLETED"
    ).first()

    if not approval_review:
        # 方式2：检查项目状态是否已过立项审批
        if project.status not in ["ST08", "ST09", "ST10", "ST11", "ST12", "ST13", "ST14", "ST15",
                                   "ST16", "ST17", "ST18", "ST19", "ST20", "ST21", "ST22", "ST23",
                                   "ST24", "ST25", "ST26", "ST27", "ST28", "ST29", "ST30"]:
            missing.append("立项评审未通过（请完成立项评审）")

    return (len(missing) == 0, missing)


def check_gate_s4_to_s5(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """
    G4: S4→S5 阶段门校验 - 方案评审通过、BOM发布

    Issue 1.3: 细化校验条件
    """
    missing = []

    # 检查方案评审已通过（有评审记录）
    from app.models.technical_review import TechnicalReview
    scheme_review = db.query(TechnicalReview).filter(
        TechnicalReview.project_id == project.id,
        TechnicalReview.review_type.in_(["DDR", "SCHEME", "DESIGN"]),
        TechnicalReview.status == "COMPLETED"
    ).first()

    if not scheme_review:
        from app.models.project import ProjectDocument
        design_docs = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project.id,
            ProjectDocument.doc_type.in_(["DESIGN", "SCHEME"]),
            ProjectDocument.status == "APPROVED"
        ).count()

        if design_docs == 0:
            missing.append("方案评审未通过（请完成方案评审或上传已评审通过的设计文档）")

    # 检查BOM已发布
    from app.models.material import BomHeader
    released_boms = db.query(BomHeader).filter(
        BomHeader.project_id == project.id,
        BomHeader.status == "RELEASED"
    ).all()

    if not released_boms:
        missing.append("BOM未发布（请发布至少一个BOM）")
    else:
        # 检查每个机台是否有BOM
        machines = db.query(Machine).filter(Machine.project_id == project.id).all()
        if machines:
            for machine in machines:
                machine_bom = db.query(BomHeader).filter(
                    BomHeader.machine_id == machine.id,
                    BomHeader.status == "RELEASED"
                ).first()
                if not machine_bom:
                    missing.append(f"机台 {machine.machine_code} 的BOM未发布")

    # 检查关键设计文档已上传
    from app.models.project import ProjectDocument
    key_doc_types = ["DESIGN", "SCHEME", "DRAWING", "ELECTRICAL", "SOFTWARE"]
    key_docs = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project.id,
        ProjectDocument.doc_type.in_(key_doc_types),
        ProjectDocument.status == "APPROVED"
    ).count()

    if key_docs == 0:
        missing.append("关键设计文档未上传（请上传机械/电气/软件设计文档）")

    return (len(missing) == 0, missing)


def check_gate_s5_to_s6(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """G5: S5→S6 阶段门校验 - 关键物料齐套率≥80%"""
    missing = []

    machines = db.query(Machine).filter(Machine.project_id == project.id).all()

    if not machines:
        missing.append("项目下没有机台")
        return (False, missing)

    from app.api.v1.endpoints.kit_rate import calculate_kit_rate
    from app.models.material import BomHeader, BomItem

    for machine in machines:
        bom = db.query(BomHeader).filter(
            BomHeader.machine_id == machine.id,
            BomHeader.status == "RELEASED"
        ).first()

        if not bom:
            missing.append(f"机台 {machine.machine_code} 的BOM未发布")
            continue

        bom_items = db.query(BomItem).filter(BomItem.bom_id == bom.id).all()

        if not bom_items:
            continue

        kit_result = calculate_kit_rate(db, bom_items, calculate_by="quantity")
        kit_rate = kit_result.get("kit_rate", 0)

        if kit_rate < 80:
            missing.append(f"机台 {machine.machine_code} 物料齐套率 {kit_rate:.1f}%，需≥80%")

        # 检查关键物料已到货
        for item in bom_items:
            material = item.material
            if material and (material.is_key_material or material.material_category in ["关键件", "核心件", "KEY"]):
                available_qty = Decimal(str(material.current_stock or 0)) + Decimal(str(item.received_qty or 0))
                required_qty = Decimal(str(item.quantity or 0))

                if available_qty < required_qty:
                    missing.append(f"关键物料 {material.material_name} 未到货（需求：{required_qty}，可用：{available_qty}）")

        # 检查外协件已完成
        from app.models.outsourcing import OutsourcingOrder
        outsourcing_orders = db.query(OutsourcingOrder).filter(
            OutsourcingOrder.project_id == project.id,
            OutsourcingOrder.machine_id == machine.id if machine else None
        ).all()

        if outsourcing_orders:
            for order in outsourcing_orders:
                if order.status not in ["COMPLETED", "CLOSED"]:
                    total_ordered = sum(float(item.order_quantity or 0) for item in order.items)
                    total_delivered = sum(float(item.delivered_quantity or 0) for item in order.items)

                    if total_delivered < total_ordered:
                        missing.append(f"外协订单 {order.order_no} 未完成（已交付：{total_delivered}，需求：{total_ordered}）")

    return (len(missing) == 0, missing)


def check_gate_s6_to_s7(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """
    G6: S6→S7 阶段门校验 - 装配完成、联调通过
    """
    missing = []

    machines = db.query(Machine).filter(Machine.project_id == project.id).all()

    if not machines:
        missing.append("项目下没有机台")
        return (False, missing)

    for machine in machines:
        if machine.progress_pct < 100:
            missing.append(f"机台 {machine.machine_code} 装配未完成（进度：{machine.progress_pct}%，需达到100%）")

        if machine.status not in ["ASSEMBLED", "READY", "COMPLETED"]:
            missing.append(f"机台 {machine.machine_code} 状态未达到装配完成（当前状态：{machine.status}）")

    # 检查联调已通过
    from app.models.project import ProjectDocument
    debug_docs = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project.id,
        ProjectDocument.doc_type.in_(["DEBUG", "TEST", "COMMISSIONING"]),
        ProjectDocument.status == "APPROVED"
    ).count()

    if debug_docs == 0:
        missing.append("联调测试报告未提交或未通过（请上传联调报告并标记为已确认）")

    # 检查技术问题已解决
    from app.models.issue import Issue
    blocking_issues = db.query(Issue).filter(
        Issue.project_id == project.id,
        Issue.is_blocking == True,
        Issue.status.notin_(["RESOLVED", "CLOSED"])
    ).count()

    if blocking_issues > 0:
        missing.append(f"存在 {blocking_issues} 个未解决的阻塞问题（请先解决所有阻塞问题）")

    # 检查技术评审问题
    from app.models.technical_review import ReviewIssue, TechnicalReview
    unresolved_review_issues = db.query(ReviewIssue).join(
        TechnicalReview, ReviewIssue.review_id == TechnicalReview.id
    ).filter(
        TechnicalReview.project_id == project.id,
        ReviewIssue.status.notin_(["RESOLVED", "VERIFIED", "CLOSED"]),
        ReviewIssue.issue_level.in_(["A", "B"])
    ).count()

    if unresolved_review_issues > 0:
        missing.append(f"存在 {unresolved_review_issues} 个未解决的评审问题（A/B级问题必须解决）")

    return (len(missing) == 0, missing)


def check_gate_s7_to_s8(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """
    G7: S7→S8 阶段门校验 - FAT验收通过
    """
    missing = []

    from app.models.acceptance import AcceptanceOrder
    fat_orders = db.query(AcceptanceOrder).filter(
        AcceptanceOrder.project_id == project.id,
        AcceptanceOrder.acceptance_type == "FAT",
        AcceptanceOrder.status == "COMPLETED",
        AcceptanceOrder.overall_result == "PASSED"
    ).all()

    if not fat_orders:
        fat_orders_failed = db.query(AcceptanceOrder).filter(
            AcceptanceOrder.project_id == project.id,
            AcceptanceOrder.acceptance_type == "FAT",
            AcceptanceOrder.status == "COMPLETED",
            AcceptanceOrder.overall_result == "FAILED"
        ).count()

        if fat_orders_failed > 0:
            missing.append("FAT验收不通过（请完成整改后重新验收）")
        else:
            missing.append("FAT验收未完成（请完成FAT验收流程）")
    else:
        from app.models.acceptance import AcceptanceReport
        fat_reports = db.query(AcceptanceReport).join(
            AcceptanceOrder, AcceptanceReport.order_id == AcceptanceOrder.id
        ).filter(
            AcceptanceOrder.project_id == project.id,
            AcceptanceOrder.acceptance_type == "FAT",
            AcceptanceOrder.status == "COMPLETED"
        ).count()

        if fat_reports == 0:
            missing.append("FAT报告未生成（请生成FAT验收报告）")

        from app.models.acceptance import AcceptanceIssue
        unresolved_issues = db.query(AcceptanceIssue).join(
            AcceptanceOrder, AcceptanceIssue.order_id == AcceptanceOrder.id
        ).filter(
            AcceptanceOrder.project_id == project.id,
            AcceptanceOrder.acceptance_type == "FAT",
            AcceptanceIssue.status.notin_(["RESOLVED", "CLOSED"])
        ).count()

        if unresolved_issues > 0:
            missing.append(f"存在 {unresolved_issues} 个未完成的FAT整改项（请完成所有整改项）")

    return (len(missing) == 0, missing)


def check_gate_s8_to_s9(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """
    G8: S8→S9 阶段门校验 - 终验收通过、回款达标
    """
    missing = []

    from app.models.acceptance import AcceptanceOrder
    final_orders = db.query(AcceptanceOrder).filter(
        AcceptanceOrder.project_id == project.id,
        AcceptanceOrder.acceptance_type == "FINAL",
        AcceptanceOrder.status == "COMPLETED",
        AcceptanceOrder.overall_result == "PASSED"
    ).all()

    if not final_orders:
        sat_orders = db.query(AcceptanceOrder).filter(
            AcceptanceOrder.project_id == project.id,
            AcceptanceOrder.acceptance_type == "SAT",
            AcceptanceOrder.status == "COMPLETED",
            AcceptanceOrder.overall_result == "PASSED"
        ).all()

        if not sat_orders:
            sat_failed = db.query(AcceptanceOrder).filter(
                AcceptanceOrder.project_id == project.id,
                AcceptanceOrder.acceptance_type == "SAT",
                AcceptanceOrder.status == "COMPLETED",
                AcceptanceOrder.overall_result == "FAILED"
            ).count()

            if sat_failed > 0:
                missing.append("SAT验收不通过（请完成整改后重新验收）")
            else:
                missing.append("终验收未完成（请完成SAT或终验收流程）")
        else:
            missing.append("终验收未完成（SAT已通过，请完成终验收）")

    # 检查回款达标
    payment_plans = db.query(ProjectPaymentPlan).filter(
        ProjectPaymentPlan.project_id == project.id
    ).all()

    if payment_plans:
        total_paid = sum(float(plan.actual_amount or 0) for plan in payment_plans if plan.status == "PAID")
        total_planned = sum(float(plan.planned_amount or 0) for plan in payment_plans)
        contract_amount = float(project.contract_amount or 0)

        base_amount = max(contract_amount, total_planned) if total_planned > 0 else contract_amount

        if base_amount > 0:
            payment_rate = (total_paid / base_amount) * 100
            if payment_rate < 80:
                missing.append(f"回款率 {payment_rate:.1f}%，需≥80%（已回款：{total_paid:.2f}，合同金额：{base_amount:.2f}）")
    else:
        if project.contract_amount and project.contract_amount > 0:
            missing.append("收款计划未设置（请设置收款计划）")

    # 检查设备交付状态
    if project.stage == "S8":
        machines = db.query(Machine).filter(Machine.project_id == project.id).all()
        if machines:
            for machine in machines:
                if machine.status not in ["DELIVERED", "COMPLETED"]:
                    missing.append(f"机台 {machine.machine_code} 未交付（当前状态：{machine.status}）")

    return (len(missing) == 0, missing)


def check_gate(db: Session, project: Project, target_stage: str) -> Tuple[bool, List[str]]:
    """
    阶段门准入校验

    Args:
        db: 数据库会话
        project: 项目对象
        target_stage: 目标阶段（S1-S9）

    Returns:
        (is_pass, missing_items): 是否通过，缺失项列表
    """
    gates = {
        'S2': check_gate_s1_to_s2,
        'S3': check_gate_s2_to_s3,
        'S4': check_gate_s3_to_s4,
        'S5': check_gate_s4_to_s5,
        'S6': check_gate_s5_to_s6,
        'S7': check_gate_s6_to_s7,
        'S8': check_gate_s7_to_s8,
        'S9': check_gate_s8_to_s9,
    }

    if target_stage in gates:
        return gates[target_stage](db, project)
    return (True, [])


def check_gate_detailed(db: Session, project: Project, target_stage: str) -> Dict[str, Any]:
    """
    Issue 1.4: 阶段门校验结果详细反馈

    返回结构化的校验结果，包含每个条件的检查状态
    """
    from app.schemas.project import GateCheckCondition

    gate_info = {
        'S2': ('G1', '需求进入→需求澄清', 'S1', 'S2'),
        'S3': ('G2', '需求澄清→立项评审', 'S2', 'S3'),
        'S4': ('G3', '立项评审→方案设计', 'S3', 'S4'),
        'S5': ('G4', '方案设计→采购制造', 'S4', 'S5'),
        'S6': ('G5', '采购制造→装配联调', 'S5', 'S6'),
        'S7': ('G6', '装配联调→出厂验收', 'S6', 'S7'),
        'S8': ('G7', '出厂验收→现场交付', 'S7', 'S8'),
        'S9': ('G8', '现场交付→质保结项', 'S8', 'S9'),
    }

    if target_stage not in gate_info:
        return {
            "gate_code": "",
            "gate_name": "",
            "from_stage": project.stage,
            "to_stage": target_stage,
            "passed": True,
            "total_conditions": 0,
            "passed_conditions": 0,
            "failed_conditions": 0,
            "conditions": [],
            "missing_items": [],
            "suggestions": [],
            "progress_pct": 100.0
        }

    gate_code, gate_name, from_stage, to_stage = gate_info[target_stage]

    # 执行校验
    gate_passed, missing_items = check_gate(db, project, target_stage)

    # 构建条件详情
    conditions = []
    passed_count = 0
    failed_count = 0

    # 根据阶段门类型构建条件列表
    if target_stage == 'S2':
        conditions = [
            GateCheckCondition(
                condition_name="客户信息齐全",
                condition_desc="客户名称、联系人、联系电话",
                status="PASSED" if project.customer_id and project.customer_name and project.customer_contact and project.customer_phone else "FAILED",
                message="客户信息已完整" if project.customer_id and project.customer_name else "请填写客户信息",
                action_url=f"/projects/{project.id}/edit",
                action_text="去填写"
            ),
            GateCheckCondition(
                condition_name="需求采集表完整",
                condition_desc="项目基本信息、需求描述",
                status="PASSED" if project.requirements else "FAILED",
                message="需求采集表已填写" if project.requirements else "请填写需求采集表",
                action_url=f"/projects/{project.id}/edit",
                action_text="去填写"
            ),
        ]
    elif target_stage == 'S3':
        from app.models.project import ProjectDocument
        spec_docs_count = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project.id,
            ProjectDocument.doc_type.in_(["REQUIREMENT", "SPECIFICATION"]),
            ProjectDocument.status == "APPROVED"
        ).count()

        conditions = [
            GateCheckCondition(
                condition_name="需求规格书已确认",
                condition_desc="需求规格书文档已上传并确认",
                status="PASSED" if spec_docs_count > 0 else "FAILED",
                message=f"已确认 {spec_docs_count} 个规格书文档" if spec_docs_count > 0 else "请上传并确认需求规格书",
                action_url=f"/projects/{project.id}/documents",
                action_text="去上传"
            ),
            GateCheckCondition(
                condition_name="验收标准明确",
                condition_desc="验收标准文档或记录",
                status="PASSED" if project.requirements and ("验收标准" in project.requirements or "acceptance" in project.requirements.lower()) else "FAILED",
                message="验收标准已明确" if project.requirements and ("验收标准" in project.requirements or "acceptance" in project.requirements.lower()) else "请明确验收标准",
                action_url=f"/projects/{project.id}/edit",
                action_text="去填写"
            ),
            GateCheckCondition(
                condition_name="客户已签字确认",
                condition_desc="需求规格书客户签字确认",
                status="PASSED" if project.status != "ST05" else "FAILED",
                message="客户已确认" if project.status != "ST05" else "待客户签字确认",
                action_url=f"/projects/{project.id}",
                action_text="查看详情"
            ),
        ]

    # 统计通过和失败的条件数
    for condition in conditions:
        if condition.status == "PASSED":
            passed_count += 1
        elif condition.status == "FAILED":
            failed_count += 1

    total_conditions = len(conditions) if conditions else len(missing_items)
    if total_conditions == 0:
        progress_pct = 100.0
    else:
        progress_pct = (passed_count / total_conditions) * 100

    # 生成建议操作
    suggestions = []
    if not gate_passed:
        suggestions.append(f"请完成以上 {failed_count} 项条件后重新尝试推进阶段")
        if missing_items:
            suggestions.append(f"缺失项：{', '.join(missing_items[:3])}{'...' if len(missing_items) > 3 else ''}")

    return {
        "gate_code": gate_code,
        "gate_name": gate_name,
        "from_stage": from_stage,
        "to_stage": to_stage,
        "passed": gate_passed,
        "total_conditions": total_conditions,
        "passed_conditions": passed_count,
        "failed_conditions": failed_count,
        "conditions": [c.model_dump() for c in conditions] if conditions else [],
        "missing_items": missing_items,
        "suggestions": suggestions,
        "progress_pct": round(progress_pct, 1)
    }
