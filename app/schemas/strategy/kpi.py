# -*- coding: utf-8 -*-
"""
战略管理 Schema - KPI 关键绩效指标
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..common import TimestampSchema


class KPICreate(BaseModel):
    """创建 KPI"""
    csf_id: int = Field(description="关联 CSF")
    code: str = Field(max_length=50, description="KPI 编码")
    name: str = Field(max_length=200, description="指标名称")
    description: Optional[str] = Field(default=None, description="指标描述")
    ipooc_type: str = Field(description="IPOOC类型：INPUT/PROCESS/OUTPUT/OUTCOME")
    unit: Optional[str] = Field(default=None, max_length=20, description="单位")
    direction: str = Field(default="UP", description="方向：UP/DOWN")
    target_value: Optional[Decimal] = Field(default=None, description="目标值")
    baseline_value: Optional[Decimal] = Field(default=None, description="基线值")
    excellent_threshold: Optional[Decimal] = Field(default=None, description="优秀阈值")
    good_threshold: Optional[Decimal] = Field(default=None, description="良好阈值")
    warning_threshold: Optional[Decimal] = Field(default=None, description="警告阈值")
    data_source_type: str = Field(default="MANUAL", description="数据源类型")
    data_source_config: Optional[Dict[str, Any]] = Field(default=None, description="数据源配置")
    frequency: str = Field(default="MONTHLY", description="更新频率")
    weight: Decimal = Field(default=0, description="权重")
    owner_user_id: Optional[int] = Field(default=None, description="责任人")


class KPIUpdate(BaseModel):
    """更新 KPI"""
    name: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    ipooc_type: Optional[str] = None
    unit: Optional[str] = None
    direction: Optional[str] = None
    target_value: Optional[Decimal] = None
    baseline_value: Optional[Decimal] = None
    current_value: Optional[Decimal] = None
    excellent_threshold: Optional[Decimal] = None
    good_threshold: Optional[Decimal] = None
    warning_threshold: Optional[Decimal] = None
    data_source_type: Optional[str] = None
    data_source_config: Optional[Dict[str, Any]] = None
    frequency: Optional[str] = None
    weight: Optional[Decimal] = None
    owner_user_id: Optional[int] = None


class KPIResponse(TimestampSchema):
    """KPI 响应"""
    id: int
    csf_id: int
    code: str
    name: str
    description: Optional[str] = None
    ipooc_type: str
    unit: Optional[str] = None
    direction: str = "UP"
    target_value: Optional[Decimal] = None
    baseline_value: Optional[Decimal] = None
    current_value: Optional[Decimal] = None
    excellent_threshold: Optional[Decimal] = None
    good_threshold: Optional[Decimal] = None
    warning_threshold: Optional[Decimal] = None
    data_source_type: str = "MANUAL"
    frequency: str = "MONTHLY"
    last_collected_at: Optional[datetime] = None
    weight: Decimal = 0
    owner_user_id: Optional[int] = None
    is_active: bool = True

    # 扩展字段
    owner_name: Optional[str] = None
    csf_name: Optional[str] = None
    csf_dimension: Optional[str] = None


class KPIDetailResponse(KPIResponse):
    """KPI 详情响应（包含计算字段）"""
    completion_rate: Optional[float] = None
    health_level: Optional[str] = None
    trend: Optional[str] = None  # UP/DOWN/STABLE


class KPIValueUpdate(BaseModel):
    """更新 KPI 当前值"""
    value: Decimal = Field(description="新的当前值")
    remark: Optional[str] = Field(default=None, description="备注")


class KPICollectRequest(BaseModel):
    """采集 KPI 数据请求"""
    force: bool = Field(default=False, description="是否强制采集")


class KPICollectResponse(BaseModel):
    """采集 KPI 数据响应"""
    kpi_id: int
    previous_value: Optional[Decimal] = None
    new_value: Optional[Decimal] = None
    source_type: str
    collected_at: datetime
    success: bool
    message: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================
# KPI History - KPI 历史记录
# ============================================

class KPIHistoryResponse(TimestampSchema):
    """KPI 历史记录响应"""
    id: int
    kpi_id: int
    snapshot_date: date
    snapshot_period: Optional[str] = None
    value: Optional[Decimal] = None
    target_value: Optional[Decimal] = None
    completion_rate: Optional[Decimal] = None
    health_level: Optional[str] = None
    source_type: Optional[str] = None
    remark: Optional[str] = None
    recorded_by: Optional[int] = None
    recorder_name: Optional[str] = None


class KPIWithHistoryResponse(KPIDetailResponse):
    """KPI 响应（含历史数据）"""
    history: List[KPIHistoryResponse] = []


class KPITrendData(BaseModel):
    """KPI 趋势数据"""
    date: date
    value: Optional[float] = None
    target: Optional[float] = None
    completion_rate: Optional[float] = None


class KPITrendResponse(BaseModel):
    """KPI 趋势响应"""
    kpi_id: int
    kpi_name: str
    period: str  # last_7_days / last_30_days / last_quarter / last_year
    data: List[KPITrendData] = []
    avg_value: Optional[float] = None
    max_value: Optional[float] = None
    min_value: Optional[float] = None

    class Config:
        from_attributes = True


# ============================================
# KPI Data Source - 数据源配置
# ============================================

class KPIDataSourceCreate(BaseModel):
    """创建 KPI 数据源"""
    kpi_id: int
    source_type: str = Field(description="类型：AUTO/FORMULA")
    source_module: Optional[str] = Field(default=None, description="来源模块")
    query_type: Optional[str] = Field(default=None, description="查询类型")
    metric: Optional[str] = Field(default=None, description="度量字段")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="过滤条件")
    aggregation: Optional[str] = Field(default=None, description="聚合方式")
    formula: Optional[str] = Field(default=None, description="计算公式")
    formula_params: Optional[Dict[str, Any]] = Field(default=None, description="公式参数")
    is_primary: bool = Field(default=False, description="是否主数据源")


class KPIDataSourceResponse(TimestampSchema):
    """KPI 数据源响应"""
    id: int
    kpi_id: int
    source_type: str
    source_module: Optional[str] = None
    query_type: Optional[str] = None
    metric: Optional[str] = None
    aggregation: Optional[str] = None
    formula: Optional[str] = None
    is_primary: bool = False
    is_active: bool = True
    last_executed_at: Optional[datetime] = None
    last_result: Optional[Decimal] = None
    last_error: Optional[str] = None
