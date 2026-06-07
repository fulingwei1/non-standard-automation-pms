# -*- coding: utf-8 -*-
"""
资源投入分析模块
提供单个线索/项目的资源投入详情查询功能
"""

from collections import defaultdict
from decimal import Decimal
from typing import Any, Dict

from app.models.timesheet import Timesheet
from app.models.user import User

WorkLog = Timesheet  # Backward-compatible symbol for older tests/imports.


def _first_real_attr(obj, *names, default=None):
    """Return the first explicitly set attribute; tolerate MagicMock fallback attrs."""
    for name in names:
        value = getattr(obj, name, None)
        if value is None:
            continue
        if value.__class__.__module__.startswith("unittest.mock"):
            continue
        return value
    return default


class InvestmentAnalysisMixin:
    """资源投入分析功能混入类"""

    def get_lead_resource_investment(self, project_id: int) -> Dict[str, Any]:
        """获取单个线索/项目的资源投入详情

        Returns:
            {
                'total_hours': float,
                'engineer_hours': dict,  # 按工程师分
                'monthly_hours': dict,   # 按月份分
                'stage_hours': dict,     # 按阶段分
                'estimated_cost': Decimal,
                'engineer_count': int
            }
        """
        timesheets = self.db.query(Timesheet).filter(Timesheet.project_id == project_id).all()

        total_hours = 0.0
        engineer_hours = defaultdict(float)
        monthly_hours = defaultdict(float)
        stage_hours = defaultdict(float)

        for sheet in timesheets:
            hours = float(_first_real_attr(sheet, "work_hours", "hours", default=0) or 0)
            total_hours += hours

            # 按工程师
            emp_id = _first_real_attr(sheet, "employee_id", "user_id", default=0) or 0
            engineer_hours[emp_id] += hours

            # 按月份
            work_date = _first_real_attr(sheet, "work_date")
            if work_date:
                month_key = work_date.strftime("%Y-%m")
                monthly_hours[month_key] += hours

            # 按工作类型/阶段
            work_type = _first_real_attr(
                sheet,
                "work_type",
                "task_name",
                "overtime_type",
                default="other",
            )
            stage_hours[work_type] += hours

        # 获取工程师详情
        engineer_details = []
        for emp_id, hours in engineer_hours.items():
            if emp_id:
                user = self.db.query(User).filter(User.id == emp_id).first()
                employee_name = _first_real_attr(
                    user,
                    "display_name",
                    "name",
                    "real_name",
                    "username",
                    default=f"Employee_{emp_id}",
                )
                engineer_details.append(
                    {
                        "employee_id": emp_id,
                        "employee_name": employee_name,
                        "hours": round(hours, 1),
                        "cost": float(Decimal(str(hours)) * self.hourly_rate),
                    }
                )

        estimated_cost = Decimal(str(total_hours)) * self.hourly_rate

        return {
            "total_hours": round(total_hours, 1),
            "engineer_hours": dict(engineer_hours),
            "engineer_details": sorted(engineer_details, key=lambda x: x["hours"], reverse=True),
            "monthly_hours": dict(sorted(monthly_hours.items())),
            "stage_hours": dict(stage_hours),
            "estimated_cost": estimated_cost,
            "engineer_count": len([h for h in engineer_hours.values() if h > 0]),
        }
