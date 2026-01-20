# -*- coding: utf-8 -*-
"""
销售人员分析模块
提供销售人员资源浪费排行和部门对比功能
"""

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func

from app.models.enums import LeadOutcomeEnum
from app.models.project import Project
from app.models.user import User
from app.models.work_log import WorkLog


class SalespersonAnalysisMixin:
    """销售人员分析功能混入类"""

    def get_salesperson_waste_ranking(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取销售人员资源浪费排行

        Returns:
            按浪费工时排序的销售人员列表
        """
        query = self.db.query(Project)

        if start_date:
            query = query.filter(Project.created_at >= start_date)
        if end_date:
            query = query.filter(Project.created_at < end_date)

        projects = query.all()

        # 按销售人员分组统计
        salesperson_stats = defaultdict(lambda: {
            'total_leads': 0,
            'won_leads': 0,
            'lost_leads': 0,
            'total_hours': 0.0,
            'wasted_hours': 0.0,
            'won_amount': Decimal('0'),
            'loss_reasons': defaultdict(int)
        })

        # 获取工时映射
        project_ids = [p.id for p in projects]
        work_hours_map = {}
        if project_ids:
            work_hours_map = dict(
                self.db.query(
                    WorkLog.project_id,
                    func.sum(WorkLog.work_hours)
                ).filter(
                    WorkLog.project_id.in_(project_ids)
                ).group_by(WorkLog.project_id).all()
            )

        for project in projects:
            sp_id = project.salesperson_id
            if not sp_id:
                continue

            stats = salesperson_stats[sp_id]
            stats['total_leads'] += 1

            hours = work_hours_map.get(project.id, 0) or 0
            stats['total_hours'] += hours

            if project.outcome == LeadOutcomeEnum.WON.value:
                stats['won_leads'] += 1
                stats['won_amount'] += project.contract_amount or Decimal('0')
            elif project.outcome in [LeadOutcomeEnum.LOST.value, LeadOutcomeEnum.ABANDONED.value]:
                stats['lost_leads'] += 1
                stats['wasted_hours'] += hours
                reason = project.loss_reason or 'OTHER'
                stats['loss_reasons'][reason] += 1

        # 获取销售人员信息并构建结果
        results = []
        for sp_id, stats in salesperson_stats.items():
            user = self.db.query(User).filter(User.id == sp_id).first()

            win_rate = stats['won_leads'] / (stats['won_leads'] + stats['lost_leads']) \
                if (stats['won_leads'] + stats['lost_leads']) > 0 else 0

            wasted_cost = Decimal(str(stats['wasted_hours'])) * self.hourly_rate

            # 资源效率：中标金额 / 总投入工时
            resource_efficiency = float(stats['won_amount']) / stats['total_hours'] \
                if stats['total_hours'] > 0 else 0

            # 主要丢标原因（Top 3）
            top_reasons = sorted(stats['loss_reasons'].items(), key=lambda x: x[1], reverse=True)[:3]

            results.append({
                'salesperson_id': sp_id,
                'salesperson_name': user.name if user else f'Sales_{sp_id}',
                'department': getattr(user, 'department_name', None) if user else None,
                'total_leads': stats['total_leads'],
                'won_leads': stats['won_leads'],
                'lost_leads': stats['lost_leads'],
                'win_rate': round(win_rate, 3),
                'total_hours': round(stats['total_hours'], 1),
                'wasted_hours': round(stats['wasted_hours'], 1),
                'wasted_cost': wasted_cost,
                'won_amount': stats['won_amount'],
                'resource_efficiency': round(resource_efficiency, 2),
                'top_loss_reasons': [{'reason': r, 'count': c} for r, c in top_reasons]
            })

        # 按浪费工时排序
        results.sort(key=lambda x: x['wasted_hours'], reverse=True)

        return results[:limit]

    def get_department_comparison(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """获取部门间资源浪费对比

        Returns:
            按部门分组的浪费统计
        """
        # 获取销售人员及其部门
        # 这里简化处理，实际应该通过部门关联
        salesperson_rankings = self.get_salesperson_waste_ranking(start_date, end_date, limit=100)

        # 按部门分组
        department_stats = defaultdict(lambda: {
            'salespeople_count': 0,
            'total_leads': 0,
            'won_leads': 0,
            'lost_leads': 0,
            'total_hours': 0.0,
            'wasted_hours': 0.0,
            'won_amount': Decimal('0')
        })

        for sp in salesperson_rankings:
            dept = sp.get('department') or '未分配部门'
            stats = department_stats[dept]
            stats['salespeople_count'] += 1
            stats['total_leads'] += sp['total_leads']
            stats['won_leads'] += sp['won_leads']
            stats['lost_leads'] += sp['lost_leads']
            stats['total_hours'] += sp['total_hours']
            stats['wasted_hours'] += sp['wasted_hours']
            stats['won_amount'] += sp['won_amount']

        results = []
        for dept, stats in department_stats.items():
            win_rate = stats['won_leads'] / (stats['won_leads'] + stats['lost_leads']) \
                if (stats['won_leads'] + stats['lost_leads']) > 0 else 0
            waste_rate = stats['wasted_hours'] / stats['total_hours'] \
                if stats['total_hours'] > 0 else 0

            results.append({
                'department': dept,
                'salespeople_count': stats['salespeople_count'],
                'total_leads': stats['total_leads'],
                'won_leads': stats['won_leads'],
                'lost_leads': stats['lost_leads'],
                'win_rate': round(win_rate, 3),
                'total_hours': round(stats['total_hours'], 1),
                'wasted_hours': round(stats['wasted_hours'], 1),
                'wasted_cost': Decimal(str(stats['wasted_hours'])) * self.hourly_rate,
                'waste_rate': round(waste_rate, 3),
                'won_amount': stats['won_amount']
            })

        # 按浪费工时排序
        results.sort(key=lambda x: x['wasted_hours'], reverse=True)

        return results
