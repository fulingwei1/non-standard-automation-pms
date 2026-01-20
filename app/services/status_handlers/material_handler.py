# -*- coding: utf-8 -*-
"""BOM和物料状态处理器"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStatusLog

if TYPE_CHECKING:
    from app.services.status_transition_service import StatusTransitionService


class MaterialStatusHandler:
    """BOM和物料事件处理器"""

    def __init__(self, db: Session, parent: "StatusTransitionService" = None):
        self.db = db
        self._parent = parent

    def handle_bom_published(
        self,
        project_id: int,
        machine_id: Optional[int] = None,
        log_status_change=None,
    ) -> bool:
        """
        处理BOM发布完成事件

        规则：BOM发布完成 → 项目状态自动更新为 S5/ST12

        Args:
            project_id: 项目ID
            machine_id: 设备ID（可选）
            log_status_change: 状态变更日志记录函数

        Returns:
            bool: 是否成功更新
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False

        # 检查是否可以从S4推进到S5
        if project.stage != "S4":
            return False

        old_stage = project.stage
        old_status = project.status

        # 更新项目状态
        project.stage = "S5"
        project.status = "ST12"

        # 记录状态变更
        self._log_status_change(
            project_id,
            old_stage=old_stage,
            new_stage="S5",
            old_status=old_status,
            new_status="ST12",
            change_type="BOM_PUBLISHED",
            change_reason="BOM发布完成，自动推进至采购阶段",
            log_status_change=log_status_change,
        )

        self.db.commit()
        return True

    def handle_material_shortage(
        self,
        project_id: int,
        is_critical: bool = True,
        log_status_change=None,
    ) -> bool:
        """
        处理关键物料缺货事件

        规则：关键物料缺货 → 项目状态→ST14，健康度→H3

        Args:
            project_id: 项目ID
            is_critical: 是否为关键物料
            log_status_change: 状态变更日志记录函数

        Returns:
            bool: 是否成功更新
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False

        if not is_critical:
            return False

        old_status = project.status
        old_health = project.health

        # 更新项目状态和健康度
        project.status = "ST14"
        project.health = "H3"

        # 记录状态变更
        self._log_status_change(
            project_id,
            old_stage=project.stage,
            new_stage=project.stage,
            old_status=old_status,
            new_status="ST14",
            old_health=old_health,
            new_health="H3",
            change_type="MATERIAL_SHORTAGE",
            change_reason="关键物料缺货，自动更新为阻塞状态",
            log_status_change=log_status_change,
        )

        self.db.commit()
        return True

    def handle_material_ready(
        self,
        project_id: int,
        log_status_change=None,
    ) -> bool:
        """
        处理物料齐套事件

        规则：物料齐套 → 项目状态→ST16，健康度→H1，可推进至S6

        Args:
            project_id: 项目ID
            log_status_change: 状态变更日志记录函数

        Returns:
            bool: 是否成功更新
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False

        # 检查是否在S5阶段
        if project.stage != "S5":
            return False

        old_status = project.status
        old_health = project.health

        # 更新项目状态和健康度
        project.status = "ST16"
        project.health = "H1"

        # 记录状态变更
        self._log_status_change(
            project_id,
            old_stage=project.stage,
            new_stage=project.stage,
            old_status=old_status,
            new_status="ST16",
            old_health=old_health,
            new_health="H1",
            change_type="MATERIAL_READY",
            change_reason="物料齐套，可推进至装配阶段",
            log_status_change=log_status_change,
        )

        self.db.commit()
        return True

    def _log_status_change(
        self,
        project_id: int,
        old_stage: Optional[str] = None,
        new_stage: Optional[str] = None,
        old_status: Optional[str] = None,
        new_status: Optional[str] = None,
        old_health: Optional[str] = None,
        new_health: Optional[str] = None,
        change_type: str = "AUTO_TRANSITION",
        change_reason: Optional[str] = None,
        changed_by: Optional[int] = None,
        log_status_change=None,
    ):
        """记录状态变更历史"""
        if log_status_change:
            log_status_change(
                project_id,
                old_stage=old_stage,
                new_stage=new_stage,
                old_status=old_status,
                new_status=new_status,
                old_health=old_health,
                new_health=new_health,
                change_type=change_type,
                change_reason=change_reason,
                changed_by=changed_by,
            )
            return

        log = ProjectStatusLog(
            project_id=project_id,
            old_stage=old_stage,
            new_stage=new_stage,
            old_status=old_status,
            new_status=new_status,
            old_health=old_health,
            new_health=new_health,
            change_type=change_type,
            change_reason=change_reason,
            changed_by=changed_by,
            changed_at=datetime.now(),
        )
        self.db.add(log)
