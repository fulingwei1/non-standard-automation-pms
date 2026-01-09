# -*- coding: utf-8 -*-
"""
客服服务模块 Schemas
包含：服务工单、现场服务记录、客户沟通、满意度调查、知识库
"""

from typing import Optional, List, Any, Dict
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field

from app.schemas.common import PaginatedResponse


# ==================== 服务工单 ====================

class ServiceTicketCreate(BaseModel):
    """创建服务工单"""
    project_id: int = Field(..., description="项目ID")
    customer_id: int = Field(..., description="客户ID")
    problem_type: str = Field(..., description="问题类型")
    problem_desc: str = Field(..., description="问题描述")
    urgency: str = Field(..., description="紧急程度")
    reported_by: str = Field(..., description="报告人")
    reported_time: datetime = Field(..., description="报告时间")


class ServiceTicketUpdate(BaseModel):
    """更新服务工单"""
    problem_desc: Optional[str] = Field(None, description="问题描述")
    urgency: Optional[str] = Field(None, description="紧急程度")
    status: Optional[str] = Field(None, description="状态")


class ServiceTicketAssign(BaseModel):
    """分配服务工单"""
    assignee_id: int = Field(..., description="处理人ID")


class ServiceTicketClose(BaseModel):
    """关闭服务工单"""
    solution: str = Field(..., description="解决方案")
    root_cause: Optional[str] = Field(None, description="根本原因")
    preventive_action: Optional[str] = Field(None, description="预防措施")
    satisfaction: Optional[int] = Field(None, ge=1, le=5, description="满意度1-5")
    feedback: Optional[str] = Field(None, description="客户反馈")


class ServiceTicketResponse(BaseModel):
    """服务工单响应"""
    id: int
    ticket_no: str
    project_id: int
    project_name: Optional[str] = None
    customer_id: int
    customer_name: Optional[str] = None
    problem_type: str
    problem_desc: str
    urgency: str
    reported_by: str
    reported_time: datetime
    assigned_to_id: Optional[int] = None
    assigned_to_name: Optional[str] = None
    assigned_time: Optional[datetime] = None
    status: str
    response_time: Optional[datetime] = None
    resolved_time: Optional[datetime] = None
    solution: Optional[str] = None
    root_cause: Optional[str] = None
    preventive_action: Optional[str] = None
    satisfaction: Optional[int] = None
    feedback: Optional[str] = None
    timeline: Optional[List[Dict]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 现场服务记录 ====================

class ServiceRecordCreate(BaseModel):
    """创建服务记录"""
    service_type: str = Field(..., description="服务类型")
    project_id: int = Field(..., description="项目ID")
    machine_no: Optional[str] = Field(None, description="机台号")
    customer_id: int = Field(..., description="客户ID")
    location: Optional[str] = Field(None, description="服务地点")
    service_date: date = Field(..., description="服务日期")
    start_time: Optional[str] = Field(None, description="开始时间")
    end_time: Optional[str] = Field(None, description="结束时间")
    duration_hours: Optional[Decimal] = Field(None, description="服务时长")
    service_engineer_id: int = Field(..., description="服务工程师ID")
    customer_contact: Optional[str] = Field(None, description="客户联系人")
    customer_phone: Optional[str] = Field(None, description="客户电话")
    service_content: str = Field(..., description="服务内容")
    service_result: Optional[str] = Field(None, description="服务结果")
    issues_found: Optional[str] = Field(None, description="发现的问题")
    solution_provided: Optional[str] = Field(None, description="提供的解决方案")
    photos: Optional[List[str]] = Field(None, description="照片列表")
    customer_satisfaction: Optional[int] = Field(None, ge=1, le=5, description="客户满意度")
    customer_feedback: Optional[str] = Field(None, description="客户反馈")
    customer_signed: Optional[bool] = Field(False, description="客户是否签字")
    status: Optional[str] = Field("SCHEDULED", description="状态")


class ServiceRecordUpdate(BaseModel):
    """更新服务记录"""
    service_content: Optional[str] = None
    service_result: Optional[str] = None
    issues_found: Optional[str] = None
    solution_provided: Optional[str] = None
    photos: Optional[List[str]] = None
    customer_satisfaction: Optional[int] = None
    customer_feedback: Optional[str] = None
    customer_signed: Optional[bool] = None
    status: Optional[str] = None


class ServiceRecordResponse(BaseModel):
    """服务记录响应"""
    id: int
    record_no: str
    service_type: str
    project_id: int
    project_name: Optional[str] = None
    machine_no: Optional[str] = None
    customer_id: int
    customer_name: Optional[str] = None
    location: Optional[str] = None
    service_date: date
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_hours: Optional[Decimal] = None
    service_engineer_id: int
    service_engineer_name: Optional[str] = None
    customer_contact: Optional[str] = None
    customer_phone: Optional[str] = None
    service_content: str
    service_result: Optional[str] = None
    issues_found: Optional[str] = None
    solution_provided: Optional[str] = None
    photos: Optional[List[str]] = None
    customer_satisfaction: Optional[int] = None
    customer_feedback: Optional[str] = None
    customer_signed: Optional[bool] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 客户沟通 ====================

class CustomerCommunicationCreate(BaseModel):
    """创建客户沟通记录"""
    communication_type: str = Field(..., description="沟通方式")
    customer_name: str = Field(..., description="客户名称")
    customer_contact: Optional[str] = Field(None, description="客户联系人")
    customer_phone: Optional[str] = Field(None, description="客户电话")
    customer_email: Optional[str] = Field(None, description="客户邮箱")
    project_code: Optional[str] = Field(None, description="项目编号")
    project_name: Optional[str] = Field(None, description="项目名称")
    communication_date: date = Field(..., description="沟通日期")
    communication_time: Optional[str] = Field(None, description="沟通时间")
    duration: Optional[int] = Field(None, description="沟通时长（分钟）")
    location: Optional[str] = Field(None, description="服务地点")
    topic: str = Field(..., description="沟通主题")
    subject: str = Field(..., description="沟通主题")
    content: str = Field(..., description="沟通内容")
    follow_up_required: Optional[bool] = Field(False, description="是否需要后续跟进")
    follow_up_task: Optional[str] = Field(None, description="跟进任务")
    follow_up_due_date: Optional[date] = Field(None, description="跟进截止日期")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    importance: Optional[str] = Field("中", description="重要性")


class CustomerCommunicationUpdate(BaseModel):
    """更新客户沟通记录"""
    content: Optional[str] = None
    follow_up_task: Optional[str] = None
    follow_up_status: Optional[str] = None
    tags: Optional[List[str]] = None


class CustomerCommunicationResponse(BaseModel):
    """客户沟通记录响应"""
    id: int
    communication_no: str
    communication_type: str
    customer_name: str
    customer_contact: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    project_code: Optional[str] = None
    project_name: Optional[str] = None
    communication_date: date
    communication_time: Optional[str] = None
    duration: Optional[int] = None
    location: Optional[str] = None
    topic: str
    subject: str
    content: str
    follow_up_required: bool
    follow_up_task: Optional[str] = None
    follow_up_due_date: Optional[date] = None
    follow_up_status: Optional[str] = None
    tags: Optional[List[str]] = None
    importance: str
    created_by: int
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 满意度调查 ====================

class CustomerSatisfactionCreate(BaseModel):
    """创建满意度调查"""
    survey_type: str = Field(..., description="调查类型")
    customer_name: str = Field(..., description="客户名称")
    customer_contact: Optional[str] = Field(None, description="客户联系人")
    customer_email: Optional[str] = Field(None, description="客户邮箱")
    customer_phone: Optional[str] = Field(None, description="客户电话")
    project_code: Optional[str] = Field(None, description="项目编号")
    project_name: Optional[str] = Field(None, description="项目名称")
    survey_date: date = Field(..., description="调查日期")
    send_method: str = Field(..., description="发送方式")
    deadline: Optional[date] = Field(None, description="截止日期")
    notes: Optional[str] = Field(None, description="备注")


class CustomerSatisfactionUpdate(BaseModel):
    """更新满意度调查"""
    status: Optional[str] = None
    response_date: Optional[date] = None
    overall_score: Optional[Decimal] = None
    scores: Optional[Dict] = None
    feedback: Optional[str] = None
    suggestions: Optional[str] = None


class CustomerSatisfactionResponse(BaseModel):
    """满意度调查响应"""
    id: int
    survey_no: str
    survey_type: str
    customer_name: str
    customer_contact: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    project_code: Optional[str] = None
    project_name: Optional[str] = None
    survey_date: date
    send_date: Optional[date] = None
    send_method: Optional[str] = None
    deadline: Optional[date] = None
    status: str
    response_date: Optional[date] = None
    overall_score: Optional[Decimal] = None
    scores: Optional[Dict] = None
    feedback: Optional[str] = None
    suggestions: Optional[str] = None
    created_by: int
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 仪表板统计 ====================

class ServiceDashboardStatistics(BaseModel):
    """客服部门仪表板统计"""
    active_cases: int = Field(0, description="活跃案例数")
    resolved_today: int = Field(0, description="今日解决案例数")
    pending_cases: int = Field(0, description="待处理案例数")
    avg_response_time: float = Field(0.0, description="平均响应时间（小时）")
    customer_satisfaction: float = Field(0.0, description="客户满意度")
    on_site_services: int = Field(0, description="现场服务次数")
    total_engineers: int = Field(0, description="服务工程师总数")
    active_engineers: int = Field(0, description="在岗工程师数")


# ==================== 知识库 ====================

class KnowledgeBaseCreate(BaseModel):
    """创建知识库文章"""
    title: str = Field(..., description="文章标题")
    category: str = Field(..., description="分类")
    content: str = Field(..., description="文章内容")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    is_faq: Optional[bool] = Field(False, description="是否FAQ")
    is_featured: Optional[bool] = Field(False, description="是否精选")
    status: Optional[str] = Field("DRAFT", description="状态")


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库文章"""
    title: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    is_faq: Optional[bool] = None
    is_featured: Optional[bool] = None
    status: Optional[str] = None


class KnowledgeBaseResponse(BaseModel):
    """知识库文章响应"""
    id: int
    article_no: str
    title: str
    category: str
    content: str
    tags: Optional[List[str]] = None
    is_faq: bool
    is_featured: bool
    status: str
    view_count: int
    like_count: int
    helpful_count: int
    author_id: int
    author_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True



