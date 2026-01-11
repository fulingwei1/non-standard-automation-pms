# -*- coding: utf-8 -*-
"""
项目缓存管理端点

包含缓存统计、清理、重置等操作
"""

from typing import Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/cache/stats", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_cache_stats(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取缓存统计信息
    """
    try:
        from app.services.cache_service import CacheService
        cache_service = CacheService()
        stats = cache_service.get_stats()

        return ResponseModel(
            code=200,
            message="获取缓存统计成功",
            data={
                "enabled": True,
                "stats": stats,
                "timestamp": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        return ResponseModel(
            code=200,
            message="缓存服务不可用",
            data={
                "enabled": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
        )


@router.post("/cache/clear", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def clear_cache(
    *,
    db: Session = Depends(deps.get_db),
    cache_type: Optional[str] = None,
    current_user: User = Depends(security.require_permission("admin:cache:clear")),
) -> Any:
    """
    清理缓存

    Args:
        cache_type: 缓存类型（可选）
            - None: 清理所有缓存
            - "project_list": 清理项目列表缓存
            - "project_detail": 清理项目详情缓存
            - "user": 清理用户缓存
    """
    try:
        from app.services.cache_service import CacheService
        cache_service = CacheService()

        if cache_type == "project_list":
            cache_service.invalidate_project_list()
            message = "项目列表缓存已清理"
        elif cache_type == "project_detail":
            # 清理所有项目详情缓存
            cache_service.invalidate_all_project_details()
            message = "项目详情缓存已清理"
        elif cache_type == "user":
            cache_service.invalidate_user_cache()
            message = "用户缓存已清理"
        else:
            cache_service.clear_all()
            message = "所有缓存已清理"

        return ResponseModel(
            code=200,
            message=message,
            data={
                "cache_type": cache_type or "all",
                "cleared_at": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        return ResponseModel(
            code=500,
            message=f"缓存清理失败: {str(e)}",
            data=None
        )


@router.post("/cache/reset-stats", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def reset_cache_stats(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("admin:cache:reset")),
) -> Any:
    """
    重置缓存统计信息
    """
    try:
        from app.services.cache_service import CacheService
        cache_service = CacheService()
        cache_service.reset_stats()

        return ResponseModel(
            code=200,
            message="缓存统计已重置",
            data={
                "reset_at": datetime.now().isoformat(),
            }
        )
    except Exception as e:
        return ResponseModel(
            code=500,
            message=f"缓存统计重置失败: {str(e)}",
            data=None
        )
