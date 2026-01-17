# -*- coding: utf-8 -*-
"""
资源规划服务
负责人员负载分析、项目资源需求预测、部门工作量统计
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.progress import Task
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User


class ResourcePlanningService:
    """资源规划服务"""

    # 标准工时配置
    STANDARD_MONTHLY_HOURS = 176  # 标准月工时（22天 × 8小时）
    STANDARD_DAILY_HOURS = 8  # 标准日工时
    MAX_LOAD_RATE = 110  # 最大负载率（%）

    def __init__(self, db: Session):
        self.db = db

    def analyze_user_workload(
        self,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        分析用户工作负载

        Args:
            user_id: 用户ID
            start_date: 开始日期（可选，默认未来30天）
            end_date: 结束日期（可选，默认未来30天）

        Returns:
            工作负载分析结果
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {'error': '用户不存在'}

        # 默认分析未来30天
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date + timedelta(days=30)

        # 查询已分配的任务（预估工时）
        tasks = self.db.query(Task).filter(
            Task.assignee_id == user_id,
            Task.status.in_(['PENDING', 'IN_PROGRESS']),
            Task.plan_start_date <= end_date,
            Task.plan_end_date >= start_date
        ).all()

        # 计算已分配工时
        assigned_hours = sum(float(task.estimated_hours or 0) for task in tasks)

        # 查询已记录的工时
        recorded_timesheets = self.db.query(Timesheet).filter(
            Timesheet.user_id == user_id,
            Timesheet.work_date >= start_date,
            Timesheet.work_date <= end_date,
            Timesheet.status == 'APPROVED'
        ).all()

        recorded_hours = sum(float(ts.hours or 0) for ts in recorded_timesheets)

        # 计算标准工时
        work_days = self._calculate_work_days(start_date, end_date)
        standard_hours = work_days * self.STANDARD_DAILY_HOURS

        # 计算负载率
        total_hours = assigned_hours + recorded_hours
        load_rate = (total_hours / standard_hours * 100) if standard_hours > 0 else 0

        # 按项目统计
        project_loads = {}
        for task in tasks:
            if task.project_id:
                project_key = task.project_id
                if project_key not in project_loads:
                    project = self.db.query(Project).filter(Project.id == project_key).first()
                    project_loads[project_key] = {
                        'project_id': project_key,
                        'project_code': project.project_code if project else None,
                        'project_name': project.project_name if project else None,
                        'assigned_hours': 0,
                        'task_count': 0
                    }
                project_loads[project_key]['assigned_hours'] += float(task.estimated_hours or 0)
                project_loads[project_key]['task_count'] += 1

        return {
            'user_id': user_id,
            'user_name': user.real_name or user.username,
            'start_date': str(start_date),
            'end_date': str(end_date),
            'work_days': work_days,
            'standard_hours': standard_hours,
            'assigned_hours': assigned_hours,
            'recorded_hours': recorded_hours,
            'total_hours': total_hours,
            'load_rate': load_rate,
            'is_overloaded': load_rate > self.MAX_LOAD_RATE,
            'project_loads': list(project_loads.values())
        }

    def predict_project_resource_needs(
        self,
        project_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        预测项目资源需求

        Args:
            project_id: 项目ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            资源需求预测
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {'error': '项目不存在'}

        # 查询项目任务
        query = self.db.query(Task).filter(Task.project_id == project_id)

        if start_date:
            query = query.filter(Task.plan_start_date >= start_date)
        if end_date:
            query = query.filter(Task.plan_end_date <= end_date)

        tasks = query.all()

        # 按人员统计需求
        resource_needs = {}
        for task in tasks:
            if task.assignee_id:
                user_key = task.assignee_id
                if user_key not in resource_needs:
                    user = self.db.query(User).filter(User.id == user_key).first()
                    resource_needs[user_key] = {
                        'user_id': user_key,
                        'user_name': user.real_name or user.username if user else None,
                        'total_hours': 0,
                        'task_count': 0,
                        'tasks': []
                    }
                resource_needs[user_key]['total_hours'] += float(task.estimated_hours or 0)
                resource_needs[user_key]['task_count'] += 1
                resource_needs[user_key]['tasks'].append({
                    'task_id': task.id,
                    'task_name': task.task_name,
                    'estimated_hours': float(task.estimated_hours or 0),
                    'plan_start_date': str(task.plan_start_date) if task.plan_start_date else None,
                    'plan_end_date': str(task.plan_end_date) if task.plan_end_date else None
                })

        # 计算总需求
        total_hours = sum(r['total_hours'] for r in resource_needs.values())
        total_personnel = len(resource_needs)

        return {
            'project_id': project_id,
            'project_code': project.project_code,
            'project_name': project.project_name,
            'total_hours': total_hours,
            'total_personnel': total_personnel,
            'resource_needs': list(resource_needs.values()),
            'start_date': str(start_date) if start_date else None,
            'end_date': str(end_date) if end_date else None
        }

    def get_department_workload_stats(
        self,
        department_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取部门工作量统计

        Args:
            department_id: 部门ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            部门工作量统计
        """
        department = self.db.query(Department).filter(Department.id == department_id).first()
        if not department:
            return {'error': '部门不存在'}

        # 获取部门成员
        users = self.db.query(User).filter(User.department_id == department_id).all()
        user_ids = [u.id for u in users]

        if not user_ids:
            return {
                'department_id': department_id,
                'department_name': department.name,
                'total_users': 0,
                'total_hours': 0,
                'user_workloads': []
            }

        # 默认统计未来30天
        if not start_date:
            start_date = date.today()
        if not end_date:
            end_date = start_date + timedelta(days=30)

        # 计算每个用户的工作负载
        user_workloads = []
        for user_id in user_ids:
            workload = self.analyze_user_workload(user_id, start_date, end_date)
            if 'error' not in workload:
                user_workloads.append(workload)

        # 汇总统计
        total_hours = sum(w.get('total_hours', 0) for w in user_workloads)
        overloaded_users = [w for w in user_workloads if w.get('is_overloaded', False)]

        return {
            'department_id': department_id,
            'department_name': department.name,
            'total_users': len(user_workloads),
            'total_hours': total_hours,
            'overloaded_count': len(overloaded_users),
            'user_workloads': user_workloads,
            'start_date': str(start_date),
            'end_date': str(end_date)
        }

    def _calculate_work_days(self, start_date: date, end_date: date) -> int:
        """
        计算工作日数（简化处理，排除周末）

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            工作日数
        """
        work_days = 0
        current_date = start_date
        while current_date <= end_date:
            # 0=Monday, 6=Sunday
            if current_date.weekday() < 5:  # 周一到周五
                work_days += 1
            current_date += timedelta(days=1)
        return work_days
