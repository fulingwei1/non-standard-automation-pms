# -*- coding: utf-8 -*-
"""
发票自动服务 - 通知和日志
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from app.models.acceptance import AcceptanceOrder
from app.models.sales import Contract
from app.services.unified_notification_service import get_notification_service
from app.services.channel_handlers.base import NotificationRequest, NotificationPriority

logger = logging.getLogger(__name__)


def send_invoice_notifications(
    service: "InvoiceAutoService",
    order: AcceptanceOrder,
    created_items: List[Dict[str, Any]],
    auto_create: bool,
) -> None:
    """
    发送开票通知给：财务、销售

    Args:
        service: InvoiceAutoService实例
        order: 验收单
        created_items: 创建的发票申请或发票列表
        auto_create: 是否自动创建发票
    """
    try:
        # 获取项目信息
        project = order.project
        if not project:
            return

        # 获取合同信息
        contract = None
        if project.contract_id:
            contract = service.db.query(Contract).filter(
                Contract.id == project.contract_id
            ).first()

        # 确定通知对象
        recipient_ids = set()

        # 1. 财务
        from app.models.user import Role, UserRole
        finance_role_ids = service.db.query(Role.id).filter(
            Role.role_code.in_(["FINANCE", "财务", "FINANCE_MANAGER", "财务经理"])
        ).all()
        finance_role_ids = [r[0] for r in finance_role_ids]
        if finance_role_ids:
            finance_user_ids = service.db.query(UserRole.user_id).filter(
                UserRole.role_id.in_(finance_role_ids)
            ).all()
            for uid in finance_user_ids:
                recipient_ids.add(uid[0])

        # 2. 销售（合同负责人）
        if contract and contract.owner_id:
            recipient_ids.add(contract.owner_id)

        # 构建通知内容
        item_type = "发票" if auto_create else "发票申请"
        item_list = [f"{item.get('invoice_code') or item.get('request_no')}（金额：¥{item.get('amount', 0):,.2f}）" for item in created_items]

        notification_content = (
            f"验收通过自动触发开票：\n"
            f"项目：{project.project_code} - {project.project_name}\n"
            f"验收单：{order.order_no}\n"
            f"已创建 {len(created_items)} 个{item_type}：\n"
            f"{chr(10).join(item_list)}\n"
            f"请及时处理。"
        )

        # 使用统一通知服务发送通知
        unified_service = get_notification_service(service.db)
        sent_count = 0
        for user_id in recipient_ids:
            request = NotificationRequest(
                recipient_id=user_id,
                notification_type="INVOICE_AUTO",
                category="invoice",
                title=f"验收通过自动触发{item_type}",
                content=notification_content,
                priority=NotificationPriority.NORMAL,
                source_type="acceptance",
                source_id=order.id,
                link_url=f"/acceptance/{order.id}",
            )
            result = unified_service.send_notification(request)
            if result.get("success"):
                sent_count += 1

        logger.info(f"已发送开票通知给 {sent_count}/{len(recipient_ids)} 个用户")

    except Exception as e:
        logger.error(f"发送开票通知失败: {e}", exc_info=True)


def log_auto_invoice(
    service: "InvoiceAutoService",
    order: AcceptanceOrder,
    created_items: List[Dict[str, Any]],
    auto_create: bool,
) -> None:
    """
    记录自动开票日志

    Args:
        service: InvoiceAutoService实例
        order: 验收单
        created_items: 创建的发票申请或发票列表
        auto_create: 是否自动创建发票
    """
    try:
        log_entry = {
            "acceptance_order_id": order.id,
            "acceptance_order_no": order.order_no,
            "project_id": order.project_id,
            "auto_create": auto_create,
            "created_items": created_items,
            "created_at": datetime.now().isoformat()
        }

        # 将日志记录到验收单的备注中（简化实现）
        if order.conditions:
            try:
                log_list = json.loads(order.conditions)
                if not isinstance(log_list, list):
                    log_list = []
            except (json.JSONDecodeError, TypeError):
                log_list = []
        else:
            log_list = []

        log_list.append(log_entry)
        order.conditions = json.dumps(log_list, ensure_ascii=False)

        logger.info(f"验收单 {order.order_no} 自动开票日志已记录")

    except Exception as e:
        logger.error(f"记录自动开票日志失败: {e}", exc_info=True)
