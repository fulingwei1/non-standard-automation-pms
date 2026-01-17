# -*- coding: utf-8 -*-
"""
工时费用化处理服务

自动识别未中标项目，将投入工时转为费用，进行成本核算
"""

import logging
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.enums import LeadOutcomeEnum
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User
from app.models.work_log import WorkLog
from app.services.hourly_rate_service import HourlyRateService

logger = logging.getLogger(__name__)


class PresaleExpense:
    """售前费用模型（临时，后续会创建ORM模型）"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class LaborCostExpenseService:
    """工时费用化处理服务"""

    def __init__(self, db: Session):
        self.db = db
        self.hourly_rate_service = HourlyRateService()

    def identify_lost_projects(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_abandoned: bool = True
    ) -> List[Dict[str, Any]]:
        """识别未中标项目

        Args:
            start_date: 开始日期
            end_date: 结束日期
            include_abandoned: 是否包含放弃的项目

        Returns:
            未中标项目列表
        """
        outcomes = [LeadOutcomeEnum.LOST.value]
        if include_abandoned:
            outcomes.append(LeadOutcomeEnum.ABANDONED.value)

        query = self.db.query(Project).filter(
            Project.outcome.in_(outcomes)
        )

        if start_date:
            query = query.filter(Project.created_at >= start_date)
        if end_date:
            query = query.filter(Project.created_at <= end_date)

        projects = query.all()

        result = []
        for project in projects:
            # 判断是否投入了详细设计
            has_detailed_design = self._has_detailed_design(project)

            # 获取工时统计
            hours = self._get_project_hours(project.id)
            cost = self._calculate_project_cost(project.id)

            result.append({
                'project_id': project.id,
                'project_code': project.project_code,
                'project_name': project.project_name,
                'outcome': project.outcome,
                'loss_reason': project.loss_reason,
                'has_detailed_design': has_detailed_design,
                'total_hours': hours,
                'total_cost': float(cost),
                'salesperson_id': project.salesperson_id,
                'source_lead_id': project.source_lead_id,
                'opportunity_id': project.opportunity_id
            })

        return result

    def expense_lost_projects(
        self,
        project_ids: Optional[List[int]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        created_by: int = None
    ) -> Dict[str, Any]:
        """将未中标项目工时费用化

        Args:
            project_ids: 项目ID列表（如果指定，只处理这些项目）
            start_date: 开始日期
            end_date: 结束日期
            created_by: 创建人ID

        Returns:
            费用化处理结果
        """
        # 识别未中标项目
        if project_ids:
            projects = self.db.query(Project).filter(
                Project.id.in_(project_ids),
                Project.outcome.in_([LeadOutcomeEnum.LOST.value, LeadOutcomeEnum.ABANDONED.value])
            ).all()
        else:
            outcomes = [LeadOutcomeEnum.LOST.value, LeadOutcomeEnum.ABANDONED.value]
            query = self.db.query(Project).filter(Project.outcome.in_(outcomes))
            if start_date:
                query = query.filter(Project.created_at >= start_date)
            if end_date:
                query = query.filter(Project.created_at <= end_date)
            projects = query.all()

        expenses = []
        total_amount = Decimal('0')
        total_hours = 0.0

        for project in projects:
            # 获取工时记录
            timesheets = self.db.query(Timesheet).filter(
                Timesheet.project_id == project.id
            ).all()

            # WorkLog通过mentions关联项目，这里简化处理，只使用Timesheet

            # 按人员分组计算费用
            person_expenses = defaultdict(lambda: {'hours': 0.0, 'cost': Decimal('0')})

            for ts in timesheets:
                user = self.db.query(User).filter(User.id == ts.user_id).first()
                if user:
                    hourly_rate = self.hourly_rate_service.get_user_hourly_rate(self.db, user.id, ts.work_date)
                    hours = float(ts.hours or 0)
                    cost = Decimal(str(hours)) * hourly_rate
                    person_expenses[ts.user_id]['hours'] += hours
                    person_expenses[ts.user_id]['cost'] += cost

            # 创建费用记录（这里先返回数据，后续会写入数据库）
            for user_id, stats in person_expenses.items():
                user = self.db.query(User).filter(User.id == user_id).first()
                # 从Timesheet获取部门信息
                user_ts = next((ts for ts in timesheets if ts.user_id == user_id), None)
                department_id = user_ts.department_id if user_ts else None
                department_name = user_ts.department_name if user_ts else (user.department if user else None)

                expense = {
                    'project_id': project.id,
                    'project_code': project.project_code,
                    'project_name': project.project_name,
                    'lead_id': self._get_lead_id_from_project(project),
                    'opportunity_id': project.opportunity_id,
                    'expense_type': 'LABOR_COST',
                    'expense_category': 'LOST_BID' if project.outcome == LeadOutcomeEnum.LOST.value else 'ABANDONED',
                    'amount': float(stats['cost']),
                    'labor_hours': stats['hours'],
                    'hourly_rate': float(self.hourly_rate_service.get_user_hourly_rate(self.db, user_id)),
                    'expense_date': project.updated_at.date() if project.updated_at else date.today(),
                    'description': f'未中标项目工时费用：{project.project_name}',
                    'user_id': user_id,
                    'user_name': user.real_name if user else f'User_{user_id}',
                    'department_id': department_id,
                    'department_name': department_name,
                    'salesperson_id': project.salesperson_id,
                    'salesperson_name': self._get_user_name(project.salesperson_id),
                    'loss_reason': project.loss_reason,
                    'created_by': created_by
                }
                expenses.append(expense)
                total_amount += stats['cost']
                total_hours += stats['hours']

        return {
            'total_projects': len(projects),
            'total_expenses': len(expenses),
            'total_amount': float(total_amount),
            'total_hours': round(total_hours, 1),
            'expenses': expenses
        }

    def get_lost_project_expenses(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        salesperson_id: Optional[int] = None,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取未中标项目费用列表

        注意：此方法返回的是计算出的费用，实际费用记录需要先调用expense_lost_projects写入数据库
        """
        # 识别未中标项目
        outcomes = [LeadOutcomeEnum.LOST.value, LeadOutcomeEnum.ABANDONED.value]
        query = self.db.query(Project).filter(Project.outcome.in_(outcomes))

        if start_date:
            query = query.filter(Project.created_at >= start_date)
        if end_date:
            query = query.filter(Project.created_at <= end_date)
        if salesperson_id:
            query = query.filter(Project.salesperson_id == salesperson_id)
        if department_id:
            query = query.join(User).filter(User.department_id == department_id)

        projects = query.all()

        expenses = []
        for project in projects:
            hours = self._get_project_hours(project.id)
            cost = self._calculate_project_cost(project.id)

            expenses.append({
                'project_id': project.id,
                'project_code': project.project_code,
                'project_name': project.project_name,
                'expense_category': 'LOST_BID' if project.outcome == LeadOutcomeEnum.LOST.value else 'ABANDONED',
                'labor_hours': hours,
                'amount': float(cost),
                'expense_date': project.updated_at.date() if project.updated_at else project.created_at.date() if project.created_at else date.today(),
                'salesperson_id': project.salesperson_id,
                'salesperson_name': self._get_user_name(project.salesperson_id),
                'loss_reason': project.loss_reason
            })

        return {
            'total_expenses': len(expenses),
            'total_amount': sum(e['amount'] for e in expenses),
            'total_hours': sum(e['labor_hours'] for e in expenses),
            'expenses': expenses
        }

    def get_expense_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        group_by: str = 'person'  # person/department/time
    ) -> Dict[str, Any]:
        """获取费用统计

        Args:
            start_date: 开始日期
            end_date: 结束日期
            group_by: 分组方式：person/department/time

        Returns:
            费用统计数据
        """
        # 获取未中标项目费用
        expenses_data = self.get_lost_project_expenses(start_date, end_date)
        expenses = expenses_data['expenses']

        if group_by == 'person':
            # 按人员统计
            person_stats = defaultdict(lambda: {'amount': 0.0, 'hours': 0.0, 'count': 0})
            for exp in expenses:
                person_id = exp['salesperson_id']
                if person_id:
                    person_stats[person_id]['amount'] += exp['amount']
                    person_stats[person_id]['hours'] += exp['labor_hours']
                    person_stats[person_id]['count'] += 1

            result = []
            for person_id, stats in person_stats.items():
                person = self.db.query(User).filter(User.id == person_id).first()
                result.append({
                    'person_id': person_id,
                    'person_name': person.name if person else f'User_{person_id}',
                    'department': person.department_name if person else None,
                    'total_amount': round(stats['amount'], 2),
                    'total_hours': round(stats['hours'], 1),
                    'project_count': stats['count']
                })
            result.sort(key=lambda x: x['total_amount'], reverse=True)

        elif group_by == 'department':
            # 按部门统计（从Timesheet获取部门信息）
            from app.models.organization import Department
            dept_stats = defaultdict(lambda: {'amount': 0.0, 'hours': 0.0, 'count': 0})
            for exp in expenses:
                project_id = exp['project_id']
                # 从项目的工时记录中获取部门信息
                timesheets = self.db.query(Timesheet).filter(
                    Timesheet.project_id == project_id
                ).all()
                for ts in timesheets:
                    if ts.department_id:
                        dept_stats[ts.department_id]['amount'] += exp['amount'] / len(timesheets) if timesheets else exp['amount']
                        dept_stats[ts.department_id]['hours'] += float(ts.hours or 0)
                        dept_stats[ts.department_id]['count'] = 1  # 每个项目只计数一次

            result = []
            for dept_id, stats in dept_stats.items():
                dept = self.db.query(Department).filter(Department.id == dept_id).first()
                # 如果没有找到部门，尝试从Timesheet获取部门名称
                dept_name = dept.dept_name if dept else None
                if not dept_name:
                    ts = self.db.query(Timesheet).filter(Timesheet.department_id == dept_id).first()
                    dept_name = ts.department_name if ts and ts.department_name else f'Dept_{dept_id}'

                result.append({
                    'department_id': dept_id,
                    'department_name': dept_name,
                    'total_amount': round(stats['amount'], 2),
                    'total_hours': round(stats['hours'], 1),
                    'project_count': stats['count']
                })
            result.sort(key=lambda x: x['total_amount'], reverse=True)

        else:  # time
            # 按时间统计（按月）
            time_stats = defaultdict(lambda: {'amount': 0.0, 'hours': 0.0, 'count': 0})
            for exp in expenses:
                expense_date = exp['expense_date']
                month_key = expense_date.strftime('%Y-%m')
                time_stats[month_key]['amount'] += exp['amount']
                time_stats[month_key]['hours'] += exp['labor_hours']
                time_stats[month_key]['count'] += 1

            result = [
                {
                    'month': month,
                    'total_amount': round(stats['amount'], 2),
                    'total_hours': round(stats['hours'], 1),
                    'project_count': stats['count']
                }
                for month, stats in sorted(time_stats.items())
            ]

        return {
            'group_by': group_by,
            'statistics': result,
            'summary': {
                'total_amount': expenses_data['total_amount'],
                'total_hours': expenses_data['total_hours'],
                'total_projects': expenses_data['total_expenses']
            }
        }

    def _has_detailed_design(self, project: Project) -> bool:
        """判断项目是否投入了详细设计"""
        # 通过项目阶段判断
        if project.stage:
            stage_order = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9']
            try:
                current_index = stage_order.index(project.stage)
                if current_index >= 3:  # S4及以后
                    return True
            except ValueError:
                pass

        # 通过工时判断（如果工时超过80小时，通常已进入详细设计）
        hours = self._get_project_hours(project.id)
        return hours > 80

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
        timesheets = self.db.query(Timesheet).filter(
            Timesheet.project_id == project_id
        ).all()

        total_cost = Decimal('0')
        for ts in timesheets:
            user = self.db.query(User).filter(User.id == ts.user_id).first()
            if user:
                hourly_rate = self.hourly_rate_service.get_user_hourly_rate(self.db, user.id, ts.work_date)
                total_cost += Decimal(str(ts.hours or 0)) * hourly_rate
            else:
                total_cost += Decimal(str(ts.hours or 0)) * Decimal('300')

        return total_cost

    def _get_lead_id_from_project(self, project: Project) -> Optional[int]:
        """从项目获取线索ID"""
        if project.source_lead_id:
            # source_lead_id是字符串，需要查询leads表
            from app.models.sales import Lead
            lead = self.db.query(Lead).filter(Lead.lead_code == project.source_lead_id).first()
            return lead.id if lead else None
        return None

    def _get_user_name(self, user_id: Optional[int]) -> Optional[str]:
        """获取用户名称"""
        if user_id:
            user = self.db.query(User).filter(User.id == user_id).first()
            return user.real_name if user and user.real_name else (user.username if user else None)
        return None
