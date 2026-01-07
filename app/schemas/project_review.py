# -*- coding: utf-8 -*-
"""
项目复盘模块 Schema
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal

from .common import BaseSchema, TimestampSchema


# ==================== 项目复盘报告 ====================

class ProjectReviewCreate(BaseModel):
    """创建项目复盘报告"""
    
    project_id: int = Field(..., description="项目ID")
    review_date: date = Field(..., description="复盘日期")
    review_type: Optional[str] = Field(default="POST_MORTEM", description="复盘类型：POST_MORTEM/MID_TERM/QUARTERLY")
    
    # 项目周期对比
    plan_duration: Optional[int] = Field(default=None, description="计划工期(天)")
    actual_duration: Optional[int] = Field(default=None, description="实际工期(天)")
    schedule_variance: Optional[int] = Field(default=None, description="进度偏差(天)")
    
    # 成本对比
    budget_amount: Optional[Decimal] = Field(default=None, description="预算金额")
    actual_cost: Optional[Decimal] = Field(default=None, description="实际成本")
    cost_variance: Optional[Decimal] = Field(default=None, description="成本偏差")
    
    # 质量指标
    quality_issues: Optional[int] = Field(default=0, description="质量问题数")
    change_count: Optional[int] = Field(default=0, description="变更次数")
    customer_satisfaction: Optional[int] = Field(default=None, ge=1, le=5, description="客户满意度1-5")
    
    # 复盘内容
    success_factors: Optional[str] = Field(default=None, description="成功因素")
    problems: Optional[str] = Field(default=None, description="问题与教训")
    improvements: Optional[str] = Field(default=None, description="改进建议")
    best_practices: Optional[str] = Field(default=None, description="最佳实践")
    conclusion: Optional[str] = Field(default=None, description="复盘结论")
    
    # 参与人
    reviewer_id: int = Field(..., description="复盘负责人ID")
    reviewer_name: str = Field(..., max_length=50, description="复盘负责人")
    participants: Optional[List[int]] = Field(default=None, description="参与人ID列表")
    participant_names: Optional[str] = Field(default=None, max_length=500, description="参与人姓名（逗号分隔）")
    
    # 附件
    attachment_ids: Optional[List[int]] = Field(default=None, description="附件ID列表")
    
    # 状态
    status: Optional[str] = Field(default="DRAFT", description="状态：DRAFT/PUBLISHED/ARCHIVED")


class ProjectReviewUpdate(BaseModel):
    """更新项目复盘报告"""
    
    review_date: Optional[date] = None
    review_type: Optional[str] = None
    
    plan_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    schedule_variance: Optional[int] = None
    
    budget_amount: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    cost_variance: Optional[Decimal] = None
    
    quality_issues: Optional[int] = None
    change_count: Optional[int] = None
    customer_satisfaction: Optional[int] = Field(default=None, ge=1, le=5)
    
    success_factors: Optional[str] = None
    problems: Optional[str] = None
    improvements: Optional[str] = None
    best_practices: Optional[str] = None
    conclusion: Optional[str] = None
    
    reviewer_id: Optional[int] = None
    reviewer_name: Optional[str] = Field(default=None, max_length=50)
    participants: Optional[List[int]] = None
    participant_names: Optional[str] = Field(default=None, max_length=500)
    
    attachment_ids: Optional[List[int]] = None
    status: Optional[str] = None


class ProjectReviewResponse(TimestampSchema):
    """项目复盘报告响应"""
    
    id: int
    review_no: str
    project_id: int
    project_code: str
    review_date: date
    review_type: str
    
    plan_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    schedule_variance: Optional[int] = None
    
    budget_amount: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    cost_variance: Optional[Decimal] = None
    
    quality_issues: int = 0
    change_count: int = 0
    customer_satisfaction: Optional[int] = None
    
    success_factors: Optional[str] = None
    problems: Optional[str] = None
    improvements: Optional[str] = None
    best_practices: Optional[str] = None
    conclusion: Optional[str] = None
    
    reviewer_id: int
    reviewer_name: str
    participants: Optional[List[int]] = None
    participant_names: Optional[str] = None
    
    attachment_ids: Optional[List[int]] = None
    status: str = "DRAFT"
    
    class Config:
        from_attributes = True


# ==================== 项目经验教训 ====================

class ProjectLessonCreate(BaseModel):
    """创建项目经验教训"""
    
    review_id: int = Field(..., description="复盘报告ID")
    project_id: int = Field(..., description="项目ID")
    lesson_type: str = Field(..., description="类型：SUCCESS/FAILURE")
    title: str = Field(..., max_length=200, description="标题")
    description: str = Field(..., description="问题/经验描述")
    
    root_cause: Optional[str] = Field(default=None, description="根本原因")
    impact: Optional[str] = Field(default=None, description="影响范围")
    
    improvement_action: Optional[str] = Field(default=None, description="改进措施")
    responsible_person: Optional[str] = Field(default=None, max_length=50, description="责任人")
    due_date: Optional[date] = Field(default=None, description="完成日期")
    
    category: Optional[str] = Field(default=None, max_length=50, description="分类：进度/成本/质量/沟通/技术/管理")
    tags: Optional[List[str]] = Field(default=None, description="标签列表")
    
    priority: Optional[str] = Field(default="MEDIUM", description="优先级：LOW/MEDIUM/HIGH")
    status: Optional[str] = Field(default="OPEN", description="状态：OPEN/IN_PROGRESS/RESOLVED/CLOSED")


class ProjectLessonUpdate(BaseModel):
    """更新项目经验教训"""
    
    lesson_type: Optional[str] = None
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    
    root_cause: Optional[str] = None
    impact: Optional[str] = None
    
    improvement_action: Optional[str] = None
    responsible_person: Optional[str] = Field(default=None, max_length=50)
    due_date: Optional[date] = None
    
    category: Optional[str] = Field(default=None, max_length=50)
    tags: Optional[List[str]] = None
    
    priority: Optional[str] = None
    status: Optional[str] = None
    resolved_date: Optional[date] = None


class ProjectLessonResponse(TimestampSchema):
    """项目经验教训响应"""
    
    id: int
    review_id: int
    project_id: int
    lesson_type: str
    title: str
    description: str
    
    root_cause: Optional[str] = None
    impact: Optional[str] = None
    
    improvement_action: Optional[str] = None
    responsible_person: Optional[str] = None
    due_date: Optional[date] = None
    
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    
    priority: str = "MEDIUM"
    status: str = "OPEN"
    resolved_date: Optional[date] = None
    
    class Config:
        from_attributes = True


# ==================== 项目最佳实践 ====================

class ProjectBestPracticeCreate(BaseModel):
    """创建项目最佳实践"""
    
    review_id: int = Field(..., description="复盘报告ID")
    project_id: int = Field(..., description="项目ID")
    title: str = Field(..., max_length=200, description="标题")
    description: str = Field(..., description="实践描述")
    
    context: Optional[str] = Field(default=None, description="适用场景")
    implementation: Optional[str] = Field(default=None, description="实施方法")
    benefits: Optional[str] = Field(default=None, description="带来的收益")
    
    category: Optional[str] = Field(default=None, max_length=50, description="分类：流程/工具/技术/管理/沟通")
    tags: Optional[List[str]] = Field(default=None, description="标签列表")
    
    is_reusable: Optional[bool] = Field(default=True, description="是否可复用")
    applicable_project_types: Optional[List[str]] = Field(default=None, description="适用项目类型列表")
    applicable_stages: Optional[List[str]] = Field(default=None, description="适用阶段列表（S1-S9）")
    
    validation_status: Optional[str] = Field(default="PENDING", description="验证状态：PENDING/VALIDATED/REJECTED")


class ProjectBestPracticeUpdate(BaseModel):
    """更新项目最佳实践"""
    
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    
    context: Optional[str] = None
    implementation: Optional[str] = None
    benefits: Optional[str] = None
    
    category: Optional[str] = Field(default=None, max_length=50)
    tags: Optional[List[str]] = None
    
    is_reusable: Optional[bool] = None
    applicable_project_types: Optional[List[str]] = None
    applicable_stages: Optional[List[str]] = None
    
    validation_status: Optional[str] = None
    validation_date: Optional[date] = None
    validated_by: Optional[int] = None


class ProjectBestPracticeResponse(TimestampSchema):
    """项目最佳实践响应"""
    
    id: int
    review_id: int
    project_id: int
    title: str
    description: str
    
    context: Optional[str] = None
    implementation: Optional[str] = None
    benefits: Optional[str] = None
    
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    
    is_reusable: bool = True
    applicable_project_types: Optional[List[str]] = None
    applicable_stages: Optional[List[str]] = None
    
    validation_status: str = "PENDING"
    validation_date: Optional[date] = None
    validated_by: Optional[int] = None
    
    reuse_count: int = 0
    last_reused_at: Optional[datetime] = None
    status: str = "ACTIVE"
    
    class Config:
        from_attributes = True


