# -*- coding: utf-8 -*-
"""
生产排程Schema
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== 基础Schema ====================

class ScheduleBase(BaseModel):
    """排程基础Schema"""
    work_order_id: int = Field(..., description="工单ID")
    equipment_id: Optional[int] = Field(None, description="设备ID")
    worker_id: Optional[int] = Field(None, description="工人ID")
    workshop_id: Optional[int] = Field(None, description="车间ID")
    process_id: Optional[int] = Field(None, description="工序ID")
    scheduled_start_time: datetime = Field(..., description="计划开始时间")
    scheduled_end_time: datetime = Field(..., description="计划结束时间")
    duration_hours: float = Field(..., description="计划时长(小时)")
    priority_score: float = Field(0, description="优先级评分")
    is_urgent: bool = Field(False, description="是否紧急插单")
    remark: Optional[str] = Field(None, description="备注")


class ScheduleCreate(ScheduleBase):
    """创建排程"""
    pass


class ScheduleUpdate(BaseModel):
    """更新排程"""
    scheduled_start_time: Optional[datetime] = None
    scheduled_end_time: Optional[datetime] = None
    equipment_id: Optional[int] = None
    worker_id: Optional[int] = None
    priority_score: Optional[float] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class ScheduleResponse(ScheduleBase):
    """排程响应"""
    id: int
    schedule_plan_id: Optional[int]
    status: str
    actual_start_time: Optional[datetime]
    actual_end_time: Optional[datetime]
    actual_duration_hours: Optional[float]
    algorithm_version: Optional[str]
    score: Optional[float]
    constraints_met: Optional[Dict[str, Any]]
    is_manually_adjusted: bool
    adjustment_reason: Optional[str]
    sequence_no: Optional[int]
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ==================== 排程生成相关 ====================

class WorkOrderScheduleInput(BaseModel):
    """工单排程输入"""
    work_order_id: int = Field(..., description="工单ID")
    priority: str = Field("NORMAL", description="优先级: LOW/NORMAL/HIGH/URGENT")
    preferred_start_time: Optional[datetime] = Field(None, description="期望开始时间")
    required_skills: Optional[List[str]] = Field(None, description="所需技能")
    equipment_requirements: Optional[List[int]] = Field(None, description="设备要求")


class ScheduleGenerateRequest(BaseModel):
    """生成排程请求"""
    work_orders: List[int] = Field(..., description="工单ID列表")
    start_date: datetime = Field(..., description="排程开始日期")
    end_date: datetime = Field(..., description="排程结束日期")
    algorithm: str = Field("GREEDY", description="排程算法: GREEDY/HEURISTIC/GENETIC")
    optimize_target: str = Field("BALANCED", description="优化目标: TIME/RESOURCE/BALANCED")
    constraints: Optional[Dict[str, Any]] = Field(None, description="约束条件")
    consider_worker_skills: bool = Field(True, description="考虑工人技能匹配")
    consider_equipment_capacity: bool = Field(True, description="考虑设备产能")
    allow_overtime: bool = Field(False, description="允许加班")
    
    class Config:
        json_schema_extra = {
            "example": {
                "work_orders": [1, 2, 3],
                "start_date": "2026-02-17T08:00:00",
                "end_date": "2026-02-28T18:00:00",
                "algorithm": "GREEDY",
                "optimize_target": "BALANCED",
                "consider_worker_skills": True,
                "consider_equipment_capacity": True
            }
        }


class ScheduleGenerateResponse(BaseModel):
    """生成排程响应"""
    plan_id: int = Field(..., description="排程方案ID")
    schedules: List[ScheduleResponse] = Field(..., description="排程列表")
    total_count: int = Field(..., description="排程总数")
    success_count: int = Field(..., description="成功排程数")
    failed_count: int = Field(..., description="失败排程数")
    conflicts_count: int = Field(..., description="冲突数量")
    score: float = Field(..., description="总评分")
    metrics: Dict[str, Any] = Field(..., description="评估指标")
    warnings: List[str] = Field(default_factory=list, description="警告信息")


# ==================== 紧急插单 ====================

class UrgentInsertRequest(BaseModel):
    """紧急插单请求"""
    work_order_id: int = Field(..., description="工单ID")
    insert_time: datetime = Field(..., description="期望插入时间")
    max_delay_hours: float = Field(4, description="允许最大延迟(小时)")
    auto_adjust: bool = Field(True, description="是否自动调整其他排程")
    priority_override: bool = Field(True, description="是否覆盖优先级")


class UrgentInsertResponse(BaseModel):
    """紧急插单响应"""
    success: bool
    schedule: Optional[ScheduleResponse]
    adjusted_schedules: List[ScheduleResponse] = Field(default_factory=list)
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    message: str


# ==================== 冲突检测 ====================

class ConflictResponse(BaseModel):
    """冲突响应"""
    id: int
    schedule_id: int
    conflicting_schedule_id: Optional[int]
    conflict_type: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    conflict_description: Optional[str]
    severity: str
    conflict_start_time: Optional[datetime]
    conflict_end_time: Optional[datetime]
    overlap_duration_hours: Optional[float]
    resolution_suggestion: Optional[str]
    status: str
    detected_at: datetime
    
    class Config:
        from_attributes = True


class ConflictCheckResponse(BaseModel):
    """冲突检测响应"""
    has_conflicts: bool
    total_conflicts: int
    conflicts_by_type: Dict[str, int]
    conflicts: List[ConflictResponse]
    severity_summary: Dict[str, int]


# ==================== 排程调整 ====================

class ScheduleAdjustRequest(BaseModel):
    """排程调整请求"""
    schedule_id: int = Field(..., description="排程ID")
    adjustment_type: str = Field(..., description="调整类型")
    new_start_time: Optional[datetime] = Field(None, description="新开始时间")
    new_end_time: Optional[datetime] = Field(None, description="新结束时间")
    new_equipment_id: Optional[int] = Field(None, description="新设备ID")
    new_worker_id: Optional[int] = Field(None, description="新工人ID")
    reason: str = Field(..., description="调整原因")
    auto_resolve_conflicts: bool = Field(True, description="自动解决冲突")


class AdjustmentLogResponse(BaseModel):
    """调整日志响应"""
    id: int
    schedule_id: int
    adjustment_type: str
    trigger_source: str
    before_data: Optional[Dict[str, Any]]
    after_data: Optional[Dict[str, Any]]
    changes_summary: Optional[str]
    reason: str
    impact_analysis: Optional[Dict[str, Any]]
    affected_schedules_count: int
    adjusted_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 排程对比 ====================

class ScheduleComparisonRequest(BaseModel):
    """排程方案对比请求"""
    plan_ids: List[int] = Field(..., description="方案ID列表", min_length=2, max_length=5)
    comparison_metrics: List[str] = Field(
        default_factory=lambda: ["completion_rate", "equipment_utilization", "total_duration"],
        description="对比指标"
    )


class ComparisonResult(BaseModel):
    """对比结果"""
    plan_id: int
    plan_name: str
    metrics: Dict[str, Any]
    rank: int
    recommendation: Optional[str]


class ScheduleComparisonResponse(BaseModel):
    """排程对比响应"""
    comparison_time: datetime
    plans_compared: int
    results: List[ComparisonResult]
    best_plan_id: int
    comparison_summary: Dict[str, Any]


# ==================== 甘特图数据 ====================

class GanttTask(BaseModel):
    """甘特图任务"""
    id: int
    name: str
    work_order_no: str
    start: datetime
    end: datetime
    duration: float
    progress: float
    resource: Optional[str]
    equipment: Optional[str]
    worker: Optional[str]
    status: str
    priority: str
    dependencies: List[int] = Field(default_factory=list)
    color: Optional[str]


class GanttDataResponse(BaseModel):
    """甘特图数据响应"""
    tasks: List[GanttTask]
    total_tasks: int
    start_date: datetime
    end_date: datetime
    resources: List[Dict[str, Any]]
    milestones: List[Dict[str, Any]] = Field(default_factory=list)


# ==================== 排程预览和历史 ====================

class SchedulePreviewResponse(BaseModel):
    """排程预览响应"""
    plan_id: int
    schedules: List[ScheduleResponse]
    statistics: Dict[str, Any]
    conflicts: List[ConflictResponse]
    warnings: List[str]
    is_optimizable: bool
    optimization_suggestions: List[str]


class ScheduleHistoryResponse(BaseModel):
    """排程历史响应"""
    schedules: List[ScheduleResponse]
    adjustments: List[AdjustmentLogResponse]
    total_count: int
    page: int
    page_size: int


# ==================== 排程评分 ====================

class ScheduleScoreMetrics(BaseModel):
    """排程评分指标"""
    completion_rate: float = Field(..., description="交期达成率 (0-1)")
    equipment_utilization: float = Field(..., description="设备利用率 (0-1)")
    worker_utilization: float = Field(..., description="工人利用率 (0-1)")
    total_duration_hours: float = Field(..., description="总时长(小时)")
    average_waiting_time: float = Field(..., description="平均等待时间(小时)")
    skill_match_rate: float = Field(..., description="技能匹配率 (0-1)")
    priority_satisfaction: float = Field(..., description="优先级满足度 (0-1)")
    conflict_count: int = Field(..., description="冲突数量")
    overtime_hours: float = Field(0, description="加班时长(小时)")
    
    def calculate_overall_score(self) -> float:
        """计算综合评分"""
        # 权重配置
        weights = {
            'completion_rate': 0.25,
            'equipment_utilization': 0.15,
            'worker_utilization': 0.10,
            'skill_match_rate': 0.15,
            'priority_satisfaction': 0.20,
        }
        
        # 负面因素惩罚
        conflict_penalty = min(self.conflict_count * 0.02, 0.5)  # 每个冲突扣2%,最多扣50%
        overtime_penalty = min(self.overtime_hours * 0.001, 0.1)  # 加班惩罚
        
        # 计算基础分数
        base_score = (
            weights['completion_rate'] * self.completion_rate +
            weights['equipment_utilization'] * self.equipment_utilization +
            weights['worker_utilization'] * self.worker_utilization +
            weights['skill_match_rate'] * self.skill_match_rate +
            weights['priority_satisfaction'] * self.priority_satisfaction
        )
        
        # 应用惩罚
        final_score = max(0, base_score - conflict_penalty - overtime_penalty)
        
        return round(final_score * 100, 2)  # 转换为百分制
