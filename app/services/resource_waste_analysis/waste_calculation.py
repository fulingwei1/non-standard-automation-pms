# -*- coding: utf-8 -*-
"""
浪费计算模块
提供指定周期内的资源浪费计算功能
"""

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any, Dict

from sqlalchemy import func

from app.models.enums import LeadOutcomeEnum
from app.models.project import Project
from app.models.work_log import WorkLog


class WasteCalculationMixin:
    """浪费计算功能混入类"""

    def calculate_waste_by_period(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """计算指定周期内的资源浪费

        Returns:
            {
                'period': str,
                'total_leads': int,
                'won_leads': int,
                'lost_leads': int,
                'win_rate': float,
                'total_investment_hours': float,
                'productive_hours': float,  # 中标项目
                'wasted_hours': float,       # 失败项目
                'wasted_cost': Decimal,
                'waste_rate': float,
                'loss_reasons': dict
            }
        """
        projects = self.db.query(Project).filter(
            Project.created_at >= start_date,
            Project.created_at < end_date
        ).all()

        total_leads = len(projects)
        won_projects = [p for p in projects if p.outcome == LeadOutcomeEnum.WON.value]
        lost_projects = [p for p in projects if p.outcome in [
            LeadOutcomeEnum.LOST.value,
            LeadOutcomeEnum.ABANDONED.value
        ]]
        pending_projects = [p for p in projects if p.outcome in [
            LeadOutcomeEnum.PENDING.value,
            LeadOutcomeEnum.ON_HOLD.value,
            None
        ]]

        # 计算各类项目的工时
        total_investment_hours = 0.0
        productive_hours = 0.0
        wasted_hours = 0.0
        loss_reasons = defaultdict(int)

        # 获取所有相关工时
        project_ids = [p.id for p in projects]
        if project_ids:
            work_hours_map = dict(
                self.db.query(
                    WorkLog.project_id,
                    func.sum(WorkLog.work_hours)
                ).filter(
                    WorkLog.project_id.in_(project_ids)
                ).group_by(WorkLog.project_id).all()
            )
        else:
            work_hours_map = {}

        for project in projects:
            hours = work_hours_map.get(project.id, 0) or 0
            total_investment_hours += hours

            if project.outcome == LeadOutcomeEnum.WON.value:
                productive_hours += hours
            elif project.outcome in [LeadOutcomeEnum.LOST.value, LeadOutcomeEnum.ABANDONED.value]:
                wasted_hours += hours
                reason = project.loss_reason or 'OTHER'
                loss_reasons[reason] += 1

        win_rate = len(won_projects) / (len(won_projects) + len(lost_projects)) if (len(won_projects) + len(lost_projects)) > 0 else 0
        waste_rate = wasted_hours / total_investment_hours if total_investment_hours > 0 else 0
        wasted_cost = Decimal(str(wasted_hours)) * self.hourly_rate

        return {
            'period': f'{start_date.isoformat()} ~ {end_date.isoformat()}',
            'total_leads': total_leads,
            'won_leads': len(won_projects),
            'lost_leads': len(lost_projects),
            'pending_leads': len(pending_projects),
            'win_rate': round(win_rate, 3),
            'total_investment_hours': round(total_investment_hours, 1),
            'productive_hours': round(productive_hours, 1),
            'wasted_hours': round(wasted_hours, 1),
            'wasted_cost': wasted_cost,
            'waste_rate': round(waste_rate, 3),
            'loss_reasons': dict(loss_reasons)
        }
