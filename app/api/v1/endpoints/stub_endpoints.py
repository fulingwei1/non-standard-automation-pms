# -*- coding: utf-8 -*-
"""
Stub endpoints — 为前端已调用但后端尚未实现的API提供空响应
避免前端因404/500报错，同时标记这些API为"待开发"

此router在api.py中最后注册，作为fallback。
只有未匹配到任何已实现endpoint的请求才会到达这里。
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi import status

router = APIRouter()

# 已由认证模块负责的路径。若请求落到 stub，返回 404 便于排查模块加载问题。
AUTH_PREFIX = "auth/"


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
async def stub_handler(request: Request, path: str):
    """
    通配stub handler — 匹配所有未实现的前端API路径。
    GET请求返回空列表/分页，其他请求返回成功响应。
    """
    full_path = f"/{path}"

    if path == "auth" or path.startswith(AUTH_PREFIX):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "detail": "认证接口未匹配到实现，请确认后端认证模块已加载并重启服务",
                "_auth_expected": True,
            },
        )

    if request.method == "GET":
        return JSONResponse(
            content={
                "items": [],
                "total": 0,
                "page": 1,
                "page_size": 20,
                "pages": 0,
                "_stub": True,
                "_message": f"此API尚未实现: {full_path}",
            }
        )
    else:
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "操作成功（stub响应）",
                "data": None,
                "_stub": True,
                "_message": f"此API尚未实现: {full_path}",
            },
        )
