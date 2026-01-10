# -*- coding: utf-8 -*-
"""
成本分析服务
负责项目成本预测、成本超支预警、成本对比分析
"""

from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.timesheet import Timesheet
from app.models.project import Project, ProjectCost
from app.models.user import User
from app.services.hourly_rate_service import HourlyRateService
from app.services.labor_cost_service import LaborCostService


class CostAnalysisService:
    """成本分析服务"""
    
    # 预警阈值
    WARNING_THRESHOLD = 80  # 警告阈值（%）
    CRITICAL_THRESHOLD = 100  # 严重阈值（%）
    
    def __init__(self, db: Session):
        self.db = db
    
    def predict_project_cost(
        self,
        project_id: int,
        based_on_history: bool = True
    ) -> Dict[str, Any]:
        """
        预测项目成本（基于历史工时数据）
        
        Args:
            project_id: 项目ID
            based_on_history: 是否基于历史数据预测
            
        Returns:
            成本预测结果
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {'error': '项目不存在'}
        
        # 获取项目预算
        budget = project.budget_amount or 0
        
        # 获取已发生的成本
        actual_cost = project.actual_cost or 0
        
        # 获取已记录的工时
        timesheets = self.db.query(Timesheet).filter(
            Timesheet.project_id == project_id,
            Timesheet.status == 'APPROVED'
        ).all()
        
        recorded_hours = sum(float(ts.hours or 0) for ts in timesheets)
        
        # 计算已发生的工时成本
        recorded_labor_cost = 0
        for ts in timesheets:
            hourly_rate = HourlyRateService.get_user_hourly_rate(self.db, ts.user_id, ts.work_date)
            recorded_labor_cost += float(ts.hours or 0) * float(hourly_rate)
        
        # 获取项目任务（预估工时）
        from app.models.progress import Task
        tasks = self.db.query(Task).filter(
            Task.project_id == project_id,
            Task.status.in_(['PENDING', 'IN_PROGRESS'])
        ).all()
        
        remaining_hours = sum(float(task.estimated_hours or 0) for task in tasks)
        
        # 预测剩余成本（基于平均时薪）
        if recorded_hours > 0:
            avg_hourly_rate = recorded_labor_cost / recorded_hours
        else:
            # 如果没有历史数据，使用默认时薪
            avg_hourly_rate = 100
        
        predicted_remaining_cost = remaining_hours * avg_hourly_rate
        predicted_total_cost = actual_cost + predicted_remaining_cost
        
        # 计算成本偏差
        cost_variance = predicted_total_cost - budget if budget > 0 else 0
        cost_variance_rate = (cost_variance / budget * 100) if budget > 0 else 0
        
        return {
            'project_id': project_id,
            'project_code': project.project_code,
            'project_name': project.project_name,
            'budget': float(budget),
            'actual_cost': float(actual_cost),
            'recorded_hours': recorded_hours,
            'recorded_labor_cost': recorded_labor_cost,
            'remaining_hours': remaining_hours,
            'predicted_remaining_cost': float(predicted_remaining_cost),
            'predicted_total_cost': float(predicted_total_cost),
            'cost_variance': float(cost_variance),
            'cost_variance_rate': cost_variance_rate,
            'is_over_budget': predicted_total_cost > budget if budget > 0 else False
        }
    
    def check_cost_overrun_alerts(
        self,
        project_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        检查成本超支预警
        
        Args:
            project_id: 项目ID（可选，如果不提供则检查所有项目）
            
        Returns:
            预警列表
        """
        query = self.db.query(Project).filter(Project.is_active == True)
        
        if project_id:
            query = query.filter(Project.id == project_id)
        
        projects = query.all()
        
        alerts = []
        
        for project in projects:
            if not project.budget_amount or project.budget_amount <= 0:
                continue  # 没有预算的项目跳过
            
            budget = float(project.budget_amount)
            actual_cost = float(project.actual_cost or 0)
            
            cost_rate = (actual_cost / budget * 100) if budget > 0 else 0
            
            # 检查是否超过阈值
            if cost_rate >= self.CRITICAL_THRESHOLD:
                alert_level = 'CRITICAL'
            elif cost_rate >= self.WARNING_THRESHOLD:
                alert_level = 'WARNING'
            else:
                continue  # 未超过阈值，不生成预警
            
            # 预测总成本
            prediction = self.predict_project_cost(project.id)
            predicted_total = prediction.get('predicted_total_cost', actual_cost)
            
            alerts.append({
                'project_id': project.id,
                'project_code': project.project_code,
                'project_name': project.project_name,
                'budget': budget,
                'actual_cost': actual_cost,
                'cost_rate': cost_rate,
                'predicted_total_cost': predicted_total,
                'alert_level': alert_level,
                'message': f"项目{project.project_code}成本超支预警：实际成本{actual_cost:.2f}元，预算{budget:.2f}元，超支率{cost_rate:.1f}%"
            })
        
        return alerts
    
    def compare_project_costs(
        self,
        project_ids: List[int]
    ) -> Dict[str, Any]:
        """
        对比不同项目的工时成本
        
        Args:
            project_ids: 项目ID列表
            
        Returns:
            成本对比分析
        """
        projects = self.db.query(Project).filter(Project.id.in_(project_ids)).all()
        
        if not projects:
            return {'error': '项目不存在'}
        
        comparison_data = []
        
        for project in projects:
            # 获取项目工时成本
            timesheets = self.db.query(Timesheet).filter(
                Timesheet.project_id == project.id,
                Timesheet.status == 'APPROVED'
            ).all()
            
            total_hours = sum(float(ts.hours or 0) for ts in timesheets)
            total_cost = 0
            
            for ts in timesheets:
                hourly_rate = HourlyRateService.get_user_hourly_rate(self.db, ts.user_id, ts.work_date)
                total_cost += float(ts.hours or 0) * float(hourly_rate)
            
            # 计算平均时薪
            avg_hourly_rate = (total_cost / total_hours) if total_hours > 0 else 0
            
            # 计算人均工时
            user_count = len(set(ts.user_id for ts in timesheets))
            avg_hours_per_person = (total_hours / user_count) if user_count > 0 else 0
            
            comparison_data.append({
                'project_id': project.id,
                'project_code': project.project_code,
                'project_name': project.project_name,
                'total_hours': total_hours,
                'total_cost': total_cost,
                'avg_hourly_rate': avg_hourly_rate,
                'personnel_count': user_count,
                'avg_hours_per_person': avg_hours_per_person,
                'budget': float(project.budget_amount or 0),
                'actual_cost': float(project.actual_cost or 0)
            })
        
        # 计算平均值
        avg_cost = sum(d['total_cost'] for d in comparison_data) / len(comparison_data) if comparison_data else 0
        avg_hours = sum(d['total_hours'] for d in comparison_data) / len(comparison_data) if comparison_data else 0
        
        return {
            'projects': comparison_data,
            'summary': {
                'project_count': len(comparison_data),
                'avg_total_cost': avg_cost,
                'avg_total_hours': avg_hours,
                'min_cost': min(d['total_cost'] for d in comparison_data) if comparison_data else 0,
                'max_cost': max(d['total_cost'] for d in comparison_data) if comparison_data else 0
            }
        }
    
    def analyze_cost_trend(
        self,
        project_id: int,
        months: int = 6
    ) -> Dict[str, Any]:
        """
        分析项目成本趋势
        
        Args:
            project_id: 项目ID
            months: 分析月数（默认6个月）
            
        Returns:
            成本趋势分析
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {'error': '项目不存在'}
        
        # 计算开始日期
        end_date = date.today()
        start_date = date(end_date.year, end_date.month, 1) - timedelta(days=months * 30)
        
        # 按月统计成本
        monthly_costs = {}
        current = start_date
        
        while current <= end_date:
            month_key = current.strftime('%Y-%m')
            monthly_costs[month_key] = {
                'month': month_key,
                'hours': 0,
                'cost': 0,
                'personnel_count': 0
            }
            
            # 计算下个月
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)
        
        # 查询工时记录
        timesheets = self.db.query(Timesheet).filter(
            Timesheet.project_id == project_id,
            Timesheet.status == 'APPROVED',
            Timesheet.work_date >= start_date,
            Timesheet.work_date <= end_date
        ).all()
        
        # 按月统计
        for ts in timesheets:
            month_key = ts.work_date.strftime('%Y-%m')
            if month_key in monthly_costs:
                monthly_costs[month_key]['hours'] += float(ts.hours or 0)
                hourly_rate = HourlyRateService.get_user_hourly_rate(self.db, ts.user_id, ts.work_date)
                monthly_costs[month_key]['cost'] += float(ts.hours or 0) * float(hourly_rate)
                monthly_costs[month_key]['personnel_count'] = len(set(
                    t.user_id for t in timesheets 
                    if t.work_date.strftime('%Y-%m') == month_key
                ))
        
        # 转换为列表并排序
        trend_data = sorted(monthly_costs.values(), key=lambda x: x['month'])
        
        return {
            'project_id': project_id,
            'project_code': project.project_code,
            'project_name': project.project_name,
            'start_date': str(start_date),
            'end_date': str(end_date),
            'monthly_trend': trend_data,
            'total_cost': sum(d['cost'] for d in trend_data),
            'total_hours': sum(d['hours'] for d in trend_data)
        }
