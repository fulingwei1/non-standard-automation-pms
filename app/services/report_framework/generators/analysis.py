# -*- coding: utf-8 -*-
"""
分析报表数据生成器

统一的负荷分析、成本分析等分析报表数据生成逻辑
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.common.date_range import month_start
from app.models.organization import Department
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User


class AnalysisReportGenerator:
    """分析报表数据生成器"""

    # 负荷级别阈值（按月度工作日计算）
    LOAD_THRESHOLDS = {
        "OVERLOAD": 22,  # 超过22天
        "HIGH": 18,      # 18-22天
        "MEDIUM": 12,    # 12-18天
        # LOW: < 12天
    }

    # 默认时薪（元）
    DEFAULT_HOURLY_RATE = 100

    @staticmethod
    def generate_workload_analysis(
        db: Session,
        department_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        生成负荷分析报告

        Args:
            db: 数据库会话
            department_id: 部门ID（可选，不指定则全公司）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            报表数据字典
        """
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        # 获取人员范围
        users, scope_name = AnalysisReportGenerator._get_user_scope(
            db, department_id
        )
        user_ids = [u.id for u in users]

        # 工时统计
        timesheets = []
        if user_ids:
            timesheets = (
                db.query(Timesheet)
                .filter(
                    Timesheet.user_id.in_(user_ids),
                    Timesheet.work_date.between(start_date, end_date),
                )
                .all()
            )

        # 按人员统计工作负荷
        workload_list, load_summary = AnalysisReportGenerator._calculate_workload(
            db, users, timesheets
        )

        return {
            "summary": {
                "scope": scope_name,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "total_users": len(users),
                "active_users": len(workload_list),
            },
            "load_distribution": load_summary,
            "workload_details": sorted(
                workload_list, key=lambda x: x["working_days"], reverse=True
            ),
            "charts": [
                {
                    "type": "pie",
                    "title": "负荷分布",
                    "data": [
                        {"name": "超负荷", "value": load_summary.get("OVERLOAD", 0)},
                        {"name": "高负荷", "value": load_summary.get("HIGH", 0)},
                        {"name": "中等负荷", "value": load_summary.get("MEDIUM", 0)},
                        {"name": "低负荷", "value": load_summary.get("LOW", 0)},
                    ],
                }
            ],
        }

    @staticmethod
    def generate_cost_analysis(
        db: Session,
        project_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        生成成本分析报告

        Args:
            db: 数据库会话
            project_id: 项目ID（可选，不指定则汇总所有进行中项目）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            报表数据字典
        """
        if not start_date:
            start_date = month_start(date.today()) # 本月初
        if not end_date:
            end_date = date.today()

        # 获取项目列表
        projects = AnalysisReportGenerator._get_projects(db, project_id)

        # 计算成本
        project_summaries, total_budget, total_actual = (
            AnalysisReportGenerator._calculate_project_costs(
                db, projects, start_date, end_date
            )
        )

        return {
            "summary": {
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "project_count": len(projects),
                "total_budget": round(total_budget, 2),
                "total_actual": round(total_actual, 2),
                "total_variance": round(total_budget - total_actual, 2),
            },
            "project_breakdown": project_summaries,
            "charts": [
                {
                    "type": "bar",
                    "title": "预算 vs 实际成本",
                    "x_field": "project_name",
                    "y_fields": ["budget", "actual_cost"],
                }
            ],
        }

    @staticmethod
    def _get_user_scope(
        db: Session, department_id: Optional[int]
    ) -> tuple[List[User], str]:
        """获取用户范围"""
        if department_id:
            dept = (
                db.query(Department)
                .filter(Department.id == department_id)
                .first()
            )
            if dept:
                # 尝试通过 department_id 查询
                users = (
                    db.query(User)
                    .filter(
                        User.department_id == department_id,
                        User.is_active,
                    )
                    .all()
                )

                # 如果没有结果，尝试通过部门名称查询
                if not users:
                    dept_name = getattr(dept, "dept_name", getattr(dept, "name", ""))
                    if dept_name:
                        users = (
                            db.query(User)
                            .filter(
                                User.department == dept_name,
                                User.is_active,
                            )
                            .all()
                        )

                scope_name = getattr(dept, "dept_name", getattr(dept, "name", "部门"))
            else:
                users = []
                scope_name = "部门"
        else:
            users = db.query(User).filter(User.is_active).all()
            scope_name = "全公司"

        return users, scope_name

    @staticmethod
    def _calculate_workload(
        db: Session,
        users: List[User],
        timesheets: List[Timesheet],
    ) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
        """计算工作负荷"""
        # 按用户汇总
        workload_by_user = {}
        for ts in timesheets:
            user_id = ts.user_id
            if user_id not in workload_by_user:
                workload_by_user[user_id] = {"hours": 0, "projects": set()}
            workload_by_user[user_id]["hours"] += float(ts.hours or 0)
            if ts.project_id:
                workload_by_user[user_id]["projects"].add(ts.project_id)

        # 转换为列表
        workload_list = []
        load_summary = {"OVERLOAD": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

        for user in users:
            data = workload_by_user.get(user.id, {"hours": 0, "projects": set()})
            hours = data["hours"]
            days = hours / 8  # 假设每天8小时
            project_count = len(data["projects"])

            # 负荷评级
            if days > AnalysisReportGenerator.LOAD_THRESHOLDS["OVERLOAD"]:
                load_level = "OVERLOAD"
            elif days > AnalysisReportGenerator.LOAD_THRESHOLDS["HIGH"]:
                load_level = "HIGH"
            elif days > AnalysisReportGenerator.LOAD_THRESHOLDS["MEDIUM"]:
                load_level = "MEDIUM"
            else:
                load_level = "LOW"

            load_summary[load_level] += 1

            workload_list.append(
                {
                    "user_id": user.id,
                    "user_name": user.real_name or user.username,
                    "department": getattr(user, "department", "") or "",
                    "total_hours": round(hours, 2),
                    "working_days": round(days, 1),
                    "project_count": project_count,
                    "load_level": load_level,
                }
            )

        return workload_list, load_summary

    @staticmethod
    def _get_projects(
        db: Session, project_id: Optional[int]
    ) -> List[Project]:
        """获取项目列表"""
        if project_id:
            return db.query(Project).filter(Project.id == project_id).all()
        else:
            return (
                db.query(Project)
                .filter(
                    Project.is_active,
                    Project.status.in_(["IN_PROGRESS", "ON_HOLD"]),
                )
                .all()
            )

    @staticmethod
    def _calculate_project_costs(
        db: Session,
        projects: List[Project],
        start_date: date,
        end_date: date,
    ) -> tuple[List[Dict[str, Any]], float, float]:
        """计算项目成本"""
        project_summaries = []
        total_budget = 0
        total_actual = 0

        for project in projects:
            budget = (
                float(project.budget_amount or 0)
                if hasattr(project, "budget_amount")
                else 0
            )
            total_budget += budget

            # 获取项目工时
            timesheets = (
                db.query(Timesheet)
                .filter(
                    Timesheet.project_id == project.id,
                    Timesheet.work_date.between(start_date, end_date),
                )
                .all()
            )
            labor_hours = sum(float(t.hours or 0) for t in timesheets)

            # 估算人工成本
            estimated_labor_cost = (
                labor_hours * AnalysisReportGenerator.DEFAULT_HOURLY_RATE
            )
            total_actual += estimated_labor_cost

            variance = budget - estimated_labor_cost
            variance_percent = (variance / budget * 100) if budget > 0 else 0

            project_summaries.append(
                {
                    "project_id": project.id,
                    "project_name": project.project_name,
                    "budget": round(budget, 2),
                    "actual_cost": round(estimated_labor_cost, 2),
                    "labor_hours": round(labor_hours, 2),
                    "variance": round(variance, 2),
                    "variance_percent": round(variance_percent, 2),
                }
            )

        return project_summaries, total_budget, total_actual
