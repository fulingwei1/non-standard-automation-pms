# -*- coding: utf-8 -*-
"""
Stub endpoints — 为前端已调用但后端尚未实现的 API 提供兜底响应。

⚠️ 设计原则（止血版）：
- 默认返回 501（Not Implemented），避免“假成功”掩盖后端缺失。
- 仅当显式设置 ALLOW_STUB_SUCCESS=true 时，才允许返回 200 兼容旧前端。
- 认证路径若落到 stub，始终返回 404，便于排查认证路由加载问题。
"""

import os

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

router = APIRouter()

# 已由认证模块负责的路径。若请求落到 stub，返回 404 便于排查模块加载问题。
AUTH_PREFIX = "auth/"

# 默认严格模式：禁止 stub 假成功
ALLOW_STUB_SUCCESS = os.getenv("ALLOW_STUB_SUCCESS", "false").lower() == "true"


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
async def stub_handler(request: Request, path: str):
    """通配 stub handler — 匹配所有未实现的前端 API 路径。"""
    full_path = f"/{path}"

    if path == "auth" or path.startswith(AUTH_PREFIX):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": "认证接口未匹配到实现，请确认后端认证模块已加载并重启服务",
                "_auth_expected": True,
            },
            headers={"X-Stub-Endpoint": "1"},
        )

    if ALLOW_STUB_SUCCESS:
        # 仅用于短期兼容；默认不启用
        if request.method == "GET":
            return JSONResponse(
                content={
                    "items": [],
                    "total": 0,
                    "page": 1,
                    "page_size": 20,
                    "pages": 0,
                    "_stub": True,
                    "_message": f"此 API 尚未实现: {full_path}",
                },
                headers={"X-Stub-Endpoint": "1"},
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "code": 200,
                "message": "操作成功（stub 响应，兼容模式）",
                "data": None,
                "_stub": True,
                "_message": f"此 API 尚未实现: {full_path}",
            },
            headers={"X-Stub-Endpoint": "1"},
        )

    # 严格模式：显式失败，禁止假成功
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "code": 501,
            "message": "API 尚未实现",
            "detail": f"此 API 尚未实现: {full_path}",
            "data": None,
            "_stub": True,
        },
        headers={"X-Stub-Endpoint": "1"},
    )
