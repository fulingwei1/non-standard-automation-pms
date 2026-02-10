# -*- coding: utf-8 -*-
"""
加班工资计算服务
负责计算加班工资和加班统计
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.timesheet import Timesheet
from app.models.user import User
from app.services.hourly_rate_service import HourlyRateService
from app.common.date_range import get_month_range_by_ym


class OvertimeCalculationService:
    """加班工资计算服务"""

    # 加班工资倍数（可根据公司政策调整）
    OVERTIME_MULTIPLIER = Decimal("1.5")  # 工作日加班：1.5倍
    WEEKEND_MULTIPLIER = Decimal("2.0")  # 周末加班：2倍
    HOLIDAY_MULTIPLIER = Decimal("3.0")  # 节假日加班：3倍

    def __init__(self, db: Session):
        self.db = db

    def calculate_overtime_pay(
        self,
        user_id: int,
        work_date: date,
        hours: Decimal,
        overtime_type: str
    ) -> Decimal:
        """
        计算单个工时记录的加班工资

        Args:
            user_id: 用户ID
            work_date: 工作日期
            hours: 工时数
            overtime_type: 加班类型（NORMAL/OVERTIME/WEEKEND/HOLIDAY）

        Returns:
            加班工资金额
        """
        # 获取用户时薪
        hourly_rate = HourlyRateService.get_user_hourly_rate(self.db, user_id, work_date)

        # 根据加班类型计算工资
        if overtime_type == 'NORMAL':
            # 正常工时，不计算加班工资
            return Decimal("0")
        elif overtime_type == 'OVERTIME':
            # 工作日加班：1.5倍
            return hours * hourly_rate * (self.OVERTIME_MULTIPLIER - Decimal("1"))
        elif overtime_type == 'WEEKEND':
            # 周末加班：2倍
            return hours * hourly_rate * (self.WEEKEND_MULTIPLIER - Decimal("1"))
        elif overtime_type == 'HOLIDAY':
            # 节假日加班：3倍
            return hours * hourly_rate * (self.HOLIDAY_MULTIPLIER - Decimal("1"))
        else:
            return Decimal("0")

    def calculate_user_monthly_overtime_pay(
        self,
        user_id: int,
        year: int,
        month: int
    ) -> Dict[str, Any]:
        """
        计算用户月度加班工资

        Args:
            user_id: 用户ID
            year: 年份
            month: 月份

        Returns:
            月度加班工资统计
        """
        start_date, end_date = get_month_range_by_ym(year, month)

        # 查询已审批的工时记录
        timesheets = self.db.query(Timesheet).filter(
            Timesheet.user_id == user_id,
            Timesheet.status == 'APPROVED',
            Timesheet.work_date >= start_date,
            Timesheet.work_date <= end_date
        ).all()

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {'error': '用户不存在'}

        # 统计各类工时和工资
        total_hours = Decimal("0")
        normal_hours = Decimal("0")
        overtime_hours = Decimal("0")
        weekend_hours = Decimal("0")
        holiday_hours = Decimal("0")

        total_overtime_pay = Decimal("0")
        overtime_pay = Decimal("0")
        weekend_pay = Decimal("0")
        holiday_pay = Decimal("0")

        daily_records = []

        for ts in timesheets:
            hours = Decimal(str(ts.hours or 0))
            total_hours += hours

            if ts.overtime_type == 'NORMAL':
                normal_hours += hours
            elif ts.overtime_type == 'OVERTIME':
                overtime_hours += hours
                pay = self.calculate_overtime_pay(user_id, ts.work_date, hours, 'OVERTIME')
                overtime_pay += pay
                total_overtime_pay += pay
            elif ts.overtime_type == 'WEEKEND':
                weekend_hours += hours
                pay = self.calculate_overtime_pay(user_id, ts.work_date, hours, 'WEEKEND')
                weekend_pay += pay
                total_overtime_pay += pay
            elif ts.overtime_type == 'HOLIDAY':
                holiday_hours += hours
                pay = self.calculate_overtime_pay(user_id, ts.work_date, hours, 'HOLIDAY')
                holiday_pay += pay
                total_overtime_pay += pay

            daily_records.append({
                'date': str(ts.work_date),
                'hours': float(hours),
                'overtime_type': ts.overtime_type,
                'overtime_pay': float(self.calculate_overtime_pay(user_id, ts.work_date, hours, ts.overtime_type)),
                'work_content': ts.work_content
            })

        # 获取用户时薪（用于显示）
        hourly_rate = HourlyRateService.get_user_hourly_rate(self.db, user_id, start_date)

        # 获取部门信息（从Timesheet记录中获取，因为Timesheet已经有department_id和department_name）
        department_id = None
        department_name = None
        if timesheets:
            first_ts = timesheets[0]
            department_id = first_ts.department_id
            department_name = first_ts.department_name

        return {
            'user_id': user_id,
            'user_name': user.real_name or user.username,
            'department_id': department_id,
            'department_name': department_name,
            'year': year,
            'month': month,
            'total_hours': float(total_hours),
            'normal_hours': float(normal_hours),
            'overtime_hours': float(overtime_hours),
            'weekend_hours': float(weekend_hours),
            'holiday_hours': float(holiday_hours),
            'hourly_rate': float(hourly_rate),
            'total_overtime_pay': float(total_overtime_pay),
            'overtime_pay': float(overtime_pay),
            'weekend_pay': float(weekend_pay),
            'holiday_pay': float(holiday_pay),
            'daily_records': daily_records
        }

    def get_overtime_statistics(
        self,
        year: int,
        month: int,
        department_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取加班统计

        Args:
            year: 年份
            month: 月份
            department_id: 部门ID（可选）

        Returns:
            加班统计数据
        """
        start_date, end_date = get_month_range_by_ym(year, month)

        query = self.db.query(Timesheet).filter(
            Timesheet.status == 'APPROVED',
            Timesheet.work_date >= start_date,
            Timesheet.work_date <= end_date
        )

        if department_id:
            query = query.filter(Timesheet.department_id == department_id)

        timesheets = query.all()

        # 统计
        total_users = len(set(ts.user_id for ts in timesheets))
        total_overtime_hours = sum(float(ts.hours or 0) for ts in timesheets if ts.overtime_type != 'NORMAL')
        total_overtime_pay = Decimal("0")

        user_overtime_stats = {}
        for ts in timesheets:
            if ts.overtime_type != 'NORMAL':
                if ts.user_id not in user_overtime_stats:
                    user_overtime_stats[ts.user_id] = {
                        'user_id': ts.user_id,
                        'user_name': ts.user_name,
                        'overtime_hours': 0,
                        'overtime_pay': Decimal("0")
                    }
                user_overtime_stats[ts.user_id]['overtime_hours'] += float(ts.hours or 0)
                pay = self.calculate_overtime_pay(ts.user_id, ts.work_date, Decimal(str(ts.hours or 0)), ts.overtime_type)
                user_overtime_stats[ts.user_id]['overtime_pay'] += pay
                total_overtime_pay += pay

        # 转换为列表并排序
        user_stats_list = []
        for user_id, stats in user_overtime_stats.items():
            user_stats_list.append({
                'user_id': stats['user_id'],
                'user_name': stats['user_name'],
                'overtime_hours': stats['overtime_hours'],
                'overtime_pay': float(stats['overtime_pay'])
            })

        # 按加班工资降序排序
        user_stats_list.sort(key=lambda x: x['overtime_pay'], reverse=True)

        return {
            'year': year,
            'month': month,
            'department_id': department_id,
            'total_users': total_users,
            'total_overtime_hours': total_overtime_hours,
            'total_overtime_pay': float(total_overtime_pay),
            'user_statistics': user_stats_list
        }
