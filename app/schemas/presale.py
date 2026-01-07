# -*- coding: utf-8 -*-
"""
售前技术支持 Schema
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from app.schemas.common import TimestampSchema


# ==================== 支持工单 ====================

class TicketCreate(BaseModel):
    """创建支持工单"""
    title: str = Field(..., description="工单标题")
    ticket_type: str = Field(..., description="工单类型")
    urgency: str = Field(default="NORMAL", description="紧急程度")
    description: Optional[str] = Field(None, description="详细描述")
    customer_id: Optional[int] = Field(None, description="客户ID")
    customer_name: Optional[str] = Field(None, description="客户名称")
    opportunity_id: Optional[int] = Field(None, description="关联商机ID")
    project_id: Optional[int] = Field(None, description="关联项目ID")
    expected_date: Optional[date] = Field(None, description="期望完成日期")
    deadline: Optional[datetime] = Field(None, description="截止时间")


class TicketUpdate(BaseModel):
    """更新工单"""
    title: Optional[str] = None
    description: Optional[str] = None
    urgency: Optional[str] = None
    expected_date: Optional[date] = None
    deadline: Optional[datetime] = None


class TicketAcceptRequest(BaseModel):
    """接单请求"""
    assignee_id: Optional[int] = Field(None, description="指派处理人ID（默认当前用户）")
    notes: Optional[str] = Field(None, description="接单备注")


class TicketProgressUpdate(BaseModel):
    """更新进度"""
    progress_note: str = Field(..., description="进度说明")
    progress_percent: Optional[int] = Field(None, ge=0, le=100, description="进度百分比")


class DeliverableCreate(BaseModel):
    """创建交付物"""
    deliverable_name: str = Field(..., description="交付物名称")
    deliverable_type: str = Field(..., description="交付物类型")
    file_path: Optional[str] = Field(None, description="文件路径")
    file_url: Optional[str] = Field(None, description="文件URL")
    description: Optional[str] = Field(None, description="说明")


class TicketRatingRequest(BaseModel):
    """工单评价请求"""
    satisfaction_score: int = Field(..., ge=1, le=5, description="满意度评分(1-5)")
    feedback: Optional[str] = Field(None, description="反馈意见")


class TicketResponse(TimestampSchema):
    """工单响应"""
    id: int
    ticket_no: str
    title: str
    ticket_type: str
    urgency: str
    description: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    opportunity_id: Optional[int] = None
    project_id: Optional[int] = None
    applicant_id: int
    applicant_name: Optional[str] = None
    applicant_dept: Optional[str] = None
    apply_time: Optional[datetime] = None
    assignee_id: Optional[int] = None
    assignee_name: Optional[str] = None
    accept_time: Optional[datetime] = None
    expected_date: Optional[date] = None
    deadline: Optional[datetime] = None
    status: str
    complete_time: Optional[datetime] = None
    actual_hours: Optional[float] = None
    satisfaction_score: Optional[int] = None
    feedback: Optional[str] = None


class DeliverableResponse(TimestampSchema):
    """交付物响应"""
    id: int
    ticket_id: int
    deliverable_name: str
    deliverable_type: str
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    description: Optional[str] = None


class TicketBoardResponse(BaseModel):
    """工单看板响应"""
    pending: List[TicketResponse] = []
    accepted: List[TicketResponse] = []
    in_progress: List[TicketResponse] = []
    completed: List[TicketResponse] = []


# ==================== 技术方案 ====================

class SolutionCreate(BaseModel):
    """创建技术方案"""
    name: str = Field(..., description="方案名称")
    solution_type: str = Field(default="CUSTOM", description="方案类型")
    industry: Optional[str] = Field(None, description="所属行业")
    test_type: Optional[str] = Field(None, description="测试类型")
    ticket_id: Optional[int] = Field(None, description="关联工单ID")
    customer_id: Optional[int] = Field(None, description="客户ID")
    opportunity_id: Optional[int] = Field(None, description="商机ID")
    requirement_summary: Optional[str] = Field(None, description="需求概述")
    solution_overview: Optional[str] = Field(None, description="方案概述")
    technical_spec: Optional[str] = Field(None, description="技术规格")
    estimated_cost: Optional[Decimal] = Field(None, description="预估成本")
    suggested_price: Optional[Decimal] = Field(None, description="建议报价")
    estimated_hours: Optional[int] = Field(None, description="预估工时")
    estimated_duration: Optional[int] = Field(None, description="预估周期")


class SolutionUpdate(BaseModel):
    """更新技术方案"""
    name: Optional[str] = None
    requirement_summary: Optional[str] = None
    solution_overview: Optional[str] = None
    technical_spec: Optional[str] = None
    estimated_cost: Optional[Decimal] = None
    suggested_price: Optional[Decimal] = None
    estimated_hours: Optional[int] = None
    estimated_duration: Optional[int] = None


class SolutionReviewRequest(BaseModel):
    """方案审核请求"""
    review_status: str = Field(..., description="审核状态")
    review_comment: Optional[str] = Field(None, description="审核意见")


class SolutionResponse(TimestampSchema):
    """方案响应"""
    id: int
    solution_no: str
    name: str
    solution_type: str
    industry: Optional[str] = None
    test_type: Optional[str] = None
    ticket_id: Optional[int] = None
    customer_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    requirement_summary: Optional[str] = None
    solution_overview: Optional[str] = None
    technical_spec: Optional[str] = None
    estimated_cost: Optional[float] = None
    suggested_price: Optional[float] = None
    cost_breakdown: Optional[Dict[str, Any]] = None
    estimated_hours: Optional[int] = None
    estimated_duration: Optional[int] = None
    status: str
    version: str
    parent_id: Optional[int] = None
    reviewer_id: Optional[int] = None
    review_time: Optional[datetime] = None
    review_status: Optional[str] = None
    review_comment: Optional[str] = None


class SolutionCostResponse(BaseModel):
    """方案成本响应"""
    solution_id: int
    total_cost: float
    breakdown: List[Dict[str, Any]] = []


# ==================== 方案模板 ====================

class TemplateCreate(BaseModel):
    """创建方案模板"""
    name: str = Field(..., description="模板名称")
    industry: Optional[str] = Field(None, description="所属行业")
    test_type: Optional[str] = Field(None, description="测试类型")
    description: Optional[str] = Field(None, description="模板描述")
    content_template: Optional[str] = Field(None, description="内容模板")
    cost_template: Optional[Dict[str, Any]] = Field(None, description="成本模板")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="附件列表")


class TemplateResponse(TimestampSchema):
    """模板响应"""
    id: int
    template_no: str
    name: str
    industry: Optional[str] = None
    test_type: Optional[str] = None
    description: Optional[str] = None
    use_count: int = 0
    is_active: bool


# ==================== 投标管理 ====================

class TenderCreate(BaseModel):
    """创建投标记录"""
    tender_no: Optional[str] = Field(None, description="招标编号（可选，自动生成）")
    tender_name: str = Field(..., description="投标项目名称")
    ticket_id: Optional[int] = Field(None, description="关联工单ID")
    opportunity_id: Optional[int] = Field(None, description="关联商机ID")
    customer_name: Optional[str] = Field(None, description="招标单位")
    publish_date: Optional[date] = Field(None, description="发布日期")
    deadline: Optional[datetime] = Field(None, description="投标截止时间")
    bid_opening_date: Optional[date] = Field(None, description="开标日期")
    budget_amount: Optional[Decimal] = Field(None, description="预算金额")
    qualification_requirements: Optional[str] = Field(None, description="资质要求")
    technical_requirements: Optional[str] = Field(None, description="技术要求")
    our_bid_amount: Optional[Decimal] = Field(None, description="我方报价")
    competitors: Optional[List[Dict[str, Any]]] = Field(None, description="竞争对手信息")
    leader_id: Optional[int] = Field(None, description="投标负责人ID")
    team_members: Optional[List[Dict[str, Any]]] = Field(None, description="投标团队")


class TenderResultUpdate(BaseModel):
    """更新投标结果"""
    result: str = Field(..., description="投标结果")
    result_reason: Optional[str] = Field(None, description="中标/落标原因分析")
    technical_score: Optional[Decimal] = Field(None, description="技术得分")
    commercial_score: Optional[Decimal] = Field(None, description="商务得分")
    total_score: Optional[Decimal] = Field(None, description="总得分")


class TenderResponse(TimestampSchema):
    """投标响应"""
    id: int
    ticket_id: Optional[int] = None
    opportunity_id: Optional[int] = None
    tender_no: Optional[str] = None
    tender_name: str
    customer_name: Optional[str] = None
    publish_date: Optional[date] = None
    deadline: Optional[datetime] = None
    bid_opening_date: Optional[date] = None
    budget_amount: Optional[float] = None
    our_bid_amount: Optional[float] = None
    technical_score: Optional[float] = None
    commercial_score: Optional[float] = None
    total_score: Optional[float] = None
    result: str
    result_reason: Optional[str] = None
    leader_id: Optional[int] = None

