# -*- coding: utf-8 -*-
"""
工时数据同步服务
负责将工时数据自动同步到财务、研发、项目和HR系统
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.project import FinancialProjectCost, Project, ProjectCost
from app.models.rd_project import RdCost, RdProject
from app.models.timesheet import Timesheet
from app.models.user import User
from app.services.hourly_rate_service import HourlyRateService
from app.services.labor_cost_service import LaborCostService


class TimesheetSyncService:
    """工时数据同步服务"""

    def __init__(self, db: Session):
        self.db = db

    def sync_to_finance(
        self,
        timesheet_id: Optional[int] = None,
        project_id: Optional[int] = None,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        同步到财务系统（生成FinancialProjectCost记录）

        Args:
            timesheet_id: 工时记录ID（可选，如果提供则只同步该记录）
            project_id: 项目ID（可选，如果提供则只同步该项目）
            year: 年份（可选，用于批量同步）
            month: 月份（可选，用于批量同步）

        Returns:
            同步结果
        """
        if timesheet_id:
            # 同步单个工时记录
            timesheet = self.db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()
            if not timesheet:
                return {'success': False, 'message': '工时记录不存在'}

            if timesheet.status != 'APPROVED':
                return {'success': False, 'message': '只能同步已审批的工时记录'}

            if not timesheet.project_id:
                return {'success': False, 'message': '工时记录未关联项目'}

            result = self._create_financial_cost_from_timesheet(timesheet)
            return result

        elif project_id and year and month:
            # 批量同步某个项目的月度数据
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)

            timesheets = self.db.query(Timesheet).filter(
                Timesheet.project_id == project_id,
                Timesheet.status == 'APPROVED',
                Timesheet.work_date >= start_date,
                Timesheet.work_date <= end_date
            ).all()

            created_count = 0
            updated_count = 0
            errors = []

            for ts in timesheets:
                try:
                    result = self._create_financial_cost_from_timesheet(ts)
                    if result.get('created'):
                        created_count += 1
                    elif result.get('updated'):
                        updated_count += 1
                except Exception as e:
                    errors.append(f"工时记录{ts.id}: {str(e)}")

            return {
                'success': True,
                'message': f'同步完成：新建{created_count}条，更新{updated_count}条',
                'created_count': created_count,
                'updated_count': updated_count,
                'errors': errors
            }

        else:
            return {'success': False, 'message': '参数不完整'}

    def _create_financial_cost_from_timesheet(self, timesheet: Timesheet) -> Dict[str, Any]:
        """从工时记录创建财务成本记录"""
        # 检查是否已存在
        existing = self.db.query(FinancialProjectCost).filter(
            FinancialProjectCost.source_type == 'TIMESHEET',
            FinancialProjectCost.source_no == str(timesheet.id)
        ).first()

        # 获取用户时薪
        hourly_rate = HourlyRateService.get_user_hourly_rate(
            self.db, timesheet.user_id, timesheet.work_date
        )

        # 计算成本金额
        cost_amount = Decimal(str(timesheet.hours or 0)) * hourly_rate
        cost_month = timesheet.work_date.strftime('%Y-%m')

        if existing:
            # 更新现有记录
            existing.amount = cost_amount
            existing.hours = Decimal(str(timesheet.hours or 0))
            existing.hourly_rate = hourly_rate
            existing.cost_date = timesheet.work_date
            existing.cost_month = cost_month
            existing.description = timesheet.work_content
            existing.user_id = timesheet.user_id
            existing.user_name = timesheet.user_name

            self.db.commit()
            return {'success': True, 'created': False, 'updated': True, 'cost_id': existing.id}
        else:
            # 创建新记录
            cost = FinancialProjectCost(
                project_id=timesheet.project_id,
                project_code=timesheet.project_code,
                project_name=timesheet.project_name,
                cost_type='LABOR',
                cost_category='人工费',
                cost_item='工时成本',
                amount=cost_amount,
                cost_date=timesheet.work_date,
                cost_month=cost_month,
                description=timesheet.work_content,
                user_id=timesheet.user_id,
                user_name=timesheet.user_name,
                hours=Decimal(str(timesheet.hours or 0)),
                hourly_rate=hourly_rate,
                source_type='TIMESHEET',
                source_no=str(timesheet.id),
                uploaded_by=timesheet.user_id,
                is_verified=True,
                verified_by=timesheet.approver_id,
                verified_at=timesheet.approve_time
            )

            self.db.add(cost)
            self.db.commit()
            self.db.refresh(cost)

            return {'success': True, 'created': True, 'updated': False, 'cost_id': cost.id}

    def sync_to_rd(
        self,
        timesheet_id: Optional[int] = None,
        rd_project_id: Optional[int] = None,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        同步到研发系统（生成RdCost记录）

        Args:
            timesheet_id: 工时记录ID（可选）
            rd_project_id: 研发项目ID（可选）
            year: 年份（可选）
            month: 月份（可选）

        Returns:
            同步结果
        """
        if timesheet_id:
            # 同步单个工时记录
            timesheet = self.db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()
            if not timesheet:
                return {'success': False, 'message': '工时记录不存在'}

            if timesheet.status != 'APPROVED':
                return {'success': False, 'message': '只能同步已审批的工时记录'}

            if not timesheet.rd_project_id:
                return {'success': False, 'message': '工时记录未关联研发项目'}

            result = self._create_rd_cost_from_timesheet(timesheet)
            return result

        elif rd_project_id and year and month:
            # 批量同步某个研发项目的月度数据
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)

            timesheets = self.db.query(Timesheet).filter(
                Timesheet.rd_project_id == rd_project_id,
                Timesheet.status == 'APPROVED',
                Timesheet.work_date >= start_date,
                Timesheet.work_date <= end_date
            ).all()

            created_count = 0
            updated_count = 0
            errors = []

            for ts in timesheets:
                try:
                    result = self._create_rd_cost_from_timesheet(ts)
                    if result.get('created'):
                        created_count += 1
                    elif result.get('updated'):
                        updated_count += 1
                except Exception as e:
                    errors.append(f"工时记录{ts.id}: {str(e)}")

            return {
                'success': True,
                'message': f'同步完成：新建{created_count}条，更新{updated_count}条',
                'created_count': created_count,
                'updated_count': updated_count,
                'errors': errors
            }

        else:
            return {'success': False, 'message': '参数不完整'}

    def _create_rd_cost_from_timesheet(self, timesheet: Timesheet) -> Dict[str, Any]:
        """从工时记录创建研发费用记录"""
        # 获取研发项目
        rd_project = self.db.query(RdProject).filter(RdProject.id == timesheet.rd_project_id).first()
        if not rd_project:
            return {'success': False, 'message': '研发项目不存在'}

        # 获取费用类型（人工费用）
        from app.models.rd_project import RdCostType
        cost_type = self.db.query(RdCostType).filter(
            RdCostType.type_code == 'LABOR'
        ).first()

        # 如果不存在，查找category为LABOR的费用类型
        if not cost_type:
            cost_type = self.db.query(RdCostType).filter(
                RdCostType.category == 'LABOR',
                RdCostType.is_active == True
            ).first()

        # 如果还是不存在，创建一个默认的人工费用类型
        if not cost_type:
            cost_type = RdCostType(
                type_code='LABOR',
                type_name='人工费用',
                category='LABOR',
                description='研发项目人工费用',
                is_active=True
            )
            self.db.add(cost_type)
            self.db.flush()

        # 检查是否已存在
        existing = self.db.query(RdCost).filter(
            RdCost.source_type == 'TIMESHEET',
            RdCost.source_id == timesheet.id
        ).first()

        # 获取用户时薪
        hourly_rate = HourlyRateService.get_user_hourly_rate(
            self.db, timesheet.user_id, timesheet.work_date
        )

        # 计算费用金额
        cost_amount = Decimal(str(timesheet.hours or 0)) * hourly_rate

        if existing:
            # 更新现有记录
            existing.cost_amount = cost_amount
            existing.hours = Decimal(str(timesheet.hours or 0))
            existing.hourly_rate = hourly_rate
            existing.cost_date = timesheet.work_date
            existing.cost_description = timesheet.work_content
            existing.user_id = timesheet.user_id

            self.db.commit()
            return {'success': True, 'created': False, 'updated': True, 'cost_id': existing.id}
        else:
            # 生成费用编号
            from datetime import datetime

            from sqlalchemy import desc
            today = datetime.now()
            date_str = today.strftime("%y%m%d")
            prefix = f"RDCOST{date_str}"

            # 查询当天最大序号
            max_cost = self.db.query(RdCost).filter(
                RdCost.cost_no.like(f"{prefix}%")
            ).order_by(desc(RdCost.cost_no)).first()

            if max_cost:
                try:
                    seq_str = max_cost.cost_no[-3:]
                    seq = int(seq_str) + 1
                except (ValueError, IndexError):
                    seq = 1
            else:
                seq = 1

            cost_no = f"{prefix}{seq:03d}"

            # 创建新记录
            cost = RdCost(
                cost_no=cost_no,
                rd_project_id=timesheet.rd_project_id,
                cost_type_id=cost_type.id,
                cost_date=timesheet.work_date,
                cost_amount=cost_amount,
                cost_description=timesheet.work_content,
                user_id=timesheet.user_id,
                hours=Decimal(str(timesheet.hours or 0)),
                hourly_rate=hourly_rate,
                source_type='CALCULATED',  # 自动计算的费用
                source_id=timesheet.id,
                status='APPROVED'  # 已审批的工时自动创建已审批的费用
            )

            self.db.add(cost)
            self.db.commit()
            self.db.refresh(cost)

            return {'success': True, 'created': True, 'updated': False, 'cost_id': cost.id}

    def sync_to_project(
        self,
        timesheet_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        同步到项目系统（更新项目成本和进度）

        Args:
            timesheet_id: 工时记录ID（可选）
            project_id: 项目ID（可选，用于批量同步）

        Returns:
            同步结果
        """
        if timesheet_id:
            # 同步单个工时记录
            timesheet = self.db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()
            if not timesheet:
                return {'success': False, 'message': '工时记录不存在'}

            if timesheet.status != 'APPROVED':
                return {'success': False, 'message': '只能同步已审批的工时记录'}

            if not timesheet.project_id:
                return {'success': False, 'message': '工时记录未关联项目'}

            # 使用LaborCostService计算项目成本
            result = LaborCostService.calculate_project_labor_cost(
                self.db,
                timesheet.project_id,
                start_date=timesheet.work_date,
                end_date=timesheet.work_date,
                recalculate=False
            )

            return result

        elif project_id:
            # 批量同步项目所有已审批工时
            result = LaborCostService.calculate_project_labor_cost(
                self.db,
                project_id,
                recalculate=False
            )

            return result

        else:
            return {'success': False, 'message': '参数不完整'}

    def sync_to_hr(
        self,
        year: int,
        month: int,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        同步到HR系统（生成加班工资数据）
        注意：这个主要是数据准备，实际工资计算由OvertimeCalculationService完成

        Args:
            year: 年份
            month: 月份
            department_id: 部门ID（可选）

        Returns:
            同步结果
        """
        from app.services.overtime_calculation_service import OvertimeCalculationService

        overtime_service = OvertimeCalculationService(self.db)

        # 获取所有用户的加班统计
        stats = overtime_service.get_overtime_statistics(year, month, department_id)

        return {
            'success': True,
            'message': 'HR数据准备完成',
            'statistics': stats
        }

    def sync_all_on_approval(self, timesheet_id: int) -> Dict[str, Any]:
        """
        工时审批通过后自动同步到所有系统

        Args:
            timesheet_id: 工时记录ID

        Returns:
            同步结果
        """
        timesheet = self.db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()
        if not timesheet:
            return {'success': False, 'message': '工时记录不存在'}

        results = {
            'timesheet_id': timesheet_id,
            'finance': None,
            'rd': None,
            'project': None,
            'hr': None
        }

        # 同步到财务（如果有项目）
        if timesheet.project_id:
            results['finance'] = self.sync_to_finance(timesheet_id=timesheet_id)
            results['project'] = self.sync_to_project(timesheet_id=timesheet_id)

        # 同步到研发（如果是研发项目）
        if timesheet.rd_project_id:
            results['rd'] = self.sync_to_rd(timesheet_id=timesheet_id)

        # HR数据会在月度汇总时统一处理，这里不单独同步

        return {
            'success': True,
            'message': '自动同步完成',
            'results': results
        }
