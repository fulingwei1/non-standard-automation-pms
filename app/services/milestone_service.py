# -*- coding: utf-8 -*-
"""
里程碑业务逻辑服务
基于统一的 BaseService 实现
"""

from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session

from app.common.crud.base import BaseService
from app.models.project import ProjectMilestone
from app.schemas.project import MilestoneCreate, MilestoneUpdate, MilestoneResponse


class MilestoneService(
    BaseService[ProjectMilestone, MilestoneCreate, MilestoneUpdate, MilestoneResponse]
):
    """
    里程碑服务类
    """

    def __init__(self, db: Session):
        super().__init__(
            model=ProjectMilestone,
            db=db,
            response_schema=MilestoneResponse,
            resource_name="里程碑",
        )

    def get_by_project(self, project_id: int) -> List[ProjectMilestone]:
        """
        获取指定项目的所有里程碑
        """
        return (
            self.db.query(self.model)
            .filter(self.model.project_id == project_id)
            .order_by(self.model.planned_date)
            .all()
        )

    def complete_milestone(
        self, milestone_id: int, actual_date: Optional[date] = None
    ) -> ProjectMilestone:
        """
        完成里程碑
        """
        milestone = self.get(milestone_id)

        update_data = MilestoneUpdate(
            status="COMPLETED",
            actual_date=actual_date or milestone.actual_date or date.today(),
        )

        # This will trigger _on_status_change
        updated_milestone = self.update(milestone_id, update_data)

        # Convert back to model if response_schema was used
        # Note: BaseService.update returns response_schema
        # If we need the model itself for further DB operations:
        return (
            self.db.query(ProjectMilestone)
            .filter(ProjectMilestone.id == milestone_id)
            .first()
        )
