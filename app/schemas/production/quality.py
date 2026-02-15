# -*- coding: utf-8 -*-
"""
质量管理 Schemas
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from ..common import PaginatedResponse, TimestampSchema


# ==================== 质检记录 ====================

class QualityInspectionCreate(BaseModel):
    """创建质检记录"""
    work_order_id: Optional[int] = Field(default=None, description="工单ID")
    material_id: Optional[int] = Field(default=None, description="物料ID")
    batch_no: Optional[str] = Field(default=None, description="批次号")
    inspection_type: str = Field(description="检验类型: IQC/IPQC/FQC/OQC")
    inspection_date: datetime = Field(description="检验时间")
    inspector_id: int = Field(description="检验员ID")
    inspection_qty: int = Field(description="检验数量")
    qualified_qty: int = Field(default=0, description="合格数量")
    defect_qty: int = Field(default=0, description="不良数量")
    inspection_result: str = Field(default="PENDING", description="检验结果: PASS/FAIL/PENDING")
    measured_value: Optional[Decimal] = Field(default=None, description="测量值")
    spec_upper_limit: Optional[Decimal] = Field(default=None, description="规格上限")
    spec_lower_limit: Optional[Decimal] = Field(default=None, description="规格下限")
    measurement_unit: Optional[str] = Field(default=None, description="测量单位")
    defect_type: Optional[str] = Field(default=None, description="不良类型")
    defect_description: Optional[str] = Field(default=None, description="不良描述")
    defect_images: Optional[str] = Field(default=None, description="不良照片(JSON数组)")
    handling_result: Optional[str] = Field(default=None, description="处理结果: REWORK/SCRAP/CONCESSION")
    remark: Optional[str] = Field(default=None, description="备注")


class QualityInspectionResponse(TimestampSchema):
    """质检记录响应"""
    id: int
    inspection_no: str
    work_order_id: Optional[int] = None
    material_id: Optional[int] = None
    batch_no: Optional[str] = None
    inspection_type: str
    inspection_date: datetime
    inspector_id: int
    inspector_name: Optional[str] = None
    inspection_qty: int
    qualified_qty: int
    defect_qty: int
    inspection_result: str
    defect_rate: float
    measured_value: Optional[float] = None
    spec_upper_limit: Optional[float] = None
    spec_lower_limit: Optional[float] = None
    measurement_unit: Optional[str] = None
    defect_type: Optional[str] = None
    defect_description: Optional[str] = None
    handling_result: Optional[str] = None
    rework_order_id: Optional[int] = None
    remark: Optional[str] = None


class QualityInspectionListResponse(PaginatedResponse):
    """质检记录列表响应"""
    items: List[QualityInspectionResponse]


# ==================== 质量趋势分析 ====================

class QualityTrendRequest(BaseModel):
    """质量趋势分析请求"""
    start_date: datetime = Field(description="开始日期")
    end_date: datetime = Field(description="结束日期")
    material_id: Optional[int] = Field(default=None, description="物料ID筛选")
    inspection_type: Optional[str] = Field(default=None, description="检验类型筛选")
    group_by: str = Field(default="day", description="聚合维度: day/week/month")


class QualityTrendDataPoint(BaseModel):
    """质量趋势数据点"""
    date: str
    total_qty: int
    qualified_qty: int
    defect_qty: int
    defect_rate: float
    inspection_count: int


class QualityTrendResponse(BaseModel):
    """质量趋势分析响应"""
    trend_data: List[QualityTrendDataPoint]
    avg_defect_rate: float
    total_inspections: int
    total_qty: int
    total_defects: int
    prediction: Optional[float] = Field(default=None, description="预测不良率(移动平均)")


# ==================== 不良品分析 ====================

class DefectAnalysisCreate(BaseModel):
    """创建不良品分析"""
    inspection_id: int = Field(description="质检记录ID")
    analyst_id: int = Field(description="分析员ID")
    defect_type: str = Field(description="不良类型")
    defect_qty: int = Field(description="不良数量")
    root_cause_man: Optional[str] = Field(default=None, description="人因")
    root_cause_machine: Optional[str] = Field(default=None, description="机因")
    root_cause_material: Optional[str] = Field(default=None, description="料因")
    root_cause_method: Optional[str] = Field(default=None, description="法因")
    root_cause_measurement: Optional[str] = Field(default=None, description="测因")
    root_cause_environment: Optional[str] = Field(default=None, description="环因")
    related_equipment_id: Optional[int] = Field(default=None, description="关联设备ID")
    related_worker_id: Optional[int] = Field(default=None, description="关联工人ID")
    related_material_id: Optional[int] = Field(default=None, description="关联物料ID")
    corrective_action: Optional[str] = Field(default=None, description="纠正措施")
    preventive_action: Optional[str] = Field(default=None, description="预防措施")
    responsible_person_id: Optional[int] = Field(default=None, description="责任人ID")
    due_date: Optional[datetime] = Field(default=None, description="完成期限")
    remark: Optional[str] = Field(default=None, description="备注")


class DefectAnalysisResponse(TimestampSchema):
    """不良品分析响应"""
    id: int
    inspection_id: int
    analysis_no: str
    analysis_date: datetime
    analyst_id: int
    analyst_name: Optional[str] = None
    defect_type: str
    defect_qty: int
    root_cause_man: Optional[str] = None
    root_cause_machine: Optional[str] = None
    root_cause_material: Optional[str] = None
    root_cause_method: Optional[str] = None
    root_cause_measurement: Optional[str] = None
    root_cause_environment: Optional[str] = None
    related_equipment_id: Optional[int] = None
    related_worker_id: Optional[int] = None
    related_material_id: Optional[int] = None
    corrective_action: Optional[str] = None
    preventive_action: Optional[str] = None
    responsible_person_id: Optional[int] = None
    due_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    verification_result: Optional[str] = None
    verification_date: Optional[datetime] = None
    remark: Optional[str] = None


# ==================== 质量预警 ====================

class QualityAlertRuleCreate(BaseModel):
    """创建质量预警规则"""
    rule_name: str = Field(description="规则名称")
    alert_type: str = Field(description="预警类型: DEFECT_RATE/SPC_UCL/SPC_LCL/TREND")
    target_material_id: Optional[int] = Field(default=None, description="目标物料ID")
    target_process_id: Optional[int] = Field(default=None, description="目标工序ID")
    threshold_value: Decimal = Field(description="阈值")
    threshold_operator: str = Field(default="GT", description="比较运算符: GT/GTE/LT/LTE/EQ")
    time_window_hours: int = Field(default=24, description="时间窗口(小时)")
    min_sample_size: int = Field(default=5, description="最小样本数")
    alert_level: str = Field(default="WARNING", description="预警级别: INFO/WARNING/CRITICAL")
    notify_users: Optional[str] = Field(default=None, description="通知用户ID列表(JSON)")
    notify_channels: Optional[str] = Field(default=None, description="通知渠道(JSON)")
    enabled: int = Field(default=1, description="是否启用")
    description: Optional[str] = Field(default=None, description="规则描述")


class QualityAlertRuleResponse(TimestampSchema):
    """质量预警规则响应"""
    id: int
    rule_no: str
    rule_name: str
    alert_type: str
    target_material_id: Optional[int] = None
    target_process_id: Optional[int] = None
    threshold_value: float
    threshold_operator: str
    time_window_hours: int
    min_sample_size: int
    alert_level: str
    notify_users: Optional[str] = None
    notify_channels: Optional[str] = None
    enabled: int
    last_triggered_at: Optional[datetime] = None
    trigger_count: int
    description: Optional[str] = None


class QualityAlertResponse(BaseModel):
    """质量预警响应"""
    alert_id: int
    rule_id: int
    rule_name: str
    alert_type: str
    alert_level: str
    trigger_time: datetime
    current_value: float
    threshold_value: float
    message: str
    material_id: Optional[int] = None
    material_name: Optional[str] = None
    process_id: Optional[int] = None
    process_name: Optional[str] = None


class QualityAlertListResponse(PaginatedResponse):
    """质量预警列表响应"""
    items: List[QualityAlertResponse]


# ==================== 返工单 ====================

class ReworkOrderCreate(BaseModel):
    """创建返工单"""
    original_work_order_id: int = Field(description="原工单ID")
    quality_inspection_id: Optional[int] = Field(default=None, description="质检记录ID")
    rework_qty: int = Field(description="返工数量")
    rework_reason: str = Field(description="返工原因")
    defect_type: Optional[str] = Field(default=None, description="不良类型")
    assigned_to: Optional[int] = Field(default=None, description="指派给(工人ID)")
    workshop_id: Optional[int] = Field(default=None, description="车间ID")
    workstation_id: Optional[int] = Field(default=None, description="工位ID")
    plan_start_date: Optional[datetime] = Field(default=None, description="计划开始时间")
    plan_end_date: Optional[datetime] = Field(default=None, description="计划结束时间")
    remark: Optional[str] = Field(default=None, description="备注")


class ReworkOrderCompleteRequest(BaseModel):
    """完成返工单请求"""
    completed_qty: int = Field(description="完成数量")
    qualified_qty: int = Field(description="合格数量")
    scrap_qty: int = Field(default=0, description="报废数量")
    actual_hours: Decimal = Field(description="实际工时")
    rework_cost: Optional[Decimal] = Field(default=None, description="返工成本")
    completion_note: Optional[str] = Field(default=None, description="完成说明")


class ReworkOrderResponse(TimestampSchema):
    """返工单响应"""
    id: int
    rework_order_no: str
    original_work_order_id: int
    original_work_order_no: Optional[str] = None
    quality_inspection_id: Optional[int] = None
    rework_qty: int
    rework_reason: str
    defect_type: Optional[str] = None
    assigned_to: Optional[int] = None
    assigned_worker_name: Optional[str] = None
    workshop_id: Optional[int] = None
    workstation_id: Optional[int] = None
    plan_start_date: Optional[datetime] = None
    plan_end_date: Optional[datetime] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    completed_qty: int
    qualified_qty: int
    scrap_qty: int
    actual_hours: float
    rework_cost: float
    status: str
    completion_note: Optional[str] = None
    remark: Optional[str] = None


class ReworkOrderListResponse(PaginatedResponse):
    """返工单列表响应"""
    items: List[ReworkOrderResponse]


# ==================== SPC控制图 ====================

class SPCDataRequest(BaseModel):
    """SPC控制图数据请求"""
    material_id: int = Field(description="物料ID")
    start_date: datetime = Field(description="开始日期")
    end_date: datetime = Field(description="结束日期")
    inspection_type: Optional[str] = Field(default=None, description="检验类型")


class SPCDataPoint(BaseModel):
    """SPC数据点"""
    inspection_no: str
    inspection_date: datetime
    measured_value: float
    spec_upper_limit: Optional[float] = None
    spec_lower_limit: Optional[float] = None


class SPCControlLimits(BaseModel):
    """SPC控制限"""
    ucl: float = Field(description="控制上限(UCL)")
    cl: float = Field(description="中心线(CL)")
    lcl: float = Field(description="控制下限(LCL)")
    spec_upper_limit: Optional[float] = None
    spec_lower_limit: Optional[float] = None


class SPCDataResponse(BaseModel):
    """SPC控制图数据响应"""
    data_points: List[SPCDataPoint]
    control_limits: SPCControlLimits
    out_of_control_points: List[str] = Field(description="失控点列表(inspection_no)")
    process_capability_index: Optional[float] = Field(default=None, description="过程能力指数Cpk")


# ==================== 帕累托分析 ====================

class ParetoAnalysisRequest(BaseModel):
    """帕累托分析请求"""
    start_date: datetime = Field(description="开始日期")
    end_date: datetime = Field(description="结束日期")
    material_id: Optional[int] = Field(default=None, description="物料ID筛选")
    top_n: int = Field(default=10, description="显示Top N不良")


class ParetoDataPoint(BaseModel):
    """帕累托数据点"""
    defect_type: str
    defect_qty: int
    defect_rate: float
    cumulative_rate: float


class ParetoAnalysisResponse(BaseModel):
    """帕累托分析响应"""
    data_points: List[ParetoDataPoint]
    total_defects: int
    top_80_percent_types: List[str] = Field(description="占80%不良的类型")


# ==================== 质量统计看板 ====================

class QualityStatisticsResponse(BaseModel):
    """质量统计看板响应"""
    total_inspections: int
    total_inspection_qty: int
    total_qualified_qty: int
    total_defect_qty: int
    overall_defect_rate: float
    pass_rate: float
    rework_orders_count: int
    pending_rework_count: int
    active_alerts_count: int
    top_defect_types: List[dict]
    trend_last_7_days: List[dict]


# ==================== 批次质量追溯 ====================

class BatchTracingRequest(BaseModel):
    """批次质量追溯请求"""
    batch_no: str = Field(description="批次号")


class BatchTracingResponse(BaseModel):
    """批次质量追溯响应"""
    batch_no: str
    material_id: Optional[int] = None
    material_name: Optional[str] = None
    inspections: List[QualityInspectionResponse]
    defect_analyses: List[DefectAnalysisResponse]
    rework_orders: List[ReworkOrderResponse]
    total_inspections: int
    total_defects: int
    batch_defect_rate: float


# ==================== 纠正措施 ====================

class CorrectiveActionCreate(BaseModel):
    """创建纠正措施"""
    defect_analysis_id: int = Field(description="不良品分析ID")
    action_description: str = Field(description="措施描述")
    responsible_person_id: int = Field(description="责任人ID")
    due_date: datetime = Field(description="完成期限")
    action_type: str = Field(description="措施类型: CORRECTIVE/PREVENTIVE")


class CorrectiveActionResponse(BaseModel):
    """纠正措施响应"""
    id: int
    defect_analysis_id: int
    action_description: str
    responsible_person_id: int
    responsible_person_name: Optional[str] = None
    due_date: datetime
    completion_date: Optional[datetime] = None
    action_type: str
    status: str
    verification_result: Optional[str] = None
