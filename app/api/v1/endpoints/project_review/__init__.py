"""
项目复盘API端点
"""

from .reviews import router as reviews_router
from .lessons import router as lessons_router
from .comparison import router as comparison_router
from .knowledge import router as knowledge_router

__all__ = [
    'reviews_router',
    'lessons_router',
    'comparison_router',
    'knowledge_router',
]
