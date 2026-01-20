"""
问题管理中心模块 - Pydantic Schemas
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

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
    service_ticket_id: Optional[int] = Field(None, description="关联服务工单ID")

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

    # 问题原因和责任工程师
    root_cause: Optional[str] = Field(None, description="问题原因：DESIGN_ERROR/MATERIAL_DEFECT/PROCESS_ERROR/EXTERNAL_FACTOR/OTHER")
    responsible_engineer_id: Optional[int] = Field(None, description="责任工程师ID")
    responsible_engineer_name: Optional[str] = Field(None, description="责任工程师姓名")
    estimated_inventory_loss: Optional[Decimal] = Field(None, description="预估库存损失金额")
    estimated_extra_hours: Optional[Decimal] = Field(None, description="预估额外工时(小时)")

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
    root_cause: Optional[str] = None
    responsible_engineer_id: Optional[int] = None
    responsible_engineer_name: Optional[str] = None
    estimated_inventory_loss: Optional[Decimal] = None
    estimated_extra_hours: Optional[Decimal] = None
    attachments: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    service_ticket_id: Optional[int] = None


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
    service_ticket_id: Optional[int] = None
    service_ticket_no: Optional[str] = None

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

    @field_validator('total', 'open', 'processing', 'resolved', 'closed', 'overdue', 'blocking', mode='before')
    @classmethod
    def convert_none_to_zero(cls, v):
        """Convert None to 0 for integer fields"""
        return v if v is not None else 0


class EngineerIssueStatistics(BaseModel):
    """工程师问题统计"""
    engineer_id: int
    engineer_name: str
    total_issues: int = 0  # 总问题数
    design_issues: int = 0  # 设计问题数
    total_inventory_loss: Decimal = Decimal(0)  # 总库存损失
    total_extra_hours: Decimal = Decimal(0)  # 总额外工时
    issues: List[IssueResponse] = []  # 问题列表


# ==================== 问题模板相关 Schema ====================

class IssueTemplateBase(BaseModel):
    """问题模板基础模型"""
    template_name: str = Field(..., max_length=100, description="模板名称")
    template_code: str = Field(..., max_length=50, description="模板编码")
    category: str = Field(..., description="问题分类")
    issue_type: str = Field(..., description="问题类型")
    default_severity: Optional[str] = Field(None, description="默认严重程度")
    default_priority: str = Field(default="MEDIUM", description="默认优先级")
    default_impact_level: Optional[str] = Field(None, description="默认影响级别")
    title_template: str = Field(..., max_length=200, description="标题模板")
    description_template: Optional[str] = Field(None, description="描述模板")
    solution_template: Optional[str] = Field(None, description="解决方案模板")
    default_tags: Optional[List[str]] = Field(default=[], description="默认标签")
    default_impact_scope: Optional[str] = Field(None, description="默认影响范围")
    default_is_blocking: bool = Field(default=False, description="默认是否阻塞")
    is_active: bool = Field(default=True, description="是否启用")
    remark: Optional[str] = Field(None, description="备注说明")


class IssueTemplateCreate(IssueTemplateBase):
    """创建问题模板"""
    pass


class IssueTemplateUpdate(BaseModel):
    """更新问题模板"""
    template_name: Optional[str] = None
    category: Optional[str] = None
    issue_type: Optional[str] = None
    default_severity: Optional[str] = None
    default_priority: Optional[str] = None
    default_impact_level: Optional[str] = None
    title_template: Optional[str] = None
    description_template: Optional[str] = None
    solution_template: Optional[str] = None
    default_tags: Optional[List[str]] = None
    default_impact_scope: Optional[str] = None
    default_is_blocking: Optional[bool] = None
    is_active: Optional[bool] = None
    remark: Optional[str] = None


class IssueTemplateResponse(IssueTemplateBase):
    """问题模板响应模型"""
    id: int
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IssueTemplateListResponse(PaginatedResponse[IssueTemplateResponse]):
    """问题模板列表响应"""
    pass


class IssueFromTemplateRequest(BaseModel):
    """从模板创建问题请求（template_id在路径参数中）"""
    project_id: Optional[int] = Field(None, description="关联项目ID")
    machine_id: Optional[int] = Field(None, description="关联机台ID")
    task_id: Optional[int] = Field(None, description="关联任务ID")
    acceptance_order_id: Optional[int] = Field(None, description="关联验收单ID")
    assignee_id: Optional[int] = Field(None, description="处理负责人ID")
    due_date: Optional[date] = Field(None, description="要求完成日期")
    # 可以覆盖模板的默认值
    severity: Optional[str] = Field(None, description="严重程度（覆盖模板默认值）")
    priority: Optional[str] = Field(None, description="优先级（覆盖模板默认值）")
    title: Optional[str] = Field(None, description="标题（覆盖模板默认值）")
    description: Optional[str] = Field(None, description="描述（覆盖模板默认值）")


# ==================== 问题统计快照相关 Schema ====================

class IssueStatisticsSnapshotResponse(BaseModel):
    """问题统计快照响应模型"""
    id: int
    snapshot_date: date
    total_issues: int
    open_issues: int
    processing_issues: int
    resolved_issues: int
    closed_issues: int
    cancelled_issues: int
    deferred_issues: int
    critical_issues: int
    major_issues: int
    minor_issues: int
    urgent_issues: int
    high_priority_issues: int
    medium_priority_issues: int
    low_priority_issues: int
    defect_issues: int
    risk_issues: int
    blocker_issues: int
    blocking_issues: int
    overdue_issues: int
    project_issues: int
    task_issues: int
    acceptance_issues: int
    avg_response_time: Optional[Decimal] = None
    avg_resolve_time: Optional[Decimal] = None
    avg_verify_time: Optional[Decimal] = None
    status_distribution: Optional[dict] = None
    severity_distribution: Optional[dict] = None
    priority_distribution: Optional[dict] = None
    category_distribution: Optional[dict] = None
    project_distribution: Optional[dict] = None
    new_issues_today: int = 0
    resolved_today: int = 0
    closed_today: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IssueStatisticsSnapshotListResponse(PaginatedResponse[IssueStatisticsSnapshotResponse]):
    """问题统计快照列表响应"""
    pass

