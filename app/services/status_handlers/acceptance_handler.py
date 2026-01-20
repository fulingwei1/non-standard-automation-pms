# -*- coding: utf-8 -*-
"""验收状态处理器"""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStatusLog

if TYPE_CHECKING:
    from app.services.status_transition_service import StatusTransitionService


class AcceptanceStatusHandler:
    """验收事件处理器（FAT/SAT/终验收）"""

    def __init__(self, db: Session, parent: "StatusTransitionService" = None):
        self.db = db
        self._parent = parent

    def handle_fat_passed(
        self,
        project_id: int,
        machine_id: Optional[int] = None,
        log_status_change=None,
    ) -> bool:
        """
        处理FAT验收通过事件

        规则：FAT通过 → 状态→ST23，可推进至S8，健康度→H1

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

        # 检查是否在S7阶段
        if project.stage != "S7":
            return False

        old_stage = project.stage
        old_status = project.status
        old_health = project.health

        # 更新项目状态
        project.stage = "S8"
        project.status = "ST23"
        if old_health == "H2":
            project.health = "H1"

        # 记录状态变更
        self._log_status_change(
            project_id,
            old_stage=old_stage,
            new_stage="S8",
            old_status=old_status,
            new_status="ST23",
            old_health=old_health,
            new_health=project.health,
            change_type="FAT_PASSED",
            change_reason="FAT验收通过，自动推进至现场交付阶段",
            log_status_change=log_status_change,
        )

        self.db.commit()
        return True

    def handle_fat_failed(
        self,
        project_id: int,
        machine_id: Optional[int] = None,
        issues: Optional[List[str]] = None,
        log_status_change=None,
    ) -> bool:
        """
        处理FAT验收不通过事件

        规则：FAT不通过 → 状态→ST22，健康度→H2

        Args:
            project_id: 项目ID
            machine_id: 设备ID（可选）
            issues: 问题列表（可选）
            log_status_change: 状态变更日志记录函数

        Returns:
            bool: 是否成功更新
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False

        old_status = project.status
        old_health = project.health

        # 更新项目状态和健康度
        project.status = "ST22"
        project.health = "H2"

        # 记录整改项到项目风险信息
        if issues:
            risk_desc = f"FAT验收不通过，整改项：{', '.join(issues)}"
            if project.description:
                project.description += f"\n{risk_desc}"
            else:
                project.description = risk_desc

        # 记录状态变更
        self._log_status_change(
            project_id,
            old_stage=project.stage,
            new_stage=project.stage,
            old_status=old_status,
            new_status="ST22",
            old_health=old_health,
            new_health="H2",
            change_type="FAT_FAILED",
            change_reason="FAT验收不通过，需要整改",
            log_status_change=log_status_change,
        )

        self.db.commit()
        return True

    def handle_sat_passed(
        self,
        project_id: int,
        machine_id: Optional[int] = None,
        log_status_change=None,
    ) -> bool:
        """
        处理SAT验收通过事件

        规则：SAT通过 → 状态→ST27，可推进至S9

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

        # 检查是否在S8阶段
        if project.stage != "S8":
            return False

        old_status = project.status

        # 更新项目状态
        project.status = "ST27"

        # 记录状态变更
        self._log_status_change(
            project_id,
            old_stage=project.stage,
            new_stage=project.stage,
            old_status=old_status,
            new_status="ST27",
            change_type="SAT_PASSED",
            change_reason="SAT验收通过，可推进至质保结项阶段",
            log_status_change=log_status_change,
        )

        self.db.commit()
        return True

    def handle_sat_failed(
        self,
        project_id: int,
        machine_id: Optional[int] = None,
        issues: Optional[List[str]] = None,
        log_status_change=None,
    ) -> bool:
        """
        处理SAT验收不通过事件

        规则：SAT不通过 → 状态→ST26，健康度→H2

        Args:
            project_id: 项目ID
            machine_id: 设备ID（可选）
            issues: 问题列表（可选）
            log_status_change: 状态变更日志记录函数

        Returns:
            bool: 是否成功更新
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False

        old_status = project.status
        old_health = project.health

        # 更新项目状态和健康度
        project.status = "ST26"
        project.health = "H2"

        # 记录整改项到项目风险信息
        if issues:
            risk_desc = f"SAT验收不通过，整改项：{', '.join(issues)}"
            if project.description:
                project.description += f"\n{risk_desc}"
            else:
                project.description = risk_desc

        # 记录状态变更
        self._log_status_change(
            project_id,
            old_stage=project.stage,
            new_stage=project.stage,
            old_status=old_status,
            new_status="ST26",
            old_health=old_health,
            new_health="H2",
            change_type="SAT_FAILED",
            change_reason="SAT验收不通过，需要整改",
            log_status_change=log_status_change,
        )

        self.db.commit()
        return True

    def handle_final_acceptance_passed(
        self,
        project_id: int,
        log_status_change=None,
    ) -> bool:
        """
        处理终验收通过事件

        规则：终验收通过 → 可推进至S9

        Args:
            project_id: 项目ID
            log_status_change: 状态变更日志记录函数

        Returns:
            bool: 是否成功更新
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False

        # 检查是否在S8阶段
        if project.stage != "S8":
            return False

        # 终验收通过后，项目可以推进至S9，但不自动推进
        # 需要检查回款达标等其他条件
        # 这里只记录状态变更，不自动推进阶段

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
