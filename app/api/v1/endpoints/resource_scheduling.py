# -*- coding: utf-8 -*-
"""Disabled legacy resource-scheduling compatibility shim.

The real scheduling surface is /engineer-scheduling. This module used to guess
non-existent import locations and fall back to a placeholder payload.
"""

from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.api_route(
    "/",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
def legacy_resource_scheduling_disabled(path: str = ""):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            "Legacy /resource-scheduling placeholder is disabled; use "
            "/engineer-scheduling."
        ),
    )


__all__ = ["router", "legacy_resource_scheduling_disabled"]
