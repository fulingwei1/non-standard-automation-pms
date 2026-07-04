# -*- coding: utf-8 -*-
"""Disabled legacy knowledge routes.

The active knowledge surfaces are /knowledge-base and /service/knowledge-base.
This package used to aggregate unfinished auto-extraction routes that depend on
legacy tables not present in the default database, so keep accidental mounts
from exposing 500s or fake AI behavior.
"""

from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
def legacy_knowledge_disabled(path: str = ""):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            "Legacy knowledge auto-extraction routes are disabled; use "
            "/knowledge-base or /service/knowledge-base."
        ),
    )
