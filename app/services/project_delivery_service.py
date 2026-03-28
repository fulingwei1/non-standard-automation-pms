# -*- coding: utf-8 -*-
"""
项目交付排产计划服务

提供排产计划的创建、查询、更新、删除等业务逻辑
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.models.project_delivery import (
    ProjectDeliverySchedule,
    ProjectDeliveryTask,
    ProjectDeliveryLongCyclePurchase,
    ProjectDeliveryMechanicalDesign,
    ProjectDeliveryChangeLog,
    ProjectDeliveryDependency,
)
from app.models.user import User
from app.schemas.project_delivery import (
    ProjectDeliveryScheduleCreate,
    ProjectDeliveryScheduleUpdate,
    ProjectDeliveryTaskCreate,
    ProjectDeliveryLongCyclePurchaseCreate,
    ProjectDeliveryMechanicalDesignCreate,
    ProjectDeliveryChangeLogCreate,
)

logger = logging.getLogger(__name__)


class ProjectDeliveryService:
    """项目交付排产计划服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 排产计划 CRUD ====================
    
    def create_schedule(
        self,
        schedule_in: ProjectDeliveryScheduleCreate,
        initiator_id: int,
        initiator_name: str
    ) -> ProjectDeliverySchedule:
        """创建排产计划"""
        
        # 生成计划编号
        schedule_no = self._generate_schedule_no()
        
        # 创建排产计划
        schedule = ProjectDeliverySchedule(
            schedule_no=schedule_no,
            schedule_name=schedule_in.schedule_name,
            lead_id=schedule_in.lead_id,
            project_id=schedule_in.project_id,
            project_template_id=schedule_in.project_template_id,
            usage_type=schedule_in.usage_type,
            initiator_id=initiator_id,
            initiator_name=initiator_name,
            is_pre_contract=True,
            status="DRAFT",
            is_active=True,
        )
        
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        
        logger.info(f"Created project delivery schedule: {schedule.schedule_no}")
        return schedule
    
    def get_schedule(self, schedule_id: int) -> Optional[ProjectDeliverySchedule]:
        """获取排产计划详情"""
        return (
            self.db.query(ProjectDeliverySchedule)
            .filter(ProjectDeliverySchedule.id == schedule_id)
            .first()
        )
    
    def list_schedules(
        self,
        lead_id: Optional[int] = None,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        usage_type: Optional[str] = None,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[ProjectDeliverySchedule], int]:
        """获取排产计划列表"""
        
        query = self.db.query(ProjectDeliverySchedule)
        
        if lead_id:
            query = query.filter(ProjectDeliverySchedule.lead_id == lead_id)
        if project_id:
            query = query.filter(ProjectDeliverySchedule.project_id == project_id)
        if status:
            query = query.filter(ProjectDeliverySchedule.status == status)
        if usage_type:
            query = query.filter(ProjectDeliverySchedule.usage_type == usage_type)
        if is_active:
            query = query.filter(ProjectDeliverySchedule.is_active == is_active)
        
        total = query.count()
        items = query.order_by(desc(ProjectDeliverySchedule.created_at)).offset(skip).limit(limit).all()
        
        return items, total
    
    def update_schedule(
        self,
        schedule_id: int,
        schedule_in: ProjectDeliveryScheduleUpdate
    ) -> Optional[ProjectDeliverySchedule]:
        """更新排产计划"""
        
        schedule = self.get_schedule(schedule_id)
        if not schedule:
            return None
        
        update_data = schedule_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(schedule, field, value)
        
        schedule.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(schedule)
        
        logger.info(f"Updated project delivery schedule: {schedule.schedule_no}")
        return schedule
    
    def confirm_schedule(
        self,
        schedule_id: int,
        confirmed_by: int,
        confirmed_by_name: str
    ) -> Optional[ProjectDeliverySchedule]:
        """确认排产计划"""
        
        schedule = self.get_schedule(schedule_id)
        if not schedule:
            return None
        
        schedule.status = "CONFIRMED"
        schedule.confirmed_by = confirmed_by
        schedule.confirmed_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(schedule)
        
        logger.info(f"Confirmed project delivery schedule: {schedule.schedule_no}")
        return schedule
    
    def create_new_version(
        self,
        schedule_id: int,
        version_comment: str,
        initiator_id: int,
        initiator_name: str
    ) -> Optional[ProjectDeliverySchedule]:
        """创建新版本"""
        
        old_schedule = self.get_schedule(schedule_id)
        if not old_schedule:
            return None
        
        # 解析版本号
        version_parts = old_schedule.version.replace("V", "").split(".")
        major = int(version_parts[0])
        minor = int(version_parts[1]) if len(version_parts) > 1 else 0
        
        # 生成新版本号
        if old_schedule.contract_signed_at:
            # 合同签订后，主版本 +1
            new_version = f"V{major + 1}.0"
        else:
            # 合同签订前，次版本 +1
            new_version = f"V{major}.{minor + 1}"
        
        # 创建新版本
        new_schedule = ProjectDeliverySchedule(
            schedule_no=old_schedule.schedule_no,
            schedule_name=old_schedule.schedule_name,
            lead_id=old_schedule.lead_id,
            project_id=old_schedule.project_id,
            project_template_id=old_schedule.project_template_id,
            contract_id=old_schedule.contract_id,
            usage_type=old_schedule.usage_type,
            initiator_id=initiator_id,
            initiator_name=initiator_name,
            is_pre_contract=old_schedule.is_pre_contract,
            status="DRAFT",
            is_active=True,
            version=new_version,
            version_comment=version_comment,
            parent_version_id=schedule_id,
        )
        
        # 标记旧版本为非活跃
        old_schedule.is_active = False
        
        self.db.add(new_schedule)
        self.db.commit()
        self.db.refresh(new_schedule)
        
        logger.info(f"Created new version: {new_version} from {old_schedule.version}")
        return new_schedule
    
    def link_contract(
        self,
        schedule_id: int,
        contract_id: int,
        contract_signed_at: datetime
    ) -> Optional[ProjectDeliverySchedule]:
        """关联合同"""
        
        schedule = self.get_schedule(schedule_id)
        if not schedule:
            return None
        
        schedule.contract_id = contract_id
        schedule.contract_signed_at = contract_signed_at
        schedule.is_pre_contract = False
        
        self.db.commit()
        self.db.refresh(schedule)
        
        logger.info(f"Linked contract {contract_id} to schedule {schedule.schedule_no}")
        return schedule
    
    # ==================== 任务管理 ====================
    
    def create_task(
        self,
        schedule_id: int,
        task_in: ProjectDeliveryTaskCreate
    ) -> ProjectDeliveryTask:
        """创建任务"""
        
        # 生成任务编号
        task_no = self._generate_task_no(schedule_id)
        
        task = ProjectDeliveryTask(
            schedule_id=schedule_id,
            task_no=task_no,
            **task_in.model_dump()
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        # 检测冲突
        self._detect_task_conflicts(task)
        
        return task
    
    def get_tasks(self, schedule_id: int) -> List[ProjectDeliveryTask]:
        """获取任务列表"""
        return (
            self.db.query(ProjectDeliveryTask)
            .filter(ProjectDeliveryTask.schedule_id == schedule_id)
            .order_by(ProjectDeliveryTask.task_no)
            .all()
        )
    
    # ==================== 长周期采购管理 ====================
    
    def create_long_cycle_purchase(
        self,
        schedule_id: int,
        purchase_in: ProjectDeliveryLongCyclePurchaseCreate
    ) -> ProjectDeliveryLongCyclePurchase:
        """创建长周期采购"""
        
        # 生成物料编号
        item_no = self._generate_purchase_item_no(schedule_id)
        
        purchase = ProjectDeliveryLongCyclePurchase(
            schedule_id=schedule_id,
            item_no=item_no,
            **purchase_in.model_dump()
        )
        
        self.db.add(purchase)
        self.db.commit()
        self.db.refresh(purchase)
        
        # 检测冲突（交期过长）
        if purchase.lead_time_days > 90:
            purchase.has_conflict = True
            purchase.conflict_reason = f"交期过长：{purchase.lead_time_days}天，可能影响项目进度"
            self.db.commit()
        
        return purchase
    
    def get_long_cycle_purchases(self, schedule_id: int) -> List[ProjectDeliveryLongCyclePurchase]:
        """获取长周期采购列表"""
        return (
            self.db.query(ProjectDeliveryLongCyclePurchase)
            .filter(ProjectDeliveryLongCyclePurchase.schedule_id == schedule_id)
            .order_by(ProjectDeliveryLongCyclePurchase.item_no)
            .all()
        )
    
    # ==================== 机械设计任务管理 ====================
    
    def create_mechanical_design(
        self,
        schedule_id: int,
        design_in: ProjectDeliveryMechanicalDesignCreate
    ) -> ProjectDeliveryMechanicalDesign:
        """创建机械设计任务"""
        
        design = ProjectDeliveryMechanicalDesign(
            schedule_id=schedule_id,
            **design_in.model_dump()
        )
        
        self.db.add(design)
        self.db.commit()
        self.db.refresh(design)
        
        return design
    
    def get_mechanical_designs(self, schedule_id: int) -> List[ProjectDeliveryMechanicalDesign]:
        """获取机械设计任务列表"""
        return (
            self.db.query(ProjectDeliveryMechanicalDesign)
            .filter(ProjectDeliveryMechanicalDesign.schedule_id == schedule_id)
            .order_by(ProjectDeliveryMechanicalDesign.design_type)
            .all()
        )
    
    # ==================== 变更管理 ====================
    
    def create_change_log(
        self,
        schedule_id: int,
        change_in: ProjectDeliveryChangeLogCreate
    ) -> ProjectDeliveryChangeLog:
        """创建变更日志"""
        
        # 生成变更编号
        change_no = self._generate_change_no(schedule_id)
        
        change_log = ProjectDeliveryChangeLog(
            schedule_id=schedule_id,
            change_no=change_no,
            changed_at=datetime.now(),
            **change_in.model_dump()
        )
        
        self.db.add(change_log)
        self.db.commit()
        self.db.refresh(change_log)
        
        # 更新排产计划状态
        schedule = self.get_schedule(schedule_id)
        if schedule and schedule.status == "CONFIRMED":
            schedule.status = "CHANGED"
            self.db.commit()
        
        return change_log
    
    def get_change_logs(self, schedule_id: int) -> List[ProjectDeliveryChangeLog]:
        """获取变更日志列表"""
        return (
            self.db.query(ProjectDeliveryChangeLog)
            .filter(ProjectDeliveryChangeLog.schedule_id == schedule_id)
            .order_by(desc(ProjectDeliveryChangeLog.changed_at))
            .all()
        )
    
    # ==================== 甘特图数据 ====================
    
    def get_gantt_data(self, schedule_id: int) -> Dict[str, Any]:
        """获取甘特图数据"""
        
        schedule = self.get_schedule(schedule_id)
        if not schedule:
            return {}
        
        # 获取任务
        tasks = self.get_tasks(schedule_id)
        gantt_tasks = [
            {
                "id": task.id,
                "task_no": task.task_no,
                "name": task.task_name,
                "engineer": task.assigned_engineer_name,
                "department": task.department_name,
                "machine": task.machine_name,
                "module": task.module_name,
                "start": task.planned_start,
                "end": task.planned_end,
                "hours": float(task.estimated_hours),
                "progress": float(task.progress_pct),
                "has_conflict": task.has_conflict,
                "predecessors": task.predecessor_tasks,
            }
            for task in tasks
        ]
        
        # 获取长周期采购
        purchases = self.get_long_cycle_purchases(schedule_id)
        gantt_purchases = [
            {
                "id": purchase.id,
                "item_no": purchase.item_no,
                "material": purchase.material_name,
                "supplier": purchase.supplier,
                "lead_time": purchase.lead_time_days,
                "order_date": purchase.planned_order_date,
                "arrival_date": purchase.planned_arrival_date,
                "is_critical": purchase.is_critical,
                "has_conflict": purchase.has_conflict,
            }
            for purchase in purchases
        ]
        
        # 获取依赖关系
        dependencies = (
            self.db.query(ProjectDeliveryDependency)
            .filter(ProjectDeliveryDependency.schedule_id == schedule_id)
            .all()
        )
        gantt_dependencies = [
            {
                "from_task": dep.predecessor_task_id,
                "to_task": dep.successor_task_id,
                "type": dep.dependency_type,
                "lag_days": dep.lag_days,
            }
            for dep in dependencies
        ]
        
        return {
            "schedule_id": schedule.id,
            "schedule_name": schedule.schedule_name,
            "version": schedule.version,
            "tasks": gantt_tasks,
            "long_cycle_purchases": gantt_purchases,
            "dependencies": gantt_dependencies,
        }
    
    # ==================== 冲突检测 ====================
    
    def detect_conflicts(self, schedule_id: int) -> Dict[str, Any]:
        """检测冲突"""
        
        tasks = self.get_tasks(schedule_id)
        purchases = self.get_long_cycle_purchases(schedule_id)
        
        engineer_conflicts = []
        purchase_conflicts = []
        
        # 检测工程师时间冲突
        engineer_conflicts = self._detect_engineer_conflicts(tasks)
        
        # 检测长周期采购冲突
        for purchase in purchases:
            if purchase.has_conflict:
                purchase_conflicts.append({
                    "purchase_id": purchase.id,
                    "material_name": purchase.material_name,
                    "supplier": purchase.supplier,
                    "lead_time_days": purchase.lead_time_days,
                    "reason": purchase.conflict_reason,
                })
        
        return {
            "schedule_id": schedule_id,
            "has_conflicts": len(engineer_conflicts) > 0 or len(purchase_conflicts) > 0,
            "engineer_conflicts": engineer_conflicts,
            "purchase_conflicts": purchase_conflicts,
            "total_conflicts": len(engineer_conflicts) + len(purchase_conflicts),
        }
    
    # ==================== 辅助方法 ====================
    
    def _generate_schedule_no(self) -> str:
        """生成计划编号 PDS-2026-001"""
        year = datetime.now().year
        max_schedule = (
            self.db.query(ProjectDeliverySchedule)
            .filter(ProjectDeliverySchedule.schedule_no.like(f"PDS-{year}-%"))
            .order_by(desc(ProjectDeliverySchedule.schedule_no))
            .first()
        )
        
        if max_schedule:
            last_no = int(max_schedule.schedule_no.split("-")[-1])
            new_no = last_no + 1
        else:
            new_no = 1
        
        return f"PDS-{year}-{new_no:03d}"
    
    def _generate_task_no(self, schedule_id: int) -> str:
        """生成任务编号 T001, T002"""
        max_task = (
            self.db.query(ProjectDeliveryTask)
            .filter(ProjectDeliveryTask.schedule_id == schedule_id)
            .order_by(desc(ProjectDeliveryTask.task_no))
            .first()
        )
        
        if max_task:
            last_no = int(max_task.task_no.replace("T", ""))
            new_no = last_no + 1
        else:
            new_no = 1
        
        return f"T{new_no:03d}"
    
    def _generate_purchase_item_no(self, schedule_id: int) -> str:
        """生成物料编号 M001, M002"""
        max_purchase = (
            self.db.query(ProjectDeliveryLongCyclePurchase)
            .filter(ProjectDeliveryLongCyclePurchase.schedule_id == schedule_id)
            .order_by(desc(ProjectDeliveryLongCyclePurchase.item_no))
            .first()
        )
        
        if max_purchase:
            last_no = int(max_purchase.item_no.replace("M", ""))
            new_no = last_no + 1
        else:
            new_no = 1
        
        return f"M{new_no:03d}"
    
    def _generate_change_no(self, schedule_id: int) -> str:
        """生成变更编号 CHG001, CHG002"""
        max_change = (
            self.db.query(ProjectDeliveryChangeLog)
            .filter(ProjectDeliveryChangeLog.schedule_id == schedule_id)
            .order_by(desc(ProjectDeliveryChangeLog.change_no))
            .first()
        )
        
        if max_change:
            last_no = int(max_change.change_no.replace("CHG", ""))
            new_no = last_no + 1
        else:
            new_no = 1
        
        return f"CHG{new_no:03d}"
    
    def _detect_task_conflicts(self, task: ProjectDeliveryTask) -> None:
        """检测任务冲突"""
        
        if not task.assigned_engineer_id:
            return
        
        # 查找该工程师在同一时间段内的其他任务
        conflicts = (
            self.db.query(ProjectDeliveryTask)
            .filter(
                ProjectDeliveryTask.assigned_engineer_id == task.assigned_engineer_id,
                ProjectDeliveryTask.id != task.id,
                ProjectDeliveryTask.planned_start <= task.planned_end,
                ProjectDeliveryTask.planned_end >= task.planned_start,
            )
            .all()
        )
        
        if conflicts:
            task.has_conflict = True
            task.conflict_details = {
                "engineer_id": task.assigned_engineer_id,
                "engineer_name": task.assigned_engineer_name,
                "conflicting_tasks": [
                    {
                        "task_id": c.id,
                        "task_name": c.task_name,
                        "start": str(c.planned_start),
                        "end": str(c.planned_end),
                    }
                    for c in conflicts
                ],
            }
            self.db.commit()
    
    def _detect_engineer_conflicts(self, tasks: List[ProjectDeliveryTask]) -> List[Dict[str, Any]]:
        """检测工程师时间冲突"""
        
        conflicts = []
        tasks_by_engineer = {}
        
        # 按工程师分组
        for task in tasks:
            if task.assigned_engineer_id:
                if task.assigned_engineer_id not in tasks_by_engineer:
                    tasks_by_engineer[task.assigned_engineer_id] = []
                tasks_by_engineer[task.assigned_engineer_id].append(task)
        
        # 检测每个工程师的任务冲突
        for engineer_id, engineer_tasks in tasks_by_engineer.items():
            for i, task1 in enumerate(engineer_tasks):
                for task2 in engineer_tasks[i+1:]:
                    # 检查时间重叠
                    if task1.planned_start <= task2.planned_end and task1.planned_end >= task2.planned_start:
                        # 计算重叠天数
                        overlap_start = max(task1.planned_start, task2.planned_start)
                        overlap_end = min(task1.planned_end, task2.planned_end)
                        overlap_days = (overlap_end - overlap_start).days + 1
                        
                        conflicts.append({
                            "engineer_id": engineer_id,
                            "engineer_name": task1.assigned_engineer_name,
                            "task1_id": task1.id,
                            "task1_name": task1.task_name,
                            "task1_start": str(task1.planned_start),
                            "task1_end": str(task1.planned_end),
                            "task2_id": task2.id,
                            "task2_name": task2.task_name,
                            "task2_start": str(task2.planned_start),
                            "task2_end": str(task2.planned_end),
                            "overlap_days": overlap_days,
                        })
        
        return conflicts


# 快捷函数
def get_project_delivery_service(db: Session) -> ProjectDeliveryService:
    """获取项目交付排产计划服务"""
    return ProjectDeliveryService(db)
