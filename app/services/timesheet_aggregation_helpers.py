# -*- coding: utf-8 -*-
"""
工时汇总辅助服务
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.timesheet import Timesheet, TimesheetSummary


def calculate_month_range(year: int, month: int) -> Tuple[date, date]:
    """
    计算月份的开始和结束日期
    
    Returns:
        Tuple[date, date]: (开始日期, 结束日期)
    """
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    return start_date, end_date


def query_timesheets(
    db: Session,
    start_date: date,
    end_date: date,
    user_id: Optional[int],
    department_id: Optional[int],
    project_id: Optional[int]
) -> List[Timesheet]:
    """
    查询已审批的工时记录
    
    Returns:
        List[Timesheet]: 工时记录列表
    """
    query = db.query(Timesheet).filter(
        Timesheet.status == 'APPROVED',
        Timesheet.work_date >= start_date,
        Timesheet.work_date <= end_date
    )
    
    if user_id:
        query = query.filter(Timesheet.user_id == user_id)
    if department_id:
        query = query.filter(Timesheet.department_id == department_id)
    if project_id:
        query = query.filter(Timesheet.project_id == project_id)
    
    return query.all()


def calculate_hours_summary(timesheets: List[Timesheet]) -> Dict[str, float]:
    """
    计算工时汇总
    
    Returns:
        Dict: 工时汇总数据
    """
    total_hours = sum(float(ts.hours or 0) for ts in timesheets)
    normal_hours = sum(float(ts.hours or 0) for ts in timesheets if ts.overtime_type == 'NORMAL')
    overtime_hours = sum(float(ts.hours or 0) for ts in timesheets if ts.overtime_type == 'OVERTIME')
    weekend_hours = sum(float(ts.hours or 0) for ts in timesheets if ts.overtime_type == 'WEEKEND')
    holiday_hours = sum(float(ts.hours or 0) for ts in timesheets if ts.overtime_type == 'HOLIDAY')
    
    return {
        "total_hours": total_hours,
        "normal_hours": normal_hours,
        "overtime_hours": overtime_hours,
        "weekend_hours": weekend_hours,
        "holiday_hours": holiday_hours,
    }


def build_project_breakdown(timesheets: List[Timesheet]) -> Dict[str, Dict[str, Any]]:
    """
    构建项目分布
    
    Returns:
        Dict: 项目分布数据
    """
    project_breakdown = {}
    
    for ts in timesheets:
        if ts.project_id:
            project_key = f"{ts.project_code or ''}_{ts.project_id}"
            if project_key not in project_breakdown:
                project_breakdown[project_key] = {
                    'project_id': ts.project_id,
                    'project_code': ts.project_code,
                    'project_name': ts.project_name,
                    'hours': 0
                }
            project_breakdown[project_key]['hours'] += float(ts.hours or 0)
    
    return project_breakdown


def build_daily_breakdown(timesheets: List[Timesheet]) -> Dict[str, Dict[str, Any]]:
    """
    构建日期分布
    
    Returns:
        Dict: 日期分布数据
    """
    daily_breakdown = {}
    
    for ts in timesheets:
        day_key = str(ts.work_date)
        if day_key not in daily_breakdown:
            daily_breakdown[day_key] = {
                'date': day_key,
                'hours': 0,
                'normal_hours': 0,
                'overtime_hours': 0
            }
        daily_breakdown[day_key]['hours'] += float(ts.hours or 0)
        if ts.overtime_type == 'NORMAL':
            daily_breakdown[day_key]['normal_hours'] += float(ts.hours or 0)
        else:
            daily_breakdown[day_key]['overtime_hours'] += float(ts.hours or 0)
    
    return daily_breakdown


def build_task_breakdown(timesheets: List[Timesheet]) -> Dict[str, Dict[str, Any]]:
    """
    构建任务分布
    
    Returns:
        Dict: 任务分布数据
    """
    task_breakdown = {}
    
    for ts in timesheets:
        if ts.task_id:
            task_key = f"task_{ts.task_id}"
            if task_key not in task_breakdown:
                task_breakdown[task_key] = {
                    'task_id': ts.task_id,
                    'task_name': ts.task_name,
                    'hours': 0
                }
            task_breakdown[task_key]['hours'] += float(ts.hours or 0)
    
    return task_breakdown


def get_or_create_summary(
    db: Session,
    summary_type: str,
    year: int,
    month: int,
    user_id: Optional[int],
    project_id: Optional[int],
    department_id: Optional[int],
    hours_summary: Dict[str, float],
    project_breakdown: Dict[str, Dict[str, Any]],
    daily_breakdown: Dict[str, Dict[str, Any]],
    task_breakdown: Dict[str, Dict[str, Any]],
    entries_count: int
) -> TimesheetSummary:
    """
    获取或创建汇总记录
    
    Returns:
        TimesheetSummary: 汇总记录对象
    """
    summary = db.query(TimesheetSummary).filter(
        TimesheetSummary.summary_type == summary_type,
        TimesheetSummary.year == year,
        TimesheetSummary.month == month
    )
    
    if user_id:
        summary = summary.filter(TimesheetSummary.user_id == user_id)
    if project_id:
        summary = summary.filter(TimesheetSummary.project_id == project_id)
    if department_id:
        summary = summary.filter(TimesheetSummary.department_id == department_id)
    
    summary = summary.first()
    
    if not summary:
        summary = TimesheetSummary(
            summary_type=summary_type,
            user_id=user_id,
            project_id=project_id,
            department_id=department_id,
            year=year,
            month=month,
            total_hours=Decimal(str(hours_summary["total_hours"])),
            normal_hours=Decimal(str(hours_summary["normal_hours"])),
            overtime_hours=Decimal(str(hours_summary["overtime_hours"])),
            weekend_hours=Decimal(str(hours_summary["weekend_hours"])),
            holiday_hours=Decimal(str(hours_summary["holiday_hours"])),
            entries_count=entries_count,
            projects_count=len(project_breakdown),
            project_breakdown=project_breakdown,
            daily_breakdown=daily_breakdown,
            task_breakdown=task_breakdown
        )
        db.add(summary)
    else:
        summary.total_hours = Decimal(str(hours_summary["total_hours"]))
        summary.normal_hours = Decimal(str(hours_summary["normal_hours"]))
        summary.overtime_hours = Decimal(str(hours_summary["overtime_hours"]))
        summary.weekend_hours = Decimal(str(hours_summary["weekend_hours"]))
        summary.holiday_hours = Decimal(str(hours_summary["holiday_hours"]))
        summary.entries_count = entries_count
        summary.projects_count = len(project_breakdown)
        summary.project_breakdown = project_breakdown
        summary.daily_breakdown = daily_breakdown
        summary.task_breakdown = task_breakdown
    
    return summary
