# -*- coding: utf-8 -*-
"""
报表配置 - 自动生成
从 report_center.py 拆分
"""

# -*- coding: utf-8 -*-
"""
报表中心 API endpoints
核心功能：多角色视角报表、智能生成、导出分享
"""

from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import Role, User
from app.schemas.report_center import (
    ReportRoleResponse,
    ReportTypeResponse,
    RoleReportMatrixResponse,
)
from app.services.report_data_generation.core import ReportDataGenerationCore

router = APIRouter()


from fastapi import APIRouter

router = APIRouter(prefix="/configs", tags=["configs"])

# 共 3 个路由

# ==================== 报表配置 ====================


@router.get("/roles", response_model=ReportRoleResponse, status_code=status.HTTP_200_OK)
def get_report_roles(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    获取支持角色列表（角色配置）
    """
    roles = db.query(Role).filter(Role.is_active).all()

    role_list = []
    for role in roles:
        role_list.append(
            {
                "role_id": role.id,
                "role_code": role.role_code,
                "role_name": role.role_name,
                "description": role.description,
            }
        )

    return ReportRoleResponse(roles=role_list)


@router.get("/types", response_model=ReportTypeResponse, status_code=status.HTTP_200_OK)
def get_report_types(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    获取报表类型列表（周报/月报/成本等）
    """
    types = list(ReportDataGenerationCore.IMPLEMENTED_REPORT_TYPE_DEFINITIONS.values())

    return ReportTypeResponse(types=types)


@router.get(
    "/role-report-matrix", response_model=RoleReportMatrixResponse, status_code=status.HTTP_200_OK
)
def get_role_report_matrix(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    角色-报表权限矩阵（权限配置）
    """
    matrix = ReportDataGenerationCore.ROLE_REPORT_MATRIX

    return RoleReportMatrixResponse(matrix=matrix)
