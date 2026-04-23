"""
项目复盘相关Schema
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from .comparison import ComparisonRequest, ComparisonResponse, ImprovementResponse
from .knowledge import KnowledgeImpactResponse, KnowledgeSyncRequest, KnowledgeSyncResponse
from .lesson import (
    LessonExtractRequest,
    LessonExtractResponse,
    ProjectLessonBase,
    ProjectLessonCreate,
    ProjectLessonResponse,
    ProjectLessonUpdate,
)
from .review import (
    ProjectReviewBase,
    ProjectReviewCreate,
    ProjectReviewListResponse,
    ProjectReviewResponse,
    ProjectReviewUpdate,
    ReviewGenerateRequest,
    ReviewGenerateResponse,
)

# Best practice
try:
    from ..project_review import (
        BestPracticeRecommendationRequest,
        BestPracticeRecommendationResponse,
    )
except ImportError:
    class BestPracticeRecommendationRequest(BaseModel):
        """最佳实践推荐请求"""

        project_id: Optional[int] = Field(None, description="项目ID")
        project_type: Optional[str] = Field(None, description="项目类型")
        current_stage: Optional[str] = Field(None, description="当前阶段（S1-S9）")
        category: Optional[str] = Field(None, description="分类筛选")
        limit: int = Field(10, ge=1, le=50, description="返回数量限制")

    class BestPracticeRecommendationResponse(BaseModel):
        """最佳实践推荐响应"""

        practice: Optional[dict] = Field(None, description="匹配到的最佳实践")
        match_score: float = Field(..., description="匹配度分数（0-1）")
        match_reasons: List[str] = Field(default_factory=list, description="匹配原因")

__all__ = [
    # Review
    "ProjectReviewBase",
    "ProjectReviewCreate",
    "ProjectReviewUpdate",
    "ProjectReviewResponse",
    "ProjectReviewListResponse",
    "ReviewGenerateRequest",
    "ReviewGenerateResponse",
    # Lesson
    "ProjectLessonBase",
    "ProjectLessonCreate",
    "ProjectLessonUpdate",
    "ProjectLessonResponse",
    "LessonExtractRequest",
    "LessonExtractResponse",
    # Comparison
    "ComparisonRequest",
    "ComparisonResponse",
    "ImprovementResponse",
    # Knowledge
    "KnowledgeSyncRequest",
    "KnowledgeSyncResponse",
    "KnowledgeImpactResponse",
    # Best practice (optional)
    "BestPracticeRecommendationRequest",
    "BestPracticeRecommendationResponse",
]
