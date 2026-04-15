# -*- coding: utf-8 -*-
"""
验收完成服务
处理验收完成后的各种联动逻辑
"""

import logging
from datetime import date, datetime
from importlib import import_module
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.acceptance import AcceptanceIssue, AcceptanceOrder, AcceptanceOrderItem
from app.models.project import Machine, Project

logger = logging.getLogger(__name__)


def _safe_import(module_path: str, attr_name: str):
    try:
        module = import_module(module_path)
        return getattr(module, attr_name, None)
    except Exception:
        return None


# 模块级别别名，兼容历史测试对本模块路径的 patch。
InvoiceAutoService = _safe_import("app.services.invoice_auto_service", "InvoiceAutoService")
StatusTransitionService = _safe_import(
    "app.services.status_transition_service", "StatusTransitionService"
)
ProgressIntegrationService = _safe_import(
    "app.services.progress_integration_service", "ProgressIntegrationService"
)
BonusCalculator = _safe_import("app.services.bonus", "BonusCalculator")

_DEFAULT_SERVICE_ALIASES = {
    "InvoiceAutoService": InvoiceAutoService,
    "StatusTransitionService": StatusTransitionService,
    "ProgressIntegrationService": ProgressIntegrationService,
    "BonusCalculator": BonusCalculator,
}


def _resolve_service(local_name: str, module_path: str, attr_name: str):
    current = globals().get(local_name)
    default = _DEFAULT_SERVICE_ALIASES.get(local_name)

    if current is not None and current is not default:
        return current

    resolved = _safe_import(module_path, attr_name)
    if resolved is not None:
        return resolved

    return current


def validate_required_check_items(db: Session, order_id: int) -> None:
    """
    验证所有必检项是否已完成检查

    Raises:
        HTTPException: 如果还有未完成的必检项
    """
    from fastapi import HTTPException

    pending_items = (
        db.query(AcceptanceOrderItem)
        .filter(
            AcceptanceOrderItem.order_id == order_id,
            AcceptanceOrderItem.is_required,
            AcceptanceOrderItem.result_status == "PENDING",
        )
        .count()
    )

    if pending_items > 0:
        raise HTTPException(status_code=400, detail=f"还有 {pending_items} 个必检项未完成检查")


def update_acceptance_order_status(
    db: Session,
    order: AcceptanceOrder,
    overall_result: str,
    conclusion: Optional[str],
    conditions: Optional[str],
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


def trigger_invoice_on_acceptance(db: Session, order_id: int, auto_trigger: bool) -> Dict[str, Any]:
    """
    验收通过后自动触发开票

    Returns:
        Dict[str, Any]: 开票结果
    """
    if not auto_trigger:
        return {"success": False, "message": "未启用自动开票"}

    try:
        import os

        service_cls = _resolve_service(
            "InvoiceAutoService",
            "app.services.invoice_auto_service",
            "InvoiceAutoService",
        )
        if service_cls is None:
            raise ImportError("InvoiceAutoService is unavailable")

        # 默认创建发票申请（不直接创建发票）
        auto_create_invoice = (
            os.getenv("AUTO_CREATE_INVOICE_ON_ACCEPTANCE", "false").lower() == "true"
        )

        service = service_cls(db)
        result = service.check_and_create_invoice_request(
            acceptance_order_id=order_id, auto_create=auto_create_invoice
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
    db: Session, order: AcceptanceOrder, overall_result: str
) -> None:
    """
    处理验收状态联动（FAT/SAT/FINAL）

    Args:
        db: 数据库会话
        order: 验收单对象
        overall_result: 验收结果
    """
    try:
        service_cls = _resolve_service(
            "StatusTransitionService",
            "app.services.status_transition_service",
            "StatusTransitionService",
        )
        if service_cls is None:
            raise ImportError("StatusTransitionService is unavailable")

        transition_service = service_cls(db)

        def _collect_issue_descriptions() -> list[str]:
            issues = (
                db.query(AcceptanceIssue)
                .filter(AcceptanceIssue.order_id == order.id, AcceptanceIssue.status != "RESOLVED")
                .all()
            )
            descriptions = []
            for issue in issues:
                description = (
                    getattr(issue, "issue_description", None)
                    or getattr(issue, "description", None)
                    or getattr(issue, "title", None)
                )
                if description:
                    descriptions.append(description)
            return descriptions

        # 根据验收类型和结果更新项目状态
        if order.acceptance_type == "FAT":
            if overall_result == "PASSED":
                transition_service.handle_fat_passed(order.project_id, order.machine_id)
                logger.info("FAT验收通过，项目状态已更新")
            elif overall_result == "FAILED":
                transition_service.handle_fat_failed(
                    order.project_id, order.machine_id, _collect_issue_descriptions()
                )
                logger.info("FAT验收不通过，项目状态已更新")

        elif order.acceptance_type == "SAT":
            if overall_result == "PASSED":
                transition_service.handle_sat_passed(order.project_id, order.machine_id)
                logger.info("SAT验收通过，项目状态已更新")
            elif overall_result == "FAILED":
                transition_service.handle_sat_failed(
                    order.project_id, order.machine_id, _collect_issue_descriptions()
                )
                logger.info("SAT验收不通过，项目状态已更新")

        elif order.acceptance_type == "FINAL":
            if overall_result == "PASSED":
                transition_service.handle_final_acceptance_passed(order.project_id)
                logger.info("终验收通过，项目可推进至S9")
    except Exception as e:
        logger.error(f"验收状态联动处理失败: {str(e)}", exc_info=True)


def handle_progress_integration(
    db: Session, order: AcceptanceOrder, overall_result: str
) -> Dict[str, Any]:
    """
    处理验收结果对进度跟踪的影响

    Returns:
        Dict[str, Any]: 处理结果
    """
    try:
        service_cls = _resolve_service(
            "ProgressIntegrationService",
            "app.services.progress_integration_service",
            "ProgressIntegrationService",
        )
        if service_cls is None:
            raise ImportError("ProgressIntegrationService is unavailable")

        integration_service = service_cls(db)

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
    db: Session, order: AcceptanceOrder, overall_result: str
) -> Dict[str, Any]:
    """
    验收通过后自动触发阶段流转检查

    Returns:
        Dict[str, Any]: 流转结果
    """
    if overall_result != "PASSED" or not order.project_id:
        return {}

    try:
        service_cls = _resolve_service(
            "StatusTransitionService",
            "app.services.status_transition_service",
            "StatusTransitionService",
        )
        if service_cls is None:
            raise ImportError("StatusTransitionService is unavailable")

        transition_service = service_cls(db)

        project = db.query(Project).filter(Project.id == order.project_id).first()
        if not project:
            return {}

        # 检查是否可以自动推进阶段
        if order.acceptance_type == "FAT" and project.stage == "S7":
            auto_transition_result = transition_service.check_auto_stage_transition(
                order.project_id, auto_advance=True
            )
            if auto_transition_result.get("auto_advanced"):
                logger.info(f"FAT验收通过后自动推进项目 {order.project_id} 至 S8 阶段")
                return auto_transition_result

        elif order.acceptance_type in ["SAT", "FINAL"] and project.stage == "S8":
            auto_transition_result = transition_service.check_auto_stage_transition(
                order.project_id, auto_advance=True
            )
            if auto_transition_result.get("auto_advanced"):
                logger.info(f"终验收通过后自动推进项目 {order.project_id} 至 S9 阶段")
                return auto_transition_result
    except Exception as e:
        logger.warning(f"验收通过后自动阶段流转失败：{str(e)}", exc_info=True)
        return {"error": str(e)}

    return {}


def trigger_warranty_period(db: Session, order: AcceptanceOrder, overall_result: str) -> None:
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

        db.flush()
        logger.info(f"终验收通过，项目 {project.project_code} 已进入质保期（S9阶段）")
    except Exception as e:
        logger.error(f"终验收后质保期触发失败: {str(e)}", exc_info=True)


def trigger_bonus_calculation(db: Session, order: AcceptanceOrder, overall_result: str) -> None:
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
        calculator_cls = _resolve_service(
            "BonusCalculator",
            "app.services.bonus",
            "BonusCalculator",
        )
        if calculator_cls is None:
            raise ImportError("BonusCalculator is unavailable")

        calculator = calculator_cls(db)

        project = db.query(Project).filter(Project.id == order.project_id).first()
        if project:
            calculator.trigger_acceptance_bonus_calculation(project, order)
    except Exception as e:
        logger.error(f"验收后奖金计算失败: {str(e)}", exc_info=True)


class AcceptanceCompletionService:
    """旧接口兼容层，供历史测试/调用继续使用。"""

    def __init__(self, db: Session):
        self.db = db

    def complete_acceptance(
        self, order_id: int, overall_result: str, conclusion: Optional[str] = None
    ) -> Dict[str, Any]:
        order = self.db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
        if not order:
            raise ValueError("验收单不存在")
        if getattr(order, "status", None) == "COMPLETED":
            raise ValueError("验收单已完成")

        order.status = "COMPLETED"
        order.overall_result = overall_result
        order.conclusion = conclusion
        if hasattr(self.db, "add"):
            self.db.add(order)
        if hasattr(self.db, "commit"):
            self.db.commit()

        return {
            "order_id": order_id,
            "status": order.status,
            "overall_result": overall_result,
            "conclusion": conclusion,
        }

    @staticmethod
    def calculate_pass_rate(passed_items: int, total_items: int) -> float:
        if not total_items:
            return 0.0
        return round((passed_items / total_items) * 100, 2)

    def generate_completion_report(self, order_id: int) -> Dict[str, Any]:
        order = self.db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
        if not order:
            raise ValueError("验收单不存在")
        return {
            "order_id": order_id,
            "status": getattr(order, "status", None),
            "summary": self.get_completion_summary(order_id),
        }

    def validate_completion(self, order_id: int) -> Dict[str, Any]:
        order = self.db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
        if not order:
            return {"valid": False, "reason": "验收单不存在"}

        items = list(getattr(order, "items", []) or [])
        if not items:
            return {"valid": False, "reason": "验收单没有检查项"}

        return {"valid": True, "item_count": len(items)}

    def get_completion_summary(self, order_id: int) -> Dict[str, Any]:
        order = self.db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
        if not order:
            raise ValueError("验收单不存在")

        passed_items = getattr(order, "passed_items", 0) or 0
        failed_items = getattr(order, "failed_items", 0) or 0
        total_items = getattr(order, "total_items", 0) or 0
        return {
            "order_id": order_id,
            "passed_items": passed_items,
            "failed_items": failed_items,
            "total_items": total_items,
            "pass_rate": self.calculate_pass_rate(passed_items, total_items),
        }
