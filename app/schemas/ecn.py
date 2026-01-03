# -*- coding: utf-8 -*-
"""
变更管理(ECN) Schema
"""

from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal

from .common import BaseSchema, TimestampSchema


# ==================== ECN ====================

class EcnCreate(BaseModel):
    """创建ECN"""
    ecn_title: str = Field(max_length=200, description="ECN标题")
    ecn_type: str = Field(description="变更类型")
    source_type: str = Field(description="来源类型")
    source_no: Optional[str] = None
    source_id: Optional[int] = None
    project_id: int = Field(description="项目ID")
    machine_id: Optional[int] = None
    change_reason: str = Field(description="变更原因")
    change_description: str = Field(description="变更内容描述")
    change_scope: str = Field(default="PARTIAL")
    priority: str = Field(default="NORMAL")
    urgency: str = Field(default="NORMAL")
    cost_impact: Optional[Decimal] = Field(default=0)
    schedule_impact_days: int = Field(default=0)
    attachments: Optional[List[Any]] = None
    remark: Optional[str] = None


class EcnUpdate(BaseModel):
    """更新ECN"""
    ecn_title: Optional[str] = None
    change_reason: Optional[str] = None
    change_description: Optional[str] = None
    change_scope: Optional[str] = None
    priority: Optional[str] = None
    urgency: Optional[str] = None
    cost_impact: Optional[Decimal] = None
    schedule_impact_days: Optional[int] = None
    quality_impact: Optional[str] = None
    attachments: Optional[List[Any]] = None


class EcnSubmit(BaseModel):
    """提交ECN"""
    remark: Optional[str] = None


class EcnResponse(TimestampSchema):
    """ECN响应"""
    id: int
    ecn_no: str
    ecn_title: str
    ecn_type: str
    source_type: str
    source_no: Optional[str] = None
    project_id: int
    project_name: Optional[str] = None
    machine_id: Optional[int] = None
    machine_name: Optional[str] = None
    change_reason: str
    change_description: str
    change_scope: str
    priority: str
    urgency: str
    cost_impact: Decimal = 0
    schedule_impact_days: int = 0
    status: str = "DRAFT"
    current_step: Optional[str] = None
    applicant_id: Optional[int] = None
    applicant_name: Optional[str] = None
    applied_at: Optional[datetime] = None
    approval_result: Optional[str] = None


class EcnListResponse(BaseSchema):
    """ECN列表响应"""
    id: int
    ecn_no: str
    ecn_title: str
    ecn_type: str
    project_name: Optional[str] = None
    priority: str
    status: str
    applicant_name: Optional[str] = None
    applied_at: Optional[datetime] = None
    created_at: datetime


# ==================== ECN评估 ====================

class EcnEvaluationCreate(BaseModel):
    """创建ECN评估"""
    ecn_id: int = Field(description="ECN ID")
    eval_dept: str = Field(description="评估部门")
    impact_analysis: Optional[str] = None
    cost_estimate: Optional[Decimal] = Field(default=0)
    schedule_estimate: int = Field(default=0)
    resource_requirement: Optional[str] = None
    risk_assessment: Optional[str] = None
    eval_result: str = Field(description="评估结论")
    eval_opinion: Optional[str] = None
    conditions: Optional[str] = None
    attachments: Optional[List[Any]] = None


class EcnEvaluationResponse(TimestampSchema):
    """ECN评估响应"""
    id: int
    ecn_id: int
    eval_dept: str
    evaluator_id: Optional[int] = None
    evaluator_name: Optional[str] = None
    impact_analysis: Optional[str] = None
    cost_estimate: Decimal = 0
    schedule_estimate: int = 0
    eval_result: Optional[str] = None
    eval_opinion: Optional[str] = None
    status: str = "PENDING"
    evaluated_at: Optional[datetime] = None


# ==================== ECN审批 ====================

class EcnApprovalCreate(BaseModel):
    """创建ECN审批"""
    ecn_id: int
    approval_level: int
    approval_role: str
    approver_id: Optional[int] = None
    due_date: Optional[datetime] = None


class EcnApprovalAction(BaseModel):
    """ECN审批操作"""
    approval_result: str = Field(description="审批结果: APPROVED/REJECTED/RETURNED")
    approval_opinion: Optional[str] = None


class EcnApprovalResponse(TimestampSchema):
    """ECN审批响应"""
    id: int
    ecn_id: int
    approval_level: int
    approval_role: str
    approver_id: Optional[int] = None
    approver_name: Optional[str] = None
    approval_result: Optional[str] = None
    approval_opinion: Optional[str] = None
    status: str = "PENDING"
    approved_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    is_overdue: bool = False


# ==================== ECN任务 ====================

class EcnTaskCreate(BaseModel):
    """创建ECN任务"""
    ecn_id: int
    task_name: str = Field(max_length=200)
    task_type: Optional[str] = None
    task_dept: Optional[str] = None
    task_description: Optional[str] = None
    deliverables: Optional[str] = None
    assignee_id: Optional[int] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None


class EcnTaskUpdate(BaseModel):
    """更新ECN任务"""
    task_name: Optional[str] = None
    task_description: Optional[str] = None
    assignee_id: Optional[int] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    progress_pct: Optional[int] = None
    status: Optional[str] = None
    completion_note: Optional[str] = None


class EcnTaskResponse(TimestampSchema):
    """ECN任务响应"""
    id: int
    ecn_id: int
    task_no: int
    task_name: str
    task_type: Optional[str] = None
    task_dept: Optional[str] = None
    assignee_id: Optional[int] = None
    assignee_name: Optional[str] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    progress_pct: int = 0
    status: str = "PENDING"
