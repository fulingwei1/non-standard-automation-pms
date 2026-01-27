# -*- coding: utf-8 -*-
"""
采购订单审批适配器

将采购订单(PurchaseOrder)模块接入统一审批系统
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance, ApprovalTask
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.project import Project
from app.models.vendor import Vendor

from .base import ApprovalAdapter


class PurchaseOrderApprovalAdapter(ApprovalAdapter):
    """
    采购订单审批适配器

    采购订单审批流程特点:
    1. 金额影响审批级别（小额采购简化流程）
    2. 关联项目的紧急程度可能影响审批
    3. 供应商信用等级可能影响审批

    支持的条件字段:
    - entity.total_amount: 订单总金额
    - entity.amount_with_tax: 含税总金额
    - entity.order_type: 订单类型（NORMAL/URGENT/CONTRACT等）
    - entity.project_id: 关联项目ID
    - entity.supplier_id: 供应商ID
    - entity.item_count: 订单明细行数
    """

    entity_type = "PURCHASE_ORDER"

    def __init__(self, db: Session):
        self.db = db

    def get_entity(self, entity_id: int) -> Optional[PurchaseOrder]:
        """获取采购订单实体"""
        return self.db.query(PurchaseOrder).filter(PurchaseOrder.id == entity_id).first()

    def get_entity_data(self, entity_id: int) -> Dict[str, Any]:
        """
        获取采购订单数据用于条件路由

        Returns:
            包含采购订单关键数据的字典
        """
        order = self.get_entity(entity_id)
        if not order:
            return {}

        # 获取订单明细数量
        item_count = self.db.query(PurchaseOrderItem).filter(
            PurchaseOrderItem.order_id == entity_id
        ).count()

        # 获取项目信息（如果有）
        project_info = {}
        if order.project_id:
            project = self.db.query(Project).filter(Project.id == order.project_id).first()
            if project:
                project_info = {
                    "project_code": project.project_code,
                    "project_name": project.project_name,
                    "project_priority": project.priority if hasattr(project, 'priority') else None,
                }

        # 获取供应商信息
        vendor_info = {}
        if order.vendor_id:
            vendor = self.db.query(Vendor).filter(Vendor.id == order.vendor_id).first()
            if vendor:
                vendor_info = {
                    "vendor_name": vendor.vendor_name,
                    "vendor_code": vendor.vendor_code,
                }

        return {
            "order_no": order.order_no,
            "order_title": order.order_title or f"采购订单-{order.order_no}",
            "order_type": order.order_type or "NORMAL",
            "status": order.status,
            "total_amount": float(order.total_amount) if order.total_amount else 0,
            "tax_rate": float(order.tax_rate) if order.tax_rate else 0,
            "tax_amount": float(order.tax_amount) if order.tax_amount else 0,
            "amount_with_tax": float(order.amount_with_tax) if order.amount_with_tax else 0,
            "currency": order.currency or "CNY",
            "order_date": order.order_date.isoformat() if order.order_date else None,
            "required_date": order.required_date.isoformat() if order.required_date else None,
            "promised_date": order.promised_date.isoformat() if order.promised_date else None,
            "payment_terms": order.payment_terms,
            "project_id": order.project_id,
            "supplier_id": order.supplier_id,
            "source_request_id": order.source_request_id,
            "item_count": item_count,
            "created_by": order.created_by,
            "contract_no": order.contract_no,
            **project_info,
            **vendor_info,
        }

    def on_submit(self, entity_id: int, instance: ApprovalInstance) -> None:
        """
        提交审批时的回调

        采购订单提交审批后状态变更为PENDING_APPROVAL
        """
        order = self.get_entity(entity_id)
        if order:
            order.status = "PENDING_APPROVAL"
            order.submitted_at = datetime.now()
            self.db.flush()

    def on_approved(self, entity_id: int, instance: ApprovalInstance) -> None:
        """
        审批通过时的回调

        采购订单审批通过后可以执行采购
        """
        order = self.get_entity(entity_id)
        if order:
            order.status = "APPROVED"
            order.approved_by = instance.approved_by
            order.approved_at = datetime.now()
            self.db.flush()

    def on_rejected(self, entity_id: int, instance: ApprovalInstance) -> None:
        """
        审批驳回时的回调

        采购订单驳回后需要修改重新提交
        """
        order = self.get_entity(entity_id)
        if order:
            order.status = "REJECTED"
            # approval_note可以记录驳回原因（如果有的话）
            if hasattr(instance, 'reject_reason'):
                order.approval_note = instance.reject_reason
            self.db.flush()

    def on_withdrawn(self, entity_id: int, instance: ApprovalInstance) -> None:
        """
        审批撤回时的回调

        采购订单撤回后恢复为草稿状态
        """
        order = self.get_entity(entity_id)
        if order:
            order.status = "DRAFT"
            order.submitted_at = None
            self.db.flush()

    def generate_title(self, entity_id: int) -> str:
        """
        生成审批标题

        Args:
            entity_id: 采购订单ID

        Returns:
            审批标题
        """
        order = self.get_entity(entity_id)
        if not order:
            return f"采购订单审批 - {entity_id}"

        title = f"采购订单审批 - {order.order_no}"
        if order.order_title:
            title += f" - {order.order_title}"

        return title

    def generate_summary(self, entity_id: int) -> str:
        """
        生成审批摘要

        Args:
            entity_id: 采购订单ID

        Returns:
            审批摘要
        """
        order = self.get_entity(entity_id)
        if not order:
            return ""

        # 获取订单明细数量
        item_count = self.db.query(PurchaseOrderItem).filter(
            PurchaseOrderItem.order_id == entity_id
        ).count()

        # 获取供应商名称
        vendor_name = "未指定"
        if order.vendor_id:
            vendor = self.db.query(Vendor).filter(Vendor.id == order.vendor_id).first()
            if vendor:
                vendor_name = vendor.vendor_name

        # 构建摘要
        summary_parts = [
            f"订单编号: {order.order_no}",
            f"供应商: {vendor_name}",
            f"订单金额: ¥{order.amount_with_tax:,.2f}" if order.amount_with_tax else "订单金额: 未填写",
            f"明细行数: {item_count}",
        ]

        if order.required_date:
            summary_parts.append(f"要求交期: {order.required_date.strftime('%Y-%m-%d')}")

        if order.project_id:
            project = self.db.query(Project).filter(Project.id == order.project_id).first()
            if project:
                summary_parts.append(f"关联项目: {project.project_name}")

        return " | ".join(summary_parts)

    def validate_submit(self, entity_id: int) -> tuple[bool, Optional[str]]:
        """
        验证是否可以提交审批

        Args:
            entity_id: 采购订单ID

        Returns:
            (是否可以提交, 错误信息)
        """
        order = self.get_entity(entity_id)
        if not order:
            return False, "采购订单不存在"

        # 验证订单状态
        if order.status not in ["DRAFT", "REJECTED"]:
            return False, f"当前状态 '{order.status}' 不允许提交审批"

        # 验证必填字段
        if not order.supplier_id:
            return False, "请选择供应商"

        if not order.order_date:
            return False, "请填写订单日期"

        # 验证是否有订单明细
        item_count = self.db.query(PurchaseOrderItem).filter(
            PurchaseOrderItem.order_id == entity_id
        ).count()

        if item_count == 0:
            return False, "采购订单至少需要一条明细"

        # 验证金额
        if not order.amount_with_tax or order.amount_with_tax <= 0:
            return False, "订单总金额必须大于0"

        return True, None

    def get_cc_user_ids(self, entity_id: int) -> List[int]:
        """
        获取默认抄送人列表

        采购订单审批抄送给：
        1. 关联项目的项目经理（如果有）
        2. 采购部门负责人

        Args:
            entity_id: 采购订单ID

        Returns:
            抄送人ID列表
        """
        cc_users = []

        order = self.get_entity(entity_id)
        if not order:
            return cc_users

        # 关联项目的项目经理
        if order.project_id:
            project = self.db.query(Project).filter(Project.id == order.project_id).first()
            if project and hasattr(project, 'manager_id') and project.manager_id:
                cc_users.append(project.manager_id)

        # TODO: 可以添加采购部门负责人的逻辑
        # 这需要访问部门和用户关系数据

        return list(set(cc_users))  # 去重
