# -*- coding: utf-8 -*-
"""
阶段状态流转模块
处理阶段的开始、完成、跳过等状态流转
"""

from datetime import date
from typing import Optional, Tuple

from sqlalchemy import and_

from app.models.enums import StageStatusEnum
from app.models.project import Project
from app.models.stage_instance import (
    ProjectNodeInstance,
    ProjectStageInstance,
)


class StageFlowMixin:
    """阶段状态流转功能混入类"""

    def start_stage(
        self,
        stage_instance_id: int,
        actual_start_date: Optional[date] = None,
    ) -> ProjectStageInstance:
        """
        开始阶段

        Args:
            stage_instance_id: 阶段实例ID
            actual_start_date: 实际开始日期

        Returns:
            ProjectStageInstance: 更新后的阶段实例
        """
        stage = self.db.query(ProjectStageInstance).filter(
            ProjectStageInstance.id == stage_instance_id
        ).first()

        if not stage:
            raise ValueError(f"阶段实例 {stage_instance_id} 不存在")

        if stage.status != StageStatusEnum.PENDING.value:
            raise ValueError(f"阶段当前状态为 {stage.status}，无法开始")

        stage.status = StageStatusEnum.IN_PROGRESS.value
        stage.actual_start_date = actual_start_date or date.today()

        # 更新项目的当前阶段
        self.db.query(Project).filter(
            Project.id == stage.project_id
        ).update({"current_stage_instance_id": stage_instance_id})

        self.db.flush()
        return stage

    def complete_stage(
        self,
        stage_instance_id: int,
        actual_end_date: Optional[date] = None,
        auto_start_next: bool = True,
    ) -> Tuple[ProjectStageInstance, Optional[ProjectStageInstance]]:
        """
        完成阶段

        Args:
            stage_instance_id: 阶段实例ID
            actual_end_date: 实际结束日期
            auto_start_next: 是否自动开始下一阶段

        Returns:
            Tuple[当前阶段, 下一阶段（如有）]
        """
        stage = self.db.query(ProjectStageInstance).filter(
            ProjectStageInstance.id == stage_instance_id
        ).first()

        if not stage:
            raise ValueError(f"阶段实例 {stage_instance_id} 不存在")

        if stage.status != StageStatusEnum.IN_PROGRESS.value:
            raise ValueError(f"阶段当前状态为 {stage.status}，无法完成")

        # 检查是否所有必需节点都已完成
        incomplete_required = self.db.query(ProjectNodeInstance).filter(
            and_(
                ProjectNodeInstance.stage_instance_id == stage_instance_id,
                ProjectNodeInstance.is_required == True,
                ProjectNodeInstance.status.notin_([
                    StageStatusEnum.COMPLETED.value,
                    StageStatusEnum.SKIPPED.value
                ])
            )
        ).count()

        if incomplete_required > 0:
            raise ValueError(f"还有 {incomplete_required} 个必需节点未完成")

        stage.status = StageStatusEnum.COMPLETED.value
        stage.actual_end_date = actual_end_date or date.today()

        # 查找下一阶段
        next_stage = None
        if auto_start_next:
            next_stage = self.db.query(ProjectStageInstance).filter(
                and_(
                    ProjectStageInstance.project_id == stage.project_id,
                    ProjectStageInstance.sequence > stage.sequence,
                    ProjectStageInstance.status == StageStatusEnum.PENDING.value
                )
            ).order_by(ProjectStageInstance.sequence).first()

            if next_stage:
                self.start_stage(next_stage.id)

        self.db.flush()
        return stage, next_stage

    def skip_stage(
        self,
        stage_instance_id: int,
        reason: Optional[str] = None,
    ) -> ProjectStageInstance:
        """
        跳过阶段

        Args:
            stage_instance_id: 阶段实例ID
            reason: 跳过原因

        Returns:
            ProjectStageInstance: 更新后的阶段实例
        """
        stage = self.db.query(ProjectStageInstance).filter(
            ProjectStageInstance.id == stage_instance_id
        ).first()

        if not stage:
            raise ValueError(f"阶段实例 {stage_instance_id} 不存在")

        if stage.status not in [StageStatusEnum.PENDING.value, StageStatusEnum.IN_PROGRESS.value]:
            raise ValueError(f"阶段当前状态为 {stage.status}，无法跳过")

        stage.status = StageStatusEnum.SKIPPED.value
        stage.remark = reason or stage.remark
        stage.is_modified = True

        # 跳过所有未完成的节点
        self.db.query(ProjectNodeInstance).filter(
            and_(
                ProjectNodeInstance.stage_instance_id == stage_instance_id,
                ProjectNodeInstance.status.in_([
                    StageStatusEnum.PENDING.value,
                    StageStatusEnum.IN_PROGRESS.value
                ])
            )
        ).update({"status": StageStatusEnum.SKIPPED.value})

        self.db.flush()
        return stage
