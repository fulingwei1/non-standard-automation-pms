# -*- coding: utf-8 -*-
"""
ECN集成服务：处理ECN与BOM、项目、采购的同步逻辑
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.ecn import Ecn, EcnAffectedMaterial, EcnAffectedOrder, EcnBomChange, EcnTask
from app.models.material import BomItem
from app.models.project import Project
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.schemas.ecn import EcnTaskCreate
from app.services.ecn.ecn_auto_assign_service import auto_assign_task
from app.services.ecn.notification import notify_task_assigned
from app.utils.db_helpers import get_or_404

logger = logging.getLogger(__name__)


class EcnIntegrationService:
    """ECN集成服务：处理ECN与其他系统的数据同步"""

    def __init__(self, db: Session):
        self.db = db

    def sync_to_bom(self, ecn_id: int) -> Dict[str, Any]:
        """
        将ECN变更同步到BOM

        Args:
            ecn_id: ECN ID

        Returns:
            同步结果字典，包含更新数量

        Raises:
            ValueError: 当ECN状态不允许同步时
        """
        ecn = get_or_404(self.db, Ecn, ecn_id, "ECN不存在")

        if ecn.status not in ["APPROVED", "EXECUTING"]:
            raise ValueError("只能同步已审批或执行中的ECN")

        affected_materials = (
            self.db.query(EcnAffectedMaterial)
            .filter(EcnAffectedMaterial.ecn_id == ecn_id, EcnAffectedMaterial.status == "PENDING")
            .all()
        )

        updated_count = 0
        for am in affected_materials:
            if am.bom_item_id:
                bom_item = self.db.query(BomItem).filter(BomItem.id == am.bom_item_id).first()
                if bom_item:
                    # 根据变更类型更新BOM
                    # EBC-1: 列名是 quantity（原误用 bom_item.qty 导致数量变更静默丢失）
                    old_parts = []
                    new_parts = []
                    if am.change_type in ("UPDATE", "REPLACE"):
                        if am.new_quantity:
                            old_parts.append(f"数量:{bom_item.quantity}")
                            new_parts.append(f"数量:{float(am.new_quantity)}")
                            bom_item.quantity = float(am.new_quantity)
                        if am.new_specification:
                            old_parts.append(f"规格:{bom_item.specification}")
                            new_parts.append(f"规格:{am.new_specification}")
                            bom_item.specification = am.new_specification
                        # REPLACE 额外支持换料号
                        if am.change_type == "REPLACE" and am.material_id:
                            old_parts.append(f"料号ID:{bom_item.material_id}")
                            new_parts.append(f"料号ID:{am.material_id}")
                            bom_item.material_id = am.material_id

                    now = datetime.now()
                    am.status = "PROCESSED"
                    am.processed_at = now
                    self.db.add(bom_item)
                    self.db.add(am)
                    # 审计留痕：记录到 ecn_bom_changes
                    self.db.add(
                        EcnBomChange(
                            ecn_id=ecn_id,
                            bom_id=bom_item.bom_id,
                            project_id=ecn.project_id,
                            material_code=am.material_code,
                            change_action=am.change_type,
                            old_value="; ".join(old_parts) or (am.old_specification or ""),
                            new_value="; ".join(new_parts) or (am.new_specification or ""),
                            cost_impact=am.cost_impact or Decimal("0"),
                            applied_at=now,
                        )
                    )
                    updated_count += 1

        self.db.commit()

        return {"updated_count": updated_count}

    def sync_to_bom_if_ready(self, ecn_id: int) -> Dict[str, Any]:
        """在 ECN 已批准或执行中时幂等同步 BOM。"""
        ecn = get_or_404(self.db, Ecn, ecn_id, "ECN不存在")
        if ecn.status not in ["APPROVED", "EXECUTING"]:
            return {"updated_count": 0, "skipped": True, "reason": f"ECN状态{ecn.status}不可同步"}
        return self.sync_to_bom(ecn_id)

    def sync_to_project(self, ecn_id: int) -> Dict[str, Any]:
        """
        将ECN变更同步到项目

        Args:
            ecn_id: ECN ID

        Returns:
            同步结果字典，包含成本和工期影响

        Raises:
            ValueError: 当ECN未关联项目时
        """
        ecn = get_or_404(self.db, Ecn, ecn_id, "ECN不存在")

        if not ecn.project_id:
            raise ValueError("ECN未关联项目")

        project = self.db.query(Project).filter(Project.id == ecn.project_id).first()
        if not project:
            raise ValueError("项目不存在")

        # 更新项目成本（累加ECN的成本影响）
        if ecn.cost_impact:
            project.total_cost = (project.total_cost or Decimal("0")) + ecn.cost_impact

        # 更新项目工期（累加ECN的工期影响）
        if ecn.schedule_impact_days:
            if project.planned_end_date:
                project.planned_end_date = project.planned_end_date + timedelta(
                    days=ecn.schedule_impact_days
                )

        self.db.add(project)
        self.db.commit()

        return {
            "cost_impact": float(ecn.cost_impact or 0),
            "schedule_impact_days": ecn.schedule_impact_days or 0,
        }

    def sync_to_purchase(self, ecn_id: int, current_user_id: int) -> Dict[str, Any]:
        """
        将ECN变更同步到采购订单

        Args:
            ecn_id: ECN ID
            current_user_id: 当前用户ID

        Returns:
            同步结果字典，包含更新数量
        """
        ecn = get_or_404(self.db, Ecn, ecn_id, "ECN不存在")
        created_count = self._ensure_purchase_affected_orders(ecn)

        affected_orders = (
            self.db.query(EcnAffectedOrder)
            .filter(
                EcnAffectedOrder.ecn_id == ecn_id,
                EcnAffectedOrder.order_type == "PURCHASE",
                EcnAffectedOrder.status == "PENDING",
            )
            .all()
        )

        updated_count = 0
        cancelled_count = 0
        change_required_count = 0
        for ao in affected_orders:
            order = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == ao.order_id).first()
            if order:
                # 根据处理方式更新订单
                if ao.action_type == "CANCEL":
                    order.status = "CANCELLED"
                    self._append_purchase_ecn_note(ecn, order, "采购订单已按ECN取消")
                    ao.status = "PROCESSED"
                    cancelled_count += 1
                elif ao.action_type == "MODIFY":
                    self._mark_purchase_change_required(ecn, order, ao)
                    change_required_count += 1
                else:
                    self._mark_purchase_change_required(ecn, order, ao)
                    change_required_count += 1

                ao.processed_by = current_user_id
                ao.processed_at = datetime.now()
                self.db.add(order)
                self.db.add(ao)
                updated_count += 1

        self.db.commit()

        return {
            "updated_count": updated_count,
            "created_count": created_count,
            "cancelled_count": cancelled_count,
            "change_required_count": change_required_count,
        }

    def _ensure_purchase_affected_orders(self, ecn: Ecn) -> int:
        affected_materials = (
            self.db.query(EcnAffectedMaterial)
            .filter(EcnAffectedMaterial.ecn_id == ecn.id)
            .all()
        )
        if not affected_materials:
            return 0

        impacts_by_order: dict[int, dict[str, Any]] = {}
        for affected_material in affected_materials:
            if not affected_material.material_id:
                continue
            rows = (
                self.db.query(PurchaseOrderItem, PurchaseOrder)
                .join(PurchaseOrder, PurchaseOrder.id == PurchaseOrderItem.order_id)
                .filter(PurchaseOrderItem.material_id == affected_material.material_id)
                .filter(PurchaseOrder.status.notin_(["CANCELLED", "DRAFT"]))
                .order_by(desc(PurchaseOrder.created_at))
                .all()
            )
            for _order_item, order in rows:
                impact = impacts_by_order.setdefault(
                    order.id,
                    {
                        "order": order,
                        "descriptions": [],
                    },
                )
                impact["descriptions"].append(
                    self._build_purchase_impact_description(affected_material)
                )

        created_count = 0
        for order_id, impact in impacts_by_order.items():
            existing = (
                self.db.query(EcnAffectedOrder)
                .filter(
                    EcnAffectedOrder.ecn_id == ecn.id,
                    EcnAffectedOrder.order_type == "PURCHASE",
                    EcnAffectedOrder.order_id == order_id,
                )
                .first()
            )
            description = "；".join(dict.fromkeys(impact["descriptions"]))
            if existing:
                if not existing.impact_description:
                    existing.impact_description = description
                if not existing.action_type:
                    existing.action_type = "MODIFY"
                if not existing.action_description:
                    existing.action_description = self._default_purchase_review_action(ecn)
                self.db.add(existing)
                continue

            order = impact["order"]
            self.db.add(
                EcnAffectedOrder(
                    ecn_id=ecn.id,
                    order_type="PURCHASE",
                    order_id=order.id,
                    order_no=order.order_no,
                    impact_description=description,
                    action_type="MODIFY",
                    action_description=self._default_purchase_review_action(ecn),
                    status="PENDING",
                )
            )
            created_count += 1

        if created_count:
            self.db.flush()
        return created_count

    @staticmethod
    def _build_purchase_impact_description(affected_material: EcnAffectedMaterial) -> str:
        parts = [
            f"物料 {affected_material.material_code} {affected_material.change_type}",
        ]
        if affected_material.old_quantity is not None or affected_material.new_quantity is not None:
            parts.append(f"数量 {affected_material.old_quantity}→{affected_material.new_quantity}")
        if (
            affected_material.old_specification is not None
            or affected_material.new_specification is not None
        ):
            parts.append(
                f"规格 {affected_material.old_specification or '-'}"
                f"→{affected_material.new_specification or '-'}"
            )
        if affected_material.new_supplier_id:
            parts.append(f"新供应商ID {affected_material.new_supplier_id}")
        if affected_material.cost_impact:
            parts.append(f"成本影响 {affected_material.cost_impact}")
        return "，".join(parts)

    @staticmethod
    def _default_purchase_review_action(ecn: Ecn) -> str:
        return (
            f"采购需评审 ECN {ecn.ecn_no} 对采购数量、规格、供应商、交期和价格的影响；"
            "确认后修改或取消对应采购行。"
        )

    def _mark_purchase_change_required(
        self, ecn: Ecn, order: PurchaseOrder, affected_order: EcnAffectedOrder
    ) -> None:
        affected_order.action_type = affected_order.action_type or "MODIFY"
        affected_order.action_description = (
            affected_order.action_description or self._default_purchase_review_action(ecn)
        )
        affected_order.status = "CHANGE_REQUIRED"
        self._append_purchase_ecn_note(ecn, order, affected_order.action_description)

    @staticmethod
    def _append_purchase_ecn_note(ecn: Ecn, order: PurchaseOrder, note: str) -> None:
        ecn_note = f"[ECN {ecn.ecn_no}] {note}"
        existing = order.remark or ""
        if ecn_note in existing:
            return
        order.remark = f"{existing}\n{ecn_note}".strip()

    def batch_sync_to_bom(self, ecn_ids: List[int]) -> Dict[str, Any]:
        """
        批量同步ECN变更到BOM

        Args:
            ecn_ids: ECN ID列表

        Returns:
            批量同步结果，包含总数、成功数、失败数和详细结果
        """
        results = []
        success_count = 0
        fail_count = 0

        for ecn_id in ecn_ids:
            try:
                ecn = self.db.query(Ecn).filter(Ecn.id == ecn_id).first()
                if not ecn:
                    results.append({"ecn_id": ecn_id, "status": "failed", "message": "ECN不存在"})
                    fail_count += 1
                    continue

                if ecn.status not in ["APPROVED", "EXECUTING"]:
                    results.append(
                        {
                            "ecn_id": ecn_id,
                            "status": "failed",
                            "message": "只能同步已审批或执行中的ECN",
                        }
                    )
                    fail_count += 1
                    continue

                # 调用单个同步逻辑
                sync_result = self.sync_to_bom(ecn_id)
                results.append(
                    {
                        "ecn_id": ecn_id,
                        "ecn_no": ecn.ecn_no,
                        "status": "success",
                        "updated_count": sync_result["updated_count"],
                    }
                )
                success_count += 1
            except Exception as e:
                self.db.rollback()
                results.append({"ecn_id": ecn_id, "status": "failed", "message": str(e)})
                fail_count += 1

        return {
            "total": len(ecn_ids),
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results,
        }

    def batch_sync_to_project(self, ecn_ids: List[int]) -> Dict[str, Any]:
        """
        批量同步ECN变更到项目

        Args:
            ecn_ids: ECN ID列表

        Returns:
            批量同步结果，包含总数、成功数、失败数和详细结果
        """
        results = []
        success_count = 0
        fail_count = 0

        for ecn_id in ecn_ids:
            try:
                ecn = self.db.query(Ecn).filter(Ecn.id == ecn_id).first()
                if not ecn:
                    results.append({"ecn_id": ecn_id, "status": "failed", "message": "ECN不存在"})
                    fail_count += 1
                    continue

                if not ecn.project_id:
                    results.append(
                        {"ecn_id": ecn_id, "status": "failed", "message": "ECN未关联项目"}
                    )
                    fail_count += 1
                    continue

                project = self.db.query(Project).filter(Project.id == ecn.project_id).first()
                if not project:
                    results.append({"ecn_id": ecn_id, "status": "failed", "message": "项目不存在"})
                    fail_count += 1
                    continue

                # 调用单个同步逻辑
                sync_result = self.sync_to_project(ecn_id)
                results.append(
                    {
                        "ecn_id": ecn_id,
                        "ecn_no": ecn.ecn_no,
                        "project_id": ecn.project_id,
                        "status": "success",
                        "cost_impact": sync_result["cost_impact"],
                        "schedule_impact_days": sync_result["schedule_impact_days"],
                    }
                )
                success_count += 1
            except Exception as e:
                self.db.rollback()
                results.append({"ecn_id": ecn_id, "status": "failed", "message": str(e)})
                fail_count += 1

        return {
            "total": len(ecn_ids),
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results,
        }

    def batch_sync_to_purchase(self, ecn_ids: List[int], current_user_id: int) -> Dict[str, Any]:
        """
        批量同步ECN变更到采购

        Args:
            ecn_ids: ECN ID列表
            current_user_id: 当前用户ID

        Returns:
            批量同步结果，包含总数、成功数、失败数和详细结果
        """
        results = []
        success_count = 0
        fail_count = 0

        for ecn_id in ecn_ids:
            try:
                ecn = self.db.query(Ecn).filter(Ecn.id == ecn_id).first()
                if not ecn:
                    results.append({"ecn_id": ecn_id, "status": "failed", "message": "ECN不存在"})
                    fail_count += 1
                    continue

                # 调用单个同步逻辑
                sync_result = self.sync_to_purchase(ecn_id, current_user_id)
                results.append(
                    {
                        "ecn_id": ecn_id,
                        "ecn_no": ecn.ecn_no,
                        "status": "success",
                        "updated_count": sync_result["updated_count"],
                    }
                )
                success_count += 1
            except Exception as e:
                self.db.rollback()
                results.append({"ecn_id": ecn_id, "status": "failed", "message": str(e)})
                fail_count += 1

        return {
            "total": len(ecn_ids),
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results,
        }

    def batch_create_tasks(self, ecn_id: int, tasks: List[EcnTaskCreate]) -> Dict[str, Any]:
        """
        批量创建ECN执行任务

        Args:
            ecn_id: ECN ID
            tasks: 任务创建数据列表

        Returns:
            创建结果，包含ECN ID、创建数量和任务ID列表

        Raises:
            ValueError: 当ECN不在执行阶段时
        """
        ecn = get_or_404(self.db, Ecn, ecn_id, "ECN不存在")

        if ecn.status not in ["APPROVED", "EXECUTING"]:
            raise ValueError("ECN当前不在执行阶段")

        # 获取最大任务序号
        max_order = (
            self.db.query(EcnTask)
            .filter(EcnTask.ecn_id == ecn_id)
            .order_by(desc(EcnTask.task_no))
            .first()
        )
        start_no = (max_order.task_no + 1) if max_order else 1

        created_tasks = []
        for idx, task_in in enumerate(tasks):
            task = EcnTask(
                ecn_id=ecn_id,
                task_no=start_no + idx,
                task_name=task_in.task_name,
                task_type=task_in.task_type,
                task_dept=task_in.task_dept,
                task_description=task_in.task_description,
                assignee_id=task_in.assignee_id,
                planned_start=task_in.planned_start,
                planned_end=task_in.planned_end,
                status="PENDING",
                progress_pct=0,
            )

            # 如果没有指定负责人，自动分配
            if not task.assignee_id:
                try:
                    assignee_id = auto_assign_task(self.db, ecn, task)
                    if assignee_id:
                        task.assignee_id = assignee_id
                except Exception as e:
                    logger.error(f"Failed to auto assign task: {e}")

            self.db.add(task)
            created_tasks.append(task)

            # 发送通知
            if task.assignee_id:
                try:
                    notify_task_assigned(self.db, ecn, task, task.assignee_id)
                except Exception as e:
                    logger.error(f"Failed to send task assigned notification: {e}")

        # 如果ECN状态是已审批，自动更新为执行中
        if ecn.status == "APPROVED":
            ecn.status = "EXECUTING"
            ecn.execution_start = datetime.now()
            ecn.current_step = "EXECUTION"
            self.db.add(ecn)

        self.db.commit()

        # 刷新任务以获取ID
        for task in created_tasks:
            self.db.refresh(task)

        return {
            "ecn_id": ecn_id,
            "created_count": len(created_tasks),
            "task_ids": [task.id for task in created_tasks],
        }
