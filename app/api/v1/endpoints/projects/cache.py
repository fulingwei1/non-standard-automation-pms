# -*- coding: utf-8 -*-
"""
项目缓存管理端点

包含缓存统计、清理、重置等操作
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, status
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
            },
        )
    except Exception as e:
        return ResponseModel(
            code=200,
            message="缓存服务不可用",
            data={
                "enabled": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            },
        )


@router.post("/cache/clear", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def clear_cache(
    *,
    db: Session = Depends(deps.get_db),
    cache_type: Optional[str] = None,
    pattern: Optional[str] = None,
    current_user: User = Depends(security.require_permission("admin:cache:clear")),
) -> Any:
    """
    清理缓存

    Args:
        cache_type: 缓存类型（可选）
            - None/"project"/"all": 清理项目命名空间缓存
            - "project_list": 清理项目列表缓存
            - "project_detail": 清理项目详情缓存
            - "project_statistics": 清理项目统计缓存
        pattern: 兼容旧前端参数，仅允许 project:* 相关白名单模式
    """
    try:
        from app.services.cache_service import CacheService

        cache_service = CacheService()
        requested_scope = (cache_type or pattern or "project").strip()

        if requested_scope in {"project", "all", "project:*"}:
            normalized_scope = "project"
            deleted_count = cache_service.invalidate_all_project_cache()
            message = "项目缓存已清理"
        elif requested_scope in {"project_list", "project:list", "project:list:*"}:
            normalized_scope = "project_list"
            deleted_count = cache_service.invalidate_project_list()
            message = "项目列表缓存已清理"
        elif requested_scope in {"project_detail", "project:detail", "project:detail:*"}:
            normalized_scope = "project_detail"
            deleted_count = cache_service.delete_pattern("project:detail:*")
            message = "项目详情缓存已清理"
        elif requested_scope in {"project_statistics", "project:statistics", "project:statistics:*"}:
            normalized_scope = "project_statistics"
            deleted_count = cache_service.invalidate_project_statistics()
            message = "项目统计缓存已清理"
        else:
            return ResponseModel(
                code=400,
                message="不支持的缓存范围",
                data={
                    "requested": requested_scope,
                    "allowed": [
                        "project",
                        "project_list",
                        "project_detail",
                        "project_statistics",
                        "project:*",
                        "project:list:*",
                        "project:detail:*",
                        "project:statistics:*",
                    ],
                },
            )

        return ResponseModel(
            code=200,
            message=message,
            data={
                "cache_type": normalized_scope,
                "requested": requested_scope,
                "deleted_count": deleted_count,
                "cleared_at": datetime.now().isoformat(),
            },
        )
    except Exception as e:
        return ResponseModel(code=500, message=f"缓存清理失败: {str(e)}", data=None)


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
            },
        )
    except Exception as e:
        return ResponseModel(code=500, message=f"缓存统计重置失败: {str(e)}", data=None)
