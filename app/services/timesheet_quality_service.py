# -*- coding: utf-8 -*-
"""
工时质量检查服务
负责工时异常检测、工作日志完整性检查、数据一致性校验
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User
from app.models.work_log import WorkLog


class TimesheetQualityService:
    """工时质量检查服务"""

    # 异常检测阈值
    MAX_DAILY_HOURS = 16  # 单日最大工时（超过视为异常）
    MIN_DAILY_HOURS = 0.5  # 单日最小工时（低于视为异常，除非是请假）
    MAX_WEEKLY_HOURS = 80  # 单周最大工时
    MAX_MONTHLY_HOURS = 300  # 单月最大工时

    def __init__(self, db: Session):
        self.db = db

    def detect_anomalies(
        self,
        user_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        检测工时异常

        Args:
            user_id: 用户ID（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            异常记录列表
        """
        query = self.db.query(Timesheet).filter(Timesheet.status == 'APPROVED')

        if user_id:
            query = query.filter(Timesheet.user_id == user_id)
        if start_date:
            query = query.filter(Timesheet.work_date >= start_date)
        if end_date:
            query = query.filter(Timesheet.work_date <= end_date)

        timesheets = query.all()

        anomalies = []

        # 按用户和日期分组，检测单日工时异常
        daily_hours = {}
        for ts in timesheets:
            key = (ts.user_id, ts.work_date)
            if key not in daily_hours:
                daily_hours[key] = 0
            daily_hours[key] += float(ts.hours or 0)

        for (user_id, work_date), hours in daily_hours.items():
            if hours > self.MAX_DAILY_HOURS:
                user = self.db.query(User).filter(User.id == user_id).first()
                anomalies.append({
                    'type': 'EXCESSIVE_DAILY_HOURS',
                    'severity': 'HIGH',
                    'user_id': user_id,
                    'user_name': user.real_name or user.username if user else None,
                    'work_date': str(work_date),
                    'hours': hours,
                    'threshold': self.MAX_DAILY_HOURS,
                    'message': f"用户{user.real_name if user else user_id}在{work_date}的工时{hours:.1f}小时超过最大限制{self.MAX_DAILY_HOURS}小时"
                })

        # 检测单周工时异常
        weekly_hours = {}
        for ts in timesheets:
            # 计算周开始日期
            week_start = ts.work_date - timedelta(days=ts.work_date.weekday())
            key = (ts.user_id, week_start)
            if key not in weekly_hours:
                weekly_hours[key] = 0
            weekly_hours[key] += float(ts.hours or 0)

        for (user_id, week_start), hours in weekly_hours.items():
            if hours > self.MAX_WEEKLY_HOURS:
                user = self.db.query(User).filter(User.id == user_id).first()
                anomalies.append({
                    'type': 'EXCESSIVE_WEEKLY_HOURS',
                    'severity': 'MEDIUM',
                    'user_id': user_id,
                    'user_name': user.real_name or user.username if user else None,
                    'week_start': str(week_start),
                    'hours': hours,
                    'threshold': self.MAX_WEEKLY_HOURS,
                    'message': f"用户{user.real_name if user else user_id}在{week_start}所在周的工时{hours:.1f}小时超过最大限制{self.MAX_WEEKLY_HOURS}小时"
                })

        # 检测单月工时异常
        monthly_hours = {}
        for ts in timesheets:
            month_key = ts.work_date.strftime('%Y-%m')
            key = (ts.user_id, month_key)
            if key not in monthly_hours:
                monthly_hours[key] = 0
            monthly_hours[key] += float(ts.hours or 0)

        for (user_id, month_key), hours in monthly_hours.items():
            if hours > self.MAX_MONTHLY_HOURS:
                user = self.db.query(User).filter(User.id == user_id).first()
                anomalies.append({
                    'type': 'EXCESSIVE_MONTHLY_HOURS',
                    'severity': 'MEDIUM',
                    'user_id': user_id,
                    'user_name': user.real_name or user.username if user else None,
                    'month': month_key,
                    'hours': hours,
                    'threshold': self.MAX_MONTHLY_HOURS,
                    'message': f"用户{user.real_name if user else user_id}在{month_key}的工时{hours:.1f}小时超过最大限制{self.MAX_MONTHLY_HOURS}小时"
                })

        return anomalies

    def check_work_log_completeness(
        self,
        user_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        检查工作日志完整性

        Args:
            user_id: 用户ID（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            完整性检查结果
        """
        # 默认检查最近30天
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        # 查询有工时记录但缺少工作日志的日期
        query = self.db.query(Timesheet.work_date, Timesheet.user_id).filter(
            Timesheet.status == 'APPROVED',
            Timesheet.work_date >= start_date,
            Timesheet.work_date <= end_date
        )

        if user_id:
            query = query.filter(Timesheet.user_id == user_id)

        timesheet_dates = query.distinct().all()

        missing_logs = []

        for work_date, user_id in timesheet_dates:
            # 检查是否有对应的工作日志
            work_log = self.db.query(WorkLog).filter(
                WorkLog.user_id == user_id,
                WorkLog.work_date == work_date
            ).first()

            if not work_log:
                user = self.db.query(User).filter(User.id == user_id).first()
                missing_logs.append({
                    'user_id': user_id,
                    'user_name': user.real_name or user.username if user else None,
                    'work_date': str(work_date),
                    'message': f"用户{user.real_name if user else user_id}在{work_date}有工时记录但缺少工作日志"
                })

        return {
            'start_date': str(start_date),
            'end_date': str(end_date),
            'total_timesheet_dates': len(timesheet_dates),
            'missing_log_count': len(missing_logs),
            'missing_logs': missing_logs,
            'completeness_rate': ((len(timesheet_dates) - len(missing_logs)) / len(timesheet_dates) * 100) if timesheet_dates else 100
        }

    def validate_data_consistency(
        self,
        user_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        校验工时记录与工作日志的一致性

        Args:
            user_id: 用户ID（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            一致性校验结果
        """
        # 默认检查最近30天
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today()

        query = self.db.query(Timesheet).filter(
            Timesheet.status == 'APPROVED',
            Timesheet.work_date >= start_date,
            Timesheet.work_date <= end_date
        )

        if user_id:
            query = query.filter(Timesheet.user_id == user_id)

        timesheets = query.all()

        inconsistencies = []

        for ts in timesheets:
            # 检查是否有对应的工作日志
            work_log = self.db.query(WorkLog).filter(
                WorkLog.user_id == ts.user_id,
                WorkLog.work_date == ts.work_date
            ).first()

            if work_log:
                # 检查工作日志是否关联了工时记录
                if work_log.timesheet_id != ts.id:
                    user = self.db.query(User).filter(User.id == ts.user_id).first()
                    inconsistencies.append({
                        'type': 'MISMATCHED_ASSOCIATION',
                        'severity': 'LOW',
                        'user_id': ts.user_id,
                        'user_name': user.real_name or user.username if user else None,
                        'work_date': str(ts.work_date),
                        'timesheet_id': ts.id,
                        'work_log_id': work_log.id,
                        'message': f"用户{user.real_name if user else ts.user_id}在{ts.work_date}的工时记录和工作日志关联不一致"
                    })

                # 检查项目关联是否一致
                if ts.project_id:
                    # 检查工作日志中是否提及了该项目
                    from app.models.work_log import WorkLogMention
                    mention = self.db.query(WorkLogMention).filter(
                        WorkLogMention.work_log_id == work_log.id,
                        WorkLogMention.mention_type == 'PROJECT',
                        WorkLogMention.mention_id == ts.project_id
                    ).first()

                    if not mention:
                        user = self.db.query(User).filter(User.id == ts.user_id).first()
                        inconsistencies.append({
                            'type': 'MISSING_PROJECT_MENTION',
                            'severity': 'LOW',
                            'user_id': ts.user_id,
                            'user_name': user.real_name or user.username if user else None,
                            'work_date': str(ts.work_date),
                            'project_id': ts.project_id,
                            'message': f"用户{user.real_name if user else ts.user_id}在{ts.work_date}的工时记录关联了项目{ts.project_id}，但工作日志中未提及"
                        })

        return {
            'start_date': str(start_date),
            'end_date': str(end_date),
            'total_timesheets': len(timesheets),
            'inconsistency_count': len(inconsistencies),
            'inconsistencies': inconsistencies,
            'consistency_rate': ((len(timesheets) - len(inconsistencies)) / len(timesheets) * 100) if timesheets else 100
        }

    def check_labor_law_compliance(
        self,
        user_id: int,
        year: int,
        month: int
    ) -> Dict[str, Any]:
        """
        检查劳动法合规性（如每月加班不超过36小时）

        Args:
            user_id: 用户ID
            year: 年份
            month: 月份

        Returns:
            合规性检查结果
        """
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        # 查询加班工时（非正常工时）
        timesheets = self.db.query(Timesheet).filter(
            Timesheet.user_id == user_id,
            Timesheet.status == 'APPROVED',
            Timesheet.work_date >= start_date,
            Timesheet.work_date <= end_date,
            Timesheet.overtime_type != 'NORMAL'
        ).all()

        overtime_hours = sum(float(ts.hours or 0) for ts in timesheets)

        # 劳动法规定：每月加班不超过36小时
        MAX_MONTHLY_OVERTIME = 36

        is_compliant = overtime_hours <= MAX_MONTHLY_OVERTIME

        return {
            'user_id': user_id,
            'year': year,
            'month': month,
            'overtime_hours': overtime_hours,
            'max_allowed': MAX_MONTHLY_OVERTIME,
            'is_compliant': is_compliant,
            'violation_hours': max(0, overtime_hours - MAX_MONTHLY_OVERTIME) if not is_compliant else 0,
            'message': f"用户{user_id}在{year}年{month}月加班{overtime_hours:.1f}小时，{'符合' if is_compliant else '超过'}劳动法规定（最多{MAX_MONTHLY_OVERTIME}小时）"
        }
