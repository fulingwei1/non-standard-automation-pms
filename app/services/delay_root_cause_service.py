# -*- coding: utf-8 -*-
"""
延期深度分析服务

进行延期根因分析、影响分析和趋势分析
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from collections import defaultdict
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from app.models.project import Project, ProjectMilestone, ProjectStage
from app.models.progress import Task
from app.models.issue import Issue
from app.models.user import User

logger = logging.getLogger(__name__)


class DelayRootCauseService:
    """延期深度分析服务"""

    def __init__(self, db: Session):
        self.db = db

    def analyze_root_cause(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """延期根因分析"""
        # 查询延期任务
        query = self.db.query(Task).filter(
            Task.is_delayed == True
        )

        if project_id:
            query = query.filter(Task.project_id == project_id)
        if start_date:
            query = query.filter(Task.plan_start_date >= start_date)
        if end_date:
            query = query.filter(Task.plan_start_date <= end_date)

        delayed_tasks = query.all()

        # 统计延期原因
        reason_stats = defaultdict(lambda: {
            'count': 0,
            'total_delay_days': 0,
            'tasks': []
        })

        for task in delayed_tasks:
            reason = task.delay_reason or 'UNKNOWN'
            delay_days = self._calculate_delay_days(task)

            reason_stats[reason]['count'] += 1
            reason_stats[reason]['total_delay_days'] += delay_days
            reason_stats[reason]['tasks'].append({
                'task_id': task.id,
                'task_name': task.task_name,
                'delay_days': delay_days,
                'project_id': task.project_id
            })

        # 转换为列表并排序
        reason_list = []
        for reason, stats in reason_stats.items():
            reason_list.append({
                'reason': reason,
                'count': stats['count'],
                'total_delay_days': stats['total_delay_days'],
                'average_delay_days': round(stats['total_delay_days'] / stats['count'], 1) if stats['count'] > 0 else 0,
                'tasks': stats['tasks'][:10]  # Top 10
            })
        reason_list.sort(key=lambda x: x['total_delay_days'], reverse=True)

        return {
            'analysis_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'total_delayed_tasks': len(delayed_tasks),
            'root_causes': reason_list,
            'summary': {
                'total_delay_days': sum(r['total_delay_days'] for r in reason_list),
                'top_reason': reason_list[0]['reason'] if reason_list else None
            }
        }

    def analyze_impact(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """延期影响分析"""
        # 查询延期项目
        projects = self.db.query(Project).filter(
            Project.status.notin_(['ST30', 'ST99'])  # 排除已结项和取消
        ).all()

        cost_impact = Decimal('0')
        revenue_impact = Decimal('0')
        affected_projects = []

        for project in projects:
            # 检查项目是否有延期
            if self._is_project_delayed(project):
                delay_days = self._calculate_project_delay_days(project)
                
                # 计算成本影响（简化：延期导致的额外成本）
                # 这里可以基于项目预算和延期天数估算
                if project.contract_amount:
                    daily_cost = Decimal(str(project.contract_amount)) * Decimal('0.001')  # 假设每天0.1%成本
                    cost_impact += daily_cost * Decimal(str(delay_days))

                # 计算回款影响（延期导致回款延迟）
                if project.contract_amount:
                    revenue_impact += Decimal(str(project.contract_amount)) * Decimal('0.0005') * Decimal(str(delay_days))

                affected_projects.append({
                    'project_id': project.id,
                    'project_code': project.project_code,
                    'project_name': project.project_name,
                    'delay_days': delay_days,
                    'cost_impact': float(daily_cost * Decimal(str(delay_days))) if project.contract_amount else 0
                })

        return {
            'analysis_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'cost_impact': {
                'total': float(cost_impact),
                'description': '延期导致的额外成本'
            },
            'revenue_impact': {
                'total': float(revenue_impact),
                'description': '延期导致回款延迟的影响'
            },
            'affected_projects': affected_projects[:20]  # Top 20
        }

    def analyze_trends(
        self,
        months: int = 12
    ) -> Dict[str, Any]:
        """延期趋势分析"""
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)

        # 按月统计延期率
        monthly_stats = defaultdict(lambda: {
            'total_tasks': 0,
            'delayed_tasks': 0,
            'delay_rate': 0.0,
            'total_delay_days': 0
        })

        # 查询任务
        tasks = self.db.query(Task).filter(
            Task.plan_start_date >= start_date,
            Task.plan_start_date <= end_date
        ).all()

        for task in tasks:
            month_key = task.plan_start_date.strftime('%Y-%m') if task.plan_start_date else None
            if month_key:
                monthly_stats[month_key]['total_tasks'] += 1
                if task.is_delayed:
                    monthly_stats[month_key]['delayed_tasks'] += 1
                    delay_days = self._calculate_delay_days(task)
                    monthly_stats[month_key]['total_delay_days'] += delay_days

        # 计算延期率
        trend_data = []
        for month in sorted(monthly_stats.keys()):
            stats = monthly_stats[month]
            stats['delay_rate'] = round(
                stats['delayed_tasks'] / stats['total_tasks'] * 100, 2
            ) if stats['total_tasks'] > 0 else 0
            trend_data.append({
                'month': month,
                **stats
            })

        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'months': months
            },
            'trends': trend_data,
            'summary': {
                'average_delay_rate': round(
                    sum(d['delay_rate'] for d in trend_data) / len(trend_data), 2
                ) if trend_data else 0,
                'trend_direction': self._calculate_trend_direction(trend_data)
            }
        }

    def _calculate_delay_days(self, task: Task) -> int:
        """计算任务延期天数"""
        if not task.is_delayed:
            return 0

        plan_end = task.plan_end_date
        actual_end = task.actual_end_date

        if plan_end and actual_end:
            return (actual_end - plan_end).days
        elif plan_end:
            # 如果计划结束日期已过但实际未结束
            today = date.today()
            if today > plan_end:
                return (today - plan_end).days

        return 0

    def _is_project_delayed(self, project: Project) -> bool:
        """判断项目是否延期"""
        if project.plan_end_date and project.actual_end_date:
            return project.actual_end_date > project.plan_end_date
        elif project.plan_end_date:
            # 如果计划结束日期已过但实际未结束
            return date.today() > project.plan_end_date
        return False

    def _calculate_project_delay_days(self, project: Project) -> int:
        """计算项目延期天数"""
        if not self._is_project_delayed(project):
            return 0

        plan_end = project.plan_end_date
        actual_end = project.actual_end_date or date.today()

        if plan_end:
            return (actual_end - plan_end).days
        return 0

    def _calculate_trend_direction(self, trend_data: List[Dict[str, Any]]) -> str:
        """计算趋势方向"""
        if len(trend_data) < 2:
            return 'STABLE'

        recent_rate = trend_data[-1]['delay_rate']
        earlier_rate = trend_data[0]['delay_rate']

        if recent_rate > earlier_rate * 1.1:
            return 'INCREASING'
        elif recent_rate < earlier_rate * 0.9:
            return 'DECREASING'
        else:
            return 'STABLE'
