# -*- coding: utf-8 -*-
"""
物料需求预测引擎

Team 3: 智能缺料预警系统
支持多种预测算法：移动平均、指数平滑、线性回归
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import statistics

from app.models.shortage.smart_alert import MaterialDemandForecast
from app.models.production.work_order import WorkOrder
from app.core.exceptions import BusinessException
from app.utils.db_helpers import save_obj

logger = logging.getLogger(__name__)


class DemandForecastEngine:
    """需求预测引擎"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def forecast_material_demand(
        self,
        material_id: int,
        forecast_horizon_days: int = 30,
        algorithm: str = 'EXP_SMOOTHING',
        historical_days: int = 90,
        project_id: Optional[int] = None
    ) -> MaterialDemandForecast:
        """
        预测物料需求
        
        Args:
            material_id: 物料ID
            forecast_horizon_days: 预测周期（天）
            algorithm: 预测算法
                - MOVING_AVERAGE: 移动平均
                - EXP_SMOOTHING: 指数平滑
                - LINEAR_REGRESSION: 线性回归
            historical_days: 历史数据周期（天）
            project_id: 项目ID（可选）
        
        Returns:
            需求预测对象
        """
        logger.info(
            f"开始预测物料需求: material_id={material_id}, "
            f"algorithm={algorithm}, horizon={forecast_horizon_days}天"
        )
        
        # 1. 收集历史数据
        historical_data = self._collect_historical_demand(
            material_id=material_id,
            days=historical_days,
            project_id=project_id
        )
        
        if not historical_data:
            raise BusinessException("历史数据不足，无法进行预测")
        
        # 2. 计算历史统计指标
        historical_avg = self._calculate_average(historical_data)
        historical_std = self._calculate_std(historical_data)
        
        # 3. 检测季节性
        seasonal_factor = self._detect_seasonality(historical_data)
        
        # 4. 根据算法进行预测
        if algorithm == 'MOVING_AVERAGE':
            forecasted_demand = self._moving_average_forecast(historical_data)
        elif algorithm == 'EXP_SMOOTHING':
            forecasted_demand = self._exponential_smoothing_forecast(historical_data)
        elif algorithm == 'LINEAR_REGRESSION':
            forecasted_demand = self._linear_regression_forecast(historical_data)
        else:
            raise BusinessException(f"不支持的预测算法: {algorithm}")
        
        # 应用季节性调整
        forecasted_demand = forecasted_demand * seasonal_factor
        
        # 5. 计算置信区间
        confidence_interval = 95.0
        lower_bound, upper_bound = self._calculate_confidence_interval(
            forecast=forecasted_demand,
            std=historical_std,
            confidence=confidence_interval
        )
        
        # 6. 创建预测记录
        forecast_start_date = datetime.now().date()
        forecast_end_date = forecast_start_date + timedelta(days=forecast_horizon_days)
        
        forecast = MaterialDemandForecast(
            forecast_no=self._generate_forecast_no(),
            material_id=material_id,
            project_id=project_id,
            forecast_start_date=forecast_start_date,
            forecast_end_date=forecast_end_date,
            forecast_horizon_days=forecast_horizon_days,
            algorithm=algorithm,
            algorithm_params={
                'historical_days': historical_days,
                'data_points': len(historical_data)
            },
            forecasted_demand=forecasted_demand,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            confidence_interval=Decimal(str(confidence_interval)),
            historical_avg=historical_avg,
            historical_std=historical_std,
            historical_period_days=historical_days,
            seasonal_factor=Decimal(str(seasonal_factor)),
            seasonal_pattern={
                'detected': seasonal_factor != 1.0,
                'factor': float(seasonal_factor)
            },
            status='ACTIVE',
            forecast_date=datetime.now().date()
        )
        
        save_obj(self.db, forecast)
        
        logger.info(
            f"预测完成: forecast_no={forecast.forecast_no}, "
            f"forecasted_demand={forecasted_demand}, "
            f"confidence_interval=({lower_bound}, {upper_bound})"
        )
        
        return forecast
    
    def validate_forecast_accuracy(
        self,
        forecast_id: int,
        actual_demand: Decimal
    ) -> Dict:
        """
        验证预测准确率
        
        Args:
            forecast_id: 预测ID
            actual_demand: 实际需求量
        
        Returns:
            准确率指标
        """
        forecast = self.db.query(MaterialDemandForecast).filter(
            MaterialDemandForecast.id == forecast_id
        ).first()
        
        if not forecast:
            raise BusinessException("预测记录不存在")
        
        # 计算误差
        forecast_error = actual_demand - forecast.forecasted_demand
        error_percentage = abs(float(forecast_error / actual_demand * 100)) if actual_demand > 0 else 0
        
        # MAE (Mean Absolute Error)
        mae = abs(forecast_error)
        
        # RMSE (Root Mean Square Error)
        rmse = abs(forecast_error)  # 简化，实际应该用多个样本
        
        # MAPE (Mean Absolute Percentage Error)
        mape = Decimal(str(error_percentage))
        
        # 准确率 (100% - MAPE)
        accuracy_score = max(Decimal('0'), Decimal('100') - mape)
        
        # 更新预测记录
        forecast.actual_demand = actual_demand
        forecast.forecast_error = forecast_error
        forecast.error_percentage = Decimal(str(error_percentage))
        forecast.mae = mae
        forecast.rmse = rmse
        forecast.mape = mape
        forecast.accuracy_score = accuracy_score
        forecast.status = 'VALIDATED'
        forecast.validated_at = datetime.now()
        
        self.db.commit()
        
        result = {
            'forecast_id': forecast_id,
            'forecasted_demand': float(forecast.forecasted_demand),
            'actual_demand': float(actual_demand),
            'error': float(forecast_error),
            'error_percentage': float(error_percentage),
            'accuracy_score': float(accuracy_score),
            'mae': float(mae),
            'rmse': float(rmse),
            'mape': float(mape),
            'within_confidence_interval': (
                forecast.lower_bound <= actual_demand <= forecast.upper_bound
            )
        }
        
        logger.info(f"预测验证完成: {result}")
        
        return result
    
    # ========== 内部方法 ==========
    
    def _collect_historical_demand(
        self,
        material_id: int,
        days: int,
        project_id: Optional[int]
    ) -> List[Decimal]:
        """
        收集历史需求数据
        
        Returns:
            历史需求量列表（按天）
        """
        start_date = datetime.now().date() - timedelta(days=days)
        
        # 从工单获取历史需求
        query = self.db.query(
            func.date(WorkOrder.plan_start_date).label('demand_date'),
            func.sum(WorkOrder.plan_qty).label('daily_demand')
        ).filter(
            and_(
                WorkOrder.material_id == material_id,
                WorkOrder.plan_start_date >= start_date,
                WorkOrder.plan_start_date < datetime.now().date()
            )
        )
        
        if project_id:
            query = query.filter(WorkOrder.project_id == project_id)
        
        query = query.group_by(func.date(WorkOrder.plan_start_date))
        
        results = query.all()
        
        # 转换为列表，包含0需求的天数
        demand_dict = {row.demand_date: Decimal(str(row.daily_demand)) for row in results}
        
        historical_data = []
        current_date = start_date
        while current_date < datetime.now().date():
            daily_demand = demand_dict.get(current_date, Decimal('0'))
            historical_data.append(daily_demand)
            current_date += timedelta(days=1)
        
        return historical_data
    
    def _calculate_average(self, data: List[Decimal]) -> Decimal:
        """计算平均值"""
        if not data:
            return Decimal('0')
        return sum(data) / len(data)
    
    def _calculate_std(self, data: List[Decimal]) -> Decimal:
        """计算标准差"""
        if len(data) < 2:
            return Decimal('0')
        
        float_data = [float(x) for x in data]
        return Decimal(str(statistics.stdev(float_data)))
    
    def _detect_seasonality(self, data: List[Decimal]) -> Decimal:
        """
        检测季节性因素
        
        简化实现：比较最近7天平均和历史平均
        """
        if len(data) < 14:
            return Decimal('1.0')
        
        recent_avg = self._calculate_average(data[-7:])
        historical_avg = self._calculate_average(data[:-7])
        
        if historical_avg == 0:
            return Decimal('1.0')
        
        seasonal_factor = recent_avg / historical_avg
        
        # 限制在 0.5 - 2.0 之间
        seasonal_factor = max(Decimal('0.5'), min(Decimal('2.0'), seasonal_factor))
        
        return seasonal_factor
    
    def _moving_average_forecast(
        self,
        data: List[Decimal],
        window: int = 7
    ) -> Decimal:
        """
        移动平均预测
        
        使用最近N天的平均值作为预测
        """
        if len(data) < window:
            window = len(data)
        
        recent_data = data[-window:]
        return self._calculate_average(recent_data)
    
    def _exponential_smoothing_forecast(
        self,
        data: List[Decimal],
        alpha: Decimal = Decimal('0.3')
    ) -> Decimal:
        """
        指数平滑预测
        
        公式: S_t = α * Y_t + (1 - α) * S_{t-1}
        """
        if not data:
            return Decimal('0')
        
        # 初始值使用第一个数据点
        smoothed = data[0]
        
        # 逐步平滑
        for value in data[1:]:
            smoothed = alpha * value + (Decimal('1') - alpha) * smoothed
        
        return smoothed
    
    def _linear_regression_forecast(self, data: List[Decimal]) -> Decimal:
        """
        线性回归预测
        
        使用最小二乘法拟合趋势线
        """
        if len(data) < 2:
            return self._calculate_average(data)
        
        n = len(data)
        x = list(range(n))
        y = [float(d) for d in data]
        
        # 计算回归系数
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return Decimal(str(y_mean))
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # 预测下一个点
        next_x = n
        forecast = slope * next_x + intercept
        
        return Decimal(str(max(0, forecast)))
    
    def _calculate_confidence_interval(
        self,
        forecast: Decimal,
        std: Decimal,
        confidence: float
    ) -> Tuple[Decimal, Decimal]:
        """
        计算置信区间
        
        Args:
            forecast: 预测值
            std: 标准差
            confidence: 置信度 (如 95)
        
        Returns:
            (下限, 上限)
        """
        # 简化：使用 1.96 * std 作为 95% 置信区间
        if confidence >= 95:
            z_score = Decimal('1.96')
        elif confidence >= 90:
            z_score = Decimal('1.645')
        else:
            z_score = Decimal('1.0')
        
        margin = z_score * std
        lower_bound = max(Decimal('0'), forecast - margin)
        upper_bound = forecast + margin
        
        return lower_bound, upper_bound
    
    def _generate_forecast_no(self) -> str:
        """生成预测编号"""
        today = datetime.now().strftime('%Y%m%d')
        count = self.db.query(func.count(MaterialDemandForecast.id)).filter(
            MaterialDemandForecast.forecast_date == datetime.now().date()
        ).scalar() or 0
        return f"FC{today}{count + 1:04d}"
    
    # ========== 高级功能 ==========
    
    def batch_forecast_for_project(
        self,
        project_id: int,
        forecast_horizon_days: int = 30
    ) -> List[MaterialDemandForecast]:
        """
        批量预测项目所需的所有物料
        
        Args:
            project_id: 项目ID
            forecast_horizon_days: 预测周期
        
        Returns:
            预测列表
        """
        # 获取项目所需的所有物料
        material_ids = self.db.query(WorkOrder.material_id.distinct()).filter(
            and_(
                WorkOrder.project_id == project_id,
                WorkOrder.status.in_(['PENDING', 'CONFIRMED', 'IN_PROGRESS'])
            )
        ).all()
        
        forecasts = []
        for (material_id,) in material_ids:
            try:
                forecast = self.forecast_material_demand(
                    material_id=material_id,
                    forecast_horizon_days=forecast_horizon_days,
                    project_id=project_id
                )
                forecasts.append(forecast)
            except Exception as e:
                logger.warning(f"预测失败 material_id={material_id}: {e}")
                continue
        
        logger.info(f"项目 {project_id} 批量预测完成，生成 {len(forecasts)} 个预测")
        return forecasts
    
    def get_forecast_accuracy_report(
        self,
        material_id: Optional[int] = None,
        days: int = 30
    ) -> Dict:
        """
        获取预测准确率报告
        
        Args:
            material_id: 物料ID（可选）
            days: 统计天数
        
        Returns:
            准确率报告
        """
        start_date = datetime.now().date() - timedelta(days=days)
        
        query = self.db.query(MaterialDemandForecast).filter(
            and_(
                MaterialDemandForecast.status == 'VALIDATED',
                MaterialDemandForecast.forecast_date >= start_date,
                MaterialDemandForecast.actual_demand.isnot(None)
            )
        )
        
        if material_id:
            query = query.filter(MaterialDemandForecast.material_id == material_id)
        
        forecasts = query.all()
        
        if not forecasts:
            return {
                'total_forecasts': 0,
                'average_accuracy': 0,
                'average_mape': 0,
                'within_ci_rate': 0
            }
        
        total = len(forecasts)
        avg_accuracy = sum(float(f.accuracy_score or 0) for f in forecasts) / total
        avg_mape = sum(float(f.mape or 0) for f in forecasts) / total
        
        within_ci_count = sum(
            1 for f in forecasts
            if f.lower_bound <= f.actual_demand <= f.upper_bound
        )
        within_ci_rate = (within_ci_count / total * 100) if total > 0 else 0
        
        # 按算法统计
        by_algorithm = {}
        for forecast in forecasts:
            algo = forecast.algorithm
            if algo not in by_algorithm:
                by_algorithm[algo] = {
                    'count': 0,
                    'avg_accuracy': 0,
                    'avg_mape': 0
                }
            by_algorithm[algo]['count'] += 1
            by_algorithm[algo]['avg_accuracy'] += float(forecast.accuracy_score or 0)
            by_algorithm[algo]['avg_mape'] += float(forecast.mape or 0)
        
        for algo in by_algorithm:
            count = by_algorithm[algo]['count']
            by_algorithm[algo]['avg_accuracy'] /= count
            by_algorithm[algo]['avg_mape'] /= count
        
        return {
            'total_forecasts': total,
            'average_accuracy': round(avg_accuracy, 2),
            'average_mape': round(avg_mape, 2),
            'within_ci_rate': round(within_ci_rate, 2),
            'by_algorithm': by_algorithm,
            'period_days': days
        }
