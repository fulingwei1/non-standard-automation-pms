# -*- coding: utf-8 -*-
"""
业务支持订单工具服务

提供编码生成、通知发送、序列化辅助、响应转换等功能
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.common.query_filters import apply_keyword_filter, apply_like_filter
from app.services.notification_dispatcher import NotificationDispatcher
from app.models.business_support import (
    CustomerSupplierRegistration,
    DeliveryOrder,
    InvoiceRequest,
    Reconciliation,
    SalesOrder,
)
from app.models.organization import Department
from app.models.project import ProjectMember
from app.models.sales import Invoice
from app.models.user import User
from app.schemas.business_support import (
    CustomerSupplierRegistrationResponse,
    InvoiceRequestResponse,
)

logger = logging.getLogger(__name__)


class BusinessSupportUtilsService:
    """业务支持订单工具服务类"""

    def __init__(self, db: Session):
        """
        初始化服务

        Args:
            db: 数据库会话
        """
        self.db = db

    # ==================== 通知发送 ====================

    def send_department_notification(
        self,
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
        发送部门通知

        Args:
            user_id: 接收通知的用户ID
            notification_type: 通知类型
            title: 通知标题
            content: 通知内容
            source_type: 来源类型
            source_id: 来源ID
            priority: 优先级
            extra_data: 额外数据
        """
        try:
            dispatcher = NotificationDispatcher(self.db)
            dispatcher.create_system_notification(
                recipient_id=user_id,
                notification_type=notification_type,
                title=title,
                content=content,
                source_type=source_type,
                source_id=source_id,
                link_url=f"/{source_type.lower()}?id={source_id}",
                priority=priority,
                extra_data=extra_data or {},
            )
            self.db.commit()
        except Exception as e:
            logger.warning(f"发送通知失败: {str(e)}")

    def send_project_department_notifications(
        self,
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
        发送项目相关部门通知（PMC、生产、采购等）

        Args:
            project_id: 项目ID
            notification_type: 通知类型
            title: 通知标题
            content: 通知内容
            source_type: 来源类型
            source_id: 来源ID
            priority: 优先级
            extra_data: 额外数据
        """
        # 获取项目成员
        project_members = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.is_active
        ).all()

        # 根据角色分类发送通知
        # 获取相关部门的ID
        dept_mapping = {
            'PMC': ['pmc', '生产管理中心'],
            'PRODUCTION': ['production', 'production_dept', '生产部', '生产制造部'],
            'PURCHASE': ['purchase', 'procurement', '采购部', '采购中心'],
            'TECHNICAL': ['technical', 'rd', '技术部', '研发部'],
            'QUALITY': ['quality', 'qa', '质量部', '品管部']
        }

        notified_users = set()

        # 通知项目成员
        for member in project_members:
            user = self.db.query(User).filter(User.id == member.user_id).first()
            if user and user.id not in notified_users:
                self.send_department_notification(
                    user_id=user.id,
                    notification_type=notification_type,
                    title=title,
                    content=content,
                    source_type=source_type,
                    source_id=source_id,
                    priority=priority,
                    extra_data=extra_data
                )
                notified_users.add(user.id)

        # 通知相关部门的其他成员
        for dept_type, role_codes in dept_mapping.items():
            dept_query = self.db.query(Department)
            dept_query = apply_keyword_filter(dept_query, Department, role_codes[0], "name")
            dept = dept_query.first()

            if dept:
                dept_users = self.db.query(User).filter(
                    User.department_id == dept.id,
                    User.is_active
                ).all()

                for user in dept_users:
                    if user.id not in notified_users:
                        # 添加部门特定信息
                        dept_content = f"{content}\n\n（发送至{dept.name}）"
                        self.send_department_notification(
                            user_id=user.id,
                            notification_type=notification_type,
                            title=title,
                            content=dept_content,
                            source_type=source_type,
                            source_id=source_id,
                            priority=priority,
                            extra_data=extra_data
                        )
                        notified_users.add(user.id)

    # ==================== 编码生成 ====================

    def generate_order_no(self) -> str:
        """生成销售订单编号：SO250101-001"""
        today = datetime.now()
        month_str = today.strftime("%y%m%d")
        prefix = f"SO{month_str}-"

        max_order_query = self.db.query(SalesOrder)
        max_order_query = apply_like_filter(
            max_order_query,
            SalesOrder,
            f"{prefix}%",
            "order_no",
            use_ilike=False,
        )
        max_order = max_order_query.order_by(desc(SalesOrder.order_no)).first()

        if max_order:
            try:
                seq = int(max_order.order_no.split("-")[-1]) + 1
            except (ValueError, TypeError, IndexError):
                seq = 1
        else:
            seq = 1

        return f"{prefix}{seq:03d}"

    def generate_delivery_no(self) -> str:
        """生成送货单号：DO250101-001"""
        today = datetime.now()
        month_str = today.strftime("%y%m%d")
        prefix = f"DO{month_str}-"

        max_delivery_query = self.db.query(DeliveryOrder)
        max_delivery_query = apply_like_filter(
            max_delivery_query,
            DeliveryOrder,
            f"{prefix}%",
            "delivery_no",
            use_ilike=False,
        )
        max_delivery = max_delivery_query.order_by(desc(DeliveryOrder.delivery_no)).first()

        if max_delivery:
            try:
                seq = int(max_delivery.delivery_no.split("-")[-1]) + 1
            except (ValueError, TypeError, IndexError):
                seq = 1
        else:
            seq = 1

        return f"{prefix}{seq:03d}"

    def generate_invoice_request_no(self) -> str:
        """生成开票申请编号：IR250101-001"""
        today = datetime.now()
        prefix = f"IR{today.strftime('%y%m%d')}-"

        latest_query = self.db.query(InvoiceRequest)
        latest_query = apply_like_filter(
            latest_query,
            InvoiceRequest,
            f"{prefix}%",
            "request_no",
            use_ilike=False,
        )
        latest = latest_query.order_by(desc(InvoiceRequest.request_no)).first()
        if latest:
            try:
                seq = int(latest.request_no.split("-")[-1]) + 1
            except Exception:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:03d}"

    def generate_registration_no(self) -> str:
        """生成客户供应商入驻编号：CR250101-001"""
        today = datetime.now()
        prefix = f"CR{today.strftime('%y%m%d')}-"

        latest_query = self.db.query(CustomerSupplierRegistration)
        latest_query = apply_like_filter(
            latest_query,
            CustomerSupplierRegistration,
            f"{prefix}%",
            "registration_no",
            use_ilike=False,
        )
        latest = latest_query.order_by(desc(CustomerSupplierRegistration.registration_no)).first()
        if latest:
            try:
                seq = int(latest.registration_no.split("-")[-1]) + 1
            except Exception:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:03d}"

    def generate_invoice_code(self) -> str:
        """生成发票编码：INV-250101-001"""
        today = datetime.now().strftime("%y%m%d")
        prefix = f"INV-{today}-"

        latest_query = self.db.query(Invoice)
        latest_query = apply_like_filter(
            latest_query,
            Invoice,
            f"{prefix}%",
            "invoice_code",
            use_ilike=False,
        )
        latest = latest_query.order_by(desc(Invoice.invoice_code)).first()
        if latest:
            try:
                seq = int(latest.invoice_code.split("-")[-1]) + 1
            except Exception:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:03d}"

    def generate_reconciliation_no(self) -> str:
        """生成对账单号：RC250101-001"""
        today = datetime.now()
        month_str = today.strftime("%y%m%d")
        prefix = f"RC{month_str}-"

        max_reconciliation_query = self.db.query(Reconciliation)
        max_reconciliation_query = apply_like_filter(
            max_reconciliation_query,
            Reconciliation,
            f"{prefix}%",
            "reconciliation_no",
            use_ilike=False,
        )
        max_reconciliation = max_reconciliation_query.order_by(desc(Reconciliation.reconciliation_no)).first()

        if max_reconciliation:
            try:
                seq = int(max_reconciliation.reconciliation_no.split("-")[-1]) + 1
            except (ValueError, TypeError, IndexError):
                seq = 1
        else:
            seq = 1

        return f"{prefix}{seq:03d}"

    # ==================== 序列化辅助 ====================

    @staticmethod
    def serialize_attachments(items: Optional[List[str]]) -> Optional[str]:
        """
        序列化附件列表为JSON字符串

        Args:
            items: 附件列表

        Returns:
            JSON字符串或None
        """
        if not items:
            return None
        try:
            return json.dumps(items, ensure_ascii=False)
        except Exception:
            return json.dumps([str(item) for item in items], ensure_ascii=False)

    @staticmethod
    def deserialize_attachments(payload: Optional[str]) -> Optional[List[str]]:
        """
        反序列化JSON字符串为附件列表

        Args:
            payload: JSON字符串

        Returns:
            附件列表或None
        """
        if not payload:
            return None
        try:
            data = json.loads(payload)
            if isinstance(data, list):
                return data
        except Exception:
            return [payload]
        return None

    # ==================== 响应转换 ====================

    def to_invoice_request_response(self, invoice_request: InvoiceRequest) -> InvoiceRequestResponse:
        """
        转换开票申请对象为响应对象

        Args:
            invoice_request: 开票申请模型对象

        Returns:
            开票申请响应对象
        """
        contract_code = invoice_request.contract.contract_code if invoice_request.contract else None
        project_name = invoice_request.project.project_name if invoice_request.project else invoice_request.project_name
        customer_name = invoice_request.customer.customer_name if invoice_request.customer else invoice_request.customer_name
        approved_by_name = None
        if invoice_request.approver:
            approved_by_name = invoice_request.approver.real_name or invoice_request.approver.username
        invoice_code = invoice_request.invoice.invoice_code if invoice_request.invoice else None

        return InvoiceRequestResponse(
            id=invoice_request.id,
            request_no=invoice_request.request_no,
            contract_id=invoice_request.contract_id,
            contract_code=contract_code,
            project_id=invoice_request.project_id,
            project_name=project_name,
            customer_id=invoice_request.customer_id,
            customer_name=customer_name,
            payment_plan_id=invoice_request.payment_plan_id,
            invoice_type=invoice_request.invoice_type,
            invoice_title=invoice_request.invoice_title,
            tax_rate=invoice_request.tax_rate,
            amount=invoice_request.amount,
            tax_amount=invoice_request.tax_amount,
            total_amount=invoice_request.total_amount,
            currency=invoice_request.currency,
            expected_issue_date=invoice_request.expected_issue_date,
            expected_payment_date=invoice_request.expected_payment_date,
            reason=invoice_request.reason,
            attachments=self.deserialize_attachments(invoice_request.attachments),
            remark=invoice_request.remark,
            status=invoice_request.status,
            approval_comment=invoice_request.approval_comment,
            requested_by=invoice_request.requested_by,
            requested_by_name=invoice_request.requested_by_name,
            approved_by=invoice_request.approved_by,
            approved_by_name=approved_by_name,
            approved_at=invoice_request.approved_at,
            invoice_id=invoice_request.invoice_id,
            invoice_code=invoice_code,
            receipt_status=invoice_request.receipt_status,
            receipt_updated_at=invoice_request.receipt_updated_at,
            created_at=invoice_request.created_at,
            updated_at=invoice_request.updated_at,
        )

    def to_registration_response(self, record: CustomerSupplierRegistration) -> CustomerSupplierRegistrationResponse:
        """
        转换客户供应商入驻对象为响应对象

        Args:
            record: 客户供应商入驻模型对象

        Returns:
            客户供应商入驻响应对象
        """
        reviewer_name = None
        if record.reviewer:
            reviewer_name = record.reviewer.real_name or record.reviewer.username
        return CustomerSupplierRegistrationResponse(
            id=record.id,
            registration_no=record.registration_no,
            customer_id=record.customer_id,
            customer_name=record.customer_name,
            platform_name=record.platform_name,
            platform_url=record.platform_url,
            registration_status=record.registration_status,
            application_date=record.application_date,
            approved_date=record.approved_date,
            expire_date=record.expire_date,
            contact_person=record.contact_person,
            contact_phone=record.contact_phone,
            contact_email=record.contact_email,
            required_docs=self.deserialize_attachments(record.required_docs),
            reviewer_id=record.reviewer_id,
            reviewer_name=reviewer_name,
            review_comment=record.review_comment,
            external_sync_status=record.external_sync_status,
            last_sync_at=record.last_sync_at,
            remark=record.remark,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
