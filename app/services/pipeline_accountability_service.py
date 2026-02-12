# -*- coding: utf-8 -*-
"""
全链条归责分析服务

支持按环节、按人员、按部门归责，计算责任成本
"""

import logging
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.sales import Lead, Quote
from app.models.timesheet import Timesheet
from app.models.user import User
from app.services.hourly_rate_service import HourlyRateService

logger = logging.getLogger(__name__)


class PipelineAccountabilityService:
    """全链条归责分析服务"""

    def __init__(self, db: Session):
        self.db = db
        self.hourly_rate_service = HourlyRateService()

    def analyze_by_stage(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """按环节归责分析"""
        from app.services.pipeline_break_analysis_service import (
            PipelineBreakAnalysisService,
        )
        break_service = PipelineBreakAnalysisService(self.db)
        breaks_analysis = break_service.analyze_pipeline_breaks(start_date, end_date)

        stage_accountability = {}

        for stage, break_data in breaks_analysis['breaks'].items():
            break_records = break_data.get('break_records', [])

            # 统计责任人
            person_stats = defaultdict(lambda: {'count': 0, 'cost_impact': Decimal('0')})
            department_stats = defaultdict(lambda: {'count': 0, 'cost_impact': Decimal('0')})

            for record in break_records:
                person_id = record.get('responsible_person_id')
                if person_id:
                    person_stats[person_id]['count'] += 1
                    # 计算成本影响（简化处理）
                    cost_impact = self._calculate_break_cost_impact(stage, record)
                    person_stats[person_id]['cost_impact'] += cost_impact

                    # 获取部门信息
                    person = self.db.query(User).filter(User.id == person_id).first()
                    if person:
                        dept_name = person.department or '未知部门'
                        department_stats[dept_name]['count'] += 1
                        department_stats[dept_name]['cost_impact'] += cost_impact

            # 转换为列表格式
            person_list = []
            for person_id, stats in person_stats.items():
                person = self.db.query(User).filter(User.id == person_id).first()
                person_list.append({
                    'person_id': person_id,
                    'person_name': person.real_name if person and person.real_name else (person.username if person else f'User_{person_id}'),
                    'department': person.department if person else None,
                    'break_count': stats['count'],
                    'cost_impact': float(stats['cost_impact'])
                })
            person_list.sort(key=lambda x: x['cost_impact'], reverse=True)

            department_list = [
                {
                    'department': dept,
                    'break_count': stats['count'],
                    'cost_impact': float(stats['cost_impact'])
                }
                for dept, stats in department_stats.items()
            ]
            department_list.sort(key=lambda x: x['cost_impact'], reverse=True)

            stage_accountability[stage] = {
                'total_breaks': break_data.get('break_count', 0),
                'by_person': person_list[:20],  # Top 20
                'by_department': department_list
            }

        return {
            'analysis_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'by_stage': stage_accountability
        }

    def analyze_by_person(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """按人员归责分析"""
        from app.services.pipeline_break_analysis_service import (
            PipelineBreakAnalysisService,
        )
        break_service = PipelineBreakAnalysisService(self.db)
        breaks_analysis = break_service.analyze_pipeline_breaks(start_date, end_date)

        person_stats = defaultdict(lambda: {
            'total_breaks': 0,
            'cost_impact': Decimal('0'),
            'opportunity_cost': Decimal('0'),
            'stages': defaultdict(int)
        })

        # 汇总所有环节的断链
        for stage, break_data in breaks_analysis['breaks'].items():
            break_records = break_data.get('break_records', [])
            for record in break_records:
                person_id = record.get('responsible_person_id')
                if person_id:
                    person_stats[person_id]['total_breaks'] += 1
                    person_stats[person_id]['stages'][stage] += 1

                    cost_impact = self._calculate_break_cost_impact(stage, record)
                    person_stats[person_id]['cost_impact'] += cost_impact

        # 转换为列表格式
        person_list = []
        for person_id, stats in person_stats.items():
            person = self.db.query(User).filter(User.id == person_id).first()
            person_list.append({
                'person_id': person_id,
                'person_name': person.real_name if person and person.real_name else (person.username if person else f'User_{person_id}'),
                'department': person.department if person else None,
                'total_breaks': stats['total_breaks'],
                'cost_impact': float(stats['cost_impact']),
                'opportunity_cost': float(stats['opportunity_cost']),
                'stages': dict(stats['stages'])
            })

        person_list.sort(key=lambda x: x['cost_impact'], reverse=True)

        return {
            'analysis_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'by_person': person_list,
            'summary': {
                'total_people': len(person_list),
                'total_breaks': sum(p['total_breaks'] for p in person_list),
                'total_cost_impact': sum(p['cost_impact'] for p in person_list)
            }
        }

    def analyze_by_department(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """按部门归责分析"""
        person_analysis = self.analyze_by_person(start_date, end_date)
        person_list = person_analysis.get('by_person', [])

        department_stats = defaultdict(lambda: {
            'total_breaks': 0,
            'cost_impact': Decimal('0'),
            'person_count': 0,
            'people': []
        })

        for person_data in person_list:
            dept = person_data.get('department') or '未知部门'
            department_stats[dept]['total_breaks'] += person_data['total_breaks']
            department_stats[dept]['cost_impact'] += Decimal(str(person_data['cost_impact']))
            department_stats[dept]['person_count'] += 1
            department_stats[dept]['people'].append({
                'person_id': person_data['person_id'],
                'person_name': person_data['person_name'],
                'break_count': person_data['total_breaks']
            })

        department_list = [
            {
                'department': dept,
                'total_breaks': stats['total_breaks'],
                'cost_impact': float(stats['cost_impact']),
                'person_count': stats['person_count'],
                'people': stats['people'][:10]  # Top 10
            }
            for dept, stats in department_stats.items()
        ]
        department_list.sort(key=lambda x: x['cost_impact'], reverse=True)

        return {
            'analysis_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'by_department': department_list,
            'summary': {
                'total_departments': len(department_list),
                'total_breaks': sum(d['total_breaks'] for d in department_list),
                'total_cost_impact': sum(d['cost_impact'] for d in department_list)
            }
        }

    def analyze_cost_impact(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """责任成本分析"""
        from app.services.pipeline_break_analysis_service import (
            PipelineBreakAnalysisService,
        )
        break_service = PipelineBreakAnalysisService(self.db)
        breaks_analysis = break_service.analyze_pipeline_breaks(start_date, end_date)

        total_cost_impact = Decimal('0')
        total_opportunity_cost = Decimal('0')
        cost_by_stage = defaultdict(lambda: Decimal('0'))
        cost_by_person = defaultdict(lambda: Decimal('0'))

        for stage, break_data in breaks_analysis['breaks'].items():
            break_records = break_data.get('break_records', [])
            for record in break_records:
                cost_impact = self._calculate_break_cost_impact(stage, record)
                total_cost_impact += cost_impact
                cost_by_stage[stage] += cost_impact

                person_id = record.get('responsible_person_id')
                if person_id:
                    cost_by_person[person_id] += cost_impact

        return {
            'analysis_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'summary': {
                'total_cost_impact': float(total_cost_impact),
                'total_opportunity_cost': float(total_opportunity_cost),
                'total_loss': float(total_cost_impact + total_opportunity_cost)
            },
            'by_stage': {
                stage: float(cost) for stage, cost in cost_by_stage.items()
            },
            'by_person': {
                person_id: float(cost) for person_id, cost in list(cost_by_person.items())[:20]
            }
        }

    def _calculate_break_cost_impact(
        self,
        stage: str,
        record: Dict[str, Any]
    ) -> Decimal:
        """计算断链造成的成本影响"""
        cost = Decimal('0')

        # 工时成本（如果有投入工时）
        if stage in ['LEAD_TO_OPP', 'OPP_TO_QUOTE']:
            # 对于线索和商机，可以查询关联项目的工时
            pipeline_id = record.get('pipeline_id')
            if pipeline_id:
                if stage == 'LEAD_TO_OPP':
                    # 查询线索关联的项目工时
                    lead = self.db.query(Lead).filter(Lead.id == pipeline_id).first()
                    if lead and lead.opportunities:
                        for opp in lead.opportunities:
                            if opp.id:
                                projects = self.db.query(Project).filter(
                                    Project.opportunity_id == opp.id
                                ).all()
                                for project in projects:
                                    timesheets = self.db.query(Timesheet).filter(
                                        Timesheet.project_id == project.id
                                    ).all()
                                    for ts in timesheets:
                                        user = self.db.query(User).filter(User.id == ts.user_id).first()
                                        if user:
                                            hourly_rate = self.hourly_rate_service.get_user_hourly_rate(
                                                self.db, user.id, ts.work_date
                                            )
                                            cost += Decimal(str(ts.hours or 0)) * hourly_rate

        # 机会成本（丢失的合同金额）
        if stage in ['QUOTE_TO_CONTRACT', 'CONTRACT_TO_PROJECT']:
            # 简化处理：使用预估金额作为机会成本
            pipeline_id = record.get('pipeline_id')
            if stage == 'QUOTE_TO_CONTRACT' and pipeline_id:
                quote = self.db.query(Quote).filter(Quote.id == pipeline_id).first()
                if quote and quote.total_amount:
                    cost += Decimal(str(quote.total_amount)) * Decimal('0.1')  # 假设10%的机会成本

        return cost
