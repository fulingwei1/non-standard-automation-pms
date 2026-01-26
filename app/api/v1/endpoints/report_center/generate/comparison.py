# -*- coding: utf-8 -*-
"""
报表生成 - 角色对比
"""
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.report_center import (
    ReportCompareRequest,
    ReportCompareResponse,
)

router = APIRouter()


@router.post("/compare-roles", response_model=ReportCompareResponse, status_code=status.HTTP_200_OK)
def compare_role_perspectives(
    *,
    db: Session = Depends(deps.get_db),
    compare_in: ReportCompareRequest,
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    比较角色视角（多角色对比）
    """
    from app.services.report_data_generation_service import report_data_service

    # 为每个角色生成报表数据
    role_data = {}
    for role in compare_in.roles:
        report_data = report_data_service.generate_report_by_type(
            db,
            compare_in.report_type,
            compare_in.project_id,
            compare_in.department_id,
            compare_in.start_date,
            compare_in.end_date
        )
        role_data[role] = report_data

    # 分析差异
    differences = []
    common_points = []

    # 比较摘要数据
    if role_data:
        first_role = compare_in.roles[0]
        first_summary = role_data.get(first_role, {}).get("summary", {})

        for key, value in first_summary.items():
            is_common = True
            values_by_role = {}

            for role in compare_in.roles:
                role_summary = role_data.get(role, {}).get("summary", {})
                role_value = role_summary.get(key)

                if role != first_role:
                    if role_value != value:
                        is_common = False

                values_by_role[role] = role_value

            if is_common and value is not None:
                common_points.append({
                    "field": key,
                    "value": value,
                    "description": f"所有角色在此项上一致"
                })
            elif values_by_role:
                differences.append({
                    "field": key,
                    "values": values_by_role,
                    "description": f"各角色在此项上存在差异"
                })

    comparison_data = {
        "roles": compare_in.roles,
        "role_data": role_data,
        "differences": differences,
        "common_points": common_points
    }

    return ReportCompareResponse(
        report_type=compare_in.report_type,
        comparison_data=comparison_data
    )
