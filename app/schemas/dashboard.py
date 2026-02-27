# -*- coding: utf-8 -*-
"""
仪表盘Schema定义
用于成本看板数据传输
"""

from datetime import date, datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class DashboardStatCard(BaseModel):
    """仪表盘统计卡片"""
    
    key: Optional[str] = Field(None, description="唯一键")
    title: str = Field(..., description="标题")
    value: Union[float, int, str] = Field(..., description="数值或字符串")
    unit: Optional[str] = Field(None, description="单位")
    change: Optional[float] = Field(None, description="变化量")
    change_pct: Optional[float] = Field(None, description="变化率(%)")
    trend: Optional[str] = Field(None, description="趋势: up/down/stable")
    
    class Config:
        from_attributes = True


class DashboardWidget(BaseModel):
    """仪表盘组件"""
    
    widget_id: str = Field(..., description="组件ID")
    widget_type: str = Field(..., description="组件类型: chart/stat/table/list")
    title: str = Field(..., description="标题")
    data: Dict = Field(..., description="数据")
    config: Optional[Dict] = Field(None, description="配置")
    
    class Config:
        from_attributes = True


class DashboardListItem(BaseModel):
    """仪表盘列表项"""
    
    item_id: str = Field(..., description="项目ID")
    title: str = Field(..., description="标题")
    subtitle: Optional[str] = Field(None, description="副标题")
    status: Optional[str] = Field(None, description="状态")
    link: Optional[str] = Field(None, description="链接")
    meta: Optional[Dict] = Field(None, description="元数据")
    
    class Config:
        from_attributes = True


class DashboardModuleInfo(BaseModel):
    """仪表盘模块信息"""
    
    module_id: str = Field(..., description="模块ID")
    module_name: str = Field(..., description="模块名称")
    module_type: str = Field(..., description="模块类型")
    icon: Optional[str] = Field(None, description="图标")
    order: int = Field(0, description="排序")
    enabled: bool = Field(True, description="是否启用")
    
    class Config:
        from_attributes = True


class CostOverviewSchema(BaseModel):
    """成本总览"""
    
    total_projects: int = Field(..., description="项目总数")
    total_budget: float = Field(..., description="预算总额")
    total_actual_cost: float = Field(..., description="实际成本总额")
    total_contract_amount: float = Field(..., description="合同总额")
    
    budget_execution_rate: float = Field(..., description="预算执行率(%)")
    cost_overrun_count: int = Field(..., description="成本超支项目数量")
    cost_normal_count: int = Field(..., description="成本正常项目数量")
    cost_alert_count: int = Field(..., description="成本预警项目数量")
    
    # 本月成本趋势
    month_budget: float = Field(..., description="本月预算")
    month_actual_cost: float = Field(..., description="本月实际成本")
    month_variance: float = Field(..., description="本月预算偏差")
    month_variance_pct: float = Field(..., description="本月预算偏差率(%)")
    
    class Config:
        from_attributes = True


class ProjectCostItem(BaseModel):
    """项目成本项"""
    
    project_id: int
    project_code: str
    project_name: str
    customer_name: Optional[str] = None
    pm_name: Optional[str] = None
    
    budget_amount: float = Field(..., description="预算金额")
    actual_cost: float = Field(..., description="实际成本")
    contract_amount: float = Field(..., description="合同金额")
    
    cost_variance: float = Field(..., description="成本偏差")
    cost_variance_pct: float = Field(..., description="成本偏差率(%)")
    
    profit: float = Field(..., description="利润")
    profit_margin: float = Field(..., description="利润率(%)")
    
    stage: Optional[str] = None
    status: Optional[str] = None
    health: Optional[str] = None
    
    class Config:
        from_attributes = True


class TopProjectsSchema(BaseModel):
    """TOP项目统计"""
    
    top_cost_projects: List[ProjectCostItem] = Field(..., description="成本最高的10个项目")
    top_overrun_projects: List[ProjectCostItem] = Field(..., description="超支最严重的10个项目")
    top_profit_margin_projects: List[ProjectCostItem] = Field(..., description="利润率最高的10个项目")
    bottom_profit_margin_projects: List[ProjectCostItem] = Field(..., description="利润率最低的10个项目")
    
    class Config:
        from_attributes = True


class CostAlertItem(BaseModel):
    """成本预警项"""
    
    alert_id: Optional[int] = None
    project_id: int
    project_code: str
    project_name: str
    
    alert_type: str = Field(..., description="预警类型: overrun/budget_critical/abnormal")
    alert_level: str = Field(..., description="预警级别: high/medium/low")
    
    budget_amount: float
    actual_cost: float
    variance: float
    variance_pct: float
    
    message: str = Field(..., description="预警信息")
    created_at: Optional[date] = None
    
    class Config:
        from_attributes = True


class CostAlertsSchema(BaseModel):
    """成本预警列表"""
    
    total_alerts: int = Field(..., description="预警总数")
    high_alerts: int = Field(..., description="高危预警数量")
    medium_alerts: int = Field(..., description="中危预警数量")
    low_alerts: int = Field(..., description="低危预警数量")
    
    alerts: List[CostAlertItem] = Field(..., description="预警列表")
    
    class Config:
        from_attributes = True


class MonthCostData(BaseModel):
    """月度成本数据"""
    
    month: str = Field(..., description="月份 YYYY-MM")
    budget: float = Field(..., description="预算")
    actual_cost: float = Field(..., description="实际成本")
    variance: float = Field(..., description="偏差")
    variance_pct: float = Field(..., description="偏差率(%)")
    
    class Config:
        from_attributes = True


class CostBreakdownItem(BaseModel):
    """成本结构项"""
    
    category: str = Field(..., description="分类")
    amount: float = Field(..., description="金额")
    percentage: float = Field(..., description="占比(%)")
    
    class Config:
        from_attributes = True


class ProjectCostDashboardSchema(BaseModel):
    """单项目成本仪表盘"""
    
    project_id: int
    project_code: str
    project_name: str
    
    # 预算 vs 实际
    budget_amount: float
    actual_cost: float
    contract_amount: float
    variance: float
    variance_pct: float
    
    # 成本结构（饼图数据）
    cost_breakdown: List[CostBreakdownItem] = Field(..., description="成本结构分类")
    
    # 月度成本（柱状图数据）
    monthly_costs: List[MonthCostData] = Field(..., description="月度成本数据")
    
    # 成本趋势（折线图数据）
    cost_trend: List[Dict[str, float]] = Field(..., description="成本趋势数据")
    
    # 收入与利润
    received_amount: float = Field(..., description="已收款金额")
    invoiced_amount: float = Field(..., description="已开票金额")
    gross_profit: float = Field(..., description="毛利润")
    profit_margin: float = Field(..., description="利润率(%)")
    
    class Config:
        from_attributes = True


class ChartConfigSchema(BaseModel):
    """图表配置"""
    
    chart_type: str = Field(..., description="图表类型: bar/line/pie/area")
    title: str = Field(..., description="图表标题")
    x_axis: Optional[str] = Field(None, description="X轴字段")
    y_axis: Optional[str] = Field(None, description="Y轴字段")
    
    data_source: str = Field(..., description="数据源")
    filters: Optional[Dict] = Field(None, description="筛选条件")
    
    custom_metrics: Optional[List[str]] = Field(None, description="自定义指标")
    
    class Config:
        from_attributes = True


class ExportDataSchema(BaseModel):
    """导出数据Schema"""
    
    export_type: str = Field(..., description="导出类型: csv/excel")
    data_type: str = Field(..., description="数据类型: cost_overview/top_projects/cost_alerts/project_dashboard")
    
    filters: Optional[Dict] = Field(None, description="筛选条件")
    
    class Config:
        from_attributes = True


class DetailedDashboardResponse(BaseModel):
    """详细仪表盘响应"""
    
    module_id: str = Field(..., description="模块ID")
    module_name: str = Field(..., description="模块名称")
    data: Dict = Field(..., description="数据内容")
    charts: Optional[List[Dict]] = Field(None, description="图表配置")
    
    class Config:
        from_attributes = True


class UnifiedDashboardResponse(BaseModel):
    """统一仪表盘响应"""
    
    role_code: str = Field(..., description="角色代码")
    role_name: str = Field("", description="角色名称")
    stats: List[DashboardStatCard] = Field(default_factory=list, description="统计卡片")
    widgets: List[DashboardWidget] = Field(default_factory=list, description="组件列表")
    modules: List[DashboardModuleInfo] = Field(default_factory=list, description="模块列表")
    overview: Optional[Dict] = Field(None, description="总览数据")
    last_updated: Optional[datetime] = Field(None, description="最后更新时间")
    refresh_interval: int = Field(300, description="刷新间隔(秒)")
    
    class Config:
        from_attributes = True
