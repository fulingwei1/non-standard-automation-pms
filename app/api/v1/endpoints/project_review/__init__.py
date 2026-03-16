"""
项目复盘API端点
"""

from fastapi import APIRouter

from .comparison import router as comparison_router
from .knowledge import router as knowledge_router
from .lessons import router as lessons_router
from .reviews import router as reviews_router

router = APIRouter()
# 先注册静态前缀路由，避免 /{review_id} 吞掉 /lessons、/comparison、/knowledge、/stats 等路径
router.include_router(lessons_router, prefix="/lessons")
router.include_router(comparison_router, prefix="/comparison")
router.include_router(knowledge_router, prefix="/knowledge")
router.include_router(reviews_router, prefix="")

__all__ = [
    "router",
    "reviews_router",
    "lessons_router",
    "comparison_router",
    "knowledge_router",
]
