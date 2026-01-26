# -*- coding: utf-8 -*-
"""
分析报表生成模块
提供工作量分析、成本分析等分析报表的生成功能
"""

from datetime import date
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User


class AnalysisReportMixin:
    """分析报表生成功能混入类"""

    @staticmethod
    def _generate_workload_analysis(
        db: Session,
        department_id: Optional[int],
        start_date: date,
        end_date: date,
        sections_config: Dict,
        metrics_config: Dict
    ) -> Dict[str, Any]:
        """生成负荷分析报表"""
        # 获取人员范围
        if department_id:
            users = db.query(User).filter(
                User.department_id == department_id,
                User.is_active == True
            ).all()
            dept = db.query(Department).filter(Department.id == department_id).first()
            scope_name = dept.name if dept else "部门"
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
        workload_list = []
        overload_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0

        for user in users:
            user_timesheets = [t for t in timesheets if t.user_id == user.id]
            hours = sum(float(t.hours or 0) for t in user_timesheets)
            working_days = hours / 8  # 假设每天8小时

            # 负荷评级
            if working_days > 22:
                load_level = "OVERLOAD"
                overload_count += 1
            elif working_days > 18:
                load_level = "HIGH"
                high_count += 1
            elif working_days > 12:
                load_level = "MEDIUM"
                medium_count += 1
            else:
                load_level = "LOW"
                low_count += 1

            workload_list.append({
                "user_id": user.id,
                "user_name": user.real_name or user.username,
                "department": user.department or "",
                "total_hours": round(hours, 2),
                "working_days": round(working_days, 1),
                "load_level": load_level
            })

        # 排序
        workload_list.sort(key=lambda x: x["working_days"], reverse=True)

        return {
            "summary": {
                "scope": scope_name,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "total_users": len(users)
            },
            "sections": {
                "workload": {
                    "title": "人员负荷详情",
                    "type": "table",
                    "data": workload_list
                }
            },
            "metrics": {
                "overload_count": overload_count,
                "high_count": high_count,
                "medium_count": medium_count,
                "low_count": low_count
            },
            "charts": [
                {
                    "type": "pie",
                    "title": "负荷分布",
                    "data": [
                        {"name": "超负荷", "value": overload_count},
                        {"name": "高负荷", "value": high_count},
                        {"name": "中等负荷", "value": medium_count},
                        {"name": "低负荷", "value": low_count}
                    ]
                }
            ]
        }

    @staticmethod
    def _generate_cost_analysis(
        db: Session,
        project_id: Optional[int],
        start_date: date,
        end_date: date,
        sections_config: Dict,
        metrics_config: Dict
    ) -> Dict[str, Any]:
        """生成成本分析报表"""
        if project_id:
            projects = db.query(Project).filter(Project.id == project_id).all()
        else:
            projects = db.query(Project).filter(
                Project.is_active == True,
                Project.status.in_(["IN_PROGRESS", "ON_HOLD"])
            ).all()

        project_data = []
        total_budget = 0
        total_actual = 0

        for project in projects:
            budget = float(project.budget_amount or 0) if hasattr(project, 'budget_amount') else 0
            total_budget += budget

            # 获取工时成本
            timesheets = db.query(Timesheet).filter(
                Timesheet.project_id == project.id,
                Timesheet.work_date.between(start_date, end_date)
            ).all()

            labor_hours = sum(float(t.hours or 0) for t in timesheets)
            estimated_labor_cost = labor_hours * 100  # 假设时薪100元

            total_actual += estimated_labor_cost

            project_data.append({
                "project_id": project.id,
                "project_name": project.project_name,
                "budget": round(budget, 2),
                "actual_cost": round(estimated_labor_cost, 2),
                "variance": round(budget - estimated_labor_cost, 2),
                "variance_percent": round((budget - estimated_labor_cost) / budget * 100, 2) if budget > 0 else 0
            })

        return {
            "summary": {
                "project_count": len(projects),
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat()
            },
            "sections": {
                "cost_breakdown": {
                    "title": "项目成本明细",
                    "type": "table",
                    "data": project_data
                }
            },
            "metrics": {
                "total_budget": round(total_budget, 2),
                "total_actual": round(total_actual, 2),
                "total_variance": round(total_budget - total_actual, 2)
            },
            "charts": [
                {
                    "type": "bar",
                    "title": "预算 vs 实际成本",
                    "x_field": "project_name",
                    "y_fields": ["budget", "actual_cost"]
                }
            ]
        }
