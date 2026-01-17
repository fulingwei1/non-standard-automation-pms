# -*- coding: utf-8 -*-
"""
数据导入模板管理 routes
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.data_import_export import ImportTemplateTypeResponse

router = APIRouter()


@router.get(
    "/templates",
    response_model=ImportTemplateTypeResponse,
    status_code=status.HTTP_200_OK,
)
def get_import_template_types(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(
        security.require_permission("data_import_export:manage")
    ),
) -> Any:
    """
    获取所有模板类型（项目/任务/人员/工时等）
    """
    types = [
        {"type": "PROJECT", "name": "项目", "description": "项目基本信息导入"},
        {"type": "TASK", "name": "任务", "description": "任务数据导入"},
        {"type": "USER", "name": "人员", "description": "人员信息导入"},
        {"type": "TIMESHEET", "name": "工时", "description": "工时数据导入"},
        {"type": "MATERIAL", "name": "物料", "description": "物料信息导入"},
        {"type": "BOM", "name": "BOM", "description": "BOM数据导入"},
    ]

    return ImportTemplateTypeResponse(types=types)


@router.get("/templates/{template_type}", response_class=StreamingResponse)
def download_import_template(
    *,
    db: Session = Depends(deps.get_db),
    template_type: str,
    current_user: User = Depends(
        security.require_permission("data_import_export:manage")
    ),
) -> Any:
    """
    下载导入模板（按类型下载）
    """
    try:
        import openpyxl
        import pandas as pd
    except ImportError:
        raise HTTPException(
            status_code=500, detail="Excel处理库未安装，请安装pandas和openpyxl"
        )

    from app.services.excel_template_service import (
        create_template_excel,
        get_template_config,
    )

    config = get_template_config(template_type)
    if not config:
        raise HTTPException(
            status_code=400, detail=f"不支持的模板类型: {template_type}"
        )

    return create_template_excel(
        template_data=config["template_data"],
        sheet_name=config["sheet_name"],
        column_widths=config["column_widths"],
        instructions=config["instructions"],
        filename_prefix=config["filename_prefix"],
    )
