# -*- coding: utf-8 -*-
"""
异常处理增强 Schemas
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from ..common import PaginatedResponse, TimestampSchema


# ==================== 异常升级 ====================

class ExceptionEscalateRequest(BaseModel):
    """异常升级请求"""
    exception_id: int = Field(description="异常ID")
    reason: str = Field(description="升级原因")
    escalation_level: str = Field(description="升级级别：LEVEL_1/LEVEL_2/LEVEL_3")
    escalated_to_id: Optional[int] = Field(default=None, description="升级至处理人ID")


class ExceptionEscalateResponse(TimestampSchema):
    """异常升级响应"""
    id: int
    exception_id: int
    status: str
    escalation_level: str
    escalation_reason: Optional[str] = None
    escalated_at: Optional[datetime] = None
    escalated_to_id: Optional[int] = None
    escalated_to_name: Optional[str] = None


# ==================== 异常处理流程 ====================

class FlowTrackingResponse(TimestampSchema):
    """流程跟踪响应"""
    id: int
    exception_id: int
    exception_no: Optional[str] = None
    exception_title: Optional[str] = None
    status: str
    escalation_level: str
    escalation_reason: Optional[str] = None
    escalated_at: Optional[datetime] = None
    escalated_to_name: Optional[str] = None
    
    # 时长统计
    pending_duration_minutes: Optional[int] = None
    processing_duration_minutes: Optional[int] = None
    total_duration_minutes: Optional[int] = None
    
    # 状态变更时间
    pending_at: Optional[datetime] = None
    processing_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # 验证信息
    verifier_name: Optional[str] = None
    verify_result: Optional[str] = None
    verify_comment: Optional[str] = None


# ==================== 异常知识库 ====================

class KnowledgeCreateRequest(BaseModel):
    """知识库创建请求"""
    title: str = Field(max_length=200, description="知识标题")
    exception_type: str = Field(description="异常类型")
    exception_level: str = Field(description="异常级别")
    symptom_description: str = Field(description="异常症状描述")
    solution: str = Field(description="解决方案")
    solution_steps: Optional[str] = Field(default=None, description="处理步骤（JSON格式）")
    prevention_measures: Optional[str] = Field(default=None, description="预防措施")
    keywords: Optional[str] = Field(default=None, description="关键词（逗号分隔）")
    source_exception_id: Optional[int] = Field(default=None, description="来源异常ID")
    attachments: Optional[str] = Field(default=None, description="附件URL（JSON格式）")


class KnowledgeUpdateRequest(BaseModel):
    """知识库更新请求"""
    title: Optional[str] = Field(default=None, max_length=200, description="知识标题")
    symptom_description: Optional[str] = Field(default=None, description="异常症状描述")
    solution: Optional[str] = Field(default=None, description="解决方案")
    solution_steps: Optional[str] = Field(default=None, description="处理步骤")
    prevention_measures: Optional[str] = Field(default=None, description="预防措施")
    keywords: Optional[str] = Field(default=None, description="关键词")


class KnowledgeResponse(TimestampSchema):
    """知识库响应"""
    id: int
    title: str
    exception_type: str
    exception_level: str
    symptom_description: str
    solution: str
    solution_steps: Optional[str] = None
    prevention_measures: Optional[str] = None
    keywords: Optional[str] = None
    source_exception_id: Optional[int] = None
    reference_count: int
    success_count: int
    last_referenced_at: Optional[datetime] = None
    is_approved: bool
    approver_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    creator_name: Optional[str] = None
    attachments: Optional[str] = None
    remark: Optional[str] = None


class KnowledgeListResponse(PaginatedResponse):
    """知识库列表响应"""
    items: List[KnowledgeResponse]


class KnowledgeSearchRequest(BaseModel):
    """知识库搜索请求"""
    keyword: Optional[str] = Field(default=None, description="搜索关键词")
    exception_type: Optional[str] = Field(default=None, description="异常类型")
    exception_level: Optional[str] = Field(default=None, description="异常级别")
    is_approved: Optional[bool] = Field(default=None, description="是否仅显示已审核")


# ==================== 异常统计 ====================

class ExceptionStatisticsResponse(BaseModel):
    """异常统计响应"""
    total_count: int = Field(description="总异常数")
    by_type: dict = Field(description="按类型统计")
    by_level: dict = Field(description="按级别统计")
    by_status: dict = Field(description="按状态统计")
    avg_resolution_time_minutes: Optional[float] = Field(description="平均解决时长（分钟）")
    escalation_rate: Optional[float] = Field(description="升级率（%）")
    recurrence_rate: Optional[float] = Field(description="重复异常率（%）")
    top_exceptions: List[dict] = Field(description="高频异常TOP10")


# ==================== PDCA ====================

class PDCACreateRequest(BaseModel):
    """PDCA创建请求"""
    exception_id: int = Field(description="异常ID")
    plan_description: str = Field(description="问题描述")
    plan_root_cause: str = Field(description="根本原因分析")
    plan_target: str = Field(description="改善目标")
    plan_measures: Optional[str] = Field(default=None, description="改善措施（JSON格式）")
    plan_owner_id: int = Field(description="计划负责人ID")
    plan_deadline: Optional[datetime] = Field(default=None, description="计划完成期限")


class PDCAAdvanceRequest(BaseModel):
    """PDCA推进请求"""
    stage: str = Field(description="推进到的阶段：DO/CHECK/ACT/COMPLETED")
    
    # Do阶段字段
    do_action_taken: Optional[str] = Field(default=None, description="实施内容")
    do_resources_used: Optional[str] = Field(default=None, description="使用资源")
    do_difficulties: Optional[str] = Field(default=None, description="遇到的困难")
    do_owner_id: Optional[int] = Field(default=None, description="执行负责人ID")
    
    # Check阶段字段
    check_result: Optional[str] = Field(default=None, description="检查结果")
    check_effectiveness: Optional[str] = Field(default=None, description="有效性：EFFECTIVE/PARTIAL/INEFFECTIVE")
    check_data: Optional[str] = Field(default=None, description="数据分析（JSON格式）")
    check_gap: Optional[str] = Field(default=None, description="差距分析")
    check_owner_id: Optional[int] = Field(default=None, description="检查负责人ID")
    
    # Act阶段字段
    act_standardization: Optional[str] = Field(default=None, description="标准化措施")
    act_horizontal_deployment: Optional[str] = Field(default=None, description="横向展开计划")
    act_remaining_issues: Optional[str] = Field(default=None, description="遗留问题")
    act_next_cycle: Optional[str] = Field(default=None, description="下一轮PDCA计划")
    act_owner_id: Optional[int] = Field(default=None, description="改进负责人ID")
    
    # 完成阶段字段
    summary: Optional[str] = Field(default=None, description="总结")
    lessons_learned: Optional[str] = Field(default=None, description="经验教训")


class PDCAResponse(TimestampSchema):
    """PDCA响应"""
    id: int
    exception_id: int
    exception_no: Optional[str] = None
    pdca_no: str
    current_stage: str
    
    # Plan
    plan_description: Optional[str] = None
    plan_root_cause: Optional[str] = None
    plan_target: Optional[str] = None
    plan_measures: Optional[str] = None
    plan_owner_name: Optional[str] = None
    plan_deadline: Optional[datetime] = None
    plan_completed_at: Optional[datetime] = None
    
    # Do
    do_action_taken: Optional[str] = None
    do_resources_used: Optional[str] = None
    do_difficulties: Optional[str] = None
    do_owner_name: Optional[str] = None
    do_completed_at: Optional[datetime] = None
    
    # Check
    check_result: Optional[str] = None
    check_effectiveness: Optional[str] = None
    check_data: Optional[str] = None
    check_gap: Optional[str] = None
    check_owner_name: Optional[str] = None
    check_completed_at: Optional[datetime] = None
    
    # Act
    act_standardization: Optional[str] = None
    act_horizontal_deployment: Optional[str] = None
    act_remaining_issues: Optional[str] = None
    act_next_cycle: Optional[str] = None
    act_owner_name: Optional[str] = None
    act_completed_at: Optional[datetime] = None
    
    # Complete
    is_completed: bool
    completed_at: Optional[datetime] = None
    summary: Optional[str] = None
    lessons_learned: Optional[str] = None


class PDCAListResponse(PaginatedResponse):
    """PDCA列表响应"""
    items: List[PDCAResponse]


# ==================== 重复异常分析 ====================

class RecurrenceAnalysisResponse(BaseModel):
    """重复异常分析响应"""
    exception_type: str = Field(description="异常类型")
    total_occurrences: int = Field(description="总发生次数")
    similar_exceptions: List[dict] = Field(description="相似异常列表")
    time_trend: List[dict] = Field(description="时间趋势")
    common_root_causes: List[str] = Field(description="常见根因")
    recommended_actions: List[str] = Field(description="建议措施")
