# -*- coding: utf-8 -*-
"""
工时分析与预测模块 Schemas - 修复版
Pydantic 2.x + Python 3.13 兼容
"""

from datetime import date
from typing import Optional, List, Dict, Any
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


# ==================== 基础类型 ====================

# 使用Literal类型替代str子类
AnalyticsPeriodType = str  # 简化为str
AnalyticsDimensionType = str
ForecastMethodType = str


# ==================== 请求参数 ====================

class TimesheetAnalyticsQuery(BaseModel):
    """工时分析查询参数"""
    period_type: str = Field(..., description="周期类型:DAILY/WEEKLY/MONTHLY/QUARTERLY/YEARLY")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    dimension: Optional[str] = Field(None, description="分析维度")
    user_ids: Optional[List[int]] = Field(None, description="用户ID列表")
    project_ids: Optional[List[int]] = Field(None, description="项目ID列表")
    department_ids: Optional[List[int]] = Field(None, description="部门ID列表")
    
    @field_validator('period_type')
    @classmethod
    def validate_period_type(cls, v):
        valid = ['DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY']
        if v not in valid:
            raise ValueError(f'period_type must be one of {valid}')
        return v


class ProjectForecastRequest(BaseModel):
    """项目工时预测请求"""
    project_id: Optional[int] = Field(None, description="项目ID(已存在项目)")
    project_name: Optional[str] = Field(None, description="项目名称(新项目)")
    project_type: Optional[str] = Field(None, description="项目类型")
    complexity: Optional[str] = Field(None, description="复杂度:LOW/MEDIUM/HIGH")
    team_size: Optional[int] = Field(None, description="团队规模")
    duration_days: Optional[int] = Field(None, description="计划周期(天)")
    forecast_method: str = Field('HISTORICAL_AVERAGE', description="预测方法")
    similar_project_ids: Optional[List[int]] = Field(None, description="相似项目ID列表")


class CompletionForecastQuery(BaseModel):
    """完工时间预测查询"""
    project_id: int = Field(..., description="项目ID")
    forecast_method: str = Field('TREND_FORECAST', description="预测方法")


class WorkloadAlertQuery(BaseModel):
    """负荷预警查询"""
    user_ids: Optional[List[int]] = Field(None, description="用户ID列表")
    department_ids: Optional[List[int]] = Field(None, description="部门ID列表")
    alert_level: Optional[str] = Field(None, description="预警级别:LOW/MEDIUM/HIGH/CRITICAL")
    forecast_days: int = Field(30, description="预测天数")


# ==================== 响应模型 ====================

class ChartDataPoint(BaseModel):
    """图表数据点"""
    label: str = Field(..., description="标签")
    value: float = Field(..., description="值")
    date: Optional[date] = Field(None, description="日期")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class TrendChartData(BaseModel):
    """趋势图数据"""
    labels: List[str] = Field(..., description="X轴标签")
    datasets: List[Dict[str, Any]] = Field(..., description="数据集")


class PieChartData(BaseModel):
    """饼图数据"""
    labels: List[str] = Field(..., description="标签")
    values: List[float] = Field(..., description="值")
    colors: Optional[List[str]] = Field(None, description="颜色")


class HeatmapData(BaseModel):
    """热力图数据"""
    rows: List[str] = Field(..., description="行标签")
    columns: List[str] = Field(..., description="列标签")
    data: List[List[float]] = Field(..., description="数据矩阵")


class TimesheetTrendResponse(BaseModel):
    """工时趋势响应"""
    period_type: str
    start_date: date
    end_date: date
    dimension: Optional[str] = None
    total_hours: Decimal
    average_hours: Decimal
    max_hours: Decimal
    min_hours: Decimal
    trend: str = Field(..., description="趋势:INCREASING/STABLE/DECREASING")
    change_rate: Decimal = Field(..., description="变化率(%)")
    chart_data: TrendChartData = Field(..., description="图表数据")
    
    class Config:
        from_attributes = True


class WorkloadHeatmapResponse(BaseModel):
    """人员负荷热力图响应"""
    period_type: str
    start_date: date
    end_date: date
    heatmap_data: HeatmapData
    statistics: Dict[str, Any] = Field(..., description="统计信息")
    overload_users: List[Dict[str, Any]] = Field(..., description="超负荷人员")
    
    class Config:
        from_attributes = True


class EfficiencyComparisonResponse(BaseModel):
    """效率对比响应"""
    period_type: str
    start_date: date
    end_date: date
    planned_hours: Decimal
    actual_hours: Decimal
    variance_hours: Decimal
    variance_rate: Decimal
    efficiency_rate: Decimal
    chart_data: Dict[str, Any]
    insights: List[str] = Field(..., description="洞察建议")
    
    class Config:
        from_attributes = True


class OvertimeStatisticsResponse(BaseModel):
    """加班统计响应"""
    period_type: str
    start_date: date
    end_date: date
    total_overtime_hours: Decimal
    weekend_hours: Decimal
    holiday_hours: Decimal
    overtime_rate: Decimal = Field(..., description="加班率(%)")
    avg_overtime_per_person: Decimal
    top_overtime_users: List[Dict[str, Any]]
    overtime_trend: TrendChartData
    
    class Config:
        from_attributes = True


class DepartmentComparisonResponse(BaseModel):
    """部门对比响应"""
    period_type: str
    start_date: date
    end_date: date
    departments: List[Dict[str, Any]] = Field(..., description="部门数据")
    chart_data: Dict[str, Any]
    rankings: List[Dict[str, Any]] = Field(..., description="排名")
    
    class Config:
        from_attributes = True


class ProjectDistributionResponse(BaseModel):
    """项目分布响应"""
    period_type: str
    start_date: date
    end_date: date
    total_projects: int
    total_hours: Decimal
    pie_chart: PieChartData
    project_details: List[Dict[str, Any]]
    concentration_index: Decimal = Field(..., description="集中度指数(0-1)")
    
    class Config:
        from_attributes = True


class ProjectForecastResponse(BaseModel):
    """项目工时预测响应"""
    forecast_no: str
    project_id: Optional[int] = None
    project_name: str
    forecast_method: str
    predicted_hours: Decimal
    predicted_hours_min: Decimal
    predicted_hours_max: Decimal
    confidence_level: Decimal
    historical_projects_count: int
    similar_projects: List[Dict[str, Any]]
    algorithm_params: Dict[str, Any]
    recommendations: List[str]
    
    class Config:
        from_attributes = True


class CompletionForecastResponse(BaseModel):
    """完工时间预测响应"""
    forecast_no: str
    project_id: int
    project_name: str
    current_progress: Decimal
    current_consumed_hours: Decimal
    predicted_hours: Decimal
    remaining_hours: Decimal
    predicted_completion_date: date
    predicted_days_remaining: int
    confidence_level: Decimal
    forecast_curve: TrendChartData
    risk_factors: List[str]
    
    class Config:
        from_attributes = True


class WorkloadAlertResponse(BaseModel):
    """负荷预警响应"""
    user_id: int
    user_name: str
    department_name: str
    workload_saturation: Decimal = Field(..., description="饱和度(%)")
    alert_level: str
    alert_message: str
    current_hours: Decimal
    available_hours: Decimal
    gap_hours: Decimal
    recommendations: List[str]
    
    class Config:
        from_attributes = True


class GapAnalysisResponse(BaseModel):
    """缺口分析响应"""
    period_type: str
    start_date: date
    end_date: date
    required_hours: Decimal
    available_hours: Decimal
    gap_hours: Decimal
    gap_rate: Decimal
    departments: List[Dict[str, Any]] = Field(..., description="部门缺口")
    projects: List[Dict[str, Any]] = Field(..., description="项目缺口")
    recommendations: List[str]
    chart_data: Dict[str, Any]
    
    class Config:
        from_attributes = True


# ==================== 汇总模型 ====================

class TimesheetAnalyticsSummary(BaseModel):
    """工时分析汇总"""
    id: int
    period_type: str
    dimension: str
    start_date: date
    end_date: date
    total_hours: Decimal
    normal_hours: Decimal
    overtime_hours: Decimal
    efficiency_rate: Optional[Decimal] = None
    utilization_rate: Optional[Decimal] = None
    overtime_rate: Optional[Decimal] = None
    workload_saturation: Optional[Decimal] = None
    entries_count: int
    
    class Config:
        from_attributes = True


class ForecastValidationResult(BaseModel):
    """预测验证结果"""
    forecast_id: int
    predicted_hours: Decimal
    actual_hours: Decimal
    prediction_error: Decimal
    error_rate: Decimal
    is_accurate: bool = Field(..., description="是否准确(误差<10%)")
    
    class Config:
        from_attributes = True
