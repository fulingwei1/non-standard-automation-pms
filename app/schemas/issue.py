"""
问题管理中心模块 - Pydantic Schemas
"""
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field
from app.schemas.common import PaginatedResponse


# ==================== 问题相关 Schema ====================

class IssueBase(BaseModel):
    """问题基础模型"""
    category: str = Field(..., description="问题分类")
    project_id: Optional[int] = Field(None, description="关联项目ID")
    machine_id: Optional[int] = Field(None, description="关联机台ID")
    task_id: Optional[int] = Field(None, description="关联任务ID")
    acceptance_order_id: Optional[int] = Field(None, description="关联验收单ID")
    related_issue_id: Optional[int] = Field(None, description="关联问题ID")
    
    issue_type: str = Field(..., description="问题类型")
    severity: str = Field(..., description="严重程度")
    priority: str = Field(default="MEDIUM", description="优先级")
    title: str = Field(..., max_length=200, description="问题标题")
    description: str = Field(..., description="问题描述")
    
    assignee_id: Optional[int] = Field(None, description="处理负责人ID")
    due_date: Optional[date] = Field(None, description="要求完成日期")
    
    impact_scope: Optional[str] = Field(None, description="影响范围")
    impact_level: Optional[str] = Field(None, description="影响级别")
    is_blocking: bool = Field(default=False, description="是否阻塞")
    
    attachments: Optional[List[str]] = Field(default=[], description="附件列表")
    tags: Optional[List[str]] = Field(default=[], description="标签列表")


class IssueCreate(IssueBase):
    """创建问题"""
    pass


class IssueUpdate(BaseModel):
    """更新问题"""
    issue_type: Optional[str] = None
    severity: Optional[str] = None
    priority: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    solution: Optional[str] = None
    impact_scope: Optional[str] = None
    impact_level: Optional[str] = None
    is_blocking: Optional[bool] = None
    attachments: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class IssueResponse(IssueBase):
    """问题响应模型"""
    id: int
    issue_no: str
    reporter_id: int
    reporter_name: Optional[str] = None
    report_date: datetime
    assignee_name: Optional[str] = None
    status: str
    solution: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolved_by_name: Optional[str] = None
    verified_at: Optional[datetime] = None
    verified_by: Optional[int] = None
    verified_by_name: Optional[str] = None
    verified_result: Optional[str] = None
    follow_up_count: int = 0
    last_follow_up_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # 关联信息
    project_code: Optional[str] = None
    project_name: Optional[str] = None
    machine_code: Optional[str] = None
    machine_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ==================== 问题跟进相关 Schema ====================

class IssueFollowUpBase(BaseModel):
    """问题跟进基础模型"""
    follow_up_type: str = Field(..., description="跟进类型")
    content: str = Field(..., description="跟进内容")
    old_status: Optional[str] = Field(None, description="原状态")
    new_status: Optional[str] = Field(None, description="新状态")
    attachments: Optional[List[str]] = Field(default=[], description="附件列表")


class IssueFollowUpCreate(IssueFollowUpBase):
    """创建问题跟进"""
    issue_id: int


class IssueFollowUpResponse(IssueFollowUpBase):
    """问题跟进响应模型"""
    id: int
    issue_id: int
    operator_id: int
    operator_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== 问题操作相关 Schema ====================

class IssueAssignRequest(BaseModel):
    """分配问题请求"""
    assignee_id: int = Field(..., description="处理负责人ID")
    due_date: Optional[date] = Field(None, description="要求完成日期")
    comment: Optional[str] = Field(None, description="分配说明")


class IssueResolveRequest(BaseModel):
    """解决问题请求"""
    solution: str = Field(..., description="解决方案")
    comment: Optional[str] = Field(None, description="解决说明")


class IssueVerifyRequest(BaseModel):
    """验证问题请求"""
    verified_result: str = Field(..., description="验证结果：VERIFIED/REJECTED")
    comment: Optional[str] = Field(None, description="验证说明")


class IssueStatusChangeRequest(BaseModel):
    """问题状态变更请求"""
    status: str = Field(..., description="新状态")
    comment: Optional[str] = Field(None, description="状态变更说明")


# ==================== 问题查询相关 Schema ====================

class IssueFilterParams(BaseModel):
    """问题筛选参数"""
    category: Optional[str] = None
    project_id: Optional[int] = None
    machine_id: Optional[int] = None
    task_id: Optional[int] = None
    issue_type: Optional[str] = None
    severity: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assignee_id: Optional[int] = None
    reporter_id: Optional[int] = None
    is_blocking: Optional[bool] = None
    is_overdue: Optional[bool] = None
    keyword: Optional[str] = None
    tags: Optional[List[str]] = None


class IssueListResponse(PaginatedResponse[IssueResponse]):
    """问题列表响应"""
    pass


class IssueStatistics(BaseModel):
    """问题统计"""
    total: int = 0
    open: int = 0
    processing: int = 0
    resolved: int = 0
    closed: int = 0
    overdue: int = 0
    blocking: int = 0
    by_severity: dict = {}
    by_category: dict = {}
    by_type: dict = {}

