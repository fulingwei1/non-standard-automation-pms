# -*- coding: utf-8 -*-
"""
AI驱动人员智能匹配系统 Pydantic Schemas
包含：标签字典、员工标签评估、员工扩展档案、项目绩效历史、项目人员需求、AI匹配
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

from pydantic import BaseModel, Field

# ==================== 标签字典 Schemas ====================

class TagDictBase(BaseModel):
    """标签字典基础"""
    tag_code: str = Field(..., max_length=50, description="标签编码")
    tag_name: str = Field(..., max_length=100, description="标签名称")
    tag_type: str = Field(..., description="标签类型 (SKILL/DOMAIN/ATTITUDE/CHARACTER/SPECIAL)")
    parent_id: Optional[int] = Field(None, description="父标签ID")
    weight: Optional[Decimal] = Field(1.0, description="权重")
    is_required: Optional[bool] = Field(False, description="是否必需标签")
    description: Optional[str] = Field(None, description="标签描述")
    sort_order: Optional[int] = Field(0, description="排序")


class TagDictCreate(TagDictBase):
    """创建标签"""
    pass


class TagDictUpdate(BaseModel):
    """更新标签"""
    tag_name: Optional[str] = Field(None, max_length=100)
    parent_id: Optional[int] = None
    weight: Optional[Decimal] = None
    is_required: Optional[bool] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class TagDictResponse(TagDictBase):
    """标签响应"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TagDictTreeNode(BaseModel):
    """标签树节点"""
    id: int
    tag_code: str
    tag_name: str
    tag_type: str
    weight: Decimal
    is_required: bool
    sort_order: int
    children: List['TagDictTreeNode'] = []

    class Config:
        from_attributes = True


# ==================== 员工标签评估 Schemas ====================

class EmployeeTagEvaluationBase(BaseModel):
    """员工标签评估基础"""
    employee_id: int = Field(..., description="员工ID")
    tag_id: int = Field(..., description="标签ID")
    score: int = Field(..., ge=1, le=5, description="评分1-5")
    evidence: Optional[str] = Field(None, description="评分依据/证据")
    evaluate_date: date = Field(..., description="评估日期")


class EmployeeTagEvaluationCreate(EmployeeTagEvaluationBase):
    """创建员工标签评估"""
    pass


class EmployeeTagEvaluationBatch(BaseModel):
    """批量创建员工标签评估"""
    employee_id: int
    evaluations: List[dict] = Field(..., description="评估列表 [{tag_id, score, evidence}]")
    evaluate_date: date


class EmployeeTagEvaluationUpdate(BaseModel):
    """更新员工标签评估"""
    score: Optional[int] = Field(None, ge=1, le=5)
    evidence: Optional[str] = None
    is_valid: Optional[bool] = None


class EmployeeTagEvaluationResponse(EmployeeTagEvaluationBase):
    """员工标签评估响应"""
    id: int
    evaluator_id: int
    is_valid: bool
    created_at: datetime
    # 关联信息
    tag_name: Optional[str] = None
    tag_type: Optional[str] = None
    evaluator_name: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== 员工扩展档案 Schemas ====================

class TagScore(BaseModel):
    """标签得分"""
    tag_id: int
    tag_code: str
    tag_name: str
    score: float
    weight: Optional[float] = 1.0


class EmployeeProfileBase(BaseModel):
    """员工档案基础"""
    employee_id: int


class EmployeeProfileUpdate(BaseModel):
    """更新员工档案"""
    current_workload_pct: Optional[Decimal] = None
    available_hours: Optional[Decimal] = None


class EmployeeProfileResponse(BaseModel):
    """员工档案响应"""
    id: int
    employee_id: int

    # 各类标签
    skill_tags: Optional[List[TagScore]] = None
    domain_tags: Optional[List[TagScore]] = None
    attitude_tags: Optional[List[TagScore]] = None
    character_tags: Optional[List[TagScore]] = None
    special_tags: Optional[List[TagScore]] = None

    # 聚合得分
    attitude_score: Optional[Decimal] = None
    quality_score: Optional[Decimal] = None

    # 工作负载
    current_workload_pct: Optional[Decimal] = None
    available_hours: Optional[Decimal] = None

    # 统计
    total_projects: int = 0
    avg_performance_score: Optional[Decimal] = None

    profile_updated_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EmployeeProfileSummary(BaseModel):
    """员工档案摘要（列表用）"""
    id: int
    employee_id: int
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    department: Optional[str] = None
    # 员工状态
    employment_status: Optional[str] = "active"  # active(在职), resigned(离职)
    employment_type: Optional[str] = "regular"  # regular(正式), probation(试用期), intern(实习期)

    # 主要技能（前3个）
    top_skills: Optional[List[str]] = None
    # 聚合得分
    attitude_score: Optional[Decimal] = None
    quality_score: Optional[Decimal] = None
    # 工作负载
    current_workload_pct: Optional[Decimal] = None
    available_hours: Optional[Decimal] = None
    # 统计
    total_projects: int = 0
    avg_performance_score: Optional[Decimal] = None

    class Config:
        from_attributes = True


# ==================== 项目绩效历史 Schemas ====================

class ProjectPerformanceBase(BaseModel):
    """项目绩效基础"""
    employee_id: int
    project_id: int
    role_code: str
    role_name: Optional[str] = None


class ProjectPerformanceCreate(ProjectPerformanceBase):
    """创建项目绩效"""
    performance_score: Optional[Decimal] = None
    quality_score: Optional[Decimal] = None
    collaboration_score: Optional[Decimal] = None
    on_time_rate: Optional[Decimal] = None
    contribution_level: Optional[str] = None
    hours_spent: Optional[Decimal] = None
    evaluation_date: Optional[date] = None
    comments: Optional[str] = None


class ProjectPerformanceUpdate(BaseModel):
    """更新项目绩效"""
    performance_score: Optional[Decimal] = None
    quality_score: Optional[Decimal] = None
    collaboration_score: Optional[Decimal] = None
    on_time_rate: Optional[Decimal] = None
    contribution_level: Optional[str] = None
    hours_spent: Optional[Decimal] = None
    comments: Optional[str] = None


class ProjectPerformanceResponse(ProjectPerformanceBase):
    """项目绩效响应"""
    id: int
    performance_score: Optional[Decimal] = None
    quality_score: Optional[Decimal] = None
    collaboration_score: Optional[Decimal] = None
    on_time_rate: Optional[Decimal] = None
    contribution_level: Optional[str] = None
    hours_spent: Optional[Decimal] = None
    evaluation_date: Optional[date] = None
    evaluator_id: Optional[int] = None
    comments: Optional[str] = None
    created_at: datetime
    # 关联信息
    project_name: Optional[str] = None
    employee_name: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== 项目人员需求 Schemas ====================

class SkillRequirement(BaseModel):
    """技能要求"""
    tag_id: int
    tag_code: Optional[str] = None
    tag_name: Optional[str] = None
    min_score: int = Field(3, ge=1, le=5, description="最低评分要求")


class StaffingNeedBase(BaseModel):
    """人员需求基础"""
    project_id: int
    role_code: str
    role_name: Optional[str] = None
    headcount: int = Field(1, ge=1)


class StaffingNeedCreate(StaffingNeedBase):
    """创建人员需求"""
    required_skills: List[SkillRequirement] = Field(..., description="必需技能")
    preferred_skills: Optional[List[SkillRequirement]] = None
    required_domains: Optional[List[SkillRequirement]] = None
    required_attitudes: Optional[List[SkillRequirement]] = None
    min_level: Optional[str] = None
    priority: str = Field('P3', description="优先级 P1-P5")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    allocation_pct: Decimal = Field(100, ge=0, le=100)
    remark: Optional[str] = None


class StaffingNeedUpdate(BaseModel):
    """更新人员需求"""
    role_name: Optional[str] = None
    headcount: Optional[int] = None
    required_skills: Optional[List[SkillRequirement]] = None
    preferred_skills: Optional[List[SkillRequirement]] = None
    required_domains: Optional[List[SkillRequirement]] = None
    required_attitudes: Optional[List[SkillRequirement]] = None
    min_level: Optional[str] = None
    priority: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    allocation_pct: Optional[Decimal] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class StaffingNeedResponse(StaffingNeedBase):
    """人员需求响应"""
    id: int
    required_skills: Optional[List[dict]] = None
    preferred_skills: Optional[List[dict]] = None
    required_domains: Optional[List[dict]] = None
    required_attitudes: Optional[List[dict]] = None
    min_level: Optional[str] = None
    priority: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    allocation_pct: Decimal
    status: str
    requester_id: Optional[int] = None
    filled_count: int = 0
    remark: Optional[str] = None
    created_at: datetime
    # 关联信息
    project_name: Optional[str] = None
    requester_name: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== AI匹配 Schemas ====================

class DimensionScores(BaseModel):
    """维度得分"""
    skill: float = Field(..., description="技能匹配分 (30%权重)")
    domain: float = Field(..., description="领域匹配分 (15%权重)")
    attitude: float = Field(..., description="态度评分 (20%权重)")
    quality: float = Field(..., description="质量评分 (15%权重)")
    workload: float = Field(..., description="工作负载分 (15%权重)")
    special: float = Field(..., description="特殊能力分 (5%权重)")


class CandidateScore(BaseModel):
    """候选人得分"""
    employee_id: int
    employee_name: str
    employee_code: Optional[str] = None
    department: Optional[str] = None
    total_score: float
    dimension_scores: DimensionScores
    rank: int
    recommendation_type: str  # STRONG/RECOMMENDED/ACCEPTABLE/WEAK
    # 详细信息
    matched_skills: Optional[List[str]] = None
    missing_skills: Optional[List[str]] = None
    current_workload_pct: Optional[float] = None
    available_hours: Optional[float] = None


class MatchingRequest(BaseModel):
    """匹配请求"""
    staffing_need_id: int
    top_n: int = Field(10, ge=1, le=50, description="返回候选人数量")
    include_overloaded: bool = Field(False, description="是否包含超负荷员工")


class MatchingResult(BaseModel):
    """匹配结果"""
    request_id: str
    staffing_need_id: int
    project_id: int
    project_name: Optional[str] = None
    role_code: str
    role_name: Optional[str] = None
    priority: str
    priority_threshold: int  # 优先级对应的最低分阈值
    candidates: List[CandidateScore]
    total_candidates: int
    qualified_count: int  # 达到阈值的候选人数
    matching_time: datetime


class MatchingAcceptRequest(BaseModel):
    """采纳候选人请求"""
    matching_log_id: int
    staffing_need_id: int
    employee_id: int


class MatchingRejectRequest(BaseModel):
    """拒绝候选人请求"""
    matching_log_id: int
    reject_reason: str


class MatchingLogResponse(BaseModel):
    """匹配日志响应"""
    id: int
    request_id: str
    project_id: int
    staffing_need_id: int
    candidate_employee_id: int
    total_score: Decimal
    dimension_scores: dict
    rank: int
    recommendation_type: Optional[str] = None
    is_accepted: Optional[bool] = None
    accept_time: Optional[datetime] = None
    acceptor_id: Optional[int] = None
    reject_reason: Optional[str] = None
    matching_time: datetime
    # 关联信息
    project_name: Optional[str] = None
    employee_name: Optional[str] = None
    acceptor_name: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== 统计和仪表板 Schemas ====================

class TagStatistics(BaseModel):
    """标签统计"""
    tag_type: str
    total_count: int
    active_count: int
    used_count: int  # 被评估使用的次数


class MatchingStatistics(BaseModel):
    """匹配统计"""
    total_requests: int
    total_candidates_matched: int
    accepted_count: int
    rejected_count: int
    pending_count: int
    avg_score: Optional[float] = None
    success_rate: Optional[float] = None  # 采纳率


class StaffingDashboard(BaseModel):
    """人员匹配仪表板"""
    # 需求统计
    open_needs: int
    matching_needs: int
    filled_needs: int
    total_headcount_needed: int
    total_headcount_filled: int

    # 按优先级统计
    needs_by_priority: dict  # {P1: 3, P2: 5, ...}

    # 匹配统计
    matching_stats: MatchingStatistics

    # 最近匹配
    recent_matches: List[MatchingLogResponse]


# ==================== 分页响应 ====================

class PaginatedResponse(BaseModel):
    """分页响应"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
