# -*- coding: utf-8 -*-
"""
工程师绩效评价模块 Pydantic Schemas
包含：请求/响应模型、数据验证
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

# ==================== 枚举值常量 ====================

JOB_TYPES = ['mechanical', 'test', 'electrical']
JOB_LEVELS = ['junior', 'intermediate', 'senior', 'expert']
CONTRIBUTION_TYPES = ['document', 'template', 'module', 'training', 'patent', 'standard']
CONTRIBUTION_STATUSES = ['draft', 'pending', 'approved', 'rejected']
REVIEW_RESULTS = ['passed', 'rejected', 'conditional']
ISSUE_SEVERITIES = ['critical', 'major', 'normal', 'minor']
ISSUE_STATUSES = ['open', 'in_progress', 'resolved', 'closed']
BUG_FOUND_STAGES = ['internal_debug', 'site_debug', 'acceptance', 'production']
PLC_BRANDS = ['siemens', 'mitsubishi', 'omron', 'beckhoff', 'inovance', 'delta']


# ==================== 基础 Schemas ====================

class EngineerProfileBase(BaseModel):
    """工程师档案基础"""
    job_type: str = Field(..., description="岗位类型")
    job_level: Optional[str] = Field('junior', description="职级")
    skills: Optional[List[str]] = Field(None, description="技能标签")
    certifications: Optional[List[str]] = Field(None, description="资质证书")
    job_start_date: Optional[date] = Field(None, description="岗位开始日期")
    level_start_date: Optional[date] = Field(None, description="级别开始日期")


class EngineerProfileCreate(EngineerProfileBase):
    """创建工程师档案"""
    user_id: int = Field(..., description="用户ID")


class EngineerProfileUpdate(BaseModel):
    """更新工程师档案"""
    job_type: Optional[str] = None
    job_level: Optional[str] = None
    skills: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    job_start_date: Optional[date] = None
    level_start_date: Optional[date] = None


class EngineerProfileResponse(EngineerProfileBase):
    """工程师档案响应"""
    id: int
    user_id: int
    user_name: Optional[str] = None
    department_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== 五维配置 Schemas ====================

class DimensionConfigBase(BaseModel):
    """五维权重配置基础"""
    job_type: str = Field(..., description="岗位类型")
    job_level: Optional[str] = Field(None, description="职级")
    department_id: Optional[int] = Field(None, description="部门ID（为空表示全局配置）")
    technical_weight: int = Field(30, ge=0, le=100, description="技术能力权重")
    execution_weight: int = Field(25, ge=0, le=100, description="项目执行权重")
    cost_quality_weight: int = Field(20, ge=0, le=100, description="成本质量权重")
    knowledge_weight: int = Field(15, ge=0, le=100, description="知识沉淀权重")
    collaboration_weight: int = Field(10, ge=0, le=100, description="团队协作权重")
    effective_date: date = Field(..., description="生效日期")
    config_name: Optional[str] = Field(None, description="配置名称")
    description: Optional[str] = Field(None, description="描述")


class DimensionConfigCreate(DimensionConfigBase):
    """创建五维配置"""
    pass


class DimensionConfigUpdate(BaseModel):
    """更新五维配置"""
    technical_weight: Optional[int] = Field(None, ge=0, le=100)
    execution_weight: Optional[int] = Field(None, ge=0, le=100)
    cost_quality_weight: Optional[int] = Field(None, ge=0, le=100)
    knowledge_weight: Optional[int] = Field(None, ge=0, le=100)
    collaboration_weight: Optional[int] = Field(None, ge=0, le=100)
    expired_date: Optional[date] = None
    description: Optional[str] = None


class DimensionConfigResponse(DimensionConfigBase):
    """五维配置响应"""
    id: int
    is_global: bool = Field(..., description="是否全局配置")
    expired_date: Optional[date] = None
    operator_id: Optional[int] = None
    approval_status: Optional[str] = Field(None, description="审批状态")
    affected_count: Optional[int] = Field(None, description="受影响人数")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== 跨部门协作 Schemas ====================

class CollaborationRatingBase(BaseModel):
    """跨部门协作评价基础"""
    ratee_id: int = Field(..., description="被评价人ID")
    communication_score: int = Field(..., ge=1, le=5, description="沟通配合")
    response_score: int = Field(..., ge=1, le=5, description="响应速度")
    delivery_score: int = Field(..., ge=1, le=5, description="交付质量")
    interface_score: int = Field(..., ge=1, le=5, description="接口规范")
    comment: Optional[str] = Field(None, description="评价备注")
    project_id: Optional[int] = Field(None, description="关联项目ID")


class CollaborationRatingCreate(CollaborationRatingBase):
    """创建跨部门评价"""
    period_id: int = Field(..., description="考核周期ID")


class CollaborationRatingResponse(CollaborationRatingBase):
    """跨部门评价响应"""
    id: int
    period_id: int
    rater_id: int
    rater_name: Optional[str] = None
    ratee_name: Optional[str] = None
    rater_job_type: Optional[str] = None
    ratee_job_type: Optional[str] = None
    total_score: Optional[Decimal] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CollaborationMatrixResponse(BaseModel):
    """协作矩阵响应"""
    period_id: int
    matrix: Dict[str, Dict[str, float]] = Field(..., description="协作评分矩阵")
    details: List[Dict[str, Any]] = Field(default_factory=list, description="详细评价")


# ==================== 知识贡献 Schemas ====================

class KnowledgeContributionBase(BaseModel):
    """知识贡献基础"""
    contribution_type: str = Field(..., description="贡献类型")
    job_type: Optional[str] = Field(None, description="所属岗位领域")
    title: str = Field(..., max_length=200, description="标题")
    description: Optional[str] = Field(None, description="描述")
    file_path: Optional[str] = Field(None, description="文件路径")
    tags: Optional[List[str]] = Field(None, description="标签")


class KnowledgeContributionCreate(KnowledgeContributionBase):
    """创建知识贡献"""
    pass


class KnowledgeContributionUpdate(BaseModel):
    """更新知识贡献"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    file_path: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None


class KnowledgeContributionResponse(KnowledgeContributionBase):
    """知识贡献响应"""
    id: int
    contributor_id: int
    contributor_name: Optional[str] = None
    reuse_count: int = 0
    rating_score: Optional[Decimal] = None
    rating_count: int = 0
    status: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeReuseCreate(BaseModel):
    """创建知识复用记录"""
    contribution_id: int = Field(..., description="贡献ID")
    project_id: Optional[int] = Field(None, description="项目ID")
    reuse_type: Optional[str] = Field(None, description="复用类型")
    rating: Optional[int] = Field(None, ge=1, le=5, description="评分")
    feedback: Optional[str] = Field(None, description="反馈")


# ==================== 设计评审 Schemas ====================

class DesignReviewBase(BaseModel):
    """设计评审基础"""
    project_id: Optional[int] = Field(None, description="项目ID")
    design_name: str = Field(..., max_length=200, description="设计名称")
    design_type: Optional[str] = Field(None, description="设计类型")
    design_code: Optional[str] = Field(None, description="设计编号")
    version: Optional[str] = Field(None, description="版本号")


class DesignReviewCreate(DesignReviewBase):
    """创建设计评审"""
    designer_id: int = Field(..., description="设计者ID")


class DesignReviewUpdate(BaseModel):
    """更新设计评审（评审结果）"""
    review_date: Optional[date] = None
    reviewer_id: Optional[int] = None
    result: Optional[str] = None
    is_first_pass: Optional[bool] = None
    issues_found: Optional[int] = None
    review_comments: Optional[str] = None


class DesignReviewResponse(DesignReviewBase):
    """设计评审响应"""
    id: int
    designer_id: int
    designer_name: Optional[str] = None
    review_date: Optional[date] = None
    reviewer_id: Optional[int] = None
    reviewer_name: Optional[str] = None
    result: Optional[str] = None
    is_first_pass: Optional[bool] = None
    issues_found: int = 0
    review_comments: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== 调试问题 Schemas ====================

class MechanicalDebugIssueBase(BaseModel):
    """机械调试问题基础"""
    project_id: Optional[int] = Field(None, description="项目ID")
    issue_description: str = Field(..., description="问题描述")
    severity: Optional[str] = Field(None, description="严重程度")
    root_cause: Optional[str] = Field(None, description="根本原因")
    affected_part: Optional[str] = Field(None, description="受影响零件")


class MechanicalDebugIssueCreate(MechanicalDebugIssueBase):
    """创建机械调试问题"""
    responsible_id: int = Field(..., description="责任人ID")
    found_date: Optional[date] = Field(None, description="发现日期")


class MechanicalDebugIssueUpdate(BaseModel):
    """更新机械调试问题"""
    status: Optional[str] = None
    resolved_date: Optional[date] = None
    resolution: Optional[str] = None
    cost_impact: Optional[Decimal] = None
    time_impact_hours: Optional[Decimal] = None


class MechanicalDebugIssueResponse(MechanicalDebugIssueBase):
    """机械调试问题响应"""
    id: int
    responsible_id: int
    responsible_name: Optional[str] = None
    reporter_id: Optional[int] = None
    issue_code: Optional[str] = None
    status: str
    found_date: Optional[date] = None
    resolved_date: Optional[date] = None
    resolution: Optional[str] = None
    cost_impact: Optional[Decimal] = None
    time_impact_hours: Optional[Decimal] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Bug记录 Schemas ====================

class TestBugRecordBase(BaseModel):
    """Bug记录基础"""
    project_id: Optional[int] = Field(None, description="项目ID")
    title: str = Field(..., max_length=200, description="标题")
    description: Optional[str] = Field(None, description="描述")
    severity: Optional[str] = Field(None, description="严重程度")
    bug_type: Optional[str] = Field(None, description="Bug类型")
    found_stage: Optional[str] = Field(None, description="发现阶段")
    priority: Optional[str] = Field('normal', description="优先级")


class TestBugRecordCreate(TestBugRecordBase):
    """创建Bug记录"""
    assignee_id: int = Field(..., description="处理人ID")
    found_time: Optional[datetime] = Field(None, description="发现时间")


class TestBugRecordUpdate(BaseModel):
    """更新Bug记录"""
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[int] = None
    resolved_time: Optional[datetime] = None
    fix_duration_hours: Optional[Decimal] = None
    resolution: Optional[str] = None


class TestBugRecordResponse(TestBugRecordBase):
    """Bug记录响应"""
    id: int
    bug_code: Optional[str] = None
    assignee_id: int
    assignee_name: Optional[str] = None
    reporter_id: Optional[int] = None
    reporter_name: Optional[str] = None
    status: str
    found_time: Optional[datetime] = None
    resolved_time: Optional[datetime] = None
    fix_duration_hours: Optional[Decimal] = None
    resolution: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== 代码模块 Schemas ====================

class CodeModuleBase(BaseModel):
    """代码模块基础"""
    module_name: str = Field(..., max_length=100, description="模块名称")
    category: Optional[str] = Field(None, description="分类")
    language: Optional[str] = Field(None, description="编程语言")
    description: Optional[str] = Field(None, description="描述")
    version: Optional[str] = Field(None, description="版本")
    repository_url: Optional[str] = Field(None, description="仓库地址")


class CodeModuleCreate(CodeModuleBase):
    """创建代码模块"""
    pass


class CodeModuleUpdate(BaseModel):
    """更新代码模块"""
    module_name: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    repository_url: Optional[str] = None
    status: Optional[str] = None


class CodeModuleResponse(CodeModuleBase):
    """代码模块响应"""
    id: int
    module_code: Optional[str] = None
    contributor_id: int
    contributor_name: Optional[str] = None
    reuse_count: int = 0
    rating_score: Optional[Decimal] = None
    rating_count: int = 0
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== PLC程序 Schemas ====================

class PlcProgramVersionBase(BaseModel):
    """PLC程序版本基础"""
    project_id: Optional[int] = Field(None, description="项目ID")
    program_name: str = Field(..., max_length=200, description="程序名称")
    plc_brand: Optional[str] = Field(None, description="PLC品牌")
    plc_model: Optional[str] = Field(None, description="PLC型号")
    version: Optional[str] = Field(None, description="版本")


class PlcProgramVersionCreate(PlcProgramVersionBase):
    """创建PLC程序版本"""
    programmer_id: int = Field(..., description="程序员ID")


class PlcProgramVersionUpdate(BaseModel):
    """更新PLC程序版本（调试结果）"""
    first_debug_date: Optional[date] = None
    is_first_pass: Optional[bool] = None
    debug_issues: Optional[int] = None
    debug_hours: Optional[Decimal] = None
    remarks: Optional[str] = None


class PlcProgramVersionResponse(PlcProgramVersionBase):
    """PLC程序版本响应"""
    id: int
    program_code: Optional[str] = None
    programmer_id: int
    programmer_name: Optional[str] = None
    first_debug_date: Optional[date] = None
    is_first_pass: Optional[bool] = None
    debug_issues: int = 0
    debug_hours: Optional[Decimal] = None
    remarks: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== PLC模块库 Schemas ====================

class PlcModuleLibraryBase(BaseModel):
    """PLC模块库基础"""
    module_name: str = Field(..., max_length=100, description="模块名称")
    category: Optional[str] = Field(None, description="分类")
    plc_brand: Optional[str] = Field(None, description="适用PLC品牌")
    description: Optional[str] = Field(None, description="描述")
    version: Optional[str] = Field(None, description="版本")
    file_path: Optional[str] = Field(None, description="文件路径")


class PlcModuleLibraryCreate(PlcModuleLibraryBase):
    """创建PLC模块"""
    pass


class PlcModuleLibraryUpdate(BaseModel):
    """更新PLC模块"""
    module_name: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    file_path: Optional[str] = None
    status: Optional[str] = None


class PlcModuleLibraryResponse(PlcModuleLibraryBase):
    """PLC模块响应"""
    id: int
    module_code: Optional[str] = None
    contributor_id: int
    contributor_name: Optional[str] = None
    reuse_count: int = 0
    rating_score: Optional[Decimal] = None
    rating_count: int = 0
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== 绩效汇总 Schemas ====================

class EngineerDimensionScore(BaseModel):
    """工程师五维得分（或方案工程师六维得分）"""
    technical_score: Decimal = Field(..., description="技术能力得分")
    execution_score: Decimal = Field(..., description="项目执行得分")
    cost_quality_score: Decimal = Field(..., description="成本质量得分")
    knowledge_score: Decimal = Field(..., description="知识沉淀得分")
    collaboration_score: Decimal = Field(..., description="团队协作得分")
    solution_success_score: Optional[Decimal] = Field(None, description="方案成功率得分（仅方案工程师）")


class EngineerPerformanceSummary(BaseModel):
    """工程师绩效汇总"""
    engineer_id: int
    engineer_name: str
    job_type: str
    job_level: str
    department_name: Optional[str] = None
    period_id: int
    period_name: str

    # 得分
    total_score: Decimal
    level: str  # S/A/B/C/D
    dimension_scores: EngineerDimensionScore

    # 排名
    dept_rank: Optional[int] = None
    job_type_rank: Optional[int] = None
    company_rank: Optional[int] = None

    # 环比
    score_change: Optional[Decimal] = None
    rank_change: Optional[int] = None


class CompanySummaryResponse(BaseModel):
    """公司整体概况响应"""
    period_id: int
    period_name: str
    total_engineers: int

    # 按岗位统计
    by_job_type: Dict[str, Dict[str, Any]]

    # 等级分布
    level_distribution: Dict[str, int]

    # 平均分
    avg_score: Decimal
    max_score: Decimal
    min_score: Decimal

    # Top 工程师
    top_engineers: List[EngineerPerformanceSummary]


class RankingQueryParams(BaseModel):
    """排名查询参数"""
    period_id: Optional[int] = Field(None, description="考核周期ID")
    job_type: Optional[str] = Field(None, description="岗位类型")
    job_level: Optional[str] = Field(None, description="职级")
    department_id: Optional[int] = Field(None, description="部门ID")
    limit: int = Field(20, ge=1, le=100, description="返回数量")
    offset: int = Field(0, ge=0, description="偏移量")


class RankingResponse(BaseModel):
    """排名响应"""
    total: int
    items: List[EngineerPerformanceSummary]
    period_id: int
    period_name: str


class EngineerTrendResponse(BaseModel):
    """工程师趋势响应"""
    engineer_id: int
    engineer_name: str
    trends: List[Dict[str, Any]] = Field(..., description="历史趋势数据")


class EngineerComparisonResponse(BaseModel):
    """工程师对比响应"""
    engineer_id: int
    engineer_name: str
    job_type: str
    job_level: str

    # 个人得分
    scores: EngineerDimensionScore
    total_score: Decimal

    # 同岗位平均
    job_type_avg: EngineerDimensionScore
    job_type_avg_total: Decimal

    # 同级别平均
    job_level_avg: EngineerDimensionScore
    job_level_avg_total: Decimal


# ==================== 计算任务 Schemas ====================

class CalculateTaskCreate(BaseModel):
    """创建计算任务"""
    period_id: int = Field(..., description="考核周期ID")
    job_types: Optional[List[str]] = Field(None, description="指定岗位类型")
    force_recalculate: bool = Field(False, description="是否强制重新计算")


class CalculateTaskStatus(BaseModel):
    """计算任务状态"""
    task_id: str
    status: str  # pending/running/completed/failed
    progress: int = Field(0, ge=0, le=100)
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
