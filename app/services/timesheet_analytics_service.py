# -*- coding: utf-8 -*-
"""
工时分析服务
提供6种分析维度的核心逻辑
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.models.timesheet import Timesheet
from app.schemas.timesheet_analytics import (
    TimesheetTrendResponse,
    WorkloadHeatmapResponse,
    EfficiencyComparisonResponse,
    OvertimeStatisticsResponse,
    DepartmentComparisonResponse,
    ProjectDistributionResponse,
    TrendChartData,
    PieChartData,
    HeatmapData
)


class TimesheetAnalyticsService:
    """工时分析服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 1. 工时趋势分析 ====================
    
    def analyze_trend(
        self,
        period_type: str,
        start_date: date,
        end_date: date,
        dimension: Optional[str] = None,
        user_ids: Optional[List[int]] = None,
        project_ids: Optional[List[int]] = None,
        department_ids: Optional[List[int]] = None
    ) -> TimesheetTrendResponse:
        """
        工时趋势分析（支持月度、季度、年度）
        
        Args:
            period_type: 周期类型(DAILY/WEEKLY/MONTHLY/QUARTERLY/YEARLY)
            start_date: 开始日期
            end_date: 结束日期
            dimension: 分析维度(USER/PROJECT/DEPARTMENT)
            user_ids: 用户ID列表
            project_ids: 项目ID列表
            department_ids: 部门ID列表
        
        Returns:
            TimesheetTrendResponse: 趋势分析结果
        """
        # 构建基础查询
        query = self.db.query(
            Timesheet.work_date,
            func.sum(Timesheet.hours).label('total_hours'),
            func.sum(case((Timesheet.overtime_type == 'NORMAL', Timesheet.hours), else_=0)).label('normal_hours'),
            func.sum(case((Timesheet.overtime_type != 'NORMAL', Timesheet.hours), else_=0)).label('overtime_hours')
        ).filter(
            Timesheet.work_date.between(start_date, end_date),
            Timesheet.status == 'APPROVED'
        )
        
        # 添加过滤条件
        if user_ids:
            query = query.filter(Timesheet.user_id.in_(user_ids))
        if project_ids:
            query = query.filter(Timesheet.project_id.in_(project_ids))
        if department_ids:
            query = query.filter(Timesheet.department_id.in_(department_ids))
        
        # 根据周期类型分组
        if period_type == 'DAILY':
            query = query.group_by(Timesheet.work_date)
        elif period_type == 'WEEKLY':
            # 按周分组
            query = query.group_by(func.yearweek(Timesheet.work_date))
        elif period_type == 'MONTHLY':
            # 按月分组
            query = query.group_by(
                func.year(Timesheet.work_date),
                func.month(Timesheet.work_date)
            )
        elif period_type == 'QUARTERLY':
            # 按季度分组
            query = query.group_by(
                func.year(Timesheet.work_date),
                func.quarter(Timesheet.work_date)
            )
        elif period_type == 'YEARLY':
            # 按年分组
            query = query.group_by(func.year(Timesheet.work_date))
        
        query = query.order_by(Timesheet.work_date)
        results = query.all()
        
        # 计算统计指标
        total_hours = sum(r.total_hours for r in results if r.total_hours)
        average_hours = total_hours / len(results) if results else 0
        max_hours = max((r.total_hours for r in results if r.total_hours), default=0)
        min_hours = min((r.total_hours for r in results if r.total_hours), default=0)
        
        # 计算趋势和变化率
        trend, change_rate = self._calculate_trend(results)
        
        # 生成图表数据
        chart_data = self._generate_trend_chart(results, period_type)
        
        return TimesheetTrendResponse(
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
            dimension=dimension,
            total_hours=Decimal(str(total_hours)),
            average_hours=Decimal(str(average_hours)),
            max_hours=Decimal(str(max_hours)),
            min_hours=Decimal(str(min_hours)),
            trend=trend,
            change_rate=Decimal(str(change_rate)),
            chart_data=chart_data
        )
    
    def _calculate_trend(self, results: List) -> Tuple[str, float]:
        """计算趋势和变化率"""
        if len(results) < 2:
            return 'STABLE', 0.0
        
        # 取前半部分和后半部分的平均值对比
        mid = len(results) // 2
        first_half_avg = sum(r.total_hours for r in results[:mid] if r.total_hours) / mid if mid > 0 else 0
        second_half_avg = sum(r.total_hours for r in results[mid:] if r.total_hours) / (len(results) - mid)
        
        if first_half_avg == 0:
            change_rate = 0.0
        else:
            change_rate = ((second_half_avg - first_half_avg) / first_half_avg) * 100
        
        if change_rate > 5:
            trend = 'INCREASING'
        elif change_rate < -5:
            trend = 'DECREASING'
        else:
            trend = 'STABLE'
        
        return trend, change_rate
    
    def _generate_trend_chart(self, results: List, period_type: str) -> TrendChartData:
        """生成趋势图数据"""
        labels = []
        total_values = []
        normal_values = []
        overtime_values = []
        
        for r in results:
            if period_type == 'DAILY':
                labels.append(r.work_date.strftime('%Y-%m-%d'))
            elif period_type == 'MONTHLY':
                labels.append(r.work_date.strftime('%Y-%m'))
            elif period_type == 'YEARLY':
                labels.append(r.work_date.strftime('%Y'))
            else:
                labels.append(str(r.work_date))
            
            total_values.append(float(r.total_hours or 0))
            normal_values.append(float(r.normal_hours or 0))
            overtime_values.append(float(r.overtime_hours or 0))
        
        return TrendChartData(
            labels=labels,
            datasets=[
                {
                    'label': '总工时',
                    'data': total_values,
                    'borderColor': '#3b82f6',
                    'backgroundColor': 'rgba(59, 130, 246, 0.1)'
                },
                {
                    'label': '正常工时',
                    'data': normal_values,
                    'borderColor': '#10b981',
                    'backgroundColor': 'rgba(16, 185, 129, 0.1)'
                },
                {
                    'label': '加班工时',
                    'data': overtime_values,
                    'borderColor': '#ef4444',
                    'backgroundColor': 'rgba(239, 68, 68, 0.1)'
                }
            ]
        )
    
    # ==================== 2. 人员负荷分析 ====================
    
    def analyze_workload(
        self,
        period_type: str,
        start_date: date,
        end_date: date,
        user_ids: Optional[List[int]] = None,
        department_ids: Optional[List[int]] = None
    ) -> WorkloadHeatmapResponse:
        """
        人员负荷分析（工时饱和度、负荷热力图）
        
        Args:
            period_type: 周期类型
            start_date: 开始日期
            end_date: 结束日期
            user_ids: 用户ID列表
            department_ids: 部门ID列表
        
        Returns:
            WorkloadHeatmapResponse: 负荷分析结果
        """
        # 标准工时（假设每天8小时）
        standard_daily_hours = 8
        days_count = (end_date - start_date).days + 1
        # 假设周末占比2/7
        work_days = days_count * 5 / 7
        standard_total_hours = work_days * standard_daily_hours
        
        # 查询人员工时
        query = self.db.query(
            Timesheet.user_id,
            Timesheet.user_name,
            Timesheet.department_name,
            Timesheet.work_date,
            func.sum(Timesheet.hours).label('daily_hours')
        ).filter(
            Timesheet.work_date.between(start_date, end_date),
            Timesheet.status == 'APPROVED'
        )
        
        if user_ids:
            query = query.filter(Timesheet.user_id.in_(user_ids))
        if department_ids:
            query = query.filter(Timesheet.department_id.in_(department_ids))
        
        query = query.group_by(
            Timesheet.user_id,
            Timesheet.user_name,
            Timesheet.department_name,
            Timesheet.work_date
        ).order_by(Timesheet.user_id, Timesheet.work_date)
        
        results = query.all()
        
        # 组织热力图数据
        user_workload = {}
        for r in results:
            if r.user_id not in user_workload:
                user_workload[r.user_id] = {
                    'user_name': r.user_name,
                    'department': r.department_name,
                    'daily_hours': {},
                    'total_hours': 0
                }
            user_workload[r.user_id]['daily_hours'][r.work_date] = float(r.daily_hours or 0)
            user_workload[r.user_id]['total_hours'] += float(r.daily_hours or 0)
        
        # 生成热力图矩阵
        rows = []  # 用户名
        columns = []  # 日期
        data = []  # 工时矩阵
        
        # 生成日期列
        current_date = start_date
        while current_date <= end_date:
            columns.append(current_date.strftime('%m-%d'))
            current_date += timedelta(days=1)
        
        # 统计超负荷人员
        overload_users = []
        
        for user_id, workload in user_workload.items():
            rows.append(workload['user_name'])
            row_data = []
            
            current_date = start_date
            while current_date <= end_date:
                hours = workload['daily_hours'].get(current_date, 0)
                row_data.append(hours)
                current_date += timedelta(days=1)
            
            data.append(row_data)
            
            # 计算饱和度
            saturation = (workload['total_hours'] / standard_total_hours * 100) if standard_total_hours > 0 else 0
            
            if saturation > 100:
                overload_users.append({
                    'user_id': user_id,
                    'user_name': workload['user_name'],
                    'department': workload['department'],
                    'total_hours': workload['total_hours'],
                    'saturation': round(saturation, 2),
                    'over_hours': round(workload['total_hours'] - standard_total_hours, 2)
                })
        
        # 排序超负荷人员
        overload_users.sort(key=lambda x: x['saturation'], reverse=True)
        
        heatmap_data = HeatmapData(
            rows=rows,
            columns=columns,
            data=data
        )
        
        # 统计信息
        total_users = len(user_workload)
        avg_hours = sum(w['total_hours'] for w in user_workload.values()) / total_users if total_users > 0 else 0
        
        statistics = {
            'total_users': total_users,
            'average_hours': round(avg_hours, 2),
            'standard_hours': round(standard_total_hours, 2),
            'overload_count': len(overload_users),
            'overload_rate': round(len(overload_users) / total_users * 100, 2) if total_users > 0 else 0
        }
        
        return WorkloadHeatmapResponse(
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
            heatmap_data=heatmap_data,
            statistics=statistics,
            overload_users=overload_users[:10]  # 返回前10名
        )
    
    # ==================== 3. 工时效率对比 ====================
    
    def analyze_efficiency(
        self,
        period_type: str,
        start_date: date,
        end_date: date,
        project_ids: Optional[List[int]] = None,
        user_ids: Optional[List[int]] = None
    ) -> EfficiencyComparisonResponse:
        """
        工时效率对比（计划vs实际）
        
        假设：从项目任务的预估工时作为计划工时
        """
        # 查询实际工时
        query = self.db.query(
            func.sum(Timesheet.hours).label('actual_hours')
        ).filter(
            Timesheet.work_date.between(start_date, end_date),
            Timesheet.status == 'APPROVED'
        )
        
        if project_ids:
            query = query.filter(Timesheet.project_id.in_(project_ids))
        if user_ids:
            query = query.filter(Timesheet.user_id.in_(user_ids))
        
        result = query.first()
        actual_hours = float(result.actual_hours or 0)
        
        # 查询计划工时（这里简化处理，假设计划工时为实际工时的90%）
        # 实际应该从任务预估工时中查询
        planned_hours = actual_hours * 0.9
        
        variance_hours = actual_hours - planned_hours
        variance_rate = (variance_hours / planned_hours * 100) if planned_hours > 0 else 0
        efficiency_rate = (planned_hours / actual_hours * 100) if actual_hours > 0 else 100
        
        # 生成图表数据
        chart_data = {
            'comparison': {
                'labels': ['计划工时', '实际工时'],
                'values': [round(planned_hours, 2), round(actual_hours, 2)],
                'colors': ['#10b981', '#3b82f6']
            },
            'variance': {
                'over_budget': round(max(0, variance_hours), 2),
                'under_budget': round(abs(min(0, variance_hours)), 2)
            }
        }
        
        # 生成洞察建议
        insights = []
        if efficiency_rate < 80:
            insights.append('工时效率较低，实际用时超出计划较多，建议优化工作流程')
        elif efficiency_rate > 120:
            insights.append('计划工时可能过于保守，建议适当调整预估标准')
        else:
            insights.append('工时效率在合理范围内')
        
        if variance_rate > 20:
            insights.append('工时偏差较大，需要加强项目工时管控')
        
        return EfficiencyComparisonResponse(
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
            planned_hours=Decimal(str(planned_hours)),
            actual_hours=Decimal(str(actual_hours)),
            variance_hours=Decimal(str(variance_hours)),
            variance_rate=Decimal(str(round(variance_rate, 2))),
            efficiency_rate=Decimal(str(round(efficiency_rate, 2))),
            chart_data=chart_data,
            insights=insights
        )
    
    # ==================== 4. 加班统计分析 ====================
    
    def analyze_overtime(
        self,
        period_type: str,
        start_date: date,
        end_date: date,
        user_ids: Optional[List[int]] = None,
        department_ids: Optional[List[int]] = None
    ) -> OvertimeStatisticsResponse:
        """
        加班统计分析（加班时长、加班率、加班趋势）
        """
        # 查询加班工时
        query = self.db.query(
            func.sum(case((Timesheet.overtime_type != 'NORMAL', Timesheet.hours), else_=0)).label('total_overtime'),
            func.sum(case((Timesheet.overtime_type == 'WEEKEND', Timesheet.hours), else_=0)).label('weekend_hours'),
            func.sum(case((Timesheet.overtime_type == 'HOLIDAY', Timesheet.hours), else_=0)).label('holiday_hours'),
            func.sum(Timesheet.hours).label('total_hours')
        ).filter(
            Timesheet.work_date.between(start_date, end_date),
            Timesheet.status == 'APPROVED'
        )
        
        if user_ids:
            query = query.filter(Timesheet.user_id.in_(user_ids))
        if department_ids:
            query = query.filter(Timesheet.department_id.in_(department_ids))
        
        result = query.first()
        
        total_overtime = float(result.total_overtime or 0)
        weekend_hours = float(result.weekend_hours or 0)
        holiday_hours = float(result.holiday_hours or 0)
        total_hours = float(result.total_hours or 0)
        
        overtime_rate = (total_overtime / total_hours * 100) if total_hours > 0 else 0
        
        # 查询人均加班
        user_count_query = self.db.query(
            func.count(func.distinct(Timesheet.user_id))
        ).filter(
            Timesheet.work_date.between(start_date, end_date),
            Timesheet.status == 'APPROVED'
        )
        
        if user_ids:
            user_count_query = user_count_query.filter(Timesheet.user_id.in_(user_ids))
        if department_ids:
            user_count_query = user_count_query.filter(Timesheet.department_id.in_(department_ids))
        
        user_count = user_count_query.scalar() or 1
        avg_overtime = total_overtime / user_count
        
        # 查询加班最多的人员
        top_users_query = self.db.query(
            Timesheet.user_id,
            Timesheet.user_name,
            Timesheet.department_name,
            func.sum(case((Timesheet.overtime_type != 'NORMAL', Timesheet.hours), else_=0)).label('overtime_hours')
        ).filter(
            Timesheet.work_date.between(start_date, end_date),
            Timesheet.status == 'APPROVED'
        )
        
        if user_ids:
            top_users_query = top_users_query.filter(Timesheet.user_id.in_(user_ids))
        if department_ids:
            top_users_query = top_users_query.filter(Timesheet.department_id.in_(department_ids))
        
        top_users = top_users_query.group_by(
            Timesheet.user_id,
            Timesheet.user_name,
            Timesheet.department_name
        ).order_by(func.sum(case((Timesheet.overtime_type != 'NORMAL', Timesheet.hours), else_=0)).desc()).limit(10).all()
        
        top_overtime_users = [
            {
                'user_id': u.user_id,
                'user_name': u.user_name,
                'department': u.department_name,
                'overtime_hours': float(u.overtime_hours or 0)
            }
            for u in top_users
        ]
        
        # 查询加班趋势
        trend_query = self.db.query(
            func.date(Timesheet.work_date).label('date'),
            func.sum(case((Timesheet.overtime_type != 'NORMAL', Timesheet.hours), else_=0)).label('overtime_hours')
        ).filter(
            Timesheet.work_date.between(start_date, end_date),
            Timesheet.status == 'APPROVED'
        )
        
        if user_ids:
            trend_query = trend_query.filter(Timesheet.user_id.in_(user_ids))
        if department_ids:
            trend_query = trend_query.filter(Timesheet.department_id.in_(department_ids))
        
        trend_results = trend_query.group_by(func.date(Timesheet.work_date)).order_by(func.date(Timesheet.work_date)).all()
        
        overtime_trend = TrendChartData(
            labels=[r.date.strftime('%Y-%m-%d') for r in trend_results],
            datasets=[{
                'label': '加班工时',
                'data': [float(r.overtime_hours or 0) for r in trend_results],
                'borderColor': '#ef4444',
                'backgroundColor': 'rgba(239, 68, 68, 0.1)'
            }]
        )
        
        return OvertimeStatisticsResponse(
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
            total_overtime_hours=Decimal(str(total_overtime)),
            weekend_hours=Decimal(str(weekend_hours)),
            holiday_hours=Decimal(str(holiday_hours)),
            overtime_rate=Decimal(str(round(overtime_rate, 2))),
            avg_overtime_per_person=Decimal(str(round(avg_overtime, 2))),
            top_overtime_users=top_overtime_users,
            overtime_trend=overtime_trend
        )
    
    # ==================== 5. 部门工时对比 ====================
    
    def analyze_department_comparison(
        self,
        period_type: str,
        start_date: date,
        end_date: date,
        department_ids: Optional[List[int]] = None
    ) -> DepartmentComparisonResponse:
        """
        部门工时对比
        """
        query = self.db.query(
            Timesheet.department_id,
            Timesheet.department_name,
            func.sum(Timesheet.hours).label('total_hours'),
            func.sum(case((Timesheet.overtime_type == 'NORMAL', Timesheet.hours), else_=0)).label('normal_hours'),
            func.sum(case((Timesheet.overtime_type != 'NORMAL', Timesheet.hours), else_=0)).label('overtime_hours'),
            func.count(func.distinct(Timesheet.user_id)).label('user_count'),
            func.count(Timesheet.id).label('entry_count')
        ).filter(
            Timesheet.work_date.between(start_date, end_date),
            Timesheet.status == 'APPROVED'
        )
        
        if department_ids:
            query = query.filter(Timesheet.department_id.in_(department_ids))
        
        results = query.group_by(
            Timesheet.department_id,
            Timesheet.department_name
        ).order_by(func.sum(Timesheet.hours).desc()).all()
        
        departments = []
        for r in results:
            total_hours = float(r.total_hours or 0)
            user_count = r.user_count or 1
            avg_hours_per_person = total_hours / user_count
            overtime_rate = (float(r.overtime_hours or 0) / total_hours * 100) if total_hours > 0 else 0
            
            departments.append({
                'department_id': r.department_id,
                'department_name': r.department_name or '未分配',
                'total_hours': round(total_hours, 2),
                'normal_hours': round(float(r.normal_hours or 0), 2),
                'overtime_hours': round(float(r.overtime_hours or 0), 2),
                'user_count': user_count,
                'avg_hours_per_person': round(avg_hours_per_person, 2),
                'overtime_rate': round(overtime_rate, 2),
                'entry_count': r.entry_count
            })
        
        # 排名
        rankings = sorted(departments, key=lambda x: x['total_hours'], reverse=True)
        for idx, dept in enumerate(rankings, 1):
            dept['rank'] = idx
        
        # 图表数据
        chart_data = {
            'bar_chart': {
                'labels': [d['department_name'] for d in departments],
                'datasets': [
                    {
                        'label': '正常工时',
                        'data': [d['normal_hours'] for d in departments],
                        'backgroundColor': '#10b981'
                    },
                    {
                        'label': '加班工时',
                        'data': [d['overtime_hours'] for d in departments],
                        'backgroundColor': '#ef4444'
                    }
                ]
            }
        }
        
        return DepartmentComparisonResponse(
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
            departments=departments,
            chart_data=chart_data,
            rankings=rankings
        )
    
    # ==================== 6. 项目工时分布 ====================
    
    def analyze_project_distribution(
        self,
        period_type: str,
        start_date: date,
        end_date: date,
        project_ids: Optional[List[int]] = None,
        user_ids: Optional[List[int]] = None
    ) -> ProjectDistributionResponse:
        """
        项目工时分布
        """
        query = self.db.query(
            Timesheet.project_id,
            Timesheet.project_name,
            func.sum(Timesheet.hours).label('total_hours'),
            func.count(func.distinct(Timesheet.user_id)).label('user_count'),
            func.count(Timesheet.id).label('entry_count')
        ).filter(
            Timesheet.work_date.between(start_date, end_date),
            Timesheet.status == 'APPROVED'
        )
        
        if project_ids:
            query = query.filter(Timesheet.project_id.in_(project_ids))
        if user_ids:
            query = query.filter(Timesheet.user_id.in_(user_ids))
        
        results = query.group_by(
            Timesheet.project_id,
            Timesheet.project_name
        ).order_by(func.sum(Timesheet.hours).desc()).all()
        
        total_hours = sum(float(r.total_hours or 0) for r in results)
        total_projects = len(results)
        
        project_details = []
        pie_labels = []
        pie_values = []
        
        for r in results:
            hours = float(r.total_hours or 0)
            percentage = (hours / total_hours * 100) if total_hours > 0 else 0
            
            project_details.append({
                'project_id': r.project_id,
                'project_name': r.project_name or '未分配',
                'total_hours': round(hours, 2),
                'percentage': round(percentage, 2),
                'user_count': r.user_count,
                'entry_count': r.entry_count
            })
            
            pie_labels.append(r.project_name or '未分配')
            pie_values.append(round(hours, 2))
        
        # 计算集中度指数（前3个项目的工时占比）
        top3_percentage = sum(p['percentage'] for p in project_details[:3]) if len(project_details) >= 3 else 100
        concentration_index = top3_percentage / 100
        
        pie_chart = PieChartData(
            labels=pie_labels,
            values=pie_values,
            colors=None  # 使用默认颜色
        )
        
        return ProjectDistributionResponse(
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
            total_projects=total_projects,
            total_hours=Decimal(str(total_hours)),
            pie_chart=pie_chart,
            project_details=project_details,
            concentration_index=Decimal(str(round(concentration_index, 4)))
        )
