# -*- coding: utf-8 -*-
"""
分析报表生成（负荷分析、成本分析）
"""

from datetime import date, timedelta
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User


class AnalysisReportMixin:
    """分析报表生成功能混入类"""

    @staticmethod
    def generate_workload_analysis(
        db: Session,
        department_id: Optional[int] = None,
        start_date: date = None,
        end_date: date = None
    ) -> Dict[str, Any]:
        """
        生成负荷分析报告

        Args:
            db: 数据库会话
            department_id: 部门ID（可选）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            报表数据
        """
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        # 获取人员范围
        if department_id:
            dept = db.query(Department).filter(Department.id == department_id).first()
            if dept:
                # User 模型只有 department 字符串字段，通过部门名称匹配
                users = db.query(User).filter(
                    User.department == dept.dept_name,
                    User.is_active == True
                ).all()
                scope_name = dept.dept_name
            else:
                users = []
                scope_name = "部门"
        else:
            users = db.query(User).filter(User.is_active == True).all()
            scope_name = "全公司"

        user_ids = [u.id for u in users]

        # 工时统计
        timesheets = db.query(Timesheet).filter(
            Timesheet.user_id.in_(user_ids),
            Timesheet.work_date.between(start_date, end_date)
        ).all()

        # 按人员统计
        workload_by_user = {}
        for ts in timesheets:
            user_id = ts.user_id
            if user_id not in workload_by_user:
                workload_by_user[user_id] = {
                    "hours": 0,
                    "days": 0,
                    "projects": set()
                }
            workload_by_user[user_id]["hours"] += float(ts.hours or 0)
            if ts.project_id:
                workload_by_user[user_id]["projects"].add(ts.project_id)

        # 转换为列表
        workload_list = []
        for user_id, data in workload_by_user.items():
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                continue

            hours = data["hours"]
            days = hours / 8  # 假设每天8小时
            project_count = len(data["projects"])

            # 负荷评级
            if days > 22:  # 超过一个月工作日
                load_level = "OVERLOAD"
            elif days > 18:
                load_level = "HIGH"
            elif days > 12:
                load_level = "MEDIUM"
            else:
                load_level = "LOW"

            workload_list.append({
                "user_id": user_id,
                "user_name": user.real_name or user.username,
                "department": user.department if hasattr(user, 'department') else "",
                "total_hours": round(hours, 2),
                "working_days": round(days, 1),
                "project_count": project_count,
                "load_level": load_level
            })

        # 按负荷分组
        load_summary = {
            "OVERLOAD": sum(1 for w in workload_list if w["load_level"] == "OVERLOAD"),
            "HIGH": sum(1 for w in workload_list if w["load_level"] == "HIGH"),
            "MEDIUM": sum(1 for w in workload_list if w["load_level"] == "MEDIUM"),
            "LOW": sum(1 for w in workload_list if w["load_level"] == "LOW")
        }

        return {
            "summary": {
                "scope": scope_name,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "total_users": len(users),
                "active_users": len(workload_list)
            },
            "load_distribution": load_summary,
            "workload_details": sorted(workload_list, key=lambda x: x["working_days"], reverse=True)
        }

    @staticmethod
    def generate_cost_analysis(
        db: Session,
        project_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        生成成本分析报告

        Args:
            db: 数据库会话
            project_id: 项目ID（可选，不指定则汇总所有项目）
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            报表数据
        """
        if not start_date:
            start_date = date.today().replace(day=1)  # 本月初
        if not end_date:
            end_date = date.today()

        # 获取项目列表
        if project_id:
            projects = db.query(Project).filter(Project.id == project_id).all()
        else:
            projects = db.query(Project).filter(
                Project.is_active == True,
                Project.status.in_(["IN_PROGRESS", "ON_HOLD"])
            ).all()

        project_summaries = []
        total_budget = 0
        total_actual = 0

        for project in projects:
            budget = float(project.budget_amount or 0) if hasattr(project, 'budget_amount') else 0
            total_budget += budget

            # 获取项目工时成本
            timesheets = db.query(Timesheet).filter(
                Timesheet.project_id == project.id,
                Timesheet.work_date.between(start_date, end_date)
            ).all()
            labor_hours = sum(float(t.hours or 0) for t in timesheets)

            # 估算人工成本（假设平均时薪100元）
            estimated_labor_cost = labor_hours * 100
            total_actual += estimated_labor_cost

            variance = budget - estimated_labor_cost
            variance_percent = (variance / budget * 100) if budget > 0 else 0

            project_summaries.append({
                "project_id": project.id,
                "project_name": project.project_name,
                "budget": round(budget, 2),
                "actual_cost": round(estimated_labor_cost, 2),
                "variance": round(variance, 2),
                "variance_percent": round(variance_percent, 2)
            })

        return {
            "summary": {
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "project_count": len(projects),
                "total_budget": round(total_budget, 2),
                "total_actual": round(total_actual, 2),
                "total_variance": round(total_budget - total_actual, 2)
            },
            "project_breakdown": project_summaries
        }
