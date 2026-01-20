# -*- coding: utf-8 -*-
"""ECN变更状态处理器"""

from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Session

from app.models.ecn import Ecn
from app.models.project import Project, ProjectStatusLog

if TYPE_CHECKING:
    from app.services.status_transition_service import StatusTransitionService


class ECNStatusHandler:
    """ECN变更事件处理器"""

    def __init__(self, db: Session, parent: "StatusTransitionService" = None):
        self.db = db
        self._parent = parent

    def handle_ecn_schedule_impact(
        self,
        project_id: int,
        ecn_id: int,
        impact_days: int,
        log_status_change=None,
    ) -> bool:
        """
        处理ECN变更影响交期事件

        规则：ECN影响交期 → 更新协商交期，记录风险

        Args:
            project_id: 项目ID
            ecn_id: ECN ID
            impact_days: 影响天数（正数表示延期）
            log_status_change: 状态变更日志记录函数

        Returns:
            bool: 是否成功更新
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False

        ecn = self.db.query(Ecn).filter(Ecn.id == ecn_id).first()
        if not ecn:
            return False

        # 更新协商交期（使用planned_end_date作为协商交期）
        if project.planned_end_date and impact_days > 0:
            # 更新计划结束日期（作为协商交期）
            project.planned_end_date = project.planned_end_date + timedelta(
                days=impact_days
            )

        # 记录风险信息
        risk_desc = f"ECN变更影响交期：{impact_days}天，ECN编号：{ecn.ecn_no}"
        if project.description:
            project.description += f"\n{risk_desc}"
        else:
            project.description = risk_desc

        # 如果延期超过阈值（如7天），更新健康度为H2
        if impact_days > 7:
            old_health = project.health
            project.health = "H2"

            # 记录健康度变更
            self._log_status_change(
                project_id,
                old_stage=project.stage,
                new_stage=project.stage,
                old_status=project.status,
                new_status=project.status,
                old_health=old_health,
                new_health="H2",
                change_type="ECN_SCHEDULE_IMPACT",
                change_reason=risk_desc,
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
