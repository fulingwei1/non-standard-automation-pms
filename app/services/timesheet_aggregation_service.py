# -*- coding: utf-8 -*-
"""
工时汇总服务
负责从工时记录自动生成多维度汇总和多格式报表
"""

from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.rd_project import RdProject
from app.models.timesheet import Timesheet
from app.services.hourly_rate_service import HourlyRateService
from app.common.date_range import get_month_range_by_ym


class TimesheetAggregationService:
    """工时汇总服务"""

    def __init__(self, db: Session):
        self.db = db

    def aggregate_monthly_timesheet(
        self,
        year: int,
        month: int,
        user_id: Optional[int] = None,
        department_id: Optional[int] = None,
        project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        月度工时汇总

        Args:
            year: 年份
            month: 月份
            user_id: 用户ID（可选）
            department_id: 部门ID（可选）
            project_id: 项目ID（可选）

        Returns:
            汇总结果字典
        """
        from app.services.timesheet_aggregation_helpers import (
            build_daily_breakdown,
            build_project_breakdown,
            build_task_breakdown,
            calculate_hours_summary,
            calculate_month_range,
            get_or_create_summary,
            query_timesheets,
        )

        # 计算月份范围
        start_date, end_date = calculate_month_range(year, month)

        # 查询工时记录
        timesheets = query_timesheets(
            self.db, start_date, end_date, user_id, department_id, project_id
        )

        # 计算汇总
        hours_summary = calculate_hours_summary(timesheets)
        project_breakdown = build_project_breakdown(timesheets)
        daily_breakdown = build_daily_breakdown(timesheets)
        task_breakdown = build_task_breakdown(timesheets)

        # 确定汇总类型
        summary_type = 'USER_MONTH' if user_id else ('PROJECT_MONTH' if project_id else ('DEPT_MONTH' if department_id else 'GLOBAL_MONTH'))

        # 获取或创建汇总记录
        summary = get_or_create_summary(
            self.db, summary_type, year, month, user_id, project_id, department_id,
            hours_summary, project_breakdown, daily_breakdown, task_breakdown,
            len(timesheets)
        )

        self.db.commit()
        self.db.refresh(summary)

        return {
            'success': True,
            'summary_id': summary.id,
            'total_hours': hours_summary["total_hours"],
            'normal_hours': hours_summary["normal_hours"],
            'overtime_hours': hours_summary["overtime_hours"],
            'weekend_hours': hours_summary["weekend_hours"],
            'holiday_hours': hours_summary["holiday_hours"],
            'entries_count': len(timesheets),
            'projects_count': len(project_breakdown),
            'project_breakdown': project_breakdown,
            'daily_breakdown': daily_breakdown,
            'task_breakdown': task_breakdown
        }

    def generate_hr_report(
        self,
        year: int,
        month: int,
        department_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        生成HR报表（用于计算加班工资）

        Args:
            year: 年份
            month: 月份
            department_id: 部门ID（可选）

        Returns:
            HR报表数据列表
        """
        start_date, end_date = get_month_range_by_ym(year, month)

        query = self.db.query(Timesheet).filter(
            Timesheet.status == 'APPROVED',
            Timesheet.work_date >= start_date,
            Timesheet.work_date <= end_date
        )

        if department_id:
            query = query.filter(Timesheet.department_id == department_id)

        timesheets = query.order_by(Timesheet.user_id, Timesheet.work_date).all()

        # 按用户分组
        user_data = {}
        for ts in timesheets:
            user_key = ts.user_id
            if user_key not in user_data:
                user_data[user_key] = {
                    'user_id': ts.user_id,
                    'user_name': ts.user_name,
                    'department_id': ts.department_id,
                    'department_name': ts.department_name,
                    'total_hours': 0,
                    'normal_hours': 0,
                    'overtime_hours': 0,
                    'weekend_hours': 0,
                    'holiday_hours': 0,
                    'daily_records': []
                }

            user_data[user_key]['total_hours'] += float(ts.hours or 0)

            if ts.overtime_type == 'NORMAL':
                user_data[user_key]['normal_hours'] += float(ts.hours or 0)
            elif ts.overtime_type == 'OVERTIME':
                user_data[user_key]['overtime_hours'] += float(ts.hours or 0)
            elif ts.overtime_type == 'WEEKEND':
                user_data[user_key]['weekend_hours'] += float(ts.hours or 0)
            elif ts.overtime_type == 'HOLIDAY':
                user_data[user_key]['holiday_hours'] += float(ts.hours or 0)

            user_data[user_key]['daily_records'].append({
                'date': str(ts.work_date),
                'hours': float(ts.hours or 0),
                'overtime_type': ts.overtime_type,
                'work_content': ts.work_content
            })

        # 转换为列表
        report_data = list(user_data.values())

        return report_data

    def generate_finance_report(
        self,
        year: int,
        month: int,
        project_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        生成财务报表（用于核算项目成本）

        Args:
            year: 年份
            month: 月份
            project_id: 项目ID（可选）

        Returns:
            财务报表数据列表
        """
        start_date, end_date = get_month_range_by_ym(year, month)

        query = self.db.query(Timesheet).filter(
            Timesheet.status == 'APPROVED',
            Timesheet.work_date >= start_date,
            Timesheet.work_date <= end_date,
            Timesheet.project_id.isnot(None)  # 只统计非标项目
        )

        if project_id:
            query = query.filter(Timesheet.project_id == project_id)

        timesheets = query.order_by(Timesheet.project_id, Timesheet.user_id, Timesheet.work_date).all()

        # 按项目分组
        project_data = {}
        for ts in timesheets:
            project_key = ts.project_id
            if project_key not in project_data:
                project_data[project_key] = {
                    'project_id': ts.project_id,
                    'project_code': ts.project_code,
                    'project_name': ts.project_name,
                    'total_hours': 0,
                    'total_cost': 0,
                    'personnel_records': []
                }

            # 获取用户时薪
            hourly_rate = HourlyRateService.get_user_hourly_rate(self.db, ts.user_id, ts.work_date)
            cost = float(ts.hours or 0) * float(hourly_rate)

            project_data[project_key]['total_hours'] += float(ts.hours or 0)
            project_data[project_key]['total_cost'] += cost

            project_data[project_key]['personnel_records'].append({
                'user_id': ts.user_id,
                'user_name': ts.user_name,
                'date': str(ts.work_date),
                'hours': float(ts.hours or 0),
                'hourly_rate': hourly_rate,
                'cost': cost,
                'work_content': ts.work_content
            })

        # 转换为列表
        report_data = list(project_data.values())

        return report_data

    def generate_rd_report(
        self,
        year: int,
        month: int,
        rd_project_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        生成研发报表（用于核算研发费用）

        Args:
            year: 年份
            month: 月份
            rd_project_id: 研发项目ID（可选）

        Returns:
            研发报表数据列表
        """
        start_date, end_date = get_month_range_by_ym(year, month)

        query = self.db.query(Timesheet).filter(
            Timesheet.status == 'APPROVED',
            Timesheet.work_date >= start_date,
            Timesheet.work_date <= end_date,
            Timesheet.rd_project_id.isnot(None)  # 只统计研发项目
        )

        if rd_project_id:
            query = query.filter(Timesheet.rd_project_id == rd_project_id)

        timesheets = query.order_by(Timesheet.rd_project_id, Timesheet.user_id, Timesheet.work_date).all()

        # 按研发项目分组
        rd_project_data = {}
        for ts in timesheets:
            project_key = ts.rd_project_id
            if project_key not in rd_project_data:
                rd_project = self.db.query(RdProject).filter(RdProject.id == project_key).first()
                rd_project_data[project_key] = {
                    'rd_project_id': ts.rd_project_id,
                    'rd_project_code': rd_project.project_code if rd_project else None,
                    'rd_project_name': rd_project.project_name if rd_project else None,
                    'total_hours': 0,
                    'total_cost': 0,
                    'personnel_records': []
                }

            # 获取用户时薪
            hourly_rate = HourlyRateService.get_user_hourly_rate(self.db, ts.user_id, ts.work_date)
            cost = float(ts.hours or 0) * float(hourly_rate)

            rd_project_data[project_key]['total_hours'] += float(ts.hours or 0)
            rd_project_data[project_key]['total_cost'] += cost

            rd_project_data[project_key]['personnel_records'].append({
                'user_id': ts.user_id,
                'user_name': ts.user_name,
                'date': str(ts.work_date),
                'hours': float(ts.hours or 0),
                'hourly_rate': hourly_rate,
                'cost': cost,
                'work_content': ts.work_content
            })

        # 转换为列表
        report_data = list(rd_project_data.values())

        return report_data

    def generate_project_report(
        self,
        project_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        生成项目报表（用于项目进度查看）

        Args:
            project_id: 项目ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            项目报表数据
        """
        query = self.db.query(Timesheet).filter(
            Timesheet.status == 'APPROVED',
            Timesheet.project_id == project_id
        )

        if start_date:
            query = query.filter(Timesheet.work_date >= start_date)
        if end_date:
            query = query.filter(Timesheet.work_date <= end_date)

        timesheets = query.order_by(Timesheet.work_date).all()

        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {'error': '项目不存在'}

        # 按人员统计
        personnel_stats = {}
        for ts in timesheets:
            user_key = ts.user_id
            if user_key not in personnel_stats:
                personnel_stats[user_key] = {
                    'user_id': ts.user_id,
                    'user_name': ts.user_name,
                    'total_hours': 0,
                    'contribution_rate': 0
                }
            personnel_stats[user_key]['total_hours'] += float(ts.hours or 0)

        total_hours = sum(float(ts.hours or 0) for ts in timesheets)
        for user_key in personnel_stats:
            if total_hours > 0:
                personnel_stats[user_key]['contribution_rate'] = \
                    (personnel_stats[user_key]['total_hours'] / total_hours) * 100

        # 按日期统计
        daily_stats = {}
        for ts in timesheets:
            day_key = str(ts.work_date)
            if day_key not in daily_stats:
                daily_stats[day_key] = {
                    'date': day_key,
                    'hours': 0,
                    'personnel_count': 0
                }
            daily_stats[day_key]['hours'] += float(ts.hours or 0)
            if ts.user_id not in [p['user_id'] for p in daily_stats[day_key].get('personnel', [])]:
                if 'personnel' not in daily_stats[day_key]:
                    daily_stats[day_key]['personnel'] = []
                daily_stats[day_key]['personnel'].append({
                    'user_id': ts.user_id,
                    'user_name': ts.user_name,
                    'hours': float(ts.hours or 0)
                })
                daily_stats[day_key]['personnel_count'] = len(daily_stats[day_key]['personnel'])

        # 按任务统计
        task_stats = {}
        for ts in timesheets:
            if ts.task_id:
                task_key = ts.task_id
                if task_key not in task_stats:
                    task_stats[task_key] = {
                        'task_id': ts.task_id,
                        'task_name': ts.task_name,
                        'total_hours': 0
                    }
                task_stats[task_key]['total_hours'] += float(ts.hours or 0)

        return {
            'project_id': project_id,
            'project_code': project.project_code,
            'project_name': project.project_name,
            'total_hours': total_hours,
            'personnel_count': len(personnel_stats),
            'personnel_stats': list(personnel_stats.values()),
            'daily_stats': list(daily_stats.values()),
            'task_stats': list(task_stats.values())
        }
