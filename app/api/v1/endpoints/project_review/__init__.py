"""
项目复盘API端点
"""

from fastapi import APIRouter

from .reviews import router as reviews_router
from .lessons import router as lessons_router
from .comparison import router as comparison_router
from .knowledge import router as knowledge_router

router = APIRouter()
router.include_router(reviews_router, prefix="")
router.include_router(lessons_router, prefix="/lessons")
router.include_router(comparison_router, prefix="/comparison")
router.include_router(knowledge_router, prefix="/knowledge")

__all__ = [
    'router',
    'reviews_router',
    'lessons_router',
    'comparison_router',
    'knowledge_router',
]
