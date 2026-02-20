# -*- coding: utf-8 -*-
"""
项目绩效服务类
提取业务逻辑：权限检查、数据聚合、报告生成等
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from collections import defaultdict

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.performance import (
    PerformancePeriod,
    PerformanceResult,
    ProjectContribution,
)
from app.models.project import Project
from app.models.progress import Task
from app.models.user import User


class ProjectPerformanceService:
    """项目绩效服务类"""

    def __init__(self, db: Session):
        """
        初始化服务

        Args:
            db: 数据库会话
        """
        self.db = db

    def check_performance_view_permission(
        self, current_user: User, target_user_id: int
    ) -> bool:
        """
        检查用户是否有权限查看指定用户的绩效

        规则：
        1. 可以查看自己的绩效
        2. 部门经理可以查看本部门员工的绩效
        3. 项目经理可以查看项目成员的绩效
        4. 管理员可以查看所有人的绩效

        Args:
            current_user: 当前用户
            target_user_id: 目标用户ID

        Returns:
            bool: 是否有权限查看
        """
        if current_user.is_superuser:
            return True

        # 查看自己的绩效
        if current_user.id == target_user_id:
            return True

        # 检查是否是部门经理
        target_user = self.db.query(User).filter(User.id == target_user_id).first()
        if not target_user:
            return False

        # 检查是否有管理角色
        manager_roles = [
            "dept_manager",
            "department_manager",
            "部门经理",
            "pm",
            "project_manager",
            "项目经理",
            "admin",
            "super_admin",
            "管理员",
        ]

        has_manager_role = False
        for user_role in current_user.roles or []:
            role_code = (
                user_role.role.role_code.lower() if user_role.role.role_code else ""
            )
            role_name = (
                user_role.role.role_name.lower() if user_role.role.role_name else ""
            )
            if role_code in manager_roles or role_name in manager_roles:
                has_manager_role = True
                break

        if not has_manager_role:
            return False

        # 检查是否是同一部门
        if (
            target_user.department_id
            and current_user.department_id == target_user.department_id
        ):
            return True

        # 检查是否管理同一项目
        user_projects = (
            self.db.query(Project).filter(Project.pm_id == current_user.id).all()
        )
        project_ids = [p.id for p in user_projects]

        target_projects = (
            self.db.query(Project).filter(Project.id.in_(project_ids)).all()
        )
        for project in target_projects:
            # 检查目标用户是否是项目成员
            member_task = (
                self.db.query(Task)
                .filter(Task.project_id == project.id, Task.owner_id == target_user_id)
                .first()
            )
            if member_task:
                return True

        return False

    def get_team_members(self, team_id: int) -> List[int]:
        """
        获取团队成员ID列表

        Args:
            team_id: 团队ID（暂时使用department_id作为team_id）

        Returns:
            List[int]: 成员ID列表
        """
        # 临时使用部门作为团队
        users = (
            self.db.query(User)
            .filter(User.department_id == team_id, User.is_active)
            .all()
        )
        return [u.id for u in users]

    def get_department_members(self, dept_id: int) -> List[int]:
        """
        获取部门成员ID列表

        Args:
            dept_id: 部门ID

        Returns:
            List[int]: 成员ID列表
        """
        users = (
            self.db.query(User)
            .filter(User.department_id == dept_id, User.is_active)
            .all()
        )
        return [u.id for u in users]

    def get_evaluator_type(self, user: User) -> str:
        """
        判断评价人类型（部门经理/项目经理）

        Args:
            user: 用户对象

        Returns:
            str: 评价人类型（DEPT_MANAGER/PROJECT_MANAGER/BOTH）
        """
        is_dept_manager = False
        is_project_manager = False

        for user_role in user.roles or []:
            role_code = (
                user_role.role.role_code.lower() if user_role.role.role_code else ""
            )
            role_name = (
                user_role.role.role_name.lower() if user_role.role.role_name else ""
            )

            if role_code in [
                "dept_manager",
                "department_manager",
                "部门经理",
            ] or role_name in ["dept_manager", "department_manager", "部门经理"]:
                is_dept_manager = True
            if role_code in ["pm", "project_manager", "项目经理"] or role_name in [
                "pm",
                "project_manager",
                "项目经理",
            ]:
                is_project_manager = True

        if is_dept_manager and is_project_manager:
            return "BOTH"
        elif is_dept_manager:
            return "DEPT_MANAGER"
        elif is_project_manager:
            return "PROJECT_MANAGER"
        else:
            return "OTHER"

    def get_team_name(self, team_id: int) -> str:
        """
        获取团队名称

        Args:
            team_id: 团队ID

        Returns:
            str: 团队名称
        """
        dept = self.db.query(Department).filter(Department.id == team_id).first()
        return dept.name if dept else f"团队{team_id}"

    def get_department_name(self, dept_id: int) -> str:
        """
        获取部门名称

        Args:
            dept_id: 部门ID

        Returns:
            str: 部门名称
        """
        dept = self.db.query(Department).filter(Department.id == dept_id).first()
        return dept.name if dept else f"部门{dept_id}"

    def get_project_performance(
        self, project_id: int, period_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取项目成员绩效（项目贡献）

        Args:
            project_id: 项目ID
            period_id: 周期ID，可选

        Returns:
            Dict: 项目绩效数据

        Raises:
            ValueError: 项目不存在或周期不存在
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError("项目不存在")

        if period_id:
            period = (
                self.db.query(PerformancePeriod)
                .filter(PerformancePeriod.id == period_id)
                .first()
            )
        else:
            period = (
                self.db.query(PerformancePeriod)
                .filter(PerformancePeriod.status == "FINALIZED")
                .order_by(desc(PerformancePeriod.end_date))
                .first()
            )

        if not period:
            raise ValueError("未找到考核周期")

        # 获取项目贡献
        contributions = (
            self.db.query(ProjectContribution)
            .filter(
                ProjectContribution.period_id == period.id,
                ProjectContribution.project_id == project_id,
            )
            .all()
        )

        members = []
        total_contribution = Decimal("0")

        for contrib in contributions:
            user = self.db.query(User).filter(User.id == contrib.user_id).first()
            score = contrib.contribution_score or Decimal("0")
            total_contribution += score

            members.append(
                {
                    "user_id": contrib.user_id,
                    "user_name": user.real_name or user.username if user else None,
                    "contribution_score": float(score),
                    "work_hours": float(contrib.hours_spent)
                    if contrib.hours_spent
                    else 0,
                    "task_count": contrib.task_count or 0,
                }
            )

        # 按贡献分排序
        members.sort(key=lambda x: x["contribution_score"], reverse=True)

        return {
            "project_id": project_id,
            "project_name": project.project_name,
            "period_id": period.id,
            "period_name": period.period_name,
            "member_count": len(members),
            "total_contribution_score": total_contribution,
            "members": members,
        }

    def get_project_progress_report(
        self,
        project_id: int,
        report_type: str = "WEEKLY",
        report_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        获取项目进展报告（周报/月报）

        Args:
            project_id: 项目ID
            report_type: 报告类型（WEEKLY/MONTHLY）
            report_date: 报告日期，可选

        Returns:
            Dict: 项目进展报告数据

        Raises:
            ValueError: 项目不存在
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError("项目不存在")

        if not report_date:
            report_date = datetime.now().date()

        # 从进度跟踪模块获取数据
        project_tasks = (
            self.db.query(Task).filter(Task.project_id == project_id).all()
        )

        total_tasks = len(project_tasks)
        completed_tasks = len([t for t in project_tasks if t.status == "DONE"])
        overall_progress = int(project.progress or 0)

        # 检查是否按计划进行
        on_schedule = True
        delayed_tasks = [
            t
            for t in project_tasks
            if t.plan_end
            and t.plan_end < datetime.now().date()
            and t.status not in ["DONE", "CANCELLED"]
        ]
        if delayed_tasks:
            on_schedule = False

        progress_summary = {
            "overall_progress": overall_progress,
            "completed_tasks": completed_tasks,
            "total_tasks": total_tasks,
            "on_schedule": on_schedule,
        }

        # 获取成员贡献
        member_contributions = []
        member_task_count = defaultdict(int)
        member_hours = defaultdict(float)

        for task in project_tasks:
            if task.owner_id:
                member_task_count[task.owner_id] += 1
                # 假设每个任务平均工时为 4 小时
                member_hours[task.owner_id] += 4

        for user_id, task_count in member_task_count.items():
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                member_contributions.append(
                    {
                        "user_id": user_id,
                        "user_name": user.real_name or user.username,
                        "task_count": task_count,
                        "estimated_hours": member_hours[user_id],
                    }
                )

        member_contributions.sort(key=lambda x: x["task_count"], reverse=True)

        # 获取关键成果（最近完成的任务）
        key_achievements = []
        completed = [t for t in project_tasks if t.status == "DONE"]
        completed.sort(
            key=lambda x: x.updated_at or x.created_at or datetime.now(), reverse=True
        )
        for task in completed[:5]:
            key_achievements.append(
                {
                    "task_name": task.task_name,
                    "completed_date": task.updated_at.isoformat()
                    if task.updated_at
                    else None,
                    "description": task.description[:100] if task.description else "",
                }
            )

        # 获取风险和问题（逾期任务）
        risks_and_issues = []
        for task in delayed_tasks[:10]:
            risks_and_issues.append(
                {
                    "type": "DELAYED_TASK",
                    "description": f"任务 '{task.task_name}' 已逾期",
                    "severity": "HIGH"
                    if (datetime.now().date() - task.plan_end).days > 7
                    else "MEDIUM",
                    "task_id": task.id,
                    "task_name": task.task_name,
                    "due_date": task.plan_end.isoformat(),
                }
            )

        return {
            "project_id": project_id,
            "project_name": project.project_name,
            "report_type": report_type,
            "report_date": report_date,
            "progress_summary": progress_summary,
            "member_contributions": member_contributions,
            "key_achievements": key_achievements,
            "risks_and_issues": risks_and_issues,
        }

    def compare_performance(
        self, user_ids: List[int], period_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        绩效对比（多人对比）

        Args:
            user_ids: 用户ID列表
            period_id: 周期ID，可选

        Returns:
            Dict: 绩效对比数据

        Raises:
            ValueError: 周期不存在
        """
        if period_id:
            period = (
                self.db.query(PerformancePeriod)
                .filter(PerformancePeriod.id == period_id)
                .first()
            )
        else:
            period = (
                self.db.query(PerformancePeriod)
                .filter(PerformancePeriod.status == "FINALIZED")
                .order_by(desc(PerformancePeriod.end_date))
                .first()
            )

        if not period:
            raise ValueError("未找到考核周期")

        comparison_data = []

        for user_id in user_ids:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                continue

            result = (
                self.db.query(PerformanceResult)
                .filter(
                    PerformanceResult.period_id == period.id,
                    PerformanceResult.user_id == user_id,
                )
                .first()
            )

            comparison_data.append(
                {
                    "user_id": user_id,
                    "user_name": user.real_name or user.username,
                    "score": float(result.total_score)
                    if result and result.total_score
                    else 0,
                    "level": result.level if result else "QUALIFIED",
                    "department_name": result.department_name if result else None,
                }
            )

        return {
            "user_ids": user_ids,
            "period_id": period.id,
            "period_name": period.period_name,
            "comparison_data": comparison_data,
        }
