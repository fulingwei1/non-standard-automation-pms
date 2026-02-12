# -*- coding: utf-8 -*-
"""
发票自动服务 - 主要功能
"""
import logging
from datetime import date
from typing import TYPE_CHECKING, Any, Dict

from app.models.acceptance import AcceptanceOrder
from app.models.project import ProjectMilestone, ProjectPaymentPlan

from .creation import create_invoice_directly, create_invoice_request
from .notifications import log_auto_invoice, send_invoice_notifications
from .validation import check_acceptance_issues_resolved, check_deliverables_complete

if TYPE_CHECKING:
    from app.services.invoice_auto_service import InvoiceAutoService

logger = logging.getLogger(__name__)


def check_and_create_invoice_request(
    service: "InvoiceAutoService",
    acceptance_order_id: int,
    auto_create: bool = False,
) -> Dict[str, Any]:
    """
    检查验收完成后的收款计划，自动创建发票申请

    Args:
        service: InvoiceAutoService实例
        acceptance_order_id: 验收单ID
        auto_create: 是否自动创建发票（True）还是只创建发票申请（False，默认）

    Returns:
        处理结果字典
    """
    order = service.db.query(AcceptanceOrder).filter(
        AcceptanceOrder.id == acceptance_order_id
    ).first()

    if not order:
        return {
            "success": False,
            "message": "验收单不存在",
            "invoice_requests": []
        }

    # 只处理验收通过的订单
    if order.overall_result != "PASSED" or order.status != "COMPLETED":
        return {
            "success": True,
            "message": "验收未通过或未完成，无需开票",
            "invoice_requests": []
        }

    # 查找关联的里程碑
    # 根据验收类型匹配里程碑类型
    milestone_type_map = {
        "FAT": "FAT_PASS",
        "SAT": "SAT_PASS",
        "FINAL": "FINAL_ACCEPTANCE",
    }
    milestone_type = milestone_type_map.get(order.acceptance_type)

    if not milestone_type:
        return {
            "success": True,
            "message": "验收类型不支持自动开票",
            "invoice_requests": []
        }

    # 查找关联的里程碑
    milestones = service.db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == order.project_id,
        ProjectMilestone.milestone_type == milestone_type,
        ProjectMilestone.status == "COMPLETED"
    ).all()

    if not milestones:
        return {
            "success": True,
            "message": "未找到关联的里程碑",
            "invoice_requests": []
        }

    created_requests = []

    for milestone in milestones:
        # 查找关联的收款计划
        payment_plans = service.db.query(ProjectPaymentPlan).filter(
            ProjectPaymentPlan.milestone_id == milestone.id,
            ProjectPaymentPlan.status.in_(["PENDING", "INVOICED"]),
            ProjectPaymentPlan.payment_type == "ACCEPTANCE"
        ).all()

        for plan in payment_plans:
            # 检查是否已开票
            if plan.invoice_id:
                continue

            # 检查收款计划是否已到期
            if plan.planned_date and plan.planned_date > date.today():
                # 如果配置允许提前开票，可以继续；否则跳过
                # 这里简化处理，如果计划日期未到，跳过
                continue

            # 检查交付物是否齐全（简化处理：检查合同交付物）
            if not check_deliverables_complete(service, plan):
                logger.warning(f"收款计划 {plan.id} 的交付物不齐全，跳过自动开票")
                continue

            # 检查验收问题：存在未闭环阻塞问题时阻止开票
            if not check_acceptance_issues_resolved(service, order):
                logger.warning(
                    f"验收单 {order.id} 存在未闭环的阻塞问题，无法开票。"
                    f"收款计划 {plan.id} 跳过自动开票"
                )
                continue

            # 创建发票申请或直接创建发票
            if auto_create:
                result = create_invoice_directly(service, plan, order, milestone)
            else:
                result = create_invoice_request(service, plan, order, milestone)

            if result.get("success"):
                created_requests.append(result)

    if created_requests:
        service.db.commit()

        # 发送通知
        send_invoice_notifications(service, order, created_requests, auto_create)

        # 记录日志
        log_auto_invoice(service, order, created_requests, auto_create)

    return {
        "success": True,
        "message": f"已创建 {len(created_requests)} 个发票{'申请' if not auto_create else ''}",
        "invoice_requests": created_requests
    }
