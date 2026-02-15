"""
售前AI知识库相关的Pydantic模型
"""
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ============= 知识库案例相关 =============

class KnowledgeCaseBase(BaseModel):
    """案例基础模型"""
    case_name: str = Field(..., description="案例名称")
    industry: Optional[str] = Field(None, description="行业分类")
    equipment_type: Optional[str] = Field(None, description="设备类型")
    customer_name: Optional[str] = Field(None, description="客户名称")
    project_amount: Optional[float] = Field(None, description="项目金额")
    project_summary: Optional[str] = Field(None, description="项目摘要")
    technical_highlights: Optional[str] = Field(None, description="技术亮点")
    success_factors: Optional[str] = Field(None, description="成功要素")
    lessons_learned: Optional[str] = Field(None, description="失败教训")
    tags: Optional[List[str]] = Field(None, description="标签数组")
    quality_score: Optional[float] = Field(0.5, ge=0, le=1, description="案例质量评分")
    is_public: Optional[bool] = Field(True, description="是否公开")


class KnowledgeCaseCreate(KnowledgeCaseBase):
    """创建案例"""
    pass


class KnowledgeCaseUpdate(BaseModel):
    """更新案例"""
    case_name: Optional[str] = None
    industry: Optional[str] = None
    equipment_type: Optional[str] = None
    customer_name: Optional[str] = None
    project_amount: Optional[float] = None
    project_summary: Optional[str] = None
    technical_highlights: Optional[str] = None
    success_factors: Optional[str] = None
    lessons_learned: Optional[str] = None
    tags: Optional[List[str]] = None
    quality_score: Optional[float] = Field(None, ge=0, le=1)
    is_public: Optional[bool] = None


class KnowledgeCaseResponse(KnowledgeCaseBase):
    """案例响应"""
    id: int
    created_at: datetime
    updated_at: datetime
    similarity_score: Optional[float] = Field(None, description="相似度评分（仅搜索时）")

    class Config:
        from_attributes = True


# ============= 语义搜索相关 =============

class SemanticSearchRequest(BaseModel):
    """语义搜索请求"""
    query: str = Field(..., description="搜索查询")
    industry: Optional[str] = Field(None, description="行业筛选")
    equipment_type: Optional[str] = Field(None, description="设备类型筛选")
    min_amount: Optional[float] = Field(None, description="最小金额")
    max_amount: Optional[float] = Field(None, description="最大金额")
    top_k: Optional[int] = Field(10, ge=1, le=50, description="返回前K个结果")


class SemanticSearchResponse(BaseModel):
    """语义搜索响应"""
    cases: List[KnowledgeCaseResponse]
    total: int
    query: str
    search_method: str = Field(default="semantic", description="搜索方法")


# ============= 最佳实践推荐相关 =============

class BestPracticeRequest(BaseModel):
    """最佳实践推荐请求"""
    scenario: str = Field(..., description="应用场景描述")
    industry: Optional[str] = None
    equipment_type: Optional[str] = None
    top_k: Optional[int] = Field(5, ge=1, le=20)


class BestPracticeResponse(BaseModel):
    """最佳实践推荐响应"""
    recommended_cases: List[KnowledgeCaseResponse]
    success_pattern_analysis: str = Field(..., description="成功模式分析")
    risk_warnings: List[str] = Field(default_factory=list, description="风险警告")


# ============= 知识提取相关 =============

class KnowledgeExtractionRequest(BaseModel):
    """知识提取请求"""
    project_data: dict = Field(..., description="项目数据")
    auto_save: Optional[bool] = Field(True, description="是否自动保存到知识库")


class KnowledgeExtractionResponse(BaseModel):
    """知识提取响应"""
    extracted_case: KnowledgeCaseCreate
    extraction_confidence: float = Field(..., ge=0, le=1, description="提取置信度")
    suggested_tags: List[str]
    quality_assessment: str


# ============= 智能问答相关 =============

class AIQARequest(BaseModel):
    """智能问答请求"""
    question: str = Field(..., description="问题")
    context: Optional[dict] = Field(None, description="上下文信息")


class AIQAResponse(BaseModel):
    """智能问答响应"""
    answer: str
    matched_cases: List[KnowledgeCaseResponse]
    confidence_score: float = Field(..., ge=0, le=1)
    sources: List[str] = Field(default_factory=list, description="信息来源")


class QAFeedbackRequest(BaseModel):
    """问答反馈请求"""
    qa_id: int
    feedback_score: int = Field(..., ge=1, le=5, description="1-5星评分")
    feedback_comment: Optional[str] = None


# ============= 通用响应 =============

class TagsResponse(BaseModel):
    """标签列表响应"""
    tags: List[str]
    tag_counts: dict = Field(default_factory=dict, description="标签统计")


class KnowledgeBaseSearchRequest(BaseModel):
    """知识库搜索请求"""
    keyword: Optional[str] = None
    tags: Optional[List[str]] = None
    industry: Optional[str] = None
    equipment_type: Optional[str] = None
    min_quality_score: Optional[float] = Field(None, ge=0, le=1)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class KnowledgeBaseSearchResponse(BaseModel):
    """知识库搜索响应"""
    cases: List[KnowledgeCaseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
