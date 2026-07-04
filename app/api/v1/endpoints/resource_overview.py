# -*- coding: utf-8 -*-
"""Legacy resource overview route shim.

The live PMO resource overview endpoint is /pmo/resource-overview. This module
is kept for import-time compatibility only and must not be mounted by api.py.
"""

from fastapi import APIRouter, HTTPException


router = APIRouter()


@router.api_route("/", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], status_code=501)
@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], status_code=501)
def legacy_resource_overview_disabled(path: str = ""):
    raise HTTPException(
        status_code=501,
        detail="Legacy resource overview is disabled. Use /pmo/resource-overview.",
    )


__all__ = ["router", "legacy_resource_overview_disabled"]
