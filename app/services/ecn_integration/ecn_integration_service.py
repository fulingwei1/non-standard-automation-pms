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

from app.models.ecn import Ecn, EcnAffectedMaterial, EcnAffectedOrder, EcnTask
from app.models.material import BomItem
from app.models.project import Project
from app.models.purchase import PurchaseOrder
from app.schemas.ecn import EcnTaskCreate
from app.services.ecn_auto_assign_service import auto_assign_task
from app.services.ecn_notification import notify_task_assigned
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

        affected_materials = self.db.query(EcnAffectedMaterial).filter(
            EcnAffectedMaterial.ecn_id == ecn_id,
            EcnAffectedMaterial.status == "PENDING"
        ).all()

        updated_count = 0
        for am in affected_materials:
            if am.bom_item_id:
                bom_item = self.db.query(BomItem).filter(BomItem.id == am.bom_item_id).first()
                if bom_item:
                    # 根据变更类型更新BOM
                    if am.change_type == "UPDATE":
                        if am.new_quantity:
                            bom_item.qty = float(am.new_quantity)
                        if am.new_specification:
                            bom_item.specification = am.new_specification
                    elif am.change_type == "REPLACE" and am.material_id:
                        bom_item.material_id = am.material_id

                    am.status = "PROCESSED"
                    am.processed_at = datetime.now()
                    self.db.add(bom_item)
                    self.db.add(am)
                    updated_count += 1

        self.db.commit()

        return {"updated_count": updated_count}

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
                project.planned_end_date = project.planned_end_date + timedelta(days=ecn.schedule_impact_days)

        self.db.add(project)
        self.db.commit()

        return {
            "cost_impact": float(ecn.cost_impact or 0),
            "schedule_impact_days": ecn.schedule_impact_days or 0
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

        affected_orders = self.db.query(EcnAffectedOrder).filter(
            EcnAffectedOrder.ecn_id == ecn_id,
            EcnAffectedOrder.order_type == "PURCHASE",
            EcnAffectedOrder.status == "PENDING"
        ).all()

        updated_count = 0
        for ao in affected_orders:
            order = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == ao.order_id).first()
            if order:
                # 根据处理方式更新订单
                if ao.action_type == "CANCEL":
                    order.status = "CANCELLED"
                elif ao.action_type == "MODIFY":
                    # 可以添加更详细的订单修改逻辑
                    pass

                ao.status = "PROCESSED"
                ao.processed_by = current_user_id
                ao.processed_at = datetime.now()
                self.db.add(order)
                self.db.add(ao)
                updated_count += 1

        self.db.commit()

        return {"updated_count": updated_count}

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
                    results.append({
                        "ecn_id": ecn_id,
                        "status": "failed",
                        "message": "只能同步已审批或执行中的ECN"
                    })
                    fail_count += 1
                    continue

                # 调用单个同步逻辑
                sync_result = self.sync_to_bom(ecn_id)
                results.append({
                    "ecn_id": ecn_id,
                    "ecn_no": ecn.ecn_no,
                    "status": "success",
                    "updated_count": sync_result["updated_count"]
                })
                success_count += 1
            except Exception as e:
                self.db.rollback()
                results.append({"ecn_id": ecn_id, "status": "failed", "message": str(e)})
                fail_count += 1

        return {
            "total": len(ecn_ids),
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results
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
                    results.append({"ecn_id": ecn_id, "status": "failed", "message": "ECN未关联项目"})
                    fail_count += 1
                    continue

                project = self.db.query(Project).filter(Project.id == ecn.project_id).first()
                if not project:
                    results.append({"ecn_id": ecn_id, "status": "failed", "message": "项目不存在"})
                    fail_count += 1
                    continue

                # 调用单个同步逻辑
                sync_result = self.sync_to_project(ecn_id)
                results.append({
                    "ecn_id": ecn_id,
                    "ecn_no": ecn.ecn_no,
                    "project_id": ecn.project_id,
                    "status": "success",
                    "cost_impact": sync_result["cost_impact"],
                    "schedule_impact_days": sync_result["schedule_impact_days"]
                })
                success_count += 1
            except Exception as e:
                self.db.rollback()
                results.append({"ecn_id": ecn_id, "status": "failed", "message": str(e)})
                fail_count += 1

        return {
            "total": len(ecn_ids),
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results
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
                results.append({
                    "ecn_id": ecn_id,
                    "ecn_no": ecn.ecn_no,
                    "status": "success",
                    "updated_count": sync_result["updated_count"]
                })
                success_count += 1
            except Exception as e:
                self.db.rollback()
                results.append({"ecn_id": ecn_id, "status": "failed", "message": str(e)})
                fail_count += 1

        return {
            "total": len(ecn_ids),
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results
        }

    def batch_create_tasks(
        self, 
        ecn_id: int, 
        tasks: List[EcnTaskCreate]
    ) -> Dict[str, Any]:
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
        max_order = self.db.query(EcnTask).filter(
            EcnTask.ecn_id == ecn_id
        ).order_by(desc(EcnTask.task_no)).first()
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
                progress_pct=0
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
            "task_ids": [task.id for task in created_tasks]
        }
