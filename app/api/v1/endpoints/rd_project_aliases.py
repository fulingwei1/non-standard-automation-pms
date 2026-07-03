# -*- coding: utf-8 -*-
"""Redirect-free aliases for RD project frontend routes."""

from fastapi import APIRouter

from app.api.v1.endpoints.rd_project.initiation import get_rd_projects
from app.schemas.common import PaginatedResponse

router = APIRouter()

router.add_api_route(
    "/rd-projects",
    get_rd_projects,
    methods=["GET"],
    response_model=PaginatedResponse,
    include_in_schema=False,
)
