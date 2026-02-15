"""
项目复盘报告Schema
"""
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field, validator


class ProjectReviewBase(BaseModel):
    """复盘报告基础Schema"""
    review_type: str = Field(default="POST_MORTEM", description="复盘类型")
    review_date: date = Field(default_factory=date.today, description="复盘日期")
    customer_satisfaction: Optional[int] = Field(None, ge=1, le=5, description="客户满意度1-5")
    quality_issues: Optional[int] = Field(0, ge=0, description="质量问题数")
    success_factors: Optional[str] = Field(None, description="成功因素")
    problems: Optional[str] = Field(None, description="问题与教训")
    improvements: Optional[str] = Field(None, description="改进建议")
    best_practices: Optional[str] = Field(None, description="最佳实践")
    conclusion: Optional[str] = Field(None, description="复盘结论")


class ProjectReviewCreate(ProjectReviewBase):
    """创建复盘报告"""
    project_id: int = Field(..., description="项目ID")
    reviewer_id: int = Field(..., description="复盘负责人ID")
    participant_ids: Optional[List[int]] = Field(None, description="参与人ID列表")


class ProjectReviewUpdate(BaseModel):
    """更新复盘报告"""
    review_type: Optional[str] = None
    review_date: Optional[date] = None
    customer_satisfaction: Optional[int] = Field(None, ge=1, le=5)
    quality_issues: Optional[int] = Field(None, ge=0)
    success_factors: Optional[str] = None
    problems: Optional[str] = None
    improvements: Optional[str] = None
    best_practices: Optional[str] = None
    conclusion: Optional[str] = None
    status: Optional[str] = Field(None, description="状态：DRAFT/PUBLISHED/ARCHIVED")


class ProjectReviewResponse(BaseModel):
    """复盘报告响应"""
    id: int
    review_no: str
    project_id: int
    project_code: str
    review_type: str
    review_date: date
    
    plan_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    schedule_variance: Optional[int] = None
    
    budget_amount: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    cost_variance: Optional[Decimal] = None
    
    quality_issues: int
    change_count: int
    customer_satisfaction: Optional[int] = None
    
    success_factors: Optional[str] = None
    problems: Optional[str] = None
    improvements: Optional[str] = None
    best_practices: Optional[str] = None
    conclusion: Optional[str] = None
    
    reviewer_id: int
    reviewer_name: str
    participant_names: Optional[str] = None
    
    ai_generated: bool = False
    ai_generated_at: Optional[datetime] = None
    ai_summary: Optional[str] = None
    quality_score: Optional[Decimal] = None
    
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProjectReviewListResponse(BaseModel):
    """复盘报告列表响应"""
    total: int
    items: List[ProjectReviewResponse]


class ReviewGenerateRequest(BaseModel):
    """生成复盘报告请求"""
    project_id: int = Field(..., description="项目ID")
    review_type: str = Field(default="POST_MORTEM", description="复盘类型")
    reviewer_id: int = Field(..., description="复盘负责人ID")
    additional_context: Optional[str] = Field(None, description="额外上下文信息")
    auto_extract_lessons: bool = Field(True, description="是否自动提取经验教训")
    auto_sync_knowledge: bool = Field(False, description="是否自动同步到知识库")


class ReviewGenerateResponse(BaseModel):
    """生成复盘报告响应"""
    success: bool
    review_id: int
    review_no: str
    processing_time_ms: float
    ai_summary: str
    extracted_lessons_count: Optional[int] = None
    synced_to_knowledge: Optional[bool] = None
    knowledge_case_id: Optional[int] = None
