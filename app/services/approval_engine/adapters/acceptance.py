# -*- coding: utf-8 -*-
"""
验收单审批适配器

将验收单(AcceptanceOrder)模块接入统一审批系统
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance
from app.models.acceptance import AcceptanceOrder, AcceptanceOrderItem, AcceptanceTemplate
from app.models.project import Project, Machine

from .base import ApprovalAdapter


class AcceptanceOrderApprovalAdapter(ApprovalAdapter):
    """
    验收单审批适配器

    验收单审批流程特点:
    1. 验收类型(FAT/SAT/FINAL)影响审批级别
    2. 验收结果(PASSED/FAILED/CONDITIONAL)决定审批决策
    3. 通过率影响审批优先级
    4. 关键项不合格必须升级审批

    支持的条件字段:
    - entity.acceptance_type: 验收类型（FAT/SAT/FINAL）
    - entity.overall_result: 验收结果（PASSED/FAILED/CONDITIONAL）
    - entity.pass_rate: 通过率（0-100）
    - entity.failed_items: 不通过项数
    - entity.total_items: 检查项总数
    - entity.project_id: 关联项目ID
    - entity.machine_id: 关联设备ID
    """

    entity_type = "ACCEPTANCE_ORDER"

    def __init__(self, db: Session):
        self.db = db

    def get_entity(self, entity_id: int) -> Optional[AcceptanceOrder]:
        """获取验收单实体"""
        return self.db.query(AcceptanceOrder).filter(
            AcceptanceOrder.id == entity_id
        ).first()

    def get_entity_data(self, entity_id: int) -> Dict[str, Any]:
        """
        获取验收单数据用于条件路由

        Returns:
            包含验收单关键数据的字典
        """
        order = self.get_entity(entity_id)
        if not order:
            return {}

        # 获取检查项统计
        item_stats = {
            "total_items": order.total_items or 0,
            "passed_items": order.passed_items or 0,
            "failed_items": order.failed_items or 0,
            "na_items": order.na_items or 0,
            "pass_rate": float(order.pass_rate) if order.pass_rate else 0,
        }

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

        # 获取模板信息
        template_info = {}
        if order.template_id:
            template = self.db.query(AcceptanceTemplate).filter(
                AcceptanceTemplate.id == order.template_id
            ).first()
            if template:
                template_info = {
                    "template_name": template.template_name,
                    "template_code": template.template_code,
                    "equipment_type": template.equipment_type,
                }

        # 检查是否有关键项不合格
        has_critical_failure = False
        if order.failed_items and order.failed_items > 0:
            # 查询是否有关键项不合格
            critical_failed_items = self.db.query(AcceptanceOrderItem).filter(
                AcceptanceOrderItem.order_id == entity_id,
                AcceptanceOrderItem.is_key_item,
                AcceptanceOrderItem.result_status == "NG"
            ).count()
            has_critical_failure = critical_failed_items > 0

        return {
            "order_no": order.order_no,
            "acceptance_type": order.acceptance_type,
            "status": order.status,
            "planned_date": order.planned_date.isoformat() if order.planned_date else None,
            "actual_start_date": order.actual_start_date.isoformat() if order.actual_start_date else None,
            "actual_end_date": order.actual_end_date.isoformat() if order.actual_end_date else None,
            "location": order.location,
            "overall_result": order.overall_result,
            "conclusion": order.conclusion,
            "conditions": order.conditions,
            "project_id": order.project_id,
            "machine_id": order.machine_id,
            "template_id": order.template_id,
            "created_by": order.created_by,
            "is_officially_completed": order.is_officially_completed,
            "has_critical_failure": has_critical_failure,
            **item_stats,
            **project_info,
            **machine_info,
            **template_info,
        }

    def on_submit(self, entity_id: int, instance: ApprovalInstance) -> None:
        """
        提交审批时的回调

        验收单提交审批后状态变更为PENDING_APPROVAL
        """
        order = self.get_entity(entity_id)
        if order:
            order.status = "PENDING_APPROVAL"
            self.db.flush()

    def on_approved(self, entity_id: int, instance: ApprovalInstance) -> None:
        """
        审批通过时的回调

        验收单审批通过后可以进入下一阶段
        - FAT通过 -> 可以包装发运
        - SAT通过 -> 可以进入质保期
        - FINAL通过 -> 项目正式验收完成
        """
        order = self.get_entity(entity_id)
        if order:
            order.status = "APPROVED"

            # 根据验收类型设置不同的后续状态
            if order.acceptance_type == "FAT":
                # FAT通过，可以安排发运
                if order.overall_result == "PASSED":
                    order.status = "COMPLETED"
                elif order.overall_result == "CONDITIONAL":
                    order.status = "CONDITIONAL_APPROVED"
            elif order.acceptance_type == "SAT":
                # SAT通过，进入质保期
                if order.overall_result == "PASSED":
                    order.status = "COMPLETED"
                elif order.overall_result == "CONDITIONAL":
                    order.status = "CONDITIONAL_APPROVED"
            elif order.acceptance_type == "FINAL":
                # 终验收通过，项目正式完成
                if order.overall_result == "PASSED":
                    order.status = "COMPLETED"
                    order.is_officially_completed = True
                    order.officially_completed_at = datetime.now()

            self.db.flush()

    def on_rejected(self, entity_id: int, instance: ApprovalInstance) -> None:
        """
        审批驳回时的回调

        验收单驳回后需要重新检查或修改
        """
        order = self.get_entity(entity_id)
        if order:
            order.status = "REJECTED"
            self.db.flush()

    def on_withdrawn(self, entity_id: int, instance: ApprovalInstance) -> None:
        """
        审批撤回时的回调

        验收单撤回后恢复为草稿状态
        """
        order = self.get_entity(entity_id)
        if order:
            order.status = "DRAFT"
            self.db.flush()

    def generate_title(self, entity_id: int) -> str:
        """
        生成审批标题

        Args:
            entity_id: 验收单ID

        Returns:
            审批标题
        """
        order = self.get_entity(entity_id)
        if not order:
            return f"验收单审批 - {entity_id}"

        # 根据验收类型生成标题
        type_name_map = {
            "FAT": "出厂验收",
            "SAT": "现场验收",
            "FINAL": "终验收"
        }
        type_name = type_name_map.get(order.acceptance_type, order.acceptance_type)

        title = f"{type_name}审批 - {order.order_no}"

        # 如果是有条件通过，在标题中标注
        if order.overall_result == "CONDITIONAL":
            title += " [有条件通过]"
        elif order.overall_result == "FAILED":
            title += " [不合格]"

        return title

    def generate_summary(self, entity_id: int) -> str:
        """
        生成审批摘要

        Args:
            entity_id: 验收单ID

        Returns:
            审批摘要
        """
        order = self.get_entity(entity_id)
        if not order:
            return ""

        # 构建摘要
        summary_parts = [
            f"验收单号: {order.order_no}",
            f"验收类型: {order.acceptance_type}",
        ]

        if order.overall_result:
            result_name_map = {
                "PASSED": "合格",
                "FAILED": "不合格",
                "CONDITIONAL": "有条件通过"
            }
            result_name = result_name_map.get(order.overall_result, order.overall_result)
            summary_parts.append(f"验收结果: {result_name}")

        if order.pass_rate is not None:
            summary_parts.append(f"通过率: {order.pass_rate:.1f}%")

        summary_parts.append(
            f"检查项: {order.passed_items}/{order.total_items}项通过"
        )

        if order.failed_items and order.failed_items > 0:
            summary_parts.append(f"不合格: {order.failed_items}项")

        if order.project_id:
            project = self.db.query(Project).filter(Project.id == order.project_id).first()
            if project:
                summary_parts.append(f"项目: {project.project_name}")

        if order.machine_id:
            machine = self.db.query(Machine).filter(Machine.id == order.machine_id).first()
            if machine and hasattr(machine, 'machine_code'):
                summary_parts.append(f"设备: {machine.machine_code}")

        if order.location:
            summary_parts.append(f"地点: {order.location}")

        return " | ".join(summary_parts)

    def validate_submit(self, entity_id: int) -> tuple[bool, Optional[str]]:
        """
        验证是否可以提交审批

        Args:
            entity_id: 验收单ID

        Returns:
            (是否可以提交, 错误信息)
        """
        order = self.get_entity(entity_id)
        if not order:
            return False, "验收单不存在"

        # 验证订单状态
        if order.status not in ["DRAFT", "REJECTED"]:
            return False, f"当前状态 '{order.status}' 不允许提交审批"

        # 验证必填字段
        if not order.project_id:
            return False, "请关联项目"

        if not order.acceptance_type:
            return False, "请选择验收类型"

        # 验证是否有检查项
        if not order.total_items or order.total_items == 0:
            return False, "验收单至少需要一项检查内容"

        # 验证是否已经完成检查
        checked_items = order.passed_items + order.failed_items + order.na_items
        if checked_items < order.total_items:
            return False, f"还有 {order.total_items - checked_items} 项未检查"

        # 验证是否有验收结论
        if not order.overall_result:
            return False, "请填写验收结论（合格/不合格/有条件通过）"

        # 如果是有条件通过，必须说明条件
        if order.overall_result == "CONDITIONAL" and not order.conditions:
            return False, "有条件通过必须说明具体条件"

        # 验证结论与检查结果的一致性
        if order.overall_result == "PASSED" and order.failed_items > 0:
            return False, "存在不合格项，不能判定为合格"

        return True, None

    def get_cc_user_ids(self, entity_id: int) -> List[int]:
        """
        获取默认抄送人列表

        验收单审批抄送给：
        1. 关联项目的项目经理
        2. 质量部门负责人
        3. 如果是SAT/FINAL，抄送销售负责人

        Args:
            entity_id: 验收单ID

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

        # 质量部门负责人
        qa_dept_codes = ['QA', 'QC', 'QUALITY', '质量部', '品质部']
        qa_manager_ids = self.get_department_manager_user_ids_by_codes(qa_dept_codes)
        cc_users.extend(qa_manager_ids)

        # 如果没找到，尝试通过部门名称查找
        if not qa_manager_ids:
            qa_manager = self.get_department_manager_user_id('质量部')
            if qa_manager:
                cc_users.append(qa_manager)

        # 对于SAT/FINAL类型，添加销售负责人
        if order.acceptance_type in ['SAT', 'FINAL'] and order.project_id:
            sales_user_id = self.get_project_sales_user_id(order.project_id)
            if sales_user_id:
                cc_users.append(sales_user_id)

        return list(set(cc_users))  # 去重
