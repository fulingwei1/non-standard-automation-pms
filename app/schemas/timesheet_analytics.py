# -*- coding: utf-8 -*-
"""
工时分析与预测模块 Schemas - 极简版
完全避免复杂嵌套和自引用
"""

from datetime import date
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field


# ==================== 请求参数 ====================

class TimesheetAnalyticsQuery(BaseModel):
    """工时分析查询参数"""
    period_type: str
    start_date: date
    end_date: date
    dimension: Optional[str] = None
    user_ids: Optional[List[int]] = None
    project_ids: Optional[List[int]] = None
    department_ids: Optional[List[int]] = None


class ProjectForecastRequest(BaseModel):
    """项目工时预测请求"""
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    forecast_method: str = 'HISTORICAL_AVERAGE'


class CompletionForecastQuery(BaseModel):
    """完工时间预测查询"""
    project_id: int
    forecast_method: str = 'TREND_FORECAST'


class WorkloadAlertQuery(BaseModel):
    """负荷预警查询"""
    user_ids: Optional[List[int]] = None
    department_ids: Optional[List[int]] = None
    forecast_days: int = 30


# ==================== 响应模型（极简版，不嵌套）====================

class TimesheetTrendResponse(BaseModel):
    """工时趋势响应"""
    period_type: str
    start_date: date
    end_date: date
    total_hours: Decimal
    average_hours: Decimal
    trend: str
    # 移除复杂的chart_data嵌套
    
    class Config:
        from_attributes = True


class WorkloadHeatmapResponse(BaseModel):
    """人员负荷热力图响应"""
    period_type: str
    start_date: date
    end_date: date
    # 移除复杂的heatmap_data嵌套
    
    class Config:
        from_attributes = True


class ProjectForecastResponse(BaseModel):
    """项目工时预测响应"""
    forecast_no: str
    project_id: Optional[int] = None
    project_name: str
    predicted_hours: Decimal
    confidence_level: Decimal
    
    class Config:
        from_attributes = True


class CompletionForecastResponse(BaseModel):
    """完工时间预测响应"""
    forecast_no: str
    project_id: int
    project_name: str
    predicted_completion_date: date
    predicted_days_remaining: int
    
    class Config:
        from_attributes = True


class WorkloadAlertResponse(BaseModel):
    """负荷预警响应"""
    user_id: int
    user_name: str
    workload_saturation: Decimal
    alert_level: str
    alert_message: str
    
    class Config:
        from_attributes = True


# ==================== 补充缺失的Response类 ====================

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
    
    class Config:
        from_attributes = True


class OvertimeStatisticsResponse(BaseModel):
    """加班统计响应"""
    period_type: str
    start_date: date
    end_date: date
    total_overtime_hours: Decimal
    overtime_rate: Decimal
    avg_overtime_per_person: Decimal
    
    class Config:
        from_attributes = True


class DepartmentComparisonResponse(BaseModel):
    """部门对比响应"""
    period_type: str
    start_date: date
    end_date: date
    
    class Config:
        from_attributes = True


class ProjectDistributionResponse(BaseModel):
    """项目分布响应"""
    period_type: str
    start_date: date
    end_date: date
    total_projects: int
    total_hours: Decimal
    
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
    
    class Config:
        from_attributes = True

# ==================== 图表数据类型（service层需要）====================

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
