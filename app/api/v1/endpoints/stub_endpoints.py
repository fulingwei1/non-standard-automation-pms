# -*- coding: utf-8 -*-
"""
Stub endpoints — 为前端已调用但后端尚未实现的API提供空响应
避免前端因404/500报错，同时标记这些API为"待开发"
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

# 前端调用但后端未实现的模块路径前缀
STUB_PREFIXES = [
    "/strategy",
    "/admin/approvals", "/admin/assets", "/admin/attendance",
    "/admin/dashboard", "/admin/expenses", "/admin/leave",
    "/admin/meeting-rooms", "/admin/supplies", "/admin/vehicles",
    "/assembly",
    "/business-support",
    "/analytics",
    "/service-tickets",
    "/finance",
    "/progress",
    "/workload",
    "/settlements",
    "/service-records",
    "/customer-satisfactions",
    "/customer-communications",
    "/budgets",
    "/technical-spec",
    "/work-orders",
    "/work-reports",
    "/workers",
    "/workstations",
    "/milestones",
    "/members",
    "/meeting-map",
    "/meeting-reports",
    "/personal-goals",
    "/strategic-meetings",
    "/stages",
    "/tasks",
    "/test",
    "/wbs-templates",
    "/wbs-template-tasks",
    "/kit-checks",
    "/material-requisitions",
    "/production-daily-reports",
    "/production-exceptions",
    "/production-plans",
    "/issue-templates",
    "/import",
    "/outsourcing",
    "/pending",
    "/employees",
    "/project-members",
    "/progress-reports",
    "/purchase-order-items",
    "/satisfaction-templates",
    "/ecn-approvals",
]


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
    
    # 只处理已知的stub前缀
    is_stub = any(full_path.startswith(prefix) for prefix in STUB_PREFIXES)
    if not is_stub:
        return JSONResponse(
            status_code=404,
            content={"code": 404, "message": f"API not found: {full_path}"}
        )
    
    if request.method == "GET":
        # 如果路径看起来像列表请求（不含具体ID或末尾是模块名）
        return JSONResponse(content={
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 20,
            "pages": 0,
            "_stub": True,
            "_message": f"此API尚未实现: {full_path}"
        })
    else:
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "message": "操作成功（stub响应）",
                "data": None,
                "_stub": True,
                "_message": f"此API尚未实现: {full_path}"
            }
        )
