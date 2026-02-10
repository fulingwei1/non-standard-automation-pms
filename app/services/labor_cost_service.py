# -*- coding: utf-8 -*-
"""
工时成本统一服务

包含三大功能：
1. LaborCostService - 工时成本自动计算（从工时记录计算项目人工成本）
2. LaborCostCalculationService - 批量月度成本计算（定时任务用）
3. LaborCostExpenseService - 未中标项目工时费用化处理
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.common.date_range import get_month_range_by_ym
from app.models.enums import LeadOutcomeEnum
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User

logger = logging.getLogger(__name__)


class LaborCostService:
    """工时成本自动计算服务"""

    # 默认时薪配置（可以后续从用户配置或系统配置中读取）
    DEFAULT_HOURLY_RATE = Decimal("100")  # 默认100元/小时

    def __init__(self, db: Session):
        """初始化工时成本服务

        Args:
            db: 数据库会话
        """
        self.db = db

    @staticmethod
    def get_user_hourly_rate(db: Session, user_id: int, work_date: Optional[date] = None) -> Decimal:
        """
        获取用户时薪（从时薪配置服务读取）

        Args:
            db: 数据库会话
            user_id: 用户ID
            work_date: 工作日期（可选）

        Returns:
            时薪（元/小时）
        """
        from app.services.hourly_rate_service import HourlyRateService
        return HourlyRateService.get_user_hourly_rate(db, user_id, work_date)

    @staticmethod
    def calculate_project_labor_cost(
        db: Session,
        project_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        recalculate: bool = False
    ) -> Dict:
        """
        计算项目人工成本

        Args:
            db: 数据库会话
            project_id: 项目ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            recalculate: 是否重新计算（如果为True，会删除现有记录重新计算）

        Returns:
            计算结果字典，包含创建的成本记录数量、总成本等
        """
        from app.services.labor_cost.utils import (
            delete_existing_costs,
            group_timesheets_by_user,
            process_user_costs,
            query_approved_timesheets,
        )

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {
                "success": False,
                "message": "项目不存在"
            }

        # 查询已审批的工时记录
        timesheets = query_approved_timesheets(db, project_id, start_date, end_date)

        if not timesheets:
            return {
                "success": True,
                "message": "没有已审批的工时记录",
                "cost_count": 0,
                "total_cost": 0
            }

        # 如果重新计算，删除现有的工时成本记录
        if recalculate:
            delete_existing_costs(db, project, project_id)

        # 按用户分组工时记录
        user_costs = group_timesheets_by_user(timesheets)

        # 处理用户成本
        created_costs, total_cost = process_user_costs(
            db, project, project_id, user_costs, end_date, recalculate
        )

        db.add(project)
        db.commit()

        return {
            "success": True,
            "message": f"成功计算{len(created_costs)}条人工成本记录",
            "cost_count": len(created_costs),
            "total_cost": float(total_cost),
            "total_hours": float(sum([user_data["total_hours"] for user_data in user_costs.values()])),
            "user_count": len(user_costs)
        }

    @staticmethod
    def calculate_all_projects_labor_cost(
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        project_ids: Optional[List[int]] = None
    ) -> Dict:
        """
        批量计算所有项目的人工成本

        Args:
            db: 数据库会话
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            project_ids: 项目ID列表（可选，不提供则计算所有项目）

        Returns:
            批量计算结果
        """
        # 查询有工时记录的项目
        query = db.query(Timesheet.project_id).filter(
            Timesheet.status == "APPROVED"
        ).distinct()

        if start_date:
            query = query.filter(Timesheet.work_date >= start_date)
        if end_date:
            query = query.filter(Timesheet.work_date <= end_date)

        if project_ids:
            query = query.filter(Timesheet.project_id.in_(project_ids))

        project_ids_with_timesheets = [row[0] for row in query.all()]

        results = []
        success_count = 0
        fail_count = 0

        for project_id in project_ids_with_timesheets:
            try:
                result = LaborCostService.calculate_project_labor_cost(
                    db, project_id, start_date, end_date, recalculate=True
                )
                results.append({
                    "project_id": project_id,
                    **result
                })
                if result.get("success"):
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                results.append({
                    "project_id": project_id,
                    "success": False,
                    "message": str(e)
                })
                fail_count += 1

        return {
            "success": True,
            "message": f"批量计算完成：成功{success_count}个，失败{fail_count}个",
            "total_projects": len(project_ids_with_timesheets),
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results
        }

    @staticmethod
    def calculate_monthly_labor_cost(
        db: Session,
        year: int,
        month: int,
        project_ids: Optional[List[int]] = None
    ) -> Dict:
        """
        计算指定月份的项目人工成本

        Args:
            db: 数据库会话
            year: 年份
            month: 月份
            project_ids: 项目ID列表（可选）

        Returns:
            月度计算结果
        """
        # 使用公共日期范围工具计算月份边界
        start_date, end_date = get_month_range_by_ym(year, month)

        return LaborCostService.calculate_all_projects_labor_cost(
            db, start_date, end_date, project_ids
        )


class LaborCostCalculationService:
    """
    人工成本批量计算服务
    用于定时任务批量计算所有项目的人工成本
    """

    def __init__(self, db: Session):
        self.db = db

    def calculate_monthly_costs(self, year: int, month: int) -> Dict:
        """
        计算指定月份所有项目的人工成本

        Args:
            year: 年份
            month: 月份

        Returns:
            Dict: 计算结果统计
        """
        from app.services.labor_cost.utils import (
            group_timesheets_by_user,
            process_user_costs,
            query_approved_timesheets,
        )

        # 使用公共日期范围工具计算月份边界
        start_date, end_date = get_month_range_by_ym(year, month)

        # 查询有工时记录的项目
        project_ids = self.db.query(Timesheet.project_id).filter(
            Timesheet.work_date >= start_date,
            Timesheet.work_date <= end_date,
            Timesheet.status == "APPROVED"
        ).distinct().all()

        projects_processed = 0
        total_cost = Decimal("0")
        errors = []

        for (project_id,) in project_ids:
            if not project_id:
                continue

            try:
                project = self.db.query(Project).filter(Project.id == project_id).first()
                if not project:
                    continue

                # 查询该项目的工时
                timesheets = query_approved_timesheets(self.db, project_id, start_date, end_date)
                if not timesheets:
                    continue

                # 按用户分组
                user_costs = group_timesheets_by_user(timesheets)

                # 处理用户成本
                _, project_cost = process_user_costs(
                    self.db, project, project_id, user_costs, end_date, recalculate=False
                )

                total_cost += project_cost
                projects_processed += 1

            except Exception as e:
                errors.append({"project_id": project_id, "error": str(e)})
                logger.error(f"计算项目 {project_id} 人工成本失败: {str(e)}")

        self.db.commit()

        return {
            "year": year,
            "month": month,
            "projects_processed": projects_processed,
            "total_cost": float(total_cost),
            "errors": errors
        }


class PresaleExpense:
    """售前费用模型（临时，后续会创建ORM模型）"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class LaborCostExpenseService:
    """工时费用化处理服务

    自动识别未中标项目，将投入工时转为费用，进行成本核算
    """

    def __init__(self, db: Session):
        self.db = db
        from app.services.hourly_rate_service import HourlyRateService
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

            # 按人员分组计算费用（不可变模式，使用 dict.get 累加）
            person_expenses: Dict[int, Dict[str, Any]] = {}

            for ts in timesheets:
                user = self.db.query(User).filter(User.id == ts.user_id).first()
                if user:
                    hourly_rate = self.hourly_rate_service.get_user_hourly_rate(self.db, user.id, ts.work_date)
                    hours = float(ts.hours or 0)
                    cost = Decimal(str(hours)) * hourly_rate
                    prev = person_expenses.get(ts.user_id, {'hours': 0.0, 'cost': Decimal('0')})
                    person_expenses[ts.user_id] = {
                        'hours': prev['hours'] + hours,
                        'cost': prev['cost'] + cost,
                    }

            # 创建费用记录
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
        group_by: str = 'person'
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
            result = self._statistics_by_person(expenses)
        elif group_by == 'department':
            result = self._statistics_by_department(expenses)
        else:
            result = self._statistics_by_time(expenses)

        return {
            'group_by': group_by,
            'statistics': result,
            'summary': {
                'total_amount': expenses_data['total_amount'],
                'total_hours': expenses_data['total_hours'],
                'total_projects': expenses_data['total_expenses']
            }
        }

    def _statistics_by_person(self, expenses: List[Dict]) -> List[Dict]:
        """按人员统计费用（使用不可变累加模式）"""
        person_stats: Dict[int, Dict[str, Any]] = {}
        for exp in expenses:
            person_id = exp['salesperson_id']
            if person_id:
                prev = person_stats.get(person_id, {'amount': 0.0, 'hours': 0.0, 'count': 0})
                person_stats[person_id] = {
                    'amount': prev['amount'] + exp['amount'],
                    'hours': prev['hours'] + exp['labor_hours'],
                    'count': prev['count'] + 1,
                }

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
        return result

    def _statistics_by_department(self, expenses: List[Dict]) -> List[Dict]:
        """按部门统计费用（使用不可变累加模式）"""
        from app.models.organization import Department

        dept_stats: Dict[int, Dict[str, Any]] = {}
        for exp in expenses:
            project_id = exp['project_id']
            # 从项目的工时记录中获取部门信息
            timesheets = self.db.query(Timesheet).filter(
                Timesheet.project_id == project_id
            ).all()
            for ts in timesheets:
                if ts.department_id:
                    share = exp['amount'] / len(timesheets) if timesheets else exp['amount']
                    prev = dept_stats.get(ts.department_id, {'amount': 0.0, 'hours': 0.0, 'count': 0})
                    dept_stats[ts.department_id] = {
                        'amount': prev['amount'] + share,
                        'hours': prev['hours'] + float(ts.hours or 0),
                        'count': 1, # 每个项目只计数一次
                    }

        result = []
        for dept_id, stats in dept_stats.items():
            dept = self.db.query(Department).filter(Department.id == dept_id).first()
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
        return result

    def _statistics_by_time(self, expenses: List[Dict]) -> List[Dict]:
        """按时间统计费用（使用不可变累加模式）"""
        time_stats: Dict[str, Dict[str, Any]] = {}
        for exp in expenses:
            expense_date = exp['expense_date']
            month_key = expense_date.strftime('%Y-%m')
            prev = time_stats.get(month_key, {'amount': 0.0, 'hours': 0.0, 'count': 0})
            time_stats[month_key] = {
                'amount': prev['amount'] + exp['amount'],
                'hours': prev['hours'] + exp['labor_hours'],
                'count': prev['count'] + 1,
            }

        return [
            {
                'month': month,
                'total_amount': round(stats['amount'], 2),
                'total_hours': round(stats['hours'], 1),
                'project_count': stats['count']
            }
            for month, stats in sorted(time_stats.items())
        ]

    def _has_detailed_design(self, project: Project) -> bool:
        """判断项目是否投入了详细设计"""
        # 通过项目阶段判断
        if project.stage:
            stage_order = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9']
            try:
                current_index = stage_order.index(project.stage)
                if current_index >= 3: # S4及以后
                    return True
            except ValueError:
                pass

        # 通过工时判断（如果工时超过80小时，通常已进入详细设计）
        hours = self._get_project_hours(project.id)
        return hours > 80

    def _get_project_hours(self, project_id: int) -> float:
        """获取项目总工时"""
        timesheet_hours = self.db.query(func.sum(Timesheet.hours)).filter(
            Timesheet.project_id == project_id
        ).scalar() or 0
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

