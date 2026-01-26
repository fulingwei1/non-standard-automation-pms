# -*- coding: utf-8 -*-
"""
节点子任务服务

提供节点子任务的 CRUD 操作、状态流转、与节点完成的联动
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.enums import StageStatusEnum
from app.models.stage_instance import NodeTask, ProjectNodeInstance


class NodeTaskService:
    """节点子任务服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 任务 CRUD ====================

    def create_task(
        self,
        node_instance_id: int,
        task_name: str,
        task_code: Optional[str] = None,
        description: Optional[str] = None,
        estimated_hours: Optional[int] = None,
        planned_start_date: Optional[date] = None,
        planned_end_date: Optional[date] = None,
        assignee_id: Optional[int] = None,
        priority: str = "NORMAL",
        tags: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> NodeTask:
        """
        创建子任务

        Args:
            node_instance_id: 所属节点实例ID
            task_name: 任务名称
            task_code: 任务编码（不传则自动生成）
            description: 任务描述
            estimated_hours: 预计工时
            planned_start_date: 计划开始日期
            planned_end_date: 计划结束日期
            assignee_id: 执行人ID（默认继承节点负责人）
            priority: 优先级
            tags: 标签
            created_by: 创建人ID

        Returns:
            NodeTask: 创建的任务
        """
        # 验证节点存在
        node = self.db.query(ProjectNodeInstance).filter(
            ProjectNodeInstance.id == node_instance_id
        ).first()

        if not node:
            raise ValueError(f"节点实例 {node_instance_id} 不存在")

        # 自动生成任务编码
        if not task_code:
            task_count = self.db.query(NodeTask).filter(
                NodeTask.node_instance_id == node_instance_id
            ).count()
            task_code = f"{node.node_code}T{task_count + 1:02d}"

        # 获取下一个序号
        max_seq = self.db.query(NodeTask).filter(
            NodeTask.node_instance_id == node_instance_id
        ).count()

        # 如果未指定执行人，继承节点负责人
        if assignee_id is None:
            assignee_id = node.assignee_id

        task = NodeTask(
            node_instance_id=node_instance_id,
            task_code=task_code,
            task_name=task_name,
            description=description,
            sequence=max_seq,
            status=StageStatusEnum.PENDING.value,
            estimated_hours=estimated_hours,
            planned_start_date=planned_start_date,
            planned_end_date=planned_end_date,
            assignee_id=assignee_id,
            priority=priority,
            tags=tags,
        )
        self.db.add(task)
        self.db.flush()
        return task

    def get_task(self, task_id: int) -> Optional[NodeTask]:
        """获取任务详情"""
        return self.db.query(NodeTask).filter(NodeTask.id == task_id).first()

    def list_tasks(
        self,
        node_instance_id: int,
        status: Optional[str] = None,
        assignee_id: Optional[int] = None,
    ) -> List[NodeTask]:
        """
        获取节点的任务列表

        Args:
            node_instance_id: 节点实例ID
            status: 状态筛选
            assignee_id: 执行人筛选

        Returns:
            List[NodeTask]: 任务列表
        """
        query = self.db.query(NodeTask).filter(
            NodeTask.node_instance_id == node_instance_id
        )

        if status:
            query = query.filter(NodeTask.status == status)
        if assignee_id:
            query = query.filter(NodeTask.assignee_id == assignee_id)

        return query.order_by(NodeTask.sequence).all()

    def update_task(
        self,
        task_id: int,
        **kwargs
    ) -> Optional[NodeTask]:
        """更新任务"""
        task = self.db.query(NodeTask).filter(NodeTask.id == task_id).first()

        if not task:
            return None

        for key, value in kwargs.items():
            if hasattr(task, key) and key not in ["id", "node_instance_id", "created_at"]:
                setattr(task, key, value)

        self.db.flush()
        return task

    def delete_task(self, task_id: int) -> bool:
        """删除任务"""
        task = self.db.query(NodeTask).filter(NodeTask.id == task_id).first()

        if not task:
            return False

        self.db.delete(task)
        return True

    def reorder_tasks(self, node_instance_id: int, task_ids: List[int]) -> bool:
        """重新排序任务"""
        for index, task_id in enumerate(task_ids):
            self.db.query(NodeTask).filter(
                and_(
                    NodeTask.id == task_id,
                    NodeTask.node_instance_id == node_instance_id
                )
            ).update({"sequence": index})
        self.db.flush()
        return True

    # ==================== 状态流转 ====================

    def start_task(
        self,
        task_id: int,
        actual_start_date: Optional[date] = None,
    ) -> NodeTask:
        """开始任务"""
        task = self.db.query(NodeTask).filter(NodeTask.id == task_id).first()

        if not task:
            raise ValueError(f"任务 {task_id} 不存在")

        if task.status != StageStatusEnum.PENDING.value:
            raise ValueError(f"任务当前状态为 {task.status}，无法开始")

        task.status = StageStatusEnum.IN_PROGRESS.value
        task.actual_start_date = actual_start_date or date.today()

        self.db.flush()
        return task

    def complete_task(
        self,
        task_id: int,
        completed_by: Optional[int] = None,
        actual_hours: Optional[int] = None,
        actual_end_date: Optional[date] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        remark: Optional[str] = None,
    ) -> NodeTask:
        """
        完成任务

        Args:
            task_id: 任务ID
            completed_by: 完成人ID
            actual_hours: 实际工时
            actual_end_date: 实际结束日期
            attachments: 附件
            remark: 备注

        Returns:
            NodeTask: 更新后的任务
        """
        task = self.db.query(NodeTask).filter(NodeTask.id == task_id).first()

        if not task:
            raise ValueError(f"任务 {task_id} 不存在")

        if task.status not in [StageStatusEnum.PENDING.value, StageStatusEnum.IN_PROGRESS.value]:
            raise ValueError(f"任务当前状态为 {task.status}，无法完成")

        task.status = StageStatusEnum.COMPLETED.value
        task.completed_by = completed_by
        task.completed_at = datetime.now()
        task.actual_end_date = actual_end_date or date.today()

        if actual_hours is not None:
            task.actual_hours = actual_hours
        if attachments:
            task.attachments = attachments
        if remark:
            task.remark = remark

        self.db.flush()

        # 检查是否需要自动完成节点
        self._check_node_auto_complete(task.node_instance_id)

        return task

    def skip_task(
        self,
        task_id: int,
        reason: Optional[str] = None,
    ) -> NodeTask:
        """跳过任务"""
        task = self.db.query(NodeTask).filter(NodeTask.id == task_id).first()

        if not task:
            raise ValueError(f"任务 {task_id} 不存在")

        if task.status not in [StageStatusEnum.PENDING.value, StageStatusEnum.IN_PROGRESS.value]:
            raise ValueError(f"任务当前状态为 {task.status}，无法跳过")

        task.status = StageStatusEnum.SKIPPED.value
        if reason:
            task.remark = reason

        self.db.flush()

        # 检查是否需要自动完成节点
        self._check_node_auto_complete(task.node_instance_id)

        return task

    # ==================== 批量操作 ====================

    def batch_create_tasks(
        self,
        node_instance_id: int,
        tasks_data: List[Dict[str, Any]],
        created_by: Optional[int] = None,
    ) -> List[NodeTask]:
        """
        批量创建任务

        Args:
            node_instance_id: 节点实例ID
            tasks_data: 任务数据列表
            created_by: 创建人ID

        Returns:
            List[NodeTask]: 创建的任务列表
        """
        created_tasks = []
        for task_data in tasks_data:
            task = self.create_task(
                node_instance_id=node_instance_id,
                task_name=task_data.get("task_name"),
                task_code=task_data.get("task_code"),
                description=task_data.get("description"),
                estimated_hours=task_data.get("estimated_hours"),
                planned_start_date=task_data.get("planned_start_date"),
                planned_end_date=task_data.get("planned_end_date"),
                assignee_id=task_data.get("assignee_id"),
                priority=task_data.get("priority", "NORMAL"),
                tags=task_data.get("tags"),
                created_by=created_by,
            )
            created_tasks.append(task)
        return created_tasks

    # ==================== 进度统计 ====================

    def get_node_task_progress(self, node_instance_id: int) -> Dict[str, Any]:
        """
        获取节点任务进度

        Returns:
            Dict: {
                "total": 总任务数,
                "completed": 已完成数,
                "in_progress": 进行中数,
                "pending": 待开始数,
                "skipped": 已跳过数,
                "progress_pct": 完成百分比,
                "total_estimated_hours": 总预计工时,
                "total_actual_hours": 总实际工时,
            }
        """
        tasks = self.db.query(NodeTask).filter(
            NodeTask.node_instance_id == node_instance_id
        ).all()

        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == StageStatusEnum.COMPLETED.value)
        in_progress = sum(1 for t in tasks if t.status == StageStatusEnum.IN_PROGRESS.value)
        pending = sum(1 for t in tasks if t.status == StageStatusEnum.PENDING.value)
        skipped = sum(1 for t in tasks if t.status == StageStatusEnum.SKIPPED.value)

        total_estimated = sum(t.estimated_hours or 0 for t in tasks)
        total_actual = sum(t.actual_hours or 0 for t in tasks)

        # 进度计算：已完成 / (总数 - 已跳过)
        effective_total = total - skipped
        progress_pct = round(completed / effective_total * 100, 1) if effective_total > 0 else 0

        return {
            "total": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "skipped": skipped,
            "progress_pct": progress_pct,
            "total_estimated_hours": total_estimated,
            "total_actual_hours": total_actual,
        }

    def get_user_tasks(
        self,
        user_id: int,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[NodeTask]:
        """
        获取用户的任务列表（跨节点）

        Args:
            user_id: 用户ID
            project_id: 项目ID筛选
            status: 状态筛选

        Returns:
            List[NodeTask]: 任务列表
        """
        query = self.db.query(NodeTask).filter(NodeTask.assignee_id == user_id)

        if project_id:
            query = query.join(ProjectNodeInstance).filter(
                ProjectNodeInstance.project_id == project_id
            )

        if status:
            query = query.filter(NodeTask.status == status)

        return query.order_by(NodeTask.priority.desc(), NodeTask.planned_end_date).all()

    # ==================== 辅助方法 ====================

    def _check_node_auto_complete(self, node_instance_id: int) -> None:
        """
        检查节点是否应该自动完成

        当节点配置了 auto_complete_on_tasks=True 且所有任务都完成/跳过时，
        自动将节点标记为完成。
        """
        node = self.db.query(ProjectNodeInstance).filter(
            ProjectNodeInstance.id == node_instance_id
        ).first()

        if not node or not node.auto_complete_on_tasks:
            return

        # 检查是否有任务
        tasks = self.db.query(NodeTask).filter(
            NodeTask.node_instance_id == node_instance_id
        ).all()

        if not tasks:
            return

        # 检查是否所有任务都完成或跳过
        incomplete = [
            t for t in tasks
            if t.status not in [StageStatusEnum.COMPLETED.value, StageStatusEnum.SKIPPED.value]
        ]

        if not incomplete:
            # 所有任务完成，自动完成节点
            if node.status in [StageStatusEnum.PENDING.value, StageStatusEnum.IN_PROGRESS.value]:
                node.status = StageStatusEnum.COMPLETED.value
                node.completed_at = datetime.now()
                node.actual_date = date.today()

    def assign_task(
        self,
        task_id: int,
        assignee_id: int,
    ) -> NodeTask:
        """分配任务给指定人员"""
        task = self.db.query(NodeTask).filter(NodeTask.id == task_id).first()

        if not task:
            raise ValueError(f"任务 {task_id} 不存在")

        task.assignee_id = assignee_id
        self.db.flush()
        return task

    def set_task_priority(
        self,
        task_id: int,
        priority: str,
    ) -> NodeTask:
        """设置任务优先级"""
        valid_priorities = ["LOW", "NORMAL", "HIGH", "URGENT"]
        if priority not in valid_priorities:
            raise ValueError(f"无效的优先级: {priority}")

        task = self.db.query(NodeTask).filter(NodeTask.id == task_id).first()

        if not task:
            raise ValueError(f"任务 {task_id} 不存在")

        task.priority = priority
        self.db.flush()
        return task
