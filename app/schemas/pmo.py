# -*- coding: utf-8 -*-
"""
PMO 项目管理部 Schema
"""
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import TimestampSchema

# ==================== 立项管理 ====================

class InitiationCreate(BaseModel):
    """创建立项申请"""
    project_name: str = Field(..., description="项目名称")
    project_type: str = Field(default="NEW", description="项目类型")
    project_level: Optional[str] = Field(None, description="建议级别")
    customer_name: str = Field(..., description="客户名称")
    contract_no: Optional[str] = Field(None, description="合同编号")
    contract_amount: Optional[Decimal] = Field(None, description="合同金额")
    required_start_date: Optional[date] = Field(None, description="要求开始日期")
    required_end_date: Optional[date] = Field(None, description="要求交付日期")
    technical_solution_id: Optional[int] = Field(None, description="技术方案ID")
    requirement_summary: Optional[str] = Field(None, description="需求概述")
    technical_difficulty: Optional[str] = Field(None, description="技术难度")
    estimated_hours: Optional[int] = Field(None, description="预估工时")
    resource_requirements: Optional[str] = Field(None, description="资源需求说明")
    risk_assessment: Optional[str] = Field(None, description="初步风险评估")


class InitiationUpdate(BaseModel):
    """更新立项申请"""
    project_name: Optional[str] = None
    project_type: Optional[str] = None
    project_level: Optional[str] = None
    customer_name: Optional[str] = None
    contract_no: Optional[str] = None
    contract_amount: Optional[Decimal] = None
    required_start_date: Optional[date] = None
    required_end_date: Optional[date] = None
    technical_solution_id: Optional[int] = None
    requirement_summary: Optional[str] = None
    technical_difficulty: Optional[str] = None
    estimated_hours: Optional[int] = None
    resource_requirements: Optional[str] = None
    risk_assessment: Optional[str] = None


class InitiationApproveRequest(BaseModel):
    """立项审批请求"""
    review_result: str = Field(..., description="评审结论")
    approved_pm_id: Optional[int] = Field(None, description="指定项目经理ID")
    approved_level: Optional[str] = Field(None, description="评定级别")


class InitiationRejectRequest(BaseModel):
    """立项驳回请求"""
    review_result: str = Field(..., description="驳回原因")


class InitiationResponse(TimestampSchema):
    """立项申请响应"""
    id: int
    application_no: str
    project_id: Optional[int] = None
    project_name: str
    project_type: str
    project_level: Optional[str] = None
    customer_name: str
    contract_no: Optional[str] = None
    contract_amount: Optional[float] = None
    required_start_date: Optional[date] = None
    required_end_date: Optional[date] = None
    technical_solution_id: Optional[int] = None
    requirement_summary: Optional[str] = None
    technical_difficulty: Optional[str] = None
    estimated_hours: Optional[int] = None
    resource_requirements: Optional[str] = None
    risk_assessment: Optional[str] = None
    applicant_id: int
    applicant_name: Optional[str] = None
    apply_time: Optional[datetime] = None
    status: str
    review_result: Optional[str] = None
    approved_pm_id: Optional[int] = None
    approved_level: Optional[str] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[int] = None


# ==================== 项目阶段 ====================

class PhaseResponse(TimestampSchema):
    """项目阶段响应"""
    id: int
    project_id: int
    phase_code: str
    phase_name: str
    phase_order: int
    plan_start_date: Optional[date] = None
    plan_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    status: str
    progress: int
    entry_criteria: Optional[str] = None
    exit_criteria: Optional[str] = None
    entry_check_result: Optional[str] = None
    exit_check_result: Optional[str] = None
    review_required: bool
    review_date: Optional[date] = None
    review_result: Optional[str] = None
    review_notes: Optional[str] = None


class PhaseEntryCheckRequest(BaseModel):
    """阶段入口检查请求"""
    check_result: str = Field(..., description="检查结果")
    notes: Optional[str] = Field(None, description="检查说明")


class PhaseExitCheckRequest(BaseModel):
    """阶段出口检查请求"""
    check_result: str = Field(..., description="检查结果")
    notes: Optional[str] = Field(None, description="检查说明")


class PhaseReviewRequest(BaseModel):
    """阶段评审请求"""
    review_result: str = Field(..., description="评审结果")
    review_notes: Optional[str] = Field(None, description="评审记录")


class PhaseAdvanceRequest(BaseModel):
    """阶段推进请求"""
    actual_start_date: Optional[date] = Field(None, description="实际开始日期")
    notes: Optional[str] = Field(None, description="推进说明")


# ==================== 风险管理 ====================

class RiskCreate(BaseModel):
    """创建风险"""
    risk_category: str = Field(..., description="风险类别")
    risk_name: str = Field(..., description="风险名称")
    description: Optional[str] = Field(None, description="风险描述")
    probability: Optional[str] = Field(None, description="发生概率")
    impact: Optional[str] = Field(None, description="影响程度")
    owner_id: Optional[int] = Field(None, description="责任人ID")
    trigger_condition: Optional[str] = Field(None, description="触发条件")


class RiskAssessRequest(BaseModel):
    """风险评估请求"""
    probability: str = Field(..., description="发生概率")
    impact: str = Field(..., description="影响程度")
    risk_level: Optional[str] = Field(None, description="风险等级（自动计算）")


class RiskResponseRequest(BaseModel):
    """风险应对计划请求"""
    response_strategy: str = Field(..., description="应对策略")
    response_plan: str = Field(..., description="应对措施")
    owner_id: Optional[int] = Field(None, description="责任人ID")


class RiskStatusUpdateRequest(BaseModel):
    """风险状态更新请求"""
    status: str = Field(..., description="状态")
    last_update: Optional[str] = Field(None, description="最新进展")
    follow_up_date: Optional[date] = Field(None, description="跟踪日期")


class RiskCloseRequest(BaseModel):
    """风险关闭请求"""
    closed_reason: str = Field(..., description="关闭原因")


class RiskResponse(TimestampSchema):
    """风险响应"""
    id: int
    project_id: int
    risk_no: str
    risk_category: str
    risk_name: str
    description: Optional[str] = None
    probability: Optional[str] = None
    impact: Optional[str] = None
    risk_level: Optional[str] = None
    response_strategy: Optional[str] = None
    response_plan: Optional[str] = None
    owner_id: Optional[int] = None
    owner_name: Optional[str] = None
    status: str
    follow_up_date: Optional[date] = None
    last_update: Optional[str] = None
    trigger_condition: Optional[str] = None
    is_triggered: bool
    triggered_date: Optional[date] = None
    closed_date: Optional[date] = None
    closed_reason: Optional[str] = None


# ==================== 项目结项 ====================

class ClosureCreate(BaseModel):
    """创建结项申请"""
    acceptance_date: Optional[date] = Field(None, description="验收日期")
    acceptance_result: Optional[str] = Field(None, description="验收结果")
    acceptance_notes: Optional[str] = Field(None, description="验收说明")
    project_summary: Optional[str] = Field(None, description="项目总结")
    achievement: Optional[str] = Field(None, description="项目成果")
    lessons_learned: Optional[str] = Field(None, description="经验教训")
    improvement_suggestions: Optional[str] = Field(None, description="改进建议")
    quality_score: Optional[int] = Field(None, ge=0, le=100, description="质量评分")
    customer_satisfaction: Optional[int] = Field(None, ge=0, le=100, description="客户满意度")


class ClosureReviewRequest(BaseModel):
    """结项评审请求"""
    review_result: str = Field(..., description="评审结果")
    review_notes: Optional[str] = Field(None, description="评审记录")


class ClosureLessonsRequest(BaseModel):
    """经验教训更新请求"""
    lessons_learned: str = Field(..., description="经验教训")
    improvement_suggestions: Optional[str] = Field(None, description="改进建议")


class ClosureResponse(TimestampSchema):
    """结项响应"""
    id: int
    project_id: int
    acceptance_date: Optional[date] = None
    acceptance_result: Optional[str] = None
    acceptance_notes: Optional[str] = None
    project_summary: Optional[str] = None
    achievement: Optional[str] = None
    lessons_learned: Optional[str] = None
    improvement_suggestions: Optional[str] = None
    final_budget: Optional[float] = None
    final_cost: Optional[float] = None
    cost_variance: Optional[float] = None
    final_planned_hours: Optional[int] = None
    final_actual_hours: Optional[int] = None
    hours_variance: Optional[int] = None
    plan_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    schedule_variance: Optional[int] = None
    quality_score: Optional[int] = None
    customer_satisfaction: Optional[int] = None
    status: str
    review_result: Optional[str] = None
    review_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None


# ==================== PMO 驾驶舱 ====================

class DashboardSummary(BaseModel):
    """驾驶舱汇总"""
    total_projects: int = 0
    active_projects: int = 0
    completed_projects: int = 0
    delayed_projects: int = 0
    total_budget: float = 0.0
    total_cost: float = 0.0
    total_risks: int = 0
    high_risks: int = 0
    critical_risks: int = 0


class DashboardResponse(BaseModel):
    """驾驶舱响应"""
    summary: DashboardSummary
    projects_by_status: Dict[str, int] = {}
    projects_by_stage: Dict[str, int] = {}
    recent_risks: List[RiskResponse] = []


class WeeklyReportResponse(BaseModel):
    """周报响应"""
    report_date: date
    week_start: date
    week_end: date
    new_projects: int = 0
    completed_projects: int = 0
    delayed_projects: int = 0
    new_risks: int = 0
    resolved_risks: int = 0
    project_updates: List[Dict[str, Any]] = []


class ResourceOverviewResponse(BaseModel):
    """资源总览响应"""
    total_resources: int = 0
    allocated_resources: int = 0
    available_resources: int = 0
    overloaded_resources: int = 0
    by_department: List[Dict[str, Any]] = []


class RiskWallResponse(BaseModel):
    """风险预警墙响应"""
    total_risks: int = 0
    critical_risks: List[RiskResponse] = []
    high_risks: List[RiskResponse] = []
    by_category: Dict[str, int] = {}
    by_project: List[Dict[str, Any]] = []


# ==================== 会议管理 ====================

class MeetingCreate(BaseModel):
    """创建会议"""
    project_id: Optional[int] = Field(None, description="项目ID（可为空表示跨项目会议）")
    meeting_type: str = Field(..., description="会议类型")
    meeting_name: str = Field(..., description="会议名称")
    meeting_date: date = Field(..., description="会议日期")
    start_time: Optional[time] = Field(None, description="开始时间")
    end_time: Optional[time] = Field(None, description="结束时间")
    location: Optional[str] = Field(None, description="会议地点")
    organizer_id: Optional[int] = Field(None, description="组织者ID")
    attendees: Optional[List[Dict[str, Any]]] = Field(None, description="参会人员")
    agenda: Optional[str] = Field(None, description="会议议程")


class MeetingUpdate(BaseModel):
    """更新会议"""
    meeting_name: Optional[str] = None
    meeting_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: Optional[str] = None
    organizer_id: Optional[int] = None
    attendees: Optional[List[Dict[str, Any]]] = None
    agenda: Optional[str] = None
    status: Optional[str] = None


class MeetingMinutesRequest(BaseModel):
    """会议纪要请求"""
    minutes: str = Field(..., description="会议纪要")
    decisions: Optional[str] = Field(None, description="会议决议")
    action_items: Optional[List[Dict[str, Any]]] = Field(None, description="待办事项")


class MeetingResponse(TimestampSchema):
    """会议响应"""
    id: int
    project_id: Optional[int] = None
    meeting_type: str
    meeting_name: str
    meeting_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: Optional[str] = None
    organizer_id: Optional[int] = None
    organizer_name: Optional[str] = None
    attendees: Optional[List[Dict[str, Any]]] = None
    agenda: Optional[str] = None
    minutes: Optional[str] = None
    decisions: Optional[str] = None
    action_items: Optional[List[Dict[str, Any]]] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    status: str
    created_by: Optional[int] = None

