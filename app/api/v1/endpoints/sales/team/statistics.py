# -*- coding: utf-8 -*-
"""
销售团队统计和导出 API endpoints
"""

import csv
import io
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel

from ..utils import build_department_name_map, get_visible_sales_users, normalize_date_range
from .utils import collect_sales_team_members

router = APIRouter()


@router.get("/team", response_model=ResponseModel)
def get_sales_team(
    *,
    db: Session = Depends(deps.get_db),
    department_id: Optional[int] = Query(None, description="部门ID筛选"),
    region: Optional[str] = Query(None, description="区域关键字筛选"),
    start_date: Optional[date] = Query(None, description="统计开始日期"),
    end_date: Optional[date] = Query(None, description="统计结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 6.4: 获取销售团队列表
    返回销售团队成员信息，包括角色、负责区域等
    """
    normalized_start, normalized_end = normalize_date_range(start_date, end_date)
    users = get_visible_sales_users(db, current_user, department_id, region)
    department_names = build_department_name_map(db, users)
    team_members = collect_sales_team_members(db, users, department_names, normalized_start, normalized_end)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "team_members": team_members,
            "total_count": len(team_members),
            "filters": {
                "start_date": normalized_start.isoformat(),
                "end_date": normalized_end.isoformat(),
                "department_id": department_id,
                "region": region,
            },
        }
    )


@router.get("/team/export")
def export_sales_team(
    *,
    db: Session = Depends(deps.get_db),
    department_id: Optional[int] = Query(None, description="部门ID筛选"),
    region: Optional[str] = Query(None, description="区域关键字筛选"),
    start_date: Optional[date] = Query(None, description="统计开始日期"),
    end_date: Optional[date] = Query(None, description="统计结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """导出销售团队数据为CSV"""
    normalized_start, normalized_end = normalize_date_range(start_date, end_date)
    users = get_visible_sales_users(db, current_user, department_id, region)
    department_names = build_department_name_map(db, users)
    team_members = collect_sales_team_members(db, users, department_names, normalized_start, normalized_end)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "成员ID", "姓名", "角色", "部门", "区域", "邮箱", "电话",
        "线索数量", "商机数量", "合同数量", "合同金额", "回款金额",
        "月度目标", "月度完成", "月度完成率(%)",
        "年度目标", "年度完成", "年度完成率(%)",
        "客户总数", "本期新增客户",
    ])

    for member in team_members:
        writer.writerow([
            member.get("user_id"),
            member.get("user_name"),
            member.get("role"),
            member.get("department_name") or "",
            member.get("region") or "",
            member.get("email") or "",
            member.get("phone") or "",
            member.get("lead_count") or 0,
            member.get("opportunity_count") or 0,
            member.get("contract_count") or 0,
            member.get("contract_amount") or 0,
            member.get("collection_amount") or 0,
            member.get("monthly_target") or 0,
            member.get("monthly_actual") or 0,
            member.get("monthly_completion_rate") or 0,
            member.get("year_target") or 0,
            member.get("year_actual") or 0,
            member.get("year_completion_rate") or 0,
            member.get("customer_total") or 0,
            member.get("new_customers") or 0,
        ])

    output.seek(0)
    filename = f"sales-team-{normalized_start.strftime('%Y%m%d')}-{normalized_end.strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue().encode("utf-8-sig")]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )
