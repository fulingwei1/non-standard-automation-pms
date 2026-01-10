# -*- coding: utf-8 -*-
"""
绩效统计服务
负责统计工程师的工作量、项目贡献度、技能评估等
"""

from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.timesheet import Timesheet
from app.models.user import User
from app.models.project import Project
from app.models.organization import Department


class PerformanceStatsService:
    """绩效统计服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_performance_stats(
        self,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取用户绩效统计
        
        Args:
            user_id: 用户ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            
        Returns:
            绩效统计数据
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {'error': '用户不存在'}
        
        query = self.db.query(Timesheet).filter(
            Timesheet.user_id == user_id,
            Timesheet.status == 'APPROVED'
        )
        
        if start_date:
            query = query.filter(Timesheet.work_date >= start_date)
        if end_date:
            query = query.filter(Timesheet.work_date <= end_date)
        
        timesheets = query.all()
        
        # 总工时
        total_hours = sum(float(ts.hours or 0) for ts in timesheets)
        
        # 按项目统计贡献度
        project_contributions = {}
        for ts in timesheets:
            if ts.project_id:
                project_key = ts.project_id
                if project_key not in project_contributions:
                    project = self.db.query(Project).filter(Project.id == project_key).first()
                    project_contributions[project_key] = {
                        'project_id': project_key,
                        'project_code': project.project_code if project else None,
                        'project_name': project.project_name if project else None,
                        'total_hours': 0,
                        'contribution_rate': 0
                    }
                project_contributions[project_key]['total_hours'] += float(ts.hours or 0)
        
        # 计算每个项目的贡献度（需要获取项目总工时）
        for project_id, contribution in project_contributions.items():
            project_total = self.db.query(func.sum(Timesheet.hours)).filter(
                Timesheet.project_id == project_id,
                Timesheet.status == 'APPROVED'
            ).scalar() or 0
            
            if project_total > 0:
                contribution['contribution_rate'] = (contribution['total_hours'] / float(project_total)) * 100
        
        # 按工作类型统计（用于技能评估）
        work_type_stats = {}
        for ts in timesheets:
            work_type = ts.overtime_type or 'NORMAL'
            if work_type not in work_type_stats:
                work_type_stats[work_type] = 0
            work_type_stats[work_type] += float(ts.hours or 0)
        
        # 按月份统计
        monthly_stats = {}
        for ts in timesheets:
            month_key = ts.work_date.strftime('%Y-%m')
            if month_key not in monthly_stats:
                monthly_stats[month_key] = 0
            monthly_stats[month_key] += float(ts.hours or 0)
        
        return {
            'user_id': user_id,
            'user_name': user.real_name or user.username,
            'total_hours': total_hours,
            'project_count': len(project_contributions),
            'project_contributions': list(project_contributions.values()),
            'work_type_distribution': work_type_stats,
            'monthly_distribution': monthly_stats,
            'start_date': str(start_date) if start_date else None,
            'end_date': str(end_date) if end_date else None
        }
    
    def get_department_performance_stats(
        self,
        department_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        获取部门绩效统计
        
        Args:
            department_id: 部门ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            
        Returns:
            部门绩效统计数据
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
                'total_hours': 0,
                'user_count': 0,
                'user_stats': []
            }
        
        query = self.db.query(Timesheet).filter(
            Timesheet.user_id.in_(user_ids),
            Timesheet.status == 'APPROVED'
        )
        
        if start_date:
            query = query.filter(Timesheet.work_date >= start_date)
        if end_date:
            query = query.filter(Timesheet.work_date <= end_date)
        
        timesheets = query.all()
        
        # 按用户统计
        user_stats = {}
        for ts in timesheets:
            user_key = ts.user_id
            if user_key not in user_stats:
                user = self.db.query(User).filter(User.id == user_key).first()
                user_stats[user_key] = {
                    'user_id': user_key,
                    'user_name': user.real_name or user.username if user else None,
                    'total_hours': 0,
                    'project_count': set(),
                    'work_days': set()
                }
            user_stats[user_key]['total_hours'] += float(ts.hours or 0)
            if ts.project_id:
                user_stats[user_key]['project_count'].add(ts.project_id)
            user_stats[user_key]['work_days'].add(ts.work_date)
        
        # 转换set为数量
        for user_key in user_stats:
            user_stats[user_key]['project_count'] = len(user_stats[user_key]['project_count'])
            user_stats[user_key]['work_days'] = len(user_stats[user_key]['work_days'])
        
        total_hours = sum(float(ts.hours or 0) for ts in timesheets)
        
        return {
            'department_id': department_id,
            'department_name': department.name,
            'total_hours': total_hours,
            'user_count': len(user_stats),
            'user_stats': list(user_stats.values())
        }
    
    def analyze_skill_expertise(
        self,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        分析用户技能专长（基于工时分布）
        
        Args:
            user_id: 用户ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            
        Returns:
            技能分析结果
        """
        query = self.db.query(Timesheet).filter(
            Timesheet.user_id == user_id,
            Timesheet.status == 'APPROVED'
        )
        
        if start_date:
            query = query.filter(Timesheet.work_date >= start_date)
        if end_date:
            query = query.filter(Timesheet.work_date <= end_date)
        
        timesheets = query.all()
        
        # 按项目类型/阶段分析（这里简化处理，实际可以根据项目属性分析）
        # 按工作内容关键词分析（简化处理）
        skill_keywords = {
            '机械': ['机械', '设计', '图纸', 'CAD', 'SolidWorks'],
            '电气': ['电气', 'PLC', '电路', '接线', '程序'],
            '测试': ['测试', '调试', '验证', 'FAT', 'SAT'],
            '研发': ['研发', '开发', '算法', '软件']
        }
        
        skill_hours = {}
        for keyword, terms in skill_keywords.items():
            skill_hours[keyword] = 0
            for ts in timesheets:
                content = (ts.work_content or '').lower()
                if any(term.lower() in content for term in terms):
                    skill_hours[keyword] += float(ts.hours or 0)
        
        total_hours = sum(float(ts.hours or 0) for ts in timesheets)
        
        # 计算技能占比
        skill_distribution = {}
        for skill, hours in skill_hours.items():
            if total_hours > 0:
                skill_distribution[skill] = {
                    'hours': hours,
                    'percentage': (hours / total_hours) * 100
                }
            else:
                skill_distribution[skill] = {
                    'hours': 0,
                    'percentage': 0
                }
        
        # 找出主要技能（占比最高的）
        primary_skill = max(skill_distribution.items(), key=lambda x: x[1]['percentage']) if skill_distribution else None
        
        return {
            'user_id': user_id,
            'total_hours': total_hours,
            'skill_distribution': skill_distribution,
            'primary_skill': primary_skill[0] if primary_skill else None,
            'primary_skill_percentage': primary_skill[1]['percentage'] if primary_skill else 0
        }
