# -*- coding: utf-8 -*-
"""
知识自动沉淀模块 - Pydantic Schemas
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import PaginatedResponse


# ── 知识条目 ──


class KnowledgeEntryBase(BaseModel):
    """知识条目基础模型"""

    knowledge_type: str = Field(..., description="知识类型：RISK_RESPONSE/ISSUE_SOLUTION/CHANGE_PATTERN/DELAY_CAUSE/BEST_PRACTICE/PITFALL")
    source_type: str = Field(..., description="来源类型：RISK/ISSUE/ECN/LOG/REVIEW/MANUAL")
    title: str = Field(..., max_length=300, description="标题")
    summary: str = Field(..., description="摘要")
    detail: Optional[str] = Field(None, description="详细内容")
    problem_description: Optional[str] = Field(None, description="问题描述")
    solution: Optional[str] = Field(None, description="解决方案")
    root_cause: Optional[str] = Field(None, description="根因分析")
    impact: Optional[str] = Field(None, description="影响范围")
    prevention: Optional[str] = Field(None, description="预防措施")
    source_project_id: Optional[int] = Field(None, description="来源项目ID")
    project_type: Optional[str] = Field(None, description="适用项目类型")
    product_category: Optional[str] = Field(None, description="适用产品类别")
    industry: Optional[str] = Field(None, description="适用行业")
    customer_id: Optional[int] = Field(None, description="关联客户ID")
    applicable_stages: Optional[List[str]] = Field(None, description="适用阶段列表")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    risk_type: Optional[str] = Field(None, description="风险类型")
    issue_category: Optional[str] = Field(None, description="问题分类")
    change_type: Optional[str] = Field(None, description="变更类型")


class KnowledgeEntryCreate(KnowledgeEntryBase):
    """创建知识条目"""

    pass


class KnowledgeEntryUpdate(BaseModel):
    """更新知识条目"""

    title: Optional[str] = Field(None, max_length=300, description="标题")
    summary: Optional[str] = Field(None, description="摘要")
    detail: Optional[str] = Field(None, description="详细内容")
    problem_description: Optional[str] = Field(None, description="问题描述")
    solution: Optional[str] = Field(None, description="解决方案")
    root_cause: Optional[str] = Field(None, description="根因分析")
    impact: Optional[str] = Field(None, description="影响范围")
    prevention: Optional[str] = Field(None, description="预防措施")
    project_type: Optional[str] = Field(None, description="适用项目类型")
    product_category: Optional[str] = Field(None, description="适用产品类别")
    industry: Optional[str] = Field(None, description="适用行业")
    applicable_stages: Optional[List[str]] = Field(None, description="适用阶段列表")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    status: Optional[str] = Field(None, description="状态")


class KnowledgeEntryResponse(KnowledgeEntryBase):
    """知识条目响应"""

    id: int
    entry_code: str
    source_record_id: Optional[int] = None
    source_record_type: Optional[str] = None
    view_count: int = 0
    cite_count: int = 0
    usefulness_score: float = 0.0
    vote_count: int = 0
    status: str
    ai_generated: bool = False
    ai_confidence: Optional[float] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # 展开字段
    source_project_name: Optional[str] = None
    customer_name: Optional[str] = None

    class Config:
        from_attributes = True


class KnowledgeEntryListResponse(PaginatedResponse):
    """知识条目列表响应"""

    items: List[KnowledgeEntryResponse] = []


# ── 坑点预警 ──


class KnowledgeAlertResponse(BaseModel):
    """预警响应"""

    id: int
    target_project_id: int
    knowledge_entry_id: int
    match_reason: Optional[str] = None
    match_score: float = 0.0
    is_read: bool = False
    is_adopted: Optional[bool] = None
    feedback: Optional[str] = None
    created_at: Optional[datetime] = None

    # 展开的知识条目摘要
    entry_title: Optional[str] = None
    entry_summary: Optional[str] = None
    entry_type: Optional[str] = None

    class Config:
        from_attributes = True


class KnowledgeAlertFeedback(BaseModel):
    """预警反馈"""

    is_adopted: bool = Field(..., description="是否采纳")
    feedback: Optional[str] = Field(None, description="反馈内容")


# ── 提取请求/响应 ──


class ExtractionRequest(BaseModel):
    """知识提取请求"""

    project_id: int = Field(..., description="项目ID")
    extract_risks: bool = Field(True, description="是否提取风险经验")
    extract_issues: bool = Field(True, description="是否提取问题经验")
    extract_ecns: bool = Field(True, description="是否提取变更经验")
    extract_logs: bool = Field(True, description="是否提取延误经验")
    auto_publish: bool = Field(False, description="是否自动发布")


class ExtractionResult(BaseModel):
    """知识提取结果"""

    project_id: int
    total_extracted: int = 0
    risk_entries: int = 0
    issue_entries: int = 0
    change_entries: int = 0
    delay_entries: int = 0
    entries: List[KnowledgeEntryResponse] = []


class BestPracticeInductionResult(BaseModel):
    """最佳实践归纳结果"""

    total_projects_analyzed: int = 0
    high_perf_projects: int = 0
    on_time_projects: int = 0
    budget_controlled_projects: int = 0
    best_practices_generated: int = 0
    entries: List[KnowledgeEntryResponse] = []


class PitfallAlertResult(BaseModel):
    """坑点预警结果"""

    target_project_id: int
    alerts_generated: int = 0
    alerts: List[KnowledgeAlertResponse] = []


# ── 搜索 ──


class KnowledgeSearchRequest(BaseModel):
    """知识检索请求"""

    keyword: Optional[str] = Field(None, description="关键词搜索")
    knowledge_type: Optional[str] = Field(None, description="知识类型筛选")
    source_type: Optional[str] = Field(None, description="来源类型筛选")
    project_type: Optional[str] = Field(None, description="项目类型筛选")
    product_category: Optional[str] = Field(None, description="产品类别筛选")
    industry: Optional[str] = Field(None, description="行业筛选")
    customer_id: Optional[int] = Field(None, description="客户ID筛选")
    risk_type: Optional[str] = Field(None, description="风险类型筛选")
    issue_category: Optional[str] = Field(None, description="问题分类筛选")
    change_type: Optional[str] = Field(None, description="变更类型筛选")
    tags: Optional[List[str]] = Field(None, description="标签筛选")
    status: Optional[str] = Field(None, description="状态筛选")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页条数")
