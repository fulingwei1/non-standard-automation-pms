# -*- coding: utf-8 -*-
"""
销售团队管理与业绩排名 API endpoints
"""

import csv
import io
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import Contract, Invoice, Lead, Opportunity
from app.models.user import Role, User, UserRole
from app.schemas.common import ResponseModel
from app.schemas.sales import SalesRankingConfigUpdateRequest
from app.services.sales_ranking_service import SalesRankingService
from app.services.sales_team_service import SalesTeamService

from .utils import (
    build_department_name_map,
    get_user_role_name,
    get_visible_sales_users,
    normalize_date_range,
)

router = APIRouter()


def _ensure_sales_director_permission(current_user: User, db: Session):
    """检查是否为销售总监（数据范围 ALL）"""
    if current_user.is_superuser:
        return
    scope = security.get_sales_data_scope(current_user, db)
    if scope != 'ALL':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅销售总监可以调整排名权重配置",
        )


def _collect_sales_team_members(
    db: Session,
    users: List[User],
    department_names: Dict[str, str],
    start_date_value: date,
    end_date_value: date,
) -> List[dict]:
    """构建销售团队成员的统计数据列表"""
    if not users:
        return []

    # 获取用户角色映射
    user_ids = [user.id for user in users]
    user_roles_map = {}
    for uid in user_ids:
        user_roles = db.query(UserRole).filter(UserRole.user_id == uid).all()
        role_names = [ur.role.role_name for ur in user_roles if ur.role]
        user_roles_map[uid] = role_names[0] if role_names else "销售专员"

    start_datetime = datetime.combine(start_date_value, datetime.min.time())
    end_datetime = datetime.combine(end_date_value, datetime.max.time())
    month_value = start_date_value.strftime("%Y-%m")
    year_value = str(start_date_value.year)

    team_service = SalesTeamService(db)
    personal_targets_map = team_service.build_personal_target_map(user_ids, month_value, year_value)
    recent_followups_map = team_service.get_recent_followups_map(user_ids, start_datetime, end_datetime)
    customer_distribution_map = team_service.get_customer_distribution_map(user_ids, start_date_value, end_date_value)
    followup_stats_map = team_service.get_followup_statistics_map(user_ids, start_datetime, end_datetime)
    lead_quality_map = team_service.get_lead_quality_stats_map(user_ids, start_datetime, end_datetime)
    opportunity_stats_map = team_service.get_opportunity_stats_map(user_ids, start_datetime, end_datetime)

    team_members: List[dict] = []
    for user in users:
        lead_query = db.query(Lead).filter(Lead.owner_id == user.id)
        lead_query = lead_query.filter(Lead.created_at >= start_datetime)
        lead_query = lead_query.filter(Lead.created_at <= end_datetime)
        lead_count = lead_query.count()

        opp_query = db.query(Opportunity).filter(Opportunity.owner_id == user.id)
        opp_query = opp_query.filter(Opportunity.created_at >= start_datetime)
        opp_query = opp_query.filter(Opportunity.created_at <= end_datetime)
        opp_count = opp_query.count()

        contract_query = db.query(Contract).filter(Contract.owner_id == user.id)
        contract_query = contract_query.filter(Contract.created_at >= start_datetime)
        contract_query = contract_query.filter(Contract.created_at <= end_datetime)
        contracts = contract_query.all()
        contract_count = len(contracts)
        contract_amount = sum(float(c.contract_amount or 0) for c in contracts)

        invoice_query = db.query(Invoice).join(Contract).filter(Contract.owner_id == user.id)
        invoice_query = invoice_query.filter(Invoice.paid_date.isnot(None))
        invoice_query = invoice_query.filter(Invoice.paid_date >= start_date_value)
        invoice_query = invoice_query.filter(Invoice.paid_date <= end_date_value)
        invoices = invoice_query.filter(Invoice.payment_status.in_(["PAID", "PARTIAL"])).all()
        collection_amount = sum(float(inv.paid_amount or 0) for inv in invoices)

        # User表使用department字符串字段
        department_name = user.department or "未分配"
        region_name = department_name

        target_snapshot = personal_targets_map.get(user.id, {})
        monthly_target_info = target_snapshot.get("monthly", {})
        yearly_target_info = target_snapshot.get("yearly", {})

        customer_distribution = customer_distribution_map.get(user.id, {})
        recent_follow_up = recent_followups_map.get(user.id)
        followup_stats = followup_stats_map.get(user.id, {})
        lead_quality_stats = lead_quality_map.get(user.id, {})
        opportunity_stats = opportunity_stats_map.get(user.id, {})

        monthly_target_value = monthly_target_info.get("target_value", 0.0)
        monthly_actual_value = monthly_target_info.get("actual_value", 0.0)
        monthly_completion_rate = monthly_target_info.get("completion_rate", 0.0)

        yearly_target_value = yearly_target_info.get("target_value", 0.0)
        yearly_actual_value = yearly_target_info.get("actual_value", 0.0)
        yearly_completion_rate = yearly_target_info.get("completion_rate", 0.0)

        team_members.append({
            "user_id": user.id,
            "user_name": user.real_name or user.username,
            "username": user.username,
            "role": user_roles_map.get(user.id, "销售专员"),
            "department_name": department_name,
            "email": user.email,
            "phone": user.phone,
            "lead_count": lead_count,
            "opportunity_count": opp_count,
            "contract_count": contract_count,
            "contract_amount": float(contract_amount),
            "collection_amount": float(collection_amount),
            "monthly_target": monthly_target_value,
            "monthly_actual": monthly_actual_value,
            "monthly_completion_rate": monthly_completion_rate,
            "year_target": yearly_target_value,
            "year_actual": yearly_actual_value,
            "year_completion_rate": yearly_completion_rate,
            "personal_targets": target_snapshot,
            "recent_follow_up": recent_follow_up,
            "customer_distribution": customer_distribution.get("categories", []),
            "customer_total": customer_distribution.get("total", 0),
            "new_customers": customer_distribution.get("new_customers", 0),
            "region": region_name,
            "follow_up_stats": followup_stats,
            "lead_quality_stats": lead_quality_stats,
            "opportunity_stats": opportunity_stats,
        })

    return team_members


@router.get("/team/ranking/config", response_model=ResponseModel)
def get_sales_ranking_config(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取销售排名权重配置"""
    service = SalesRankingService(db)
    config = service.get_active_config()
    return ResponseModel(
        code=200,
        message="success",
        data={
            "metrics": config.metrics,
            "total_weight": sum(m.get("weight", 0) for m in config.metrics),
            "updated_at": config.updated_at,
        },
    )


@router.put("/team/ranking/config", response_model=ResponseModel, status_code=200)
def update_sales_ranking_config(
    *,
    request: SalesRankingConfigUpdateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新销售排名权重配置（仅销售总监）"""
    _ensure_sales_director_permission(current_user, db)
    service = SalesRankingService(db)
    try:
        config = service.save_config(request.metrics, operator_id=current_user.id)
    except ValueError as exc:  # 权重校验失败
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return ResponseModel(
        code=200,
        message="配置已更新",
        data={
            "metrics": config.metrics,
            "total_weight": sum(m.get("weight", 0) for m in config.metrics),
            "updated_at": config.updated_at,
        },
    )


# ==================== 销售团队管理与业绩排名 ====================


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
    team_members = _collect_sales_team_members(db, users, department_names, normalized_start, normalized_end)

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
    team_members = _collect_sales_team_members(db, users, department_names, normalized_start, normalized_end)

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


@router.get("/team/ranking", response_model=ResponseModel)
def get_sales_team_ranking(
    *,
    db: Session = Depends(deps.get_db),
    ranking_type: str = Query("score", description="排名类型：score 或具体指标（lead_count/opportunity_count/contract_amount/collection_amount 等）"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    department_id: Optional[int] = Query(None, description="部门ID筛选"),
    region: Optional[str] = Query(None, description="区域关键字筛选"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    normalized_start, normalized_end = normalize_date_range(start_date, end_date)
    start_datetime = datetime.combine(normalized_start, datetime.min.time())
    end_datetime = datetime.combine(normalized_end, datetime.max.time())

    users = get_visible_sales_users(db, current_user, department_id, region)
    ranking_service = SalesRankingService(db)
    ranking_result = ranking_service.calculate_rankings(
        users, start_datetime, end_datetime, ranking_type=ranking_type
    )
    ranking_list = ranking_result.get("rankings", [])[:limit]
    total_count = len(ranking_result.get("rankings", []))

    return ResponseModel(
        code=200,
        message="success",
        data={
            "ranking_type": ranking_result.get("ranking_type"),
            "start_date": normalized_start.isoformat(),
            "end_date": normalized_end.isoformat(),
            "rankings": ranking_list,
            "total_count": total_count,
            "config": ranking_result.get("config"),
            "max_values": ranking_result.get("max_values"),
        }
    )
