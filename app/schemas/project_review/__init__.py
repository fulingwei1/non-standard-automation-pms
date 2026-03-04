"""
项目复盘相关Schema
"""

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
    BestPracticeRecommendationRequest = None
    BestPracticeRecommendationResponse = None

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
