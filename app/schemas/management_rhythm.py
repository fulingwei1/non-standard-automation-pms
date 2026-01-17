# -*- coding: utf-8 -*-
"""
管理节律 Schema 定义
"""

from datetime import date, datetime, time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ==================== 管理节律配置 ====================

class RhythmConfigCreate(BaseModel):
    """创建节律配置"""
    rhythm_level: str = Field(..., description="节律层级:STRATEGIC/OPERATIONAL/OPERATION/TASK")
    cycle_type: str = Field(..., description="周期类型:QUARTERLY/MONTHLY/WEEKLY/DAILY")
    config_name: str = Field(..., description="配置名称")
    description: Optional[str] = Field(None, description="配置描述")
    meeting_template: Optional[Dict[str, Any]] = Field(None, description="会议模板配置(JSON)")
    key_metrics: Optional[List[Dict[str, Any]]] = Field(None, description="关键指标清单(JSON)")
    output_artifacts: Optional[List[str]] = Field(None, description="输出成果清单(JSON)")
    is_active: Optional[str] = Field("ACTIVE", description="是否启用:ACTIVE/INACTIVE")


class RhythmConfigUpdate(BaseModel):
    """更新节律配置"""
    config_name: Optional[str] = None
    description: Optional[str] = None
    meeting_template: Optional[Dict[str, Any]] = None
    key_metrics: Optional[List[Dict[str, Any]]] = None
    output_artifacts: Optional[List[str]] = None
    is_active: Optional[str] = None


class RhythmConfigResponse(BaseModel):
    """节律配置响应"""
    id: int
    rhythm_level: str
    cycle_type: str
    config_name: str
    description: Optional[str]
    meeting_template: Optional[Dict[str, Any]]
    key_metrics: Optional[List[Dict[str, Any]]]
    output_artifacts: Optional[List[str]]
    is_active: str
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 战略会议 ====================

class StrategicMeetingCreate(BaseModel):
    """创建战略会议"""
    project_id: Optional[int] = Field(None, description="项目ID（可为空表示跨项目会议）")
    rhythm_config_id: Optional[int] = Field(None, description="节律配置ID")
    rhythm_level: str = Field(..., description="会议层级:STRATEGIC/OPERATIONAL/OPERATION/TASK")
    cycle_type: str = Field(..., description="周期类型:QUARTERLY/MONTHLY/WEEKLY/DAILY")
    meeting_name: str = Field(..., description="会议名称")
    meeting_type: Optional[str] = Field(None, description="会议类型")
    meeting_date: date = Field(..., description="会议日期")
    start_time: Optional[time] = Field(None, description="开始时间")
    end_time: Optional[time] = Field(None, description="结束时间")
    location: Optional[str] = Field(None, description="会议地点")
    organizer_id: Optional[int] = Field(None, description="组织者ID")
    organizer_name: Optional[str] = Field(None, description="组织者")
    attendees: Optional[List[Dict[str, Any]]] = Field(None, description="参会人员")
    agenda: Optional[str] = Field(None, description="会议议程")
    strategic_context: Optional[Dict[str, Any]] = Field(None, description="战略背景(JSON)")
    strategic_structure: Optional[Dict[str, Any]] = Field(None, description="五层战略结构(JSON):愿景/机会/定位/目标/路径")
    key_decisions: Optional[List[Dict[str, Any]]] = Field(None, description="关键决策(JSON)")
    resource_allocation: Optional[Dict[str, Any]] = Field(None, description="资源分配(JSON)")


class StrategicMeetingUpdate(BaseModel):
    """更新战略会议"""
    meeting_name: Optional[str] = None
    meeting_type: Optional[str] = None
    meeting_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: Optional[str] = None
    organizer_id: Optional[int] = None
    organizer_name: Optional[str] = None
    attendees: Optional[List[Dict[str, Any]]] = None
    agenda: Optional[str] = None
    status: Optional[str] = None
    strategic_context: Optional[Dict[str, Any]] = None
    strategic_structure: Optional[Dict[str, Any]] = None
    key_decisions: Optional[List[Dict[str, Any]]] = None
    resource_allocation: Optional[Dict[str, Any]] = None


class StrategicMeetingMinutesRequest(BaseModel):
    """会议纪要请求"""
    minutes: str = Field(..., description="会议纪要")
    decisions: Optional[str] = Field(None, description="会议决议")
    strategic_structure: Optional[Dict[str, Any]] = Field(None, description="五层战略结构(JSON)")
    key_decisions: Optional[List[Dict[str, Any]]] = Field(None, description="关键决策(JSON)")
    metrics_snapshot: Optional[Dict[str, Any]] = Field(None, description="指标快照(JSON)")


class StrategicStructureTemplate(BaseModel):
    """五层战略结构模板"""
    vision: Optional[Dict[str, Any]] = Field(None, description="使命/愿景层")
    opportunity: Optional[Dict[str, Any]] = Field(None, description="战略机会层")
    positioning: Optional[Dict[str, Any]] = Field(None, description="战略定位层")
    goals: Optional[Dict[str, Any]] = Field(None, description="战略目标层")
    path: Optional[Dict[str, Any]] = Field(None, description="战略路径层")


class StrategicMeetingResponse(BaseModel):
    """战略会议响应"""
    id: int
    project_id: Optional[int]
    rhythm_config_id: Optional[int]
    rhythm_level: str
    cycle_type: str
    meeting_name: str
    meeting_type: Optional[str]
    meeting_date: date
    start_time: Optional[time]
    end_time: Optional[time]
    location: Optional[str]
    organizer_id: Optional[int]
    organizer_name: Optional[str]
    attendees: Optional[List[Dict[str, Any]]]
    agenda: Optional[str]
    minutes: Optional[str]
    decisions: Optional[str]
    strategic_context: Optional[Dict[str, Any]]
    strategic_structure: Optional[Dict[str, Any]]
    key_decisions: Optional[List[Dict[str, Any]]]
    resource_allocation: Optional[Dict[str, Any]]
    metrics_snapshot: Optional[Dict[str, Any]]
    attachments: Optional[List[Dict[str, Any]]]
    status: str
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    action_items_count: Optional[int] = 0
    completed_action_items_count: Optional[int] = 0

    class Config:
        from_attributes = True


# ==================== 会议行动项 ====================

class ActionItemCreate(BaseModel):
    """创建行动项"""
    meeting_id: int = Field(..., description="会议ID")
    action_description: str = Field(..., description="行动描述")
    owner_id: int = Field(..., description="责任人ID")
    owner_name: Optional[str] = Field(None, description="责任人姓名")
    due_date: date = Field(..., description="截止日期")
    priority: Optional[str] = Field("NORMAL", description="优先级:LOW/NORMAL/HIGH/URGENT")


class ActionItemUpdate(BaseModel):
    """更新行动项"""
    action_description: Optional[str] = None
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    completion_notes: Optional[str] = None
    priority: Optional[str] = None


class ActionItemResponse(BaseModel):
    """行动项响应"""
    id: int
    meeting_id: int
    action_description: str
    owner_id: int
    owner_name: Optional[str]
    due_date: date
    completed_date: Optional[date]
    status: str
    completion_notes: Optional[str]
    priority: str
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 节律仪表盘 ====================

class RhythmDashboardResponse(BaseModel):
    """节律仪表盘响应"""
    rhythm_level: str
    cycle_type: str
    current_cycle: Optional[str]
    key_metrics_snapshot: Optional[Dict[str, Any]]
    health_status: str
    last_meeting_date: Optional[date]
    next_meeting_date: Optional[date]
    meetings_count: int
    completed_meetings_count: int
    total_action_items: int
    completed_action_items: int
    overdue_action_items: int
    completion_rate: Optional[str]
    snapshot_date: date

    class Config:
        from_attributes = True


class RhythmDashboardSummary(BaseModel):
    """节律仪表盘汇总"""
    strategic: Optional[RhythmDashboardResponse]
    operational: Optional[RhythmDashboardResponse]
    operation: Optional[RhythmDashboardResponse]
    task: Optional[RhythmDashboardResponse]


# ==================== 会议地图 ====================

class MeetingMapItem(BaseModel):
    """会议地图项"""
    id: int
    rhythm_level: str
    cycle_type: str
    meeting_name: str
    meeting_date: date
    start_time: Optional[time]
    status: str
    organizer_name: Optional[str]
    action_items_count: int
    completed_action_items_count: int


class MeetingMapResponse(BaseModel):
    """会议地图响应"""
    items: List[MeetingMapItem]
    by_level: Dict[str, List[MeetingMapItem]]
    by_cycle: Dict[str, List[MeetingMapItem]]


class MeetingCalendarResponse(BaseModel):
    """会议日历响应"""
    date: date
    meetings: List[MeetingMapItem]


class MeetingStatisticsResponse(BaseModel):
    """会议统计响应"""
    total_meetings: int
    completed_meetings: int
    scheduled_meetings: int
    cancelled_meetings: int
    total_action_items: int
    completed_action_items: int
    overdue_action_items: int
    completion_rate: float
    by_level: Dict[str, int]
    by_cycle: Dict[str, int]


# ==================== 会议报告 ====================

class MeetingReportGenerateRequest(BaseModel):
    """生成会议报告请求"""
    report_type: str = Field(..., description="报告类型:ANNUAL/MONTHLY")
    period_year: int = Field(..., description="报告年份")
    period_month: Optional[int] = Field(None, description="报告月份（月度报告必填）")
    rhythm_level: Optional[str] = Field(None, description="节律层级筛选（可选）")
    config_id: Optional[int] = Field(None, description="报告配置ID（可选，不指定则使用默认配置）")


class MeetingReportResponse(BaseModel):
    """会议报告响应"""
    id: int
    report_no: str
    report_type: str
    report_title: str
    period_year: int
    period_month: Optional[int]
    period_start: date
    period_end: date
    rhythm_level: str
    report_data: Optional[Dict[str, Any]]
    comparison_data: Optional[Dict[str, Any]]
    file_path: Optional[str]
    file_size: Optional[int]
    status: str
    generated_by: Optional[int]
    generated_at: datetime
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MeetingReportSummary(BaseModel):
    """会议报告摘要"""
    total_meetings: int
    completed_meetings: int
    total_action_items: int
    completed_action_items: int
    completion_rate: str
    key_decisions_count: int
    strategic_structure_completed: bool


# ==================== 报告配置 ====================

class MetricConfigItem(BaseModel):
    """指标配置项"""
    category: str = Field(..., description="指标分类")
    metric_code: str = Field(..., description="指标编码")
    metric_name: str = Field(..., description="指标名称")
    data_source: str = Field(..., description="数据源表名")
    calculation: str = Field(..., description="计算方式")
    enabled: bool = Field(True, description="是否启用")
    show_in_summary: bool = Field(True, description="是否在摘要中显示")
    show_in_detail: bool = Field(True, description="是否在详细中显示")
    show_comparison: bool = Field(True, description="是否显示对比")
    comparison_type: List[str] = Field(default=["环比"], description="对比类型:环比/同比")
    display_order: int = Field(1, description="显示顺序")


class ComparisonConfig(BaseModel):
    """对比配置"""
    enable_mom: bool = Field(True, description="启用环比")
    enable_yoy: bool = Field(True, description="启用同比")
    comparison_periods: List[str] = Field(default=["previous_month", "same_month_last_year"], description="对比周期")
    highlight_threshold: Optional[Dict[str, Any]] = Field(None, description="高亮阈值")


class DisplaySection(BaseModel):
    """显示章节"""
    name: str = Field(..., description="章节名称")
    enabled: bool = Field(True, description="是否启用")
    order: int = Field(1, description="显示顺序")


class DisplayConfig(BaseModel):
    """显示配置"""
    sections: List[DisplaySection] = Field(default_factory=list, description="章节列表")
    chart_types: Optional[Dict[str, bool]] = Field(None, description="图表类型配置")


class MeetingReportConfigCreate(BaseModel):
    """创建报告配置"""
    config_name: str = Field(..., description="配置名称")
    report_type: str = Field(..., description="报告类型:ANNUAL/MONTHLY")
    description: Optional[str] = Field(None, description="配置描述")
    enabled_metrics: List[MetricConfigItem] = Field(default_factory=list, description="启用的指标列表")
    comparison_config: Optional[ComparisonConfig] = Field(None, description="对比配置")
    display_config: Optional[DisplayConfig] = Field(None, description="显示配置")
    is_default: bool = Field(False, description="是否默认配置")


class MeetingReportConfigUpdate(BaseModel):
    """更新报告配置"""
    config_name: Optional[str] = None
    description: Optional[str] = None
    enabled_metrics: Optional[List[MetricConfigItem]] = None
    comparison_config: Optional[ComparisonConfig] = None
    display_config: Optional[DisplayConfig] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class MeetingReportConfigResponse(BaseModel):
    """报告配置响应"""
    id: int
    config_name: str
    report_type: str
    description: Optional[str]
    enabled_metrics: Optional[List[Dict[str, Any]]]
    comparison_config: Optional[Dict[str, Any]]
    display_config: Optional[Dict[str, Any]]
    is_default: bool
    is_active: bool
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReportMetricDefinitionCreate(BaseModel):
    """创建指标定义"""
    metric_code: str = Field(..., description="指标编码")
    metric_name: str = Field(..., description="指标名称")
    category: str = Field(..., description="指标分类")
    description: Optional[str] = Field(None, description="指标说明")
    data_source: str = Field(..., description="数据源表名")
    data_field: Optional[str] = Field(None, description="数据字段")
    filter_conditions: Optional[Dict[str, Any]] = Field(None, description="筛选条件")
    calculation_type: str = Field(..., description="计算类型:COUNT/SUM/AVG/MAX/MIN/RATIO/CUSTOM")
    calculation_formula: Optional[str] = Field(None, description="计算公式")
    support_mom: bool = Field(True, description="支持环比")
    support_yoy: bool = Field(True, description="支持同比")
    unit: Optional[str] = Field(None, description="单位")
    format_type: str = Field("NUMBER", description="格式类型:NUMBER/PERCENTAGE/CURRENCY")
    decimal_places: int = Field(2, description="小数位数")


class ReportMetricDefinitionUpdate(BaseModel):
    """更新指标定义"""
    metric_name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    data_source: Optional[str] = None
    data_field: Optional[str] = None
    filter_conditions: Optional[Dict[str, Any]] = None
    calculation_type: Optional[str] = None
    calculation_formula: Optional[str] = None
    support_mom: Optional[bool] = None
    support_yoy: Optional[bool] = None
    unit: Optional[str] = None
    format_type: Optional[str] = None
    decimal_places: Optional[int] = None
    is_active: Optional[bool] = None


class ReportMetricDefinitionResponse(BaseModel):
    """指标定义响应"""
    id: int
    metric_code: str
    metric_name: str
    category: str
    description: Optional[str]
    data_source: str
    data_field: Optional[str]
    filter_conditions: Optional[Dict[str, Any]]
    calculation_type: str
    calculation_formula: Optional[str]
    support_mom: bool
    support_yoy: bool
    unit: Optional[str]
    format_type: str
    decimal_places: int
    is_active: bool
    is_system: bool
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AvailableMetricsResponse(BaseModel):
    """可用指标列表响应"""
    metrics: List[ReportMetricDefinitionResponse]
    categories: List[str]
    total_count: int
