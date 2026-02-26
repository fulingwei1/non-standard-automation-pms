# -*- coding: utf-8 -*-
"""
成本过高分析服务

分析成本超支原因、归责和影响
"""

import logging
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.project import FinancialProjectCost, Project, ProjectCost
from app.models.timesheet import Timesheet
from app.models.user import User
from app.services.hourly_rate_service import HourlyRateService

logger = logging.getLogger(__name__)


class CostOverrunAnalysisService:
    """成本过高分析服务"""

    def __init__(self, db: Session):
        self.db = db
        self.hourly_rate_service = HourlyRateService()

    def analyze_reasons(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """成本超支原因分析"""
        # 查询有成本超支的项目
        projects = self.db.query(Project).filter(
            Project.status.notin_(['ST30', 'ST99'])
        )

        if project_id:
            projects = projects.filter(Project.id == project_id)
        if start_date:
            projects = projects.filter(Project.created_at >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            projects = projects.filter(Project.created_at <= datetime.combine(end_date, datetime.max.time()))

        projects = projects.all()

        overrun_projects = []
        reason_stats = defaultdict(lambda: {
            'count': 0,
            'total_overrun': Decimal('0'),
            'projects': []
        })

        for project in projects:
            overrun_analysis = self._analyze_project_overrun(project)
            if overrun_analysis['has_overrun']:
                overrun_projects.append(overrun_analysis)

                # 统计原因
                for reason in overrun_analysis.get('reasons', []):
                    reason_stats[reason]['count'] += 1
                    reason_stats[reason]['total_overrun'] += Decimal(str(overrun_analysis['overrun_amount']))
                    reason_stats[reason]['projects'].append({
                        'project_id': project.id,
                        'project_code': project.project_code,
                        'overrun_amount': overrun_analysis['overrun_amount']
                    })

        # 转换为列表
        reason_list = [
            {
                'reason': reason,
                'count': stats['count'],
                'total_overrun': float(stats['total_overrun']),
                'average_overrun': float(stats['total_overrun'] / stats['count']) if stats['count'] > 0 else 0,
                'projects': stats['projects'][:10]
            }
            for reason, stats in reason_stats.items()
        ]
        reason_list.sort(key=lambda x: x['total_overrun'], reverse=True)

        return {
            'analysis_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'total_overrun_projects': len(overrun_projects),
            'reasons': reason_list,
            'projects': overrun_projects[:20]  # Top 20
        }

    def analyze_accountability(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """成本超支归责"""
        reasons_analysis = self.analyze_reasons(start_date, end_date)
        projects = reasons_analysis.get('projects', [])

        # 按人员归责
        person_stats = defaultdict(lambda: {
            'overrun_count': 0,
            'total_overrun': Decimal('0'),
            'reasons': defaultdict(int)
        })

        # 按部门归责
        defaultdict(lambda: {
            'overrun_count': 0,
            'total_overrun': Decimal('0'),
            'people': []
        })

        for project_data in projects:
            project_id = project_data['project_id']
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                continue

            # 归责到报价人员（如果报价不准确）
            if project.opportunity_id:
                opp = project.opportunity
                if opp and opp.owner_id:
                    person_stats[opp.owner_id]['overrun_count'] += 1
                    person_stats[opp.owner_id]['total_overrun'] += Decimal(str(project_data['overrun_amount']))
                    person_stats[opp.owner_id]['reasons']['报价不准确'] += 1

            # 归责到销售（如果需求把握不准）
            if project.salesperson_id:
                person_stats[project.salesperson_id]['overrun_count'] += 1
                person_stats[project.salesperson_id]['total_overrun'] += Decimal(str(project_data['overrun_amount']))
                person_stats[project.salesperson_id]['reasons']['需求把握不准'] += 1

            # 归责到项目经理（成本控制不力）
            if project.pm_id:
                person_stats[project.pm_id]['overrun_count'] += 1
                person_stats[project.pm_id]['total_overrun'] += Decimal(str(project_data['overrun_amount']))
                person_stats[project.pm_id]['reasons']['成本控制不力'] += 1

            # 归责到工程师（工时超支）
            timesheets = self.db.query(Timesheet).filter(
                Timesheet.project_id == project_id
            ).all()
            for ts in timesheets:
                if ts.user_id:
                    person_stats[ts.user_id]['overrun_count'] += 1
                    # 计算工时超支成本
                    plan_hours = 0  # 需要从项目计划中获取
                    actual_hours = float(ts.hours or 0)
                    if actual_hours > plan_hours:
                        user = self.db.query(User).filter(User.id == ts.user_id).first()
                        if user:
                            hourly_rate = self.hourly_rate_service.get_user_hourly_rate(self.db, user.id, ts.work_date)
                            overrun_cost = Decimal(str(actual_hours - plan_hours)) * hourly_rate
                            person_stats[ts.user_id]['total_overrun'] += overrun_cost
                            person_stats[ts.user_id]['reasons']['工时超支'] += 1

        # 转换为列表
        person_list = []
        for person_id, stats in person_stats.items():
            person = self.db.query(User).filter(User.id == person_id).first()
            person_list.append({
                'person_id': person_id,
                'person_name': person.real_name if person and person.real_name else (person.username if person else f'User_{person_id}'),
                'department': person.department if person else None,
                'overrun_count': stats['overrun_count'],
                'total_overrun': float(stats['total_overrun']),
                'reasons': dict(stats['reasons'])
            })
        person_list.sort(key=lambda x: x['total_overrun'], reverse=True)

        return {
            'analysis_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'by_person': person_list[:20],  # Top 20
            'by_department': []  # 可以进一步按部门汇总
        }

    def analyze_impact(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """成本超支影响分析"""
        reasons_analysis = self.analyze_reasons(start_date, end_date)
        projects = reasons_analysis.get('projects', [])

        total_overrun = Decimal('0')
        total_contract_amount = Decimal('0')
        affected_projects = []

        for project_data in projects:
            project_id = project_data['project_id']
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                continue

            overrun_amount = Decimal(str(project_data['overrun_amount']))
            total_overrun += overrun_amount

            contract_amount = project.contract_amount or Decimal('0')
            total_contract_amount += contract_amount

            # 计算毛利率影响
            if contract_amount > 0:
                original_margin = project.est_margin or Decimal('0')
                overrun_ratio = overrun_amount / contract_amount
                affected_margin = original_margin - (overrun_ratio * Decimal('100'))

                affected_projects.append({
                    'project_id': project_id,
                    'project_code': project.project_code,
                    'contract_amount': float(contract_amount),
                    'overrun_amount': float(overrun_amount),
                    'original_margin': float(original_margin),
                    'affected_margin': float(affected_margin),
                    'margin_impact': float(original_margin - affected_margin)
                })

        # 计算总体影响
        overall_margin_impact = 0.0
        if total_contract_amount > 0:
            overall_overrun_ratio = total_overrun / total_contract_amount
            overall_margin_impact = float(overall_overrun_ratio * Decimal('100'))

        return {
            'analysis_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'summary': {
                'total_overrun': float(total_overrun),
                'total_contract_amount': float(total_contract_amount),
                'overrun_ratio': float(total_overrun / total_contract_amount * 100) if total_contract_amount > 0 else 0,
                'overall_margin_impact': overall_margin_impact
            },
            'affected_projects': affected_projects[:20]  # Top 20
        }

    def _analyze_project_overrun(self, project: Project) -> Dict[str, Any]:
        """分析单个项目的成本超支"""
        # 获取项目预算
        budget = project.budget or Decimal('0')

        # 计算实际成本
        actual_cost = self._calculate_actual_cost(project.id)

        has_overrun = actual_cost > budget
        overrun_amount = actual_cost - budget if has_overrun else Decimal('0')
        overrun_ratio = (overrun_amount / budget * 100) if budget > 0 else Decimal('0')

        reasons = []
        if has_overrun:
            # 分析超支原因
            # 1. 检查工时是否超支
            plan_hours = project.plan_manhours or 0
            actual_hours = self._calculate_actual_hours(project.id)
            if actual_hours > plan_hours:
                reasons.append('工时超支')

            # 2. 检查是否有需求变更
            # 可以通过ECN或项目变更记录判断
            if project.ecns:
                reasons.append('需求变更导致成本增加')

            # 3. 检查物料成本
            material_cost = self._calculate_material_cost(project.id)
            if material_cost > (budget * Decimal('0.5')):  # 如果物料成本超过预算50%
                reasons.append('物料成本超支')

            # 4. 检查外协成本
            outsourcing_cost = self._calculate_outsourcing_cost(project.id)
            if outsourcing_cost > (budget * Decimal('0.2')):  # 如果外协成本超过预算20%
                reasons.append('外协成本超支')

            if not reasons:
                reasons.append('其他原因')

        return {
            'project_id': project.id,
            'project_code': project.project_code,
            'project_name': project.project_name,
            'has_overrun': has_overrun,
            'budget': float(budget),
            'actual_cost': float(actual_cost),
            'overrun_amount': float(overrun_amount),
            'overrun_ratio': float(overrun_ratio),
            'reasons': reasons
        }

    def _calculate_actual_cost(self, project_id: int) -> Decimal:
        """计算项目实际成本"""
        # 物料成本
        material_cost = self._calculate_material_cost(project_id)

        # 工时成本
        labor_cost = self._calculate_labor_cost(project_id)

        # 外协成本
        outsourcing_cost = self._calculate_outsourcing_cost(project_id)

        # 其他成本
        other_costs = self.db.query(func.sum(FinancialProjectCost.amount)).filter(
            FinancialProjectCost.project_id == project_id
        ).scalar() or Decimal('0')

        return material_cost + labor_cost + outsourcing_cost + Decimal(str(other_costs))

    def _calculate_material_cost(self, project_id: int) -> Decimal:
        """计算物料成本"""
        from app.services.cost.cost_data_queries import get_cost_by_type

        return get_cost_by_type(self.db, project_id, "MATERIAL")

    def _calculate_labor_cost(self, project_id: int) -> Decimal:
        """计算工时成本"""
        timesheets = self.db.query(Timesheet).filter(
            Timesheet.project_id == project_id
        ).all()

        total_cost = Decimal('0')
        for ts in timesheets:
            user = self.db.query(User).filter(User.id == ts.user_id).first()
            if user:
                hourly_rate = self.hourly_rate_service.get_user_hourly_rate(self.db, user.id, ts.work_date)
                total_cost += Decimal(str(ts.hours or 0)) * hourly_rate

        return total_cost

    def _calculate_outsourcing_cost(self, project_id: int) -> Decimal:
        """计算外协成本"""
        from app.models.outsourcing import OutsourcingOrder
        outsourcing_orders = self.db.query(OutsourcingOrder).filter(
            OutsourcingOrder.project_id == project_id
        ).all()

        total_cost = Decimal('0')
        for order in outsourcing_orders:
            total_cost += Decimal(str(order.total_amount or 0))

        return total_cost

    def _calculate_actual_hours(self, project_id: int) -> float:
        """计算实际工时"""
        total_hours = self.db.query(func.sum(Timesheet.hours)).filter(
            Timesheet.project_id == project_id
        ).scalar() or 0
        return float(total_hours)
