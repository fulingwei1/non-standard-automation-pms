# -*- coding: utf-8 -*-
"""Legacy AI strategy route shim.

The real strategy module is mounted under /strategy. This legacy module is kept
for import-time compatibility only and must not be mounted by app/api/v1/api.py.
"""

from fastapi import APIRouter, HTTPException


router = APIRouter()


@router.api_route("/", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], status_code=501)
@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], status_code=501)
def legacy_ai_strategy_disabled(path: str = ""):
    raise HTTPException(
        status_code=501,
        detail="AI strategy assistant is not implemented. Use /strategy for supported strategy APIs.",
    )


__all__ = ["router", "legacy_ai_strategy_disabled"]
