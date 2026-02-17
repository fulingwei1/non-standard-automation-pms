# -*- coding: utf-8 -*-
"""
工时分析与预测模块 Schemas - 极简版
完全避免复杂嵌套和自引用
"""

from datetime import date
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


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
