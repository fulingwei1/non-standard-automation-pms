# -*- coding: utf-8 -*-
"""
资源投入分析模块
提供单个线索/项目的资源投入详情查询功能
"""

from collections import defaultdict
from decimal import Decimal
from typing import Any, Dict

from app.models.user import User
from app.models.work_log import WorkLog


class InvestmentAnalysisMixin:
    """资源投入分析功能混入类"""

    def get_lead_resource_investment(
        self,
        project_id: int
    ) -> Dict[str, Any]:
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
        work_logs = self.db.query(WorkLog).filter(
            WorkLog.project_id == project_id
        ).all()

        total_hours = 0.0
        engineer_hours = defaultdict(float)
        monthly_hours = defaultdict(float)
        stage_hours = defaultdict(float)

        for log in work_logs:
            hours = log.work_hours or 0
            total_hours += hours

            # 按工程师
            emp_id = log.employee_id or 0
            engineer_hours[emp_id] += hours

            # 按月份
            if log.work_date:
                month_key = log.work_date.strftime('%Y-%m')
                monthly_hours[month_key] += hours

            # 按工作类型/阶段
            work_type = getattr(log, 'work_type', 'other') or 'other'
            stage_hours[work_type] += hours

        # 获取工程师详情
        engineer_details = []
        for emp_id, hours in engineer_hours.items():
            if emp_id:
                user = self.db.query(User).filter(User.id == emp_id).first()
                engineer_details.append({
                    'employee_id': emp_id,
                    'employee_name': user.name if user else f'Employee_{emp_id}',
                    'hours': round(hours, 1),
                    'cost': float(Decimal(str(hours)) * self.hourly_rate)
                })

        estimated_cost = Decimal(str(total_hours)) * self.hourly_rate

        return {
            'total_hours': round(total_hours, 1),
            'engineer_hours': dict(engineer_hours),
            'engineer_details': sorted(engineer_details, key=lambda x: x['hours'], reverse=True),
            'monthly_hours': dict(sorted(monthly_hours.items())),
            'stage_hours': dict(stage_hours),
            'estimated_cost': estimated_cost,
            'engineer_count': len([h for h in engineer_hours.values() if h > 0])
        }
