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

router = APIRouter()



from fastapi import APIRouter

router = APIRouter(
    prefix="/configs",
    tags=["configs"]
)

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
        role_list.append({
            "role_id": role.id,
            "role_code": role.role_code,
            "role_name": role.role_name,
            "description": role.description
        })

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
    types = [
        {"type": "PROJECT_WEEKLY", "name": "项目周报", "description": "项目每周进展报告"},
        {"type": "PROJECT_MONTHLY", "name": "项目月报", "description": "项目每月进展报告"},
        {"type": "DEPT_WEEKLY", "name": "部门周报", "description": "部门每周工作汇总"},
        {"type": "DEPT_MONTHLY", "name": "部门月报", "description": "部门每月工作汇总"},
        {"type": "COMPANY_MONTHLY", "name": "公司月报", "description": "公司每月经营报告"},
        {"type": "COST_ANALYSIS", "name": "成本分析", "description": "项目成本分析报告"},
        {"type": "WORKLOAD_ANALYSIS", "name": "负荷分析", "description": "人员负荷分析报告"},
        {"type": "RISK_REPORT", "name": "风险报告", "description": "项目风险分析报告"},
        {"type": "CUSTOM", "name": "自定义报表", "description": "用户自定义报表"}
    ]

    return ReportTypeResponse(types=types)


@router.get("/role-report-matrix", response_model=RoleReportMatrixResponse, status_code=status.HTTP_200_OK)
def get_role_report_matrix(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    角色-报表权限矩阵（权限配置）
    """
    from app.services.report_data_generation.core import ReportDataGenerationCore

    matrix = ReportDataGenerationCore.ROLE_REPORT_MATRIX

    return RoleReportMatrixResponse(matrix=matrix)



