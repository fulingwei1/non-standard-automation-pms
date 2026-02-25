# -*- coding: utf-8 -*-
"""
员工绩效服务
处理员工端绩效相关业务逻辑
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List

from fastapi import HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.performance import (
    MonthlyWorkSummary,
    PerformanceEvaluationRecord,
)
from app.models.project import Project
from app.models.user import User
from app.schemas.performance import MonthlyWorkSummaryCreate, MonthlyWorkSummaryUpdate
from app.services.performance_service import PerformanceService


class EmployeePerformanceService:
    """员工绩效服务"""

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
            from app.models.progress import Task

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

            if role_code in ["dept_manager", "department_manager", "部门经理"] or role_name in [
                "dept_manager",
                "department_manager",
                "部门经理",
            ]:
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

    def create_monthly_work_summary(
        self, current_user: User, summary_in: MonthlyWorkSummaryCreate
    ) -> MonthlyWorkSummary:
        """
        员工创建月度工作总结（提交）

        Args:
            current_user: 当前用户
            summary_in: 工作总结创建数据

        Returns:
            MonthlyWorkSummary: 创建的工作总结

        Raises:
            HTTPException: 如果已存在该周期的总结
        """
        # 检查是否已存在该周期的总结
        existing = (
            self.db.query(MonthlyWorkSummary)
            .filter(
                MonthlyWorkSummary.employee_id == current_user.id,
                MonthlyWorkSummary.period == summary_in.period,
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"您已提交过 {summary_in.period} 的工作总结",
            )

        # 创建工作总结
        summary = MonthlyWorkSummary(
            employee_id=current_user.id,
            period=summary_in.period,
            work_content=summary_in.work_content,
            self_evaluation=summary_in.self_evaluation,
            highlights=summary_in.highlights,
            problems=summary_in.problems,
            next_month_plan=summary_in.next_month_plan,
            status="SUBMITTED",
            submit_date=datetime.now(),
        )

        self.db.add(summary)
        self.db.commit()
        self.db.refresh(summary)

        # 创建待评价任务（通知部门经理和项目经理）
        PerformanceService.create_evaluation_tasks(self.db, summary)

        return summary

    def save_monthly_summary_draft(
        self, current_user: User, period: str, summary_update: MonthlyWorkSummaryUpdate
    ) -> MonthlyWorkSummary:
        """
        员工保存工作总结草稿

        Args:
            current_user: 当前用户
            period: 评价周期 (YYYY-MM)
            summary_update: 工作总结更新数据

        Returns:
            MonthlyWorkSummary: 保存的工作总结

        Raises:
            HTTPException: 如果尝试更新非草稿状态的总结
        """
        # 查找现有草稿
        summary = (
            self.db.query(MonthlyWorkSummary)
            .filter(
                MonthlyWorkSummary.employee_id == current_user.id,
                MonthlyWorkSummary.period == period,
            )
            .first()
        )

        if not summary:
            # 创建新草稿
            summary = MonthlyWorkSummary(
                employee_id=current_user.id,
                period=period,
                work_content=summary_update.work_content or "",
                self_evaluation=summary_update.self_evaluation or "",
                highlights=summary_update.highlights,
                problems=summary_update.problems,
                next_month_plan=summary_update.next_month_plan,
                status="DRAFT",
            )
            self.db.add(summary)
        else:
            # 更新草稿（只能更新DRAFT状态的）
            if summary.status != "DRAFT":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="只能更新草稿状态的工作总结",
                )

            # 更新字段
            if summary_update.work_content is not None:
                summary.work_content = summary_update.work_content
            if summary_update.self_evaluation is not None:
                summary.self_evaluation = summary_update.self_evaluation
            if summary_update.highlights is not None:
                summary.highlights = summary_update.highlights
            if summary_update.problems is not None:
                summary.problems = summary_update.problems
            if summary_update.next_month_plan is not None:
                summary.next_month_plan = summary_update.next_month_plan

        self.db.commit()
        self.db.refresh(summary)

        return summary

    def get_monthly_summary_history(
        self, current_user: User, limit: int = 12
    ) -> List[Dict[str, Any]]:
        """
        员工查看历史工作总结

        Args:
            current_user: 当前用户
            limit: 获取最近N个月

        Returns:
            List[Dict[str, Any]]: 历史工作总结列表
        """
        summaries = (
            self.db.query(MonthlyWorkSummary)
            .filter(MonthlyWorkSummary.employee_id == current_user.id)
            .order_by(desc(MonthlyWorkSummary.period))
            .limit(limit)
            .all()
        )

        result = []
        for summary in summaries:
            # 统计评价数量
            eval_count = (
                self.db.query(PerformanceEvaluationRecord)
                .filter(
                    PerformanceEvaluationRecord.summary_id == summary.id,
                    PerformanceEvaluationRecord.status == "COMPLETED",
                )
                .count()
            )

            result.append(
                {
                    "id": summary.id,
                    "period": summary.period,
                    "status": summary.status,
                    "submit_date": summary.submit_date,
                    "evaluation_count": eval_count,
                    "created_at": summary.created_at,
                }
            )

        return result

    def get_my_performance(self, current_user: User) -> Dict[str, Any]:
        """
        员工查看我的绩效（新系统）

        Args:
            current_user: 当前用户

        Returns:
            Dict[str, Any]: 绩效数据
        """
        # 获取最新周期
        current_date = date.today()
        current_period = current_date.strftime("%Y-%m")

        # 获取当前周期的工作总结
        current_summary = (
            self.db.query(MonthlyWorkSummary)
            .filter(
                MonthlyWorkSummary.employee_id == current_user.id,
                MonthlyWorkSummary.period == current_period,
            )
            .first()
        )

        # 当前评价状态
        if current_summary:
            # 获取部门经理评价
            dept_eval = (
                self.db.query(PerformanceEvaluationRecord)
                .filter(
                    PerformanceEvaluationRecord.summary_id == current_summary.id,
                    PerformanceEvaluationRecord.evaluator_type == "DEPT_MANAGER",
                )
                .first()
            )

            dept_evaluation_status = {
                "status": dept_eval.status if dept_eval else "PENDING",
                "evaluator": (
                    dept_eval.evaluator.real_name
                    if dept_eval and dept_eval.evaluator
                    else "未知"
                ),
                "score": (
                    dept_eval.score
                    if dept_eval and dept_eval.status == "COMPLETED"
                    else None
                ),
            }

            # 获取项目经理评价
            project_evals = (
                self.db.query(PerformanceEvaluationRecord)
                .filter(
                    PerformanceEvaluationRecord.summary_id == current_summary.id,
                    PerformanceEvaluationRecord.evaluator_type == "PROJECT_MANAGER",
                )
                .all()
            )

            project_evaluations_status = []
            for proj_eval in project_evals:
                project_evaluations_status.append(
                    {
                        "project_name": (
                            proj_eval.project.project_name
                            if proj_eval.project
                            else "未知项目"
                        ),
                        "status": proj_eval.status,
                        "evaluator": (
                            proj_eval.evaluator.real_name
                            if proj_eval.evaluator
                            else "未知"
                        ),
                        "score": (
                            proj_eval.score if proj_eval.status == "COMPLETED" else None
                        ),
                        "weight": proj_eval.project_weight,
                    }
                )

            current_status = {
                "period": current_period,
                "summary_status": current_summary.status,
                "dept_evaluation": dept_evaluation_status,
                "project_evaluations": project_evaluations_status,
            }
        else:
            current_status = {
                "period": current_period,
                "summary_status": "NOT_SUBMITTED",
                "dept_evaluation": {"status": "PENDING", "evaluator": "未知", "score": None},
                "project_evaluations": [],
            }

        # 计算最新绩效结果
        latest_result = None
        if current_summary and current_summary.status == "COMPLETED":
            score_result = PerformanceService.calculate_final_score(
                self.db, current_summary.id, current_summary.period
            )
            if score_result:
                latest_result = {
                    "period": current_summary.period,
                    "final_score": score_result["final_score"],
                    "level": PerformanceService.get_score_level(
                        score_result["final_score"]
                    ),
                    "dept_score": score_result["dept_score"],
                    "project_score": score_result["project_score"],
                }

        # 季度趋势（最近3个月）
        quarterly_trend = []
        for i in range(3):
            past_period = (date.today() - timedelta(days=30 * i)).strftime("%Y-%m")
            past_summary = (
                self.db.query(MonthlyWorkSummary)
                .filter(
                    MonthlyWorkSummary.employee_id == current_user.id,
                    MonthlyWorkSummary.period == past_period,
                    MonthlyWorkSummary.status == "COMPLETED",
                )
                .first()
            )

            if past_summary:
                score_result = PerformanceService.calculate_final_score(
                    self.db, past_summary.id, past_summary.period
                )
                if score_result:
                    quarterly_trend.append(
                        {"period": past_summary.period, "score": score_result["final_score"]}
                    )

        # 历史记录（最近3个月）
        history = PerformanceService.get_historical_performance(
            self.db, current_user.id, 3
        )

        return {
            "current_status": current_status,
            "latest_result": latest_result,
            "quarterly_trend": quarterly_trend,
            "history": history,
        }
