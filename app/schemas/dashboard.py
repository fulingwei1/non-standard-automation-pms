# -*- coding: utf-8 -*-
"""
统一工作台 Dashboard Schema 定义
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


# ==================== 基础统计卡片 ====================

class DashboardStatCard(BaseModel):
    """统计卡片（用于顶部快速统计）"""
    key: str = Field(description="统计项标识")
    label: str = Field(description="统计项名称")
    value: Union[int, float, str, Decimal] = Field(description="统计值")
    trend: Optional[float] = Field(default=None, description="趋势（百分比，正数上升，负数下降）")
    unit: Optional[str] = Field(default=None, description="单位")
    icon: Optional[str] = Field(default=None, description="图标名称")
    color: Optional[str] = Field(default=None, description="颜色")


# ==================== 列表项 ====================

class DashboardListItem(BaseModel):
    """列表项（用于最近记录、待办事项等）"""
    id: Union[int, str] = Field(description="项目ID")
    title: str = Field(description="标题")
    subtitle: Optional[str] = Field(default=None, description="副标题")
    status: Optional[str] = Field(default=None, description="状态")
    priority: Optional[str] = Field(default=None, description="优先级")
    event_date: Optional[Union[date, datetime]] = Field(default=None, description="日期")  # 重命名避免与datetime.date冲突
    extra: Optional[Dict[str, Any]] = Field(default=None, description="额外信息")


# ==================== 图表数据 ====================

class DashboardChartDataPoint(BaseModel):
    """图表数据点"""
    label: str = Field(description="标签")
    value: Union[int, float, Decimal] = Field(description="数值")
    extra: Optional[Dict[str, Any]] = Field(default=None, description="额外信息")


class DashboardChartData(BaseModel):
    """图表数据"""
    type: str = Field(description="图表类型：line/bar/pie/area/scatter")
    title: Optional[str] = Field(default=None, description="图表标题")
    data: List[DashboardChartDataPoint] = Field(description="数据点列表")
    series: Optional[List[Dict[str, Any]]] = Field(default=None, description="多系列数据")


# ==================== Widget 定义 ====================

class DashboardWidget(BaseModel):
    """Dashboard Widget（可配置的模块）"""
    widget_id: str = Field(description="Widget ID")
    widget_type: str = Field(description="Widget类型：stats/list/chart/table/custom")
    title: str = Field(description="Widget标题")
    data: Any = Field(description="Widget数据")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Widget配置")
    order: int = Field(default=0, description="显示顺序")
    span: int = Field(default=12, description="占据列数（1-24）")


# ==================== 统一 Dashboard 响应 ====================

class UnifiedDashboardResponse(BaseModel):
    """统一工作台响应"""
    role_code: str = Field(description="角色代码")
    role_name: Optional[str] = Field(default=None, description="角色名称")

    # 顶部统计卡片
    stats: List[DashboardStatCard] = Field(default=[], description="统计卡片列表")

    # Widget列表（可配置的模块）
    widgets: List[DashboardWidget] = Field(default=[], description="Widget列表")

    # 快捷操作
    quick_actions: Optional[List[Dict[str, Any]]] = Field(default=None, description="快捷操作")

    # 元数据
    last_updated: Optional[datetime] = Field(default=None, description="最后更新时间")
    refresh_interval: Optional[int] = Field(default=None, description="刷新间隔（秒）")


# ==================== 详细 Dashboard 响应 ====================

class DetailedDashboardResponse(BaseModel):
    """详细工作台响应（包含更多业务数据）"""
    module: str = Field(description="模块标识")
    module_name: str = Field(description="模块名称")

    # 基础统计
    summary: Dict[str, Any] = Field(description="汇总数据")

    # 详细数据
    details: Dict[str, Any] = Field(description="详细数据")

    # 图表数据
    charts: Optional[List[DashboardChartData]] = Field(default=None, description="图表数据")

    # 最近记录
    recent_items: Optional[List[DashboardListItem]] = Field(default=None, description="最近记录")

    # 待办事项
    todos: Optional[List[DashboardListItem]] = Field(default=None, description="待办事项")

    # 元数据
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")


# ==================== Dashboard 配置 ====================

class DashboardConfig(BaseModel):
    """Dashboard 配置"""
    user_id: int = Field(description="用户ID")
    role_code: str = Field(description="角色代码")
    widgets: List[str] = Field(description="启用的Widget ID列表")
    layout: Optional[Dict[str, Any]] = Field(default=None, description="布局配置")
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="用户偏好")


# ==================== 模块注册信息 ====================

class DashboardModuleInfo(BaseModel):
    """Dashboard 模块信息"""
    module_id: str = Field(description="模块ID")
    module_name: str = Field(description="模块名称")
    description: Optional[str] = Field(default=None, description="描述")
    roles: List[str] = Field(description="适用角色列表")
    endpoint: str = Field(description="API端点")
    widgets: List[str] = Field(description="提供的Widget列表")
    is_active: bool = Field(default=True, description="是否启用")
