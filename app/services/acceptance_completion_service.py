# -*- coding: utf-8 -*-
"""
验收完成服务
处理验收完成后的各种联动逻辑
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.acceptance import AcceptanceIssue, AcceptanceOrder, AcceptanceOrderItem
from app.models.project import Machine, Project

logger = logging.getLogger(__name__)


def validate_required_check_items(
    db: Session,
    order_id: int
) -> None:
    """
    验证所有必检项是否已完成检查

    Raises:
        HTTPException: 如果还有未完成的必检项
    """
    from fastapi import HTTPException

    pending_items = db.query(AcceptanceOrderItem).filter(
        AcceptanceOrderItem.order_id == order_id,
        AcceptanceOrderItem.is_required == True,
        AcceptanceOrderItem.result_status == "PENDING"
    ).count()

    if pending_items > 0:
        raise HTTPException(status_code=400, detail=f"还有 {pending_items} 个必检项未完成检查")


def update_acceptance_order_status(
    db: Session,
    order: AcceptanceOrder,
    overall_result: str,
    conclusion: Optional[str],
    conditions: Optional[str]
) -> None:
    """
    更新验收单状态

    Args:
        db: 数据库会话
        order: 验收单对象
        overall_result: 验收结果
        conclusion: 验收结论
        conditions: 验收条件
    """
    order.status = "COMPLETED"
    order.actual_end_date = datetime.now()
    order.overall_result = overall_result
    order.conclusion = conclusion
    order.conditions = conditions

    db.add(order)
    db.flush()


def trigger_invoice_on_acceptance(
    db: Session,
    order_id: int,
    auto_trigger: bool
) -> Dict[str, Any]:
    """
    验收通过后自动触发开票

    Returns:
        Dict[str, Any]: 开票结果
    """
    if not auto_trigger:
        return {"success": False, "message": "未启用自动开票"}

    try:
        import os

        from app.services.invoice_auto_service import InvoiceAutoService

        # 默认创建发票申请（不直接创建发票）
        auto_create_invoice = os.getenv("AUTO_CREATE_INVOICE_ON_ACCEPTANCE", "false").lower() == "true"

        service = InvoiceAutoService(db)
        result = service.check_and_create_invoice_request(
            acceptance_order_id=order_id,
            auto_create=auto_create_invoice
        )

        if result.get("success") and result.get("invoice_requests"):
            logger.info(
                f"验收通过，已自动创建 {len(result.get('invoice_requests', []))} "
                f"个发票{'申请' if not auto_create_invoice else ''}"
            )

        return result
    except Exception as e:
        logger.error(f"自动触发开票失败: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def handle_acceptance_status_transition(
    db: Session,
    order: AcceptanceOrder,
    overall_result: str
) -> None:
    """
    处理验收状态联动（FAT/SAT/FINAL）

    Args:
        db: 数据库会话
        order: 验收单对象
        overall_result: 验收结果
    """
    try:
        from app.services.status_transition_service import StatusTransitionService
        transition_service = StatusTransitionService(db)

        # 根据验收类型和结果更新项目状态
        if order.acceptance_type == "FAT":
            if overall_result == "PASSED":
                transition_service.handle_fat_passed(order.project_id, order.machine_id)
                logger.info(f"FAT验收通过，项目状态已更新")
            elif overall_result == "FAILED":
                issues = db.query(AcceptanceIssue).filter(
                    AcceptanceIssue.order_id == order.id,
                    AcceptanceIssue.status != "RESOLVED"
                ).all()
                issue_descriptions = [issue.issue_description for issue in issues if issue.issue_description]
                transition_service.handle_fat_failed(order.project_id, order.machine_id, issue_descriptions)
                logger.info(f"FAT验收不通过，项目状态已更新")

        elif order.acceptance_type == "SAT":
            if overall_result == "PASSED":
                transition_service.handle_sat_passed(order.project_id, order.machine_id)
                logger.info(f"SAT验收通过，项目状态已更新")
            elif overall_result == "FAILED":
                issues = db.query(AcceptanceIssue).filter(
                    AcceptanceIssue.order_id == order.id,
                    AcceptanceIssue.status != "RESOLVED"
                ).all()
                issue_descriptions = [issue.issue_description for issue in issues if issue.issue_description]
                transition_service.handle_sat_failed(order.project_id, order.machine_id, issue_descriptions)
                logger.info(f"SAT验收不通过，项目状态已更新")

        elif order.acceptance_type == "FINAL":
            if overall_result == "PASSED":
                transition_service.handle_final_acceptance_passed(order.project_id)
                logger.info(f"终验收通过，项目可推进至S9")
    except Exception as e:
        logger.error(f"验收状态联动处理失败: {str(e)}", exc_info=True)


def handle_progress_integration(
    db: Session,
    order: AcceptanceOrder,
    overall_result: str
) -> Dict[str, Any]:
    """
    处理验收结果对进度跟踪的影响

    Returns:
        Dict[str, Any]: 处理结果
    """
    try:
        from app.services.progress_integration_service import ProgressIntegrationService
        integration_service = ProgressIntegrationService(db)

        if overall_result == "FAILED":
            blocked_milestones = integration_service.handle_acceptance_failed(order)
            logger.info(f"验收失败，已阻塞 {len(blocked_milestones)} 个里程碑")
            return {"blocked_milestones": blocked_milestones}
        elif overall_result == "PASSED":
            unblocked_milestones = integration_service.handle_acceptance_passed(order)
            logger.info(f"验收通过，已解除 {len(unblocked_milestones)} 个里程碑阻塞")
            return {"unblocked_milestones": unblocked_milestones}
    except Exception as e:
        logger.error(f"验收联动处理失败: {str(e)}", exc_info=True)
        return {"error": str(e)}

    return {}


def check_auto_stage_transition_after_acceptance(
    db: Session,
    order: AcceptanceOrder,
    overall_result: str
) -> Dict[str, Any]:
    """
    验收通过后自动触发阶段流转检查

    Returns:
        Dict[str, Any]: 流转结果
    """
    if overall_result != "PASSED" or not order.project_id:
        return {}

    try:
        from app.services.status_transition_service import StatusTransitionService
        transition_service = StatusTransitionService(db)

        project = db.query(Project).filter(Project.id == order.project_id).first()
        if not project:
            return {}

        # 检查是否可以自动推进阶段
        if order.acceptance_type == "FAT" and project.stage == "S7":
            auto_transition_result = transition_service.check_auto_stage_transition(
                order.project_id,
                auto_advance=True
            )
            if auto_transition_result.get("auto_advanced"):
                logger.info(f"FAT验收通过后自动推进项目 {order.project_id} 至 S8 阶段")
                return auto_transition_result

        elif order.acceptance_type in ["SAT", "FINAL"] and project.stage == "S8":
            auto_transition_result = transition_service.check_auto_stage_transition(
                order.project_id,
                auto_advance=True
            )
            if auto_transition_result.get("auto_advanced"):
                logger.info(f"终验收通过后自动推进项目 {order.project_id} 至 S9 阶段")
                return auto_transition_result
    except Exception as e:
        logger.warning(f"验收通过后自动阶段流转失败：{str(e)}", exc_info=True)
        return {"error": str(e)}

    return {}


def trigger_warranty_period(
    db: Session,
    order: AcceptanceOrder,
    overall_result: str
) -> None:
    """
    终验收通过后自动触发质保期

    Args:
        db: 数据库会话
        order: 验收单对象
        overall_result: 验收结果
    """
    if overall_result != "PASSED" or order.acceptance_type != "FINAL":
        return

    try:
        project = db.query(Project).filter(Project.id == order.project_id).first()
        if not project:
            return

        # 更新项目阶段为S9（质保结项）
        project.stage = "S9"
        project.actual_end_date = date.today()
        db.add(project)

        # 更新所有设备状态
        machines = db.query(Machine).filter(Machine.project_id == order.project_id).all()
        for machine in machines:
            machine.stage = "S9"
            machine.status = "COMPLETED"
            db.add(machine)

        logger.info(f"终验收通过，项目 {project.project_code} 已进入质保期（S9阶段）")
    except Exception as e:
        logger.error(f"终验收后质保期触发失败: {str(e)}", exc_info=True)


def trigger_bonus_calculation(
    db: Session,
    order: AcceptanceOrder,
    overall_result: str
) -> None:
    """
    验收通过后自动触发奖金计算

    Args:
        db: 数据库会话
        order: 验收单对象
        overall_result: 验收结果
    """
    if overall_result != "PASSED":
        return

    try:
        from app.services.bonus import BonusCalculator
        calculator = BonusCalculator(db)

        project = db.query(Project).filter(Project.id == order.project_id).first()
        if project:
            calculator.trigger_acceptance_bonus_calculation(project, order)
    except Exception as e:
        logger.error(f"验收后奖金计算失败: {str(e)}", exc_info=True)
