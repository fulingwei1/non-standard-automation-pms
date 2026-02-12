# -*- coding: utf-8 -*-
"""
外协订单审批适配器

将外协订单(OutsourcingOrder)模块接入统一审批系统
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance
from app.models.outsourcing import OutsourcingOrder, OutsourcingOrderItem
from app.models.project import Project, Machine
from app.models.vendor import Vendor

from .base import ApprovalAdapter


class OutsourcingOrderApprovalAdapter(ApprovalAdapter):
    """
    外协订单审批适配器

    外协订单审批流程特点:
    1. 金额和订单类型影响审批级别
    2. 加工工艺要求复杂度可能影响审批
    3. 关联项目的进度状态可能影响审批优先级

    支持的条件字段:
    - entity.total_amount: 订单总金额
    - entity.amount_with_tax: 含税总金额
    - entity.order_type: 订单类型（MACHINING/WELDING/PAINTING等）
    - entity.project_id: 关联项目ID
    - entity.machine_id: 关联设备ID
    - entity.vendor_id: 外协商ID
    - entity.item_count: 订单明细行数
    """

    entity_type = "OUTSOURCING_ORDER"

    def __init__(self, db: Session):
        self.db = db

    def get_entity(self, entity_id: int) -> Optional[OutsourcingOrder]:
        """获取外协订单实体"""
        return self.db.query(OutsourcingOrder).filter(
            OutsourcingOrder.id == entity_id
        ).first()

    def get_entity_data(self, entity_id: int) -> Dict[str, Any]:
        """
        获取外协订单数据用于条件路由

        Returns:
            包含外协订单关键数据的字典
        """
        order = self.get_entity(entity_id)
        if not order:
            return {}

        # 获取订单明细数量
        item_count = self.db.query(OutsourcingOrderItem).filter(
            OutsourcingOrderItem.order_id == entity_id
        ).count()

        # 获取项目信息
        project_info = {}
        if order.project_id:
            project = self.db.query(Project).filter(Project.id == order.project_id).first()
            if project:
                project_info = {
                    "project_code": project.project_code,
                    "project_name": project.project_name,
                    "project_status": project.status if hasattr(project, 'status') else None,
                }

        # 获取设备信息（如果有）
        machine_info = {}
        if order.machine_id:
            machine = self.db.query(Machine).filter(Machine.id == order.machine_id).first()
            if machine:
                machine_info = {
                    "machine_code": machine.machine_code,
                    "machine_name": machine.machine_name if hasattr(machine, 'machine_name') else None,
                }

        # 获取外协商信息
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
            "order_title": order.order_title,
            "order_type": order.order_type,
            "order_description": order.order_description,
            "status": order.status,
            "total_amount": float(order.total_amount) if order.total_amount else 0,
            "tax_rate": float(order.tax_rate) if order.tax_rate else 0,
            "tax_amount": float(order.tax_amount) if order.tax_amount else 0,
            "amount_with_tax": float(order.amount_with_tax) if order.amount_with_tax else 0,
            "required_date": order.required_date.isoformat() if order.required_date else None,
            "estimated_date": order.estimated_date.isoformat() if order.estimated_date else None,
            "actual_date": order.actual_date.isoformat() if order.actual_date else None,
            "payment_status": order.payment_status,
            "paid_amount": float(order.paid_amount) if order.paid_amount else 0,
            "contract_no": order.contract_no,
            "project_id": order.project_id,
            "machine_id": order.machine_id,
            "vendor_id": order.vendor_id,
            "item_count": item_count,
            "created_by": order.created_by,
            **project_info,
            **machine_info,
            **vendor_info,
        }

    def on_submit(self, entity_id: int, instance: ApprovalInstance) -> None:
        """
        提交审批时的回调

        外协订单提交审批后状态变更为PENDING_APPROVAL
        """
        order = self.get_entity(entity_id)
        if order:
            order.status = "PENDING_APPROVAL"
            self.db.flush()

    def on_approved(self, entity_id: int, instance: ApprovalInstance) -> None:
        """
        审批通过时的回调

        外协订单审批通过后可以下发给外协商
        """
        order = self.get_entity(entity_id)
        if order:
            order.status = "APPROVED"
            self.db.flush()

    def on_rejected(self, entity_id: int, instance: ApprovalInstance) -> None:
        """
        审批驳回时的回调

        外协订单驳回后需要修改重新提交
        """
        order = self.get_entity(entity_id)
        if order:
            order.status = "REJECTED"
            self.db.flush()

    def on_withdrawn(self, entity_id: int, instance: ApprovalInstance) -> None:
        """
        审批撤回时的回调

        外协订单撤回后恢复为草稿状态
        """
        order = self.get_entity(entity_id)
        if order:
            order.status = "DRAFT"
            self.db.flush()

    def generate_title(self, entity_id: int) -> str:
        """
        生成审批标题

        Args:
            entity_id: 外协订单ID

        Returns:
            审批标题
        """
        order = self.get_entity(entity_id)
        if not order:
            return f"外协订单审批 - {entity_id}"

        title = f"外协订单审批 - {order.order_no}"
        if order.order_title:
            title += f" - {order.order_title}"

        return title

    def generate_summary(self, entity_id: int) -> str:
        """
        生成审批摘要

        Args:
            entity_id: 外协订单ID

        Returns:
            审批摘要
        """
        order = self.get_entity(entity_id)
        if not order:
            return ""

        # 获取订单明细数量
        item_count = self.db.query(OutsourcingOrderItem).filter(
            OutsourcingOrderItem.order_id == entity_id
        ).count()

        # 获取外协商名称
        vendor_name = "未指定"
        if order.vendor_id:
            vendor = self.db.query(Vendor).filter(Vendor.id == order.vendor_id).first()
            if vendor:
                vendor_name = vendor.vendor_name

        # 构建摘要
        summary_parts = [
            f"订单编号: {order.order_no}",
            f"外协商: {vendor_name}",
            f"订单类型: {order.order_type}",
            f"订单金额: ¥{order.amount_with_tax:,.2f}" if order.amount_with_tax else "订单金额: 未填写",
            f"明细行数: {item_count}",
        ]

        if order.required_date:
            summary_parts.append(f"要求交期: {order.required_date.strftime('%Y-%m-%d')}")

        if order.project_id:
            project = self.db.query(Project).filter(Project.id == order.project_id).first()
            if project:
                summary_parts.append(f"关联项目: {project.project_name}")

        if order.machine_id:
            machine = self.db.query(Machine).filter(Machine.id == order.machine_id).first()
            if machine and hasattr(machine, 'machine_code'):
                summary_parts.append(f"关联设备: {machine.machine_code}")

        return " | ".join(summary_parts)

    def validate_submit(self, entity_id: int) -> tuple[bool, Optional[str]]:
        """
        验证是否可以提交审批

        Args:
            entity_id: 外协订单ID

        Returns:
            (是否可以提交, 错误信息)
        """
        order = self.get_entity(entity_id)
        if not order:
            return False, "外协订单不存在"

        # 验证订单状态
        if order.status not in ["DRAFT", "REJECTED"]:
            return False, f"当前状态 '{order.status}' 不允许提交审批"

        # 验证必填字段
        if not order.vendor_id:
            return False, "请选择外协商"

        if not order.project_id:
            return False, "请关联项目"

        if not order.order_title:
            return False, "请填写订单标题"

        if not order.order_type:
            return False, "请选择订单类型"

        # 验证是否有订单明细
        item_count = self.db.query(OutsourcingOrderItem).filter(
            OutsourcingOrderItem.order_id == entity_id
        ).count()

        if item_count == 0:
            return False, "外协订单至少需要一条明细"

        # 验证金额
        if not order.amount_with_tax or order.amount_with_tax <= 0:
            return False, "订单总金额必须大于0"

        # 验证交期
        if not order.required_date:
            return False, "请填写要求交期"

        return True, None

    def get_cc_user_ids(self, entity_id: int) -> List[int]:
        """
        获取默认抄送人列表

        外协订单审批抄送给：
        1. 关联项目的项目经理
        2. 生产部门负责人

        Args:
            entity_id: 外协订单ID

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

        # 生产部门负责人
        # 常见的生产部门编码：PROD, PRODUCTION, MFG, MANUFACTURING
        prod_dept_codes = ['PROD', 'PRODUCTION', 'MFG', '生产部']
        prod_manager_ids = self.get_department_manager_user_ids_by_codes(prod_dept_codes)
        cc_users.extend(prod_manager_ids)

        # 如果没找到，尝试通过部门名称查找
        if not prod_manager_ids:
            prod_manager = self.get_department_manager_user_id('生产部')
            if prod_manager:
                cc_users.append(prod_manager)

        return list(set(cc_users))  # 去重
