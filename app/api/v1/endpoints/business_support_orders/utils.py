# -*- coding: utf-8 -*-
"""
商务支持订单模块公共工具函数

包含编码生成、通知发送、序列化辅助函数等
已重构为薄 Controller 层，业务逻辑已迁移至 BusinessSupportUtilsService
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.services.business_support_utils import BusinessSupportUtilsService
from app.models.business_support import (
    CustomerSupplierRegistration,
    InvoiceRequest,
)
from app.schemas.business_support import (
    CustomerSupplierRegistrationResponse,
    InvoiceRequestResponse,
)


# ==================== 通知发送函数 ====================


def _send_department_notification(
    db: Session,
    user_id: int,
    notification_type: str,
    title: str,
    content: str,
    source_type: str,
    source_id: int,
    priority: str = "NORMAL",
    extra_data: Optional[dict] = None
) -> None:
    """
    发送部门通知（薄 Controller）

    Args:
        db: 数据库会话
        user_id: 接收通知的用户ID
        notification_type: 通知类型
        title: 通知标题
        content: 通知内容
        source_type: 来源类型
        source_id: 来源ID
        priority: 优先级
        extra_data: 额外数据
    """
    service = BusinessSupportUtilsService(db)
    service.send_department_notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        content=content,
        source_type=source_type,
        source_id=source_id,
        priority=priority,
        extra_data=extra_data
    )


def _send_project_department_notifications(
    db: Session,
    project_id: int,
    notification_type: str,
    title: str,
    content: str,
    source_type: str,
    source_id: int,
    priority: str = "NORMAL",
    extra_data: Optional[dict] = None
) -> None:
    """
    发送项目相关部门通知（PMC、生产、采购等）（薄 Controller）

    Args:
        db: 数据库会话
        project_id: 项目ID
        notification_type: 通知类型
        title: 通知标题
        content: 通知内容
        source_type: 来源类型
        source_id: 来源ID
        priority: 优先级
        extra_data: 额外数据
    """
    service = BusinessSupportUtilsService(db)
    service.send_project_department_notifications(
        project_id=project_id,
        notification_type=notification_type,
        title=title,
        content=content,
        source_type=source_type,
        source_id=source_id,
        priority=priority,
        extra_data=extra_data
    )


# ==================== 编码生成函数 ====================


def generate_order_no(db: Session) -> str:
    """生成销售订单编号：SO250101-001（薄 Controller）"""
    service = BusinessSupportUtilsService(db)
    return service.generate_order_no()


def generate_delivery_no(db: Session) -> str:
    """生成送货单号：DO250101-001（薄 Controller）"""
    service = BusinessSupportUtilsService(db)
    return service.generate_delivery_no()


def generate_invoice_request_no(db: Session) -> str:
    """生成开票申请编号：IR250101-001（薄 Controller）"""
    service = BusinessSupportUtilsService(db)
    return service.generate_invoice_request_no()


def generate_registration_no(db: Session) -> str:
    """生成客户供应商入驻编号：CR250101-001（薄 Controller）"""
    service = BusinessSupportUtilsService(db)
    return service.generate_registration_no()


def generate_invoice_code(db: Session) -> str:
    """生成发票编码：INV-250101-001（薄 Controller）"""
    service = BusinessSupportUtilsService(db)
    return service.generate_invoice_code()


def generate_reconciliation_no(db: Session) -> str:
    """生成对账单号：RC250101-001（薄 Controller）"""
    service = BusinessSupportUtilsService(db)
    return service.generate_reconciliation_no()


# ==================== 序列化辅助函数 ====================


def _serialize_attachments(items: Optional[List[str]]) -> Optional[str]:
    """序列化附件列表为JSON字符串（薄 Controller）"""
    return BusinessSupportUtilsService.serialize_attachments(items)


def _deserialize_attachments(payload: Optional[str]) -> Optional[List[str]]:
    """反序列化JSON字符串为附件列表（薄 Controller）"""
    return BusinessSupportUtilsService.deserialize_attachments(payload)


# ==================== 响应转换函数 ====================


def _to_invoice_request_response(invoice_request: InvoiceRequest) -> InvoiceRequestResponse:
    """转换开票申请对象为响应对象（薄 Controller）"""
    # 需要一个临时 db session，从模型的 session 中获取
    db = Session.object_session(invoice_request)
    service = BusinessSupportUtilsService(db)
    return service.to_invoice_request_response(invoice_request)


def _to_registration_response(record: CustomerSupplierRegistration) -> CustomerSupplierRegistrationResponse:
    """转换客户供应商入驻对象为响应对象（薄 Controller）"""
    # 需要一个临时 db session，从模型的 session 中获取
    db = Session.object_session(record)
    service = BusinessSupportUtilsService(db)
    return service.to_registration_response(record)
