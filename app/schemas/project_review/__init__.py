"""
项目复盘相关Schema
"""

from .review import (
    ProjectReviewBase,
    ProjectReviewCreate,
    ProjectReviewUpdate,
    ProjectReviewResponse,
    ProjectReviewListResponse,
    ReviewGenerateRequest,
    ReviewGenerateResponse
)

from .lesson import (
    ProjectLessonBase,
    ProjectLessonCreate,
    ProjectLessonUpdate,
    ProjectLessonResponse,
    LessonExtractRequest,
    LessonExtractResponse
)

from .comparison import (
    ComparisonRequest,
    ComparisonResponse,
    ImprovementResponse
)

from .knowledge import (
    KnowledgeSyncRequest,
    KnowledgeSyncResponse,
    KnowledgeImpactResponse
)

# Best practice
try:
    from ..project_review import (
        BestPracticeRecommendationRequest,
        BestPracticeRecommendationResponse
    )
except ImportError:
    BestPracticeRecommendationRequest = None
    BestPracticeRecommendationResponse = None

__all__ = [
    # Review
    'ProjectReviewBase',
    'ProjectReviewCreate',
    'ProjectReviewUpdate',
    'ProjectReviewResponse',
    'ProjectReviewListResponse',
    'ReviewGenerateRequest',
    'ReviewGenerateResponse',
    
    # Lesson
    'ProjectLessonBase',
    'ProjectLessonCreate',
    'ProjectLessonUpdate',
    'ProjectLessonResponse',
    'LessonExtractRequest',
    'LessonExtractResponse',
    
    # Comparison
    'ComparisonRequest',
    'ComparisonResponse',
    'ImprovementResponse',
    
    # Knowledge
    'KnowledgeSyncRequest',
    'KnowledgeSyncResponse',
    'KnowledgeImpactResponse',
    
    # Best practice (optional)
    'BestPracticeRecommendationRequest',
    'BestPracticeRecommendationResponse',
]
