# -*- coding: utf-8 -*-
"""
未中标深度原因分析服务

分析投入了详细设计但未中标的原因，识别投入阶段、未中标原因、投入产出和模式
"""

import logging
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.enums import LeadOutcomeEnum, LossReasonEnum
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User
from app.services.hourly_rate_service import HourlyRateService

logger = logging.getLogger(__name__)


class LossDeepAnalysisService:
    """未中标深度原因分析服务"""

    # 项目阶段定义（用于判断投入阶段）
    STAGE_REQUIREMENT = 'S1'  # 需求进入
    STAGE_DESIGN = 'S2'  # 方案设计
    STAGE_DETAILED_DESIGN = 'S4'  # 加工制造（通常详细设计在S4之前完成）

    def __init__(self, db: Session):
        self.db = db
        self.hourly_rate_service = HourlyRateService()

    def analyze_lost_projects(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        salesperson_id: Optional[int] = None,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """分析未中标项目

        Args:
            start_date: 开始日期
            end_date: 结束日期
            salesperson_id: 销售人员ID
            department_id: 部门ID

        Returns:
            包含投入阶段分析、未中标原因分析、投入产出分析、模式识别的字典
        """
        # 查询未中标项目
        query = self.db.query(Project).filter(
            Project.outcome.in_([LeadOutcomeEnum.LOST.value, LeadOutcomeEnum.ABANDONED.value])
        )

        if start_date:
            query = query.filter(Project.created_at >= start_date)
        if end_date:
            query = query.filter(Project.created_at <= end_date)
        if salesperson_id:
            query = query.filter(Project.salesperson_id == salesperson_id)
        if department_id:
            query = query.join(User).filter(User.department_id == department_id)

        lost_projects = query.all()

        # 1. 投入阶段分析
        stage_analysis = self._analyze_investment_stage(lost_projects)

        # 2. 未中标原因分析
        reason_analysis = self._analyze_loss_reasons(lost_projects)

        # 3. 投入产出分析
        investment_analysis = self._analyze_investment_output(lost_projects)

        # 4. 模式识别
        pattern_analysis = self._identify_patterns(lost_projects)

        return {
            'total_lost_projects': len(lost_projects),
            'analysis_period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'stage_analysis': stage_analysis,
            'reason_analysis': reason_analysis,
            'investment_analysis': investment_analysis,
            'pattern_analysis': pattern_analysis
        }

    def _analyze_investment_stage(self, projects: List[Project]) -> Dict[str, Any]:
        """分析投入阶段"""
        stage_stats = {
            'requirement_only': 0,  # 仅需求调研
            'design': 0,  # 方案设计
            'detailed_design': 0,  # 详细设计（重点）
            'quotation': 0,  # 报价阶段
            'unknown': 0
        }

        stage_details = []

        for project in projects:
            # 判断投入阶段
            stage = self._determine_investment_stage(project)
            stage_stats[stage] += 1

            # 获取工时统计
            hours = self._get_project_hours(project.id)
            cost = self._calculate_project_cost(project.id)

            stage_details.append({
                'project_id': project.id,
                'project_code': project.project_code,
                'project_name': project.project_name,
                'stage': stage,
                'total_hours': hours,
                'total_cost': float(cost),
                'loss_reason': project.loss_reason,
                'loss_reason_detail': project.loss_reason_detail
            })

        return {
            'statistics': stage_stats,
            'details': stage_details,
            'summary': {
                'detailed_design_count': stage_stats['detailed_design'],
                'detailed_design_percentage': round(
                    stage_stats['detailed_design'] / len(projects) * 100, 2
                ) if projects else 0
            }
        }

    def _determine_investment_stage(self, project: Project) -> str:
        """判断项目投入到了哪个阶段"""
        # 检查项目阶段
        if project.stage:
            # 如果项目阶段在S4（加工制造）或之后，说明已完成详细设计
            stage_order = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9']
            try:
                current_index = stage_order.index(project.stage)
                if current_index >= 3:  # S4及以后
                    return 'detailed_design'
                elif current_index >= 1:  # S2-S3
                    return 'design'
                else:  # S1
                    return 'requirement_only'
            except ValueError:
                pass

        # 通过工时记录判断（如果有详细设计相关的工时）
        hours = self._get_project_hours(project.id)
        if hours > 80:  # 如果工时超过80小时，通常已进入详细设计
            return 'detailed_design'
        elif hours > 40:  # 如果工时超过40小时，通常已进入方案设计
            return 'design'
        elif hours > 0:
            return 'requirement_only'

        return 'unknown'

    def _analyze_loss_reasons(self, projects: List[Project]) -> Dict[str, Any]:
        """分析未中标原因"""
        reason_stats = defaultdict(int)
        reason_details = defaultdict(list)

        for project in projects:
            reason = project.loss_reason or LossReasonEnum.OTHER.value
            reason_stats[reason] += 1

            hours = self._get_project_hours(project.id)
            cost = self._calculate_project_cost(project.id)

            reason_details[reason].append({
                'project_id': project.id,
                'project_code': project.project_code,
                'hours': hours,
                'cost': float(cost),
                'detail': project.loss_reason_detail
            })

        # 按数量排序
        sorted_reasons = sorted(reason_stats.items(), key=lambda x: x[1], reverse=True)

        return {
            'statistics': dict(reason_stats),
            'top_reasons': [
                {
                    'reason': reason,
                    'count': count,
                    'percentage': round(count / len(projects) * 100, 2) if projects else 0,
                    'total_hours': sum(d['hours'] for d in reason_details[reason]),
                    'total_cost': sum(d['cost'] for d in reason_details[reason])
                }
                for reason, count in sorted_reasons[:10]
            ],
            'details': dict(reason_details)
        }

    def _analyze_investment_output(self, projects: List[Project]) -> Dict[str, Any]:
        """分析投入产出"""
        total_hours = 0.0
        total_cost = Decimal('0')
        total_expected_revenue = Decimal('0')
        total_loss = Decimal('0')

        by_stage = defaultdict(lambda: {'hours': 0.0, 'cost': Decimal('0'), 'count': 0})
        by_person = defaultdict(lambda: {'hours': 0.0, 'cost': Decimal('0'), 'count': 0})
        by_department = defaultdict(lambda: {'hours': 0.0, 'cost': Decimal('0'), 'count': 0})

        for project in projects:
            hours = self._get_project_hours(project.id)
            cost = self._calculate_project_cost(project.id)
            expected_revenue = project.contract_amount or Decimal('0')

            total_hours += hours
            total_cost += cost
            total_expected_revenue += expected_revenue
            total_loss += cost  # 损失 = 投入成本

            # 按阶段统计
            stage = self._determine_investment_stage(project)
            by_stage[stage]['hours'] += hours
            by_stage[stage]['cost'] += cost
            by_stage[stage]['count'] += 1

            # 按人员统计
            if project.salesperson_id:
                by_person[project.salesperson_id]['hours'] += hours
                by_person[project.salesperson_id]['cost'] += cost
                by_person[project.salesperson_id]['count'] += 1

            # 按部门统计（从Timesheet获取部门信息）
            timesheets = self.db.query(Timesheet).filter(
                Timesheet.project_id == project.id
            ).all()
            for ts in timesheets:
                if ts.department_id:
                    by_department[ts.department_id]['hours'] += float(ts.hours or 0)
                    # 计算成本
                    user = self.db.query(User).filter(User.id == ts.user_id).first()
                    if user:
                        hourly_rate = self.hourly_rate_service.get_user_hourly_rate(self.db, user.id, ts.work_date)
                        cost = Decimal(str(ts.hours or 0)) * hourly_rate
                        by_department[ts.department_id]['cost'] += cost
                    by_department[ts.department_id]['count'] = 1  # 每个项目只计数一次

        # 获取人员详情
        person_details = []
        for person_id, stats in by_person.items():
            person = self.db.query(User).filter(User.id == person_id).first()
            person_details.append({
                'person_id': person_id,
                'person_name': person.real_name if person and person.real_name else (person.username if person else f'User_{person_id}'),
                'department': person.department if person else None,
                'hours': round(stats['hours'], 1),
                'cost': float(stats['cost']),
                'project_count': stats['count']
            })
        person_details.sort(key=lambda x: x['cost'], reverse=True)

        # 获取部门详情
        from app.models.organization import Department
        department_details = []
        for dept_id, stats in by_department.items():
            dept = self.db.query(Department).filter(Department.id == dept_id).first()
            # 如果没有找到部门，尝试从Timesheet获取部门名称
            dept_name = dept.dept_name if dept else None
            if not dept_name:
                ts = self.db.query(Timesheet).filter(Timesheet.department_id == dept_id).first()
                dept_name = ts.department_name if ts and ts.department_name else f'Dept_{dept_id}'

            department_details.append({
                'department_id': dept_id,
                'department_name': dept_name,
                'hours': round(stats['hours'], 1),
                'cost': float(stats['cost']),
                'project_count': stats['count']
            })
        department_details.sort(key=lambda x: x['cost'], reverse=True)

        return {
            'summary': {
                'total_projects': len(projects),
                'total_hours': round(total_hours, 1),
                'total_cost': float(total_cost),
                'total_expected_revenue': float(total_expected_revenue),
                'total_loss': float(total_loss),
                'average_hours_per_project': round(total_hours / len(projects), 1) if projects else 0,
                'average_cost_per_project': float(total_cost / len(projects)) if projects else 0
            },
            'by_stage': {
                stage: {
                    'hours': round(stats['hours'], 1),
                    'cost': float(stats['cost']),
                    'count': stats['count']
                }
                for stage, stats in by_stage.items()
            },
            'by_person': person_details[:20],  # Top 20
            'by_department': department_details
        }

    def _identify_patterns(self, projects: List[Project]) -> Dict[str, Any]:
        """识别未中标模式"""
        patterns = {
            'high_investment_low_win_rate': [],  # 高投入低中标率
            'detailed_design_loss_patterns': [],  # 详细设计后未中标模式
            'salesperson_patterns': [],  # 销售人员模式
            'customer_patterns': [],  # 客户模式
            'industry_patterns': []  # 行业模式
        }

        # 分析详细设计后未中标
        detailed_design_projects = [
            p for p in projects
            if self._determine_investment_stage(p) == 'detailed_design'
        ]

        if detailed_design_projects:
            # 统计详细设计后未中标的主要原因
            detailed_reasons = defaultdict(int)
            for p in detailed_design_projects:
                reason = p.loss_reason or LossReasonEnum.OTHER.value
                detailed_reasons[reason] += 1

            patterns['detailed_design_loss_patterns'] = [
                {
                    'reason': reason,
                    'count': count,
                    'percentage': round(count / len(detailed_design_projects) * 100, 2)
                }
                for reason, count in sorted(detailed_reasons.items(), key=lambda x: x[1], reverse=True)
            ]

        # 分析销售人员模式
        salesperson_stats = defaultdict(lambda: {'total': 0, 'lost': 0, 'hours': 0.0, 'cost': Decimal('0')})
        for project in projects:
            if project.salesperson_id:
                stats = salesperson_stats[project.salesperson_id]
                stats['total'] += 1
                stats['lost'] += 1
                stats['hours'] += self._get_project_hours(project.id)
                stats['cost'] += self._calculate_project_cost(project.id)

        # 找出高投入但未中标率高的销售人员
        for person_id, stats in salesperson_stats.items():
            if stats['cost'] > 50000:  # 投入超过5万
                person = self.db.query(User).filter(User.id == person_id).first()
                patterns['salesperson_patterns'].append({
                    'person_id': person_id,
                    'person_name': person.real_name if person and person.real_name else (person.username if person else f'User_{person_id}'),
                    'lost_count': stats['lost'],
                    'total_hours': round(stats['hours'], 1),
                    'total_cost': float(stats['cost'])
                })

        patterns['salesperson_patterns'].sort(key=lambda x: x['total_cost'], reverse=True)

        return patterns

    def _get_project_hours(self, project_id: int) -> float:
        """获取项目总工时"""
        # 从Timesheet表获取
        timesheet_hours = self.db.query(func.sum(Timesheet.hours)).filter(
            Timesheet.project_id == project_id
        ).scalar() or 0

        # WorkLog通过mentions关联项目，这里简化处理，只使用Timesheet
        return float(timesheet_hours)

    def _calculate_project_cost(self, project_id: int) -> Decimal:
        """计算项目成本"""
        self._get_project_hours(project_id)

        # 获取项目相关人员的工时记录，按角色计算成本
        timesheets = self.db.query(Timesheet).filter(
            Timesheet.project_id == project_id
        ).all()

        total_cost = Decimal('0')
        for ts in timesheets:
            # 获取用户角色和工时单价
            user = self.db.query(User).filter(User.id == ts.user_id).first()
            if user:
                hourly_rate = self.hourly_rate_service.get_user_hourly_rate(self.db, user.id, ts.work_date)
                total_cost += Decimal(str(ts.hours or 0)) * hourly_rate
            else:
                # 默认工时单价
                total_cost += Decimal(str(ts.hours or 0)) * Decimal('300')

        return total_cost

    def analyze_by_stage(
        self,
        stage: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """按投入阶段分析未中标情况"""
        projects = self.db.query(Project).filter(
            Project.outcome.in_([LeadOutcomeEnum.LOST.value, LeadOutcomeEnum.ABANDONED.value])
        ).all()

        if start_date:
            projects = [p for p in projects if p.created_at and p.created_at >= start_date]
        if end_date:
            projects = [p for p in projects if p.created_at and p.created_at <= end_date]

        # 筛选指定阶段的项目
        stage_projects = [
            p for p in projects
            if self._determine_investment_stage(p) == stage
        ]

        return {
            'stage': stage,
            'total_projects': len(stage_projects),
            'total_hours': sum(self._get_project_hours(p.id) for p in stage_projects),
            'total_cost': sum(self._calculate_project_cost(p.id) for p in stage_projects),
            'projects': [
                {
                    'project_id': p.id,
                    'project_code': p.project_code,
                    'project_name': p.project_name,
                    'hours': self._get_project_hours(p.id),
                    'cost': float(self._calculate_project_cost(p.id)),
                    'loss_reason': p.loss_reason
                }
                for p in stage_projects
            ]
        }
