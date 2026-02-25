# -*- coding: utf-8 -*-
"""
工时预测服务
实现3种预测方法：历史平均法、线性回归、趋势预测
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session
import math
import numpy as np

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not installed, linear regression will use fallback method")

from app.models.timesheet import Timesheet
from app.models.project import Project
from app.schemas.timesheet_analytics import (
    ProjectForecastResponse,
    CompletionForecastResponse,
    WorkloadAlertResponse,
    GapAnalysisResponse,
    TrendChartData
)


class TimesheetForecastService:
    """工时预测服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 1. 项目工时预测 ====================
    
    def forecast_project_hours(
        self,
        project_id: Optional[int] = None,
        project_name: Optional[str] = None,
        project_type: Optional[str] = None,
        complexity: Optional[str] = 'MEDIUM',
        team_size: Optional[int] = 5,
        duration_days: Optional[int] = 30,
        forecast_method: str = 'HISTORICAL_AVERAGE',
        similar_project_ids: Optional[List[int]] = None
    ) -> ProjectForecastResponse:
        """
        预测项目工时
        
        支持3种方法：
        1. HISTORICAL_AVERAGE - 历史平均法（基于相似项目）
        2. LINEAR_REGRESSION - 线性回归（基于项目特征）
        3. TREND_FORECAST - 趋势预测（基于历史趋势）
        """
        if forecast_method == 'HISTORICAL_AVERAGE':
            return self._forecast_by_historical_average(
                project_id, project_name, project_type, complexity,
                team_size, duration_days, similar_project_ids
            )
        elif forecast_method == 'LINEAR_REGRESSION':
            return self._forecast_by_linear_regression(
                project_id, project_name, project_type, complexity,
                team_size, duration_days
            )
        elif forecast_method == 'TREND_FORECAST':
            return self._forecast_by_trend(
                project_id, project_name, project_type, complexity,
                team_size, duration_days
            )
        else:
            raise ValueError(f"Unsupported forecast method: {forecast_method}")
    
    def _forecast_by_historical_average(
        self,
        project_id: Optional[int],
        project_name: str,
        project_type: Optional[str],
        complexity: str,
        team_size: int,
        duration_days: int,
        similar_project_ids: Optional[List[int]]
    ) -> ProjectForecastResponse:
        """方法1：历史平均法（相似项目平均工时）"""
        
        # 查找相似项目
        similar_projects = []
        
        if similar_project_ids:
            # 使用指定的相似项目
            similar_query = self.db.query(
                Timesheet.project_id,
                Timesheet.project_name,
                func.sum(Timesheet.hours).label('total_hours')
            ).filter(
                Timesheet.project_id.in_(similar_project_ids),
                Timesheet.status == 'APPROVED'
            ).group_by(Timesheet.project_id, Timesheet.project_name)
        else:
            # 自动查找相似项目（基于项目类型、复杂度等）
            # 这里简化处理，查询最近完成的项目
            similar_query = self.db.query(
                Timesheet.project_id,
                Timesheet.project_name,
                func.sum(Timesheet.hours).label('total_hours')
            ).filter(
                Timesheet.status == 'APPROVED',
                Timesheet.project_id.isnot(None)
            ).group_by(
                Timesheet.project_id,
                Timesheet.project_name
            ).limit(10)
        
        similar_results = similar_query.all()
        
        if not similar_results:
            # 如果没有历史数据，使用默认估算
            # 假设：中等复杂度项目，每人每天8小时
            base_hours_per_person_per_day = 8
            complexity_factor = {'LOW': 0.7, 'MEDIUM': 1.0, 'HIGH': 1.3}.get(complexity, 1.0)
            predicted_hours = team_size * duration_days * base_hours_per_person_per_day * complexity_factor
            confidence_level = 50  # 低置信度
            similar_projects = []
        else:
            # 计算相似项目的平均工时
            hours_list = [float(r.total_hours) for r in similar_results]
            predicted_hours = np.mean(hours_list)
            if math.isnan(float(predicted_hours)):
                predicted_hours = 0.0
            confidence_level = 70  # 中等置信度
            
            # 根据团队规模和周期调整
            # 假设相似项目的平均团队规模和周期
            avg_team_size = 5
            avg_duration = 30
            scale_factor = (team_size / avg_team_size) * (duration_days / avg_duration)
            predicted_hours *= scale_factor
            
            # 复杂度调整
            complexity_factor = {'LOW': 0.8, 'MEDIUM': 1.0, 'HIGH': 1.2}.get(complexity, 1.0)
            predicted_hours *= complexity_factor
            
            # 记录相似项目
            for r in similar_results:
                similar_projects.append({
                    'project_id': r.project_id,
                    'project_name': r.project_name,
                    'total_hours': float(r.total_hours),
                    'similarity_score': 0.85  # 简化处理
                })
        
        # 计算预测范围（±20%）
        predicted_hours_min = predicted_hours * 0.8
        predicted_hours_max = predicted_hours * 1.2
        
        # 生成预测编号
        forecast_no = f'FC-{datetime.now().strftime("%Y%m%d%H%M%S")}'
        
        # 算法参数
        algorithm_params = {
            'method': 'HISTORICAL_AVERAGE',
            'similar_projects_count': len(similar_projects),
            'complexity_factor': complexity_factor,
            'scale_factor': scale_factor if similar_results else 1.0
        }
        
        # 建议
        recommendations = []
        if predicted_hours > 1000:
            recommendations.append('项目工时较大，建议分阶段实施')
        if team_size > 10:
            recommendations.append('团队规模较大，注意协调沟通成本')
        if complexity == 'HIGH':
            recommendations.append('高复杂度项目，建议预留缓冲时间')
        
        return ProjectForecastResponse(
            forecast_no=forecast_no,
            project_id=project_id,
            project_name=project_name or '新项目',
            forecast_method='HISTORICAL_AVERAGE',
            predicted_hours=Decimal(str(round(float(predicted_hours) if not (predicted_hours != predicted_hours) else 0.0, 2))),
            predicted_hours_min=Decimal(str(round(predicted_hours_min, 2))),
            predicted_hours_max=Decimal(str(round(predicted_hours_max, 2))),
            confidence_level=Decimal(str(confidence_level)),
            historical_projects_count=len(similar_projects),
            similar_projects=similar_projects,
            algorithm_params=algorithm_params,
            recommendations=recommendations
        )
    
    def _forecast_by_linear_regression(
        self,
        project_id: Optional[int],
        project_name: str,
        project_type: Optional[str],
        complexity: str,
        team_size: int,
        duration_days: int
    ) -> ProjectForecastResponse:
        """方法2：线性回归（基于项目特征）"""
        
        # 查询历史项目数据作为训练集
        historical_data = self.db.query(
            Timesheet.project_id,
            Timesheet.project_name,
            func.sum(Timesheet.hours).label('total_hours'),
            func.count(func.distinct(Timesheet.user_id)).label('team_size'),
            func.datediff(func.max(Timesheet.work_date), func.min(Timesheet.work_date)).label('duration')
        ).filter(
            Timesheet.status == 'APPROVED',
            Timesheet.project_id.isnot(None)
        ).group_by(
            Timesheet.project_id,
            Timesheet.project_name
        ).having(
            func.count(func.distinct(Timesheet.user_id)) > 0
        ).all()
        
        if len(historical_data) < 3:
            # 数据不足，退回到历史平均法
            return self._forecast_by_historical_average(
                project_id, project_name, project_type, complexity,
                team_size, duration_days, None
            )
        
        # 准备训练数据
        X = []  # 特征：[team_size, duration, complexity_encoded]
        y = []  # 目标：total_hours
        
        complexity_encoding = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}
        
        for data in historical_data:
            if data.team_size and data.duration:
                X.append([
                    float(data.team_size),
                    float(data.duration or 30),
                    2.0  # 假设历史项目复杂度为MEDIUM
                ])
                y.append(float(data.total_hours))
        
        # 使用线性回归
        if SKLEARN_AVAILABLE and len(X) >= 3:
            X_array = np.array(X)
            y_array = np.array(y)
            
            model = LinearRegression()
            model.fit(X_array, y_array)
            
            # 预测新项目
            X_new = np.array([[
                float(team_size),
                float(duration_days),
                float(complexity_encoding.get(complexity, 2))
            ]])
            predicted_hours = model.predict(X_new)[0]
            
            # 计算R²
            y_pred = model.predict(X_array)
            r_squared = r2_score(y_array, y_pred)
            confidence_level = min(r_squared * 100, 95)
            
            feature_importance = {
                'team_size_coef': float(model.coef_[0]),
                'duration_coef': float(model.coef_[1]),
                'complexity_coef': float(model.coef_[2]),
                'intercept': float(model.intercept_)
            }
        else:
            # Fallback: 简单的线性估算
            avg_hours_per_person_per_day = np.mean([
                y[i] / (X[i][0] * X[i][1]) for i in range(len(X)) if X[i][0] * X[i][1] > 0
            ])
            
            complexity_factor = complexity_encoding.get(complexity, 2) / 2
            predicted_hours = team_size * duration_days * avg_hours_per_person_per_day * complexity_factor
            confidence_level = 65
            r_squared = None
            feature_importance = {}
        
        # 计算预测范围
        predicted_hours_min = predicted_hours * 0.85
        predicted_hours_max = predicted_hours * 1.15
        
        forecast_no = f'FC-{datetime.now().strftime("%Y%m%d%H%M%S")}'
        
        algorithm_params = {
            'method': 'LINEAR_REGRESSION',
            'training_samples': len(X),
            'r_squared': r_squared,
            'feature_importance': feature_importance
        }
        
        recommendations = []
        if predicted_hours > 800:
            recommendations.append('预测工时较高，建议评估资源可用性')
        if confidence_level < 70:
            recommendations.append('预测置信度较低，建议结合专家评审')
        
        return ProjectForecastResponse(
            forecast_no=forecast_no,
            project_id=project_id,
            project_name=project_name or '新项目',
            forecast_method='LINEAR_REGRESSION',
            predicted_hours=Decimal(str(round(float(predicted_hours) if not (predicted_hours != predicted_hours) else 0.0, 2))),
            predicted_hours_min=Decimal(str(round(predicted_hours_min, 2))),
            predicted_hours_max=Decimal(str(round(predicted_hours_max, 2))),
            confidence_level=Decimal(str(round(confidence_level, 2))),
            historical_projects_count=len(X),
            similar_projects=[],
            algorithm_params=algorithm_params,
            recommendations=recommendations
        )
    
    def _forecast_by_trend(
        self,
        project_id: Optional[int],
        project_name: str,
        project_type: Optional[str],
        complexity: str,
        team_size: int,
        duration_days: int
    ) -> ProjectForecastResponse:
        """方法3：趋势预测（基于历史趋势）"""
        
        # 查询过去一段时间的工时趋势
        end_date = date.today()
        start_date = end_date - timedelta(days=90)
        
        trend_data = self.db.query(
            func.date(Timesheet.work_date).label('date'),
            func.sum(Timesheet.hours).label('daily_hours')
        ).filter(
            Timesheet.work_date.between(start_date, end_date),
            Timesheet.status == 'APPROVED'
        ).group_by(
            func.date(Timesheet.work_date)
        ).order_by(
            func.date(Timesheet.work_date)
        ).all()
        
        if len(trend_data) < 10:
            # 数据不足，使用默认方法
            return self._forecast_by_historical_average(
                project_id, project_name, project_type, complexity,
                team_size, duration_days, None
            )
        
        # 计算每日平均工时
        daily_hours_list = [float(r.daily_hours) for r in trend_data]
        avg_daily_hours = np.mean(daily_hours_list)
        
        # 计算趋势（使用移动平均）
        window_size = min(7, len(daily_hours_list) // 2)
        if len(daily_hours_list) >= window_size * 2:
            recent_avg = np.mean(daily_hours_list[-window_size:])
            earlier_avg = np.mean(daily_hours_list[:window_size])
            trend_factor = recent_avg / earlier_avg if earlier_avg > 0 else 1.0
        else:
            trend_factor = 1.0
        
        # 预测项目工时
        # 基于团队规模和周期调整
        predicted_hours = avg_daily_hours * duration_days * (team_size / 5) * trend_factor
        
        # 复杂度调整
        complexity_factor = {'LOW': 0.75, 'MEDIUM': 1.0, 'HIGH': 1.25}.get(complexity, 1.0)
        predicted_hours *= complexity_factor
        
        # 计算置信度（基于数据稳定性）
        std_dev = np.std(daily_hours_list)
        cv = std_dev / avg_daily_hours if avg_daily_hours > 0 else 1
        confidence_level = max(50, min(90, 100 - cv * 50))
        
        predicted_hours_min = predicted_hours * 0.8
        predicted_hours_max = predicted_hours * 1.2
        
        forecast_no = f'FC-{datetime.now().strftime("%Y%m%d%H%M%S")}'
        
        algorithm_params = {
            'method': 'TREND_FORECAST',
            'avg_daily_hours': round(avg_daily_hours, 2),
            'trend_factor': round(trend_factor, 4),
            'complexity_factor': complexity_factor,
            'data_points': len(trend_data)
        }
        
        recommendations = []
        if trend_factor > 1.1:
            recommendations.append('工时呈上升趋势，可能需要更多资源')
        elif trend_factor < 0.9:
            recommendations.append('工时呈下降趋势，效率有所提升')
        
        return ProjectForecastResponse(
            forecast_no=forecast_no,
            project_id=project_id,
            project_name=project_name or '新项目',
            forecast_method='TREND_FORECAST',
            predicted_hours=Decimal(str(round(float(predicted_hours) if not (predicted_hours != predicted_hours) else 0.0, 2))),
            predicted_hours_min=Decimal(str(round(predicted_hours_min, 2))),
            predicted_hours_max=Decimal(str(round(predicted_hours_max, 2))),
            confidence_level=Decimal(str(round(confidence_level, 2))),
            historical_projects_count=len(trend_data),
            similar_projects=[],
            algorithm_params=algorithm_params,
            recommendations=recommendations
        )
    
    # ==================== 2. 完工时间预测 ====================
    
    def forecast_completion(
        self,
        project_id: int,
        forecast_method: str = 'TREND_FORECAST'
    ) -> CompletionForecastResponse:
        """
        预测项目完工时间（基于当前进度和工时消耗速度）
        """
        # 查询项目信息
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        
        # 查询已消耗工时
        consumed_result = self.db.query(
            func.sum(Timesheet.hours).label('consumed_hours')
        ).filter(
            Timesheet.project_id == project_id,
            Timesheet.status == 'APPROVED'
        ).first()
        
        consumed_hours = float(consumed_result.consumed_hours or 0)
        
        # 获取当前进度（假设从项目表获取，这里简化处理）
        current_progress = 50.0  # 示例值，实际应从项目或任务表计算
        
        if current_progress >= 100:
            # 项目已完成
            predicted_completion_date = date.today()
            predicted_days_remaining = 0
            remaining_hours = 0
            confidence_level = 100
        elif current_progress <= 0 or consumed_hours <= 0:
            # 项目未开始或无数据
            predicted_hours = 500  # 默认估算
            remaining_hours = predicted_hours
            predicted_days_remaining = 30
            predicted_completion_date = date.today() + timedelta(days=predicted_days_remaining)
            confidence_level = 40
        else:
            # 基于当前进度推算总工时
            predicted_total_hours = (consumed_hours / current_progress) * 100
            remaining_hours = predicted_total_hours - consumed_hours
            
            # 查询最近的工时消耗速度
            recent_days = 14
            recent_start = date.today() - timedelta(days=recent_days)
            
            recent_result = self.db.query(
                func.sum(Timesheet.hours).label('recent_hours'),
                func.count(func.distinct(Timesheet.work_date)).label('work_days')
            ).filter(
                Timesheet.project_id == project_id,
                Timesheet.work_date >= recent_start,
                Timesheet.status == 'APPROVED'
            ).first()
            
            recent_hours = float(recent_result.recent_hours or 0)
            work_days = recent_result.work_days or 1
            
            # 计算日均消耗速度
            daily_velocity = recent_hours / work_days if work_days > 0 else (consumed_hours / 30)
            
            if daily_velocity > 0:
                predicted_days_remaining = int(remaining_hours / daily_velocity)
                predicted_completion_date = date.today() + timedelta(days=predicted_days_remaining)
                confidence_level = min(85, 50 + (work_days / recent_days) * 35)
            else:
                predicted_days_remaining = 30
                predicted_completion_date = date.today() + timedelta(days=30)
                confidence_level = 40
        
        # 生成预测曲线
        forecast_curve = self._generate_forecast_curve(
            consumed_hours,
            float(remaining_hours),
            current_progress,
            predicted_days_remaining
        )
        
        # 风险因素
        risk_factors = []
        if predicted_days_remaining > 60:
            risk_factors.append('预计完工时间较长，存在需求变更风险')
        if confidence_level < 60:
            risk_factors.append('数据不足，预测置信度较低')
        if current_progress < 20:
            risk_factors.append('项目初期，进度波动可能较大')
        
        forecast_no = f'FC-{datetime.now().strftime("%Y%m%d%H%M%S")}'
        
        return CompletionForecastResponse(
            forecast_no=forecast_no,
            project_id=project_id,
            project_name=project.name,
            current_progress=Decimal(str(round(current_progress, 2))),
            current_consumed_hours=Decimal(str(round(consumed_hours, 2))),
            predicted_hours=Decimal(str(round(consumed_hours + remaining_hours, 2))),
            remaining_hours=Decimal(str(round(remaining_hours, 2))),
            predicted_completion_date=predicted_completion_date,
            predicted_days_remaining=predicted_days_remaining,
            confidence_level=Decimal(str(round(confidence_level, 2))),
            forecast_curve=forecast_curve,
            risk_factors=risk_factors
        )
    
    def _generate_forecast_curve(
        self,
        consumed_hours: float,
        remaining_hours: float,
        current_progress: float,
        days_remaining: int
    ) -> TrendChartData:
        """生成预测曲线数据"""
        labels = []
        actual_data = []
        forecast_data = []
        
        # 过去30天
        for i in range(30, 0, -1):
            day = date.today() - timedelta(days=i)
            labels.append(day.strftime('%m-%d'))
            # 简化：线性累积
            actual_data.append(round(consumed_hours * (30 - i) / 30, 2))
            forecast_data.append(None)
        
        # 未来预测
        for i in range(1, min(days_remaining + 1, 31)):
            day = date.today() + timedelta(days=i)
            labels.append(day.strftime('%m-%d'))
            actual_data.append(None)
            forecast_value = consumed_hours + (remaining_hours * i / days_remaining) if days_remaining > 0 else consumed_hours
            forecast_data.append(round(forecast_value, 2))
        
        return TrendChartData(
            labels=labels,
            datasets=[
                {
                    'label': '实际工时',
                    'data': actual_data,
                    'borderColor': '#3b82f6',
                    'backgroundColor': 'rgba(59, 130, 246, 0.1)'
                },
                {
                    'label': '预测工时',
                    'data': forecast_data,
                    'borderColor': '#f59e0b',
                    'borderDash': [5, 5],
                    'backgroundColor': 'rgba(245, 158, 11, 0.1)'
                }
            ]
        )
    
    # ==================== 3. 人员工时饱和度预警 ====================
    
    def forecast_workload_alert(
        self,
        user_ids: Optional[List[int]] = None,
        department_ids: Optional[List[int]] = None,
        alert_level: Optional[str] = None,
        forecast_days: int = 30
    ) -> List[WorkloadAlertResponse]:
        """
        人员工时饱和度预警
        """
        # 标准工时（每天8小时，每周5天）
        standard_daily_hours = 8
        
        # 查询用户最近的工时情况
        recent_start = date.today() - timedelta(days=forecast_days)
        recent_end = date.today()
        
        query = self.db.query(
            Timesheet.user_id,
            Timesheet.user_name,
            Timesheet.department_name,
            func.sum(Timesheet.hours).label('total_hours'),
            func.sum(case((Timesheet.overtime_type != 'NORMAL', Timesheet.hours), else_=0)).label('overtime_hours')
        ).filter(
            Timesheet.work_date.between(recent_start, recent_end),
            Timesheet.status == 'APPROVED'
        )
        
        if user_ids:
            query = query.filter(Timesheet.user_id.in_(user_ids))
        if department_ids:
            query = query.filter(Timesheet.department_id.in_(department_ids))
        
        results = query.group_by(
            Timesheet.user_id,
            Timesheet.user_name,
            Timesheet.department_name
        ).all()
        
        alerts = []
        work_days = forecast_days * 5 / 7  # 工作日
        standard_total = work_days * standard_daily_hours
        
        for r in results:
            total_hours = float(r.total_hours or 0)
            overtime_hours = float(r.overtime_hours or 0)
            
            # 计算饱和度
            saturation = (total_hours / standard_total * 100) if standard_total > 0 else 0
            
            # 可用工时（未来forecast_days天）
            future_standard_hours = (forecast_days * 5 / 7) * standard_daily_hours
            # 基于历史趋势预测未来已占用工时
            predicted_occupied = total_hours * (forecast_days / forecast_days)  # 简化处理
            available_hours = future_standard_hours - predicted_occupied
            gap_hours = -available_hours if available_hours < 0 else 0
            
            # 判断预警级别
            if saturation >= 120:
                level = 'CRITICAL'
                message = f'严重超负荷！饱和度{saturation:.1f}%，建议立即调整任务分配'
            elif saturation >= 100:
                level = 'HIGH'
                message = f'高负荷预警！饱和度{saturation:.1f}%，需要关注工作量'
            elif saturation >= 85:
                level = 'MEDIUM'
                message = f'中等负荷，饱和度{saturation:.1f}%，接近满负荷'
            elif saturation < 60:
                level = 'LOW'
                message = f'负荷较低，饱和度{saturation:.1f}%，可承接更多任务'
            else:
                continue  # 正常范围，不生成预警
            
            # 过滤预警级别
            if alert_level and level != alert_level:
                continue
            
            # 建议
            recommendations = []
            if saturation >= 100:
                recommendations.append('减少任务分配或延长交付周期')
                recommendations.append('考虑增加协作人员分担工作')
            if overtime_hours / total_hours > 0.2:
                recommendations.append('加班比例较高，注意工作与休息平衡')
            if saturation < 60:
                recommendations.append('工时利用率较低，可分配更多任务')
            
            alerts.append(WorkloadAlertResponse(
                user_id=r.user_id,
                user_name=r.user_name,
                department_name=r.department_name or '未分配',
                workload_saturation=Decimal(str(round(saturation, 2))),
                alert_level=level,
                alert_message=message,
                current_hours=Decimal(str(round(total_hours, 2))),
                available_hours=Decimal(str(round(available_hours, 2))),
                gap_hours=Decimal(str(round(gap_hours, 2))),
                recommendations=recommendations
            ))
        
        # 按饱和度降序排序
        alerts.sort(key=lambda x: x.workload_saturation, reverse=True)
        
        return alerts
    
    # ==================== 4. 工时缺口分析 ====================
    
    def analyze_gap(
        self,
        period_type: str,
        start_date: date,
        end_date: date,
        department_ids: Optional[List[int]] = None,
        project_ids: Optional[List[int]] = None
    ) -> GapAnalysisResponse:
        """
        工时缺口分析（需求工时 vs 可用工时）
        """
        days_count = (end_date - start_date).days + 1
        work_days = days_count * 5 / 7
        
        # 查询部门人员数量（简化：假设每个部门5人）
        # 实际应从用户表查询
        total_staff = 20  # 示例
        
        # 可用工时 = 人数 × 工作日 × 每日8小时
        available_hours = total_staff * work_days * 8
        
        # 查询项目需求工时（简化：基于项目计划）
        # 实际应从项目计划、任务预估中查询
        # 这里基于历史工时推算
        historical_query = self.db.query(
            func.sum(Timesheet.hours).label('total_hours')
        ).filter(
            Timesheet.work_date.between(start_date, end_date),
            Timesheet.status == 'APPROVED'
        )
        
        if department_ids:
            historical_query = historical_query.filter(Timesheet.department_id.in_(department_ids))
        if project_ids:
            historical_query = historical_query.filter(Timesheet.project_id.in_(project_ids))
        
        result = historical_query.first()
        required_hours = float(result.total_hours or 0) if result else available_hours * 0.9
        
        # 计算缺口
        gap_hours = required_hours - available_hours
        gap_rate = (gap_hours / required_hours * 100) if required_hours > 0 else 0
        
        # 部门缺口（简化处理）
        departments_gap = [
            {
                'department_id': 1,
                'department_name': '研发部',
                'required_hours': round(required_hours * 0.6, 2),
                'available_hours': round(available_hours * 0.5, 2),
                'gap_hours': round(required_hours * 0.6 - available_hours * 0.5, 2)
            },
            {
                'department_id': 2,
                'department_name': '测试部',
                'required_hours': round(required_hours * 0.3, 2),
                'available_hours': round(available_hours * 0.3, 2),
                'gap_hours': round(required_hours * 0.3 - available_hours * 0.3, 2)
            }
        ]
        
        # 项目缺口
        projects_gap = []
        if project_ids:
            for pid in project_ids[:5]:  # 限制数量
                projects_gap.append({
                    'project_id': pid,
                    'project_name': f'项目{pid}',
                    'required_hours': round(required_hours / len(project_ids), 2),
                    'allocated_hours': round(available_hours / len(project_ids), 2),
                    'gap_hours': round((required_hours - available_hours) / len(project_ids), 2)
                })
        
        # 建议
        recommendations = []
        if gap_hours > 0:
            recommendations.append(f'工时缺口{abs(gap_hours):.0f}小时，建议增加人力或延长周期')
            recommendations.append('优先级排序，聚焦核心任务')
            if gap_rate > 20:
                recommendations.append('缺口较大，考虑外部资源协助')
        else:
            recommendations.append('工时资源充足，可适当增加项目')
        
        # 图表数据
        chart_data = {
            'comparison': {
                'labels': ['需求工时', '可用工时'],
                'values': [round(required_hours, 2), round(available_hours, 2)],
                'colors': ['#ef4444', '#10b981']
            },
            'gap': {
                'shortage': round(max(0, gap_hours), 2),
                'surplus': round(abs(min(0, gap_hours)), 2)
            }
        }
        
        return GapAnalysisResponse(
            period_type=period_type,
            start_date=start_date,
            end_date=end_date,
            required_hours=Decimal(str(round(required_hours, 2))),
            available_hours=Decimal(str(round(available_hours, 2))),
            gap_hours=Decimal(str(round(gap_hours, 2))),
            gap_rate=Decimal(str(round(gap_rate, 2))),
            departments=departments_gap,
            projects=projects_gap,
            recommendations=recommendations,
            chart_data=chart_data
        )


# 辅助函数
def case(condition_tuple, else_=None):
    """SQLAlchemy case helper"""
    from sqlalchemy import case as sa_case
    return sa_case((condition_tuple,), else_=else_)
