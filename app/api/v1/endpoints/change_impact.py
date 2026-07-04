# -*- coding: utf-8 -*-
"""Disabled legacy change-impact compatibility shim.

The active project change impact API is exposed at /project-change-impacts.
This module previously guessed several non-existent import locations and then
returned a placeholder payload, which made the feature look live.
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
def legacy_change_impact_disabled(path: str = ""):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            "Legacy /change-impact placeholder is disabled; use "
            "/project-change-impacts."
        ),
    )


__all__ = ["router", "legacy_change_impact_disabled"]
