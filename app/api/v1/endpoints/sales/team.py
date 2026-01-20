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
from app.models.user import User, UserRole
from app.schemas.common import ResponseModel
from app.schemas.sales import SalesRankingConfigUpdateRequest
from app.services.sales_ranking_service import SalesRankingService
from app.services.sales_team_service import SalesTeamService

from .utils import (
    build_department_name_map,
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


# ==================== 销售团队（SalesTeam）管理 ====================
# 注意：这里的 sales-teams 是团队实体管理，与上面的 /team 个人统计不同


from app.models.sales import SalesTeam, SalesTeamMember, TeamPKRecord
from app.schemas.sales import (
    SalesTeamCreate,
    SalesTeamUpdate,
    TeamMemberAddRequest,
    TeamMemberUpdateRequest,
    TeamMemberBatchAddRequest,
    TeamPKCreateRequest,
    TeamPKUpdateRequest,
)
import json


def _build_team_response(team: SalesTeam, db: Session, include_members: bool = True) -> dict:
    """构建团队响应数据"""
    # 获取成员数量
    member_count = db.query(SalesTeamMember).filter(
        SalesTeamMember.team_id == team.id,
        SalesTeamMember.is_active == True,
    ).count()

    # 获取部门名称
    department_name = None
    if team.department:
        department_name = team.department.name

    # 获取负责人名称
    leader_name = None
    if team.leader:
        leader_name = team.leader.real_name or team.leader.username

    # 获取上级团队名称
    parent_team_name = None
    if team.parent_team:
        parent_team_name = team.parent_team.team_name

    result = {
        "id": team.id,
        "team_code": team.team_code,
        "team_name": team.team_name,
        "description": team.description,
        "team_type": team.team_type,
        "department_id": team.department_id,
        "department_name": department_name,
        "leader_id": team.leader_id,
        "leader_name": leader_name,
        "parent_team_id": team.parent_team_id,
        "parent_team_name": parent_team_name,
        "is_active": team.is_active,
        "sort_order": team.sort_order,
        "member_count": member_count,
        "created_at": team.created_at,
        "updated_at": team.updated_at,
    }

    if include_members:
        members = db.query(SalesTeamMember).filter(
            SalesTeamMember.team_id == team.id,
            SalesTeamMember.is_active == True,
        ).all()
        result["members"] = [
            {
                "id": m.id,
                "user_id": m.user_id,
                "user_name": m.user.real_name if m.user else None,
                "username": m.user.username if m.user else None,
                "role": m.role,
                "is_primary": m.is_primary,
                "is_active": m.is_active,
                "joined_at": m.joined_at,
                "remark": m.remark,
            }
            for m in members
        ]
    else:
        result["members"] = []

    return result


@router.get("/sales-teams", response_model=ResponseModel)
def list_sales_teams(
    *,
    db: Session = Depends(deps.get_db),
    team_type: Optional[str] = Query(None, description="团队类型筛选"),
    department_id: Optional[int] = Query(None, description="部门ID筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    keyword: Optional[str] = Query(None, description="团队名称/编码关键字"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取销售团队列表"""
    query = db.query(SalesTeam)

    if team_type:
        query = query.filter(SalesTeam.team_type == team_type)
    if department_id:
        query = query.filter(SalesTeam.department_id == department_id)
    if is_active is not None:
        query = query.filter(SalesTeam.is_active == is_active)
    if keyword:
        query = query.filter(
            (SalesTeam.team_name.contains(keyword)) |
            (SalesTeam.team_code.contains(keyword))
        )

    total = query.count()
    teams = query.order_by(SalesTeam.sort_order, SalesTeam.id).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for team in teams:
        member_count = db.query(SalesTeamMember).filter(
            SalesTeamMember.team_id == team.id,
            SalesTeamMember.is_active == True,
        ).count()
        sub_team_count = db.query(SalesTeam).filter(
            SalesTeam.parent_team_id == team.id,
            SalesTeam.is_active == True,
        ).count()

        items.append({
            "id": team.id,
            "team_code": team.team_code,
            "team_name": team.team_name,
            "team_type": team.team_type,
            "department_name": team.department.name if team.department else None,
            "leader_name": (team.leader.real_name or team.leader.username) if team.leader else None,
            "is_active": team.is_active,
            "member_count": member_count,
            "sub_team_count": sub_team_count,
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.post("/sales-teams", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_sales_team(
    *,
    db: Session = Depends(deps.get_db),
    request: SalesTeamCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建销售团队"""
    # 检查团队编码唯一性
    existing = db.query(SalesTeam).filter(SalesTeam.team_code == request.team_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"团队编码 {request.team_code} 已存在",
        )

    team = SalesTeam(
        team_code=request.team_code,
        team_name=request.team_name,
        description=request.description,
        team_type=request.team_type,
        department_id=request.department_id,
        leader_id=request.leader_id,
        parent_team_id=request.parent_team_id,
        sort_order=request.sort_order,
        created_by=current_user.id,
    )
    db.add(team)
    db.commit()
    db.refresh(team)

    # 如果指定了负责人，自动添加为团队成员
    if request.leader_id:
        member = SalesTeamMember(
            team_id=team.id,
            user_id=request.leader_id,
            role="LEADER",
            is_primary=True,
        )
        db.add(member)
        db.commit()

    return ResponseModel(
        code=201,
        message="团队创建成功",
        data=_build_team_response(team, db),
    )


@router.get("/sales-teams/{team_id}", response_model=ResponseModel)
def get_sales_team(
    *,
    db: Session = Depends(deps.get_db),
    team_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取销售团队详情"""
    team = db.query(SalesTeam).filter(SalesTeam.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="团队不存在",
        )

    return ResponseModel(
        code=200,
        message="success",
        data=_build_team_response(team, db),
    )


@router.put("/sales-teams/{team_id}", response_model=ResponseModel)
def update_sales_team(
    *,
    db: Session = Depends(deps.get_db),
    team_id: int,
    request: SalesTeamUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新销售团队"""
    team = db.query(SalesTeam).filter(SalesTeam.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="团队不存在",
        )

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)

    db.commit()
    db.refresh(team)

    return ResponseModel(
        code=200,
        message="团队更新成功",
        data=_build_team_response(team, db),
    )


@router.delete("/sales-teams/{team_id}", response_model=ResponseModel)
def delete_sales_team(
    *,
    db: Session = Depends(deps.get_db),
    team_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """删除销售团队（软删除）"""
    team = db.query(SalesTeam).filter(SalesTeam.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="团队不存在",
        )

    # 检查是否有子团队
    sub_teams = db.query(SalesTeam).filter(
        SalesTeam.parent_team_id == team_id,
        SalesTeam.is_active == True,
    ).count()
    if sub_teams > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该团队下有子团队，无法删除",
        )

    team.is_active = False
    db.commit()

    return ResponseModel(
        code=200,
        message="团队已删除",
        data={"team_id": team_id},
    )


# ==================== 团队成员管理 ====================


@router.get("/sales-teams/{team_id}/members", response_model=ResponseModel)
def list_team_members(
    *,
    db: Session = Depends(deps.get_db),
    team_id: int,
    include_inactive: bool = Query(False, description="是否包含已移除成员"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取团队成员列表"""
    team = db.query(SalesTeam).filter(SalesTeam.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="团队不存在",
        )

    query = db.query(SalesTeamMember).filter(SalesTeamMember.team_id == team_id)
    if not include_inactive:
        query = query.filter(SalesTeamMember.is_active == True)

    members = query.all()
    items = [
        {
            "id": m.id,
            "user_id": m.user_id,
            "user_name": m.user.real_name if m.user else None,
            "username": m.user.username if m.user else None,
            "email": m.user.email if m.user else None,
            "phone": m.user.phone if m.user else None,
            "role": m.role,
            "is_primary": m.is_primary,
            "is_active": m.is_active,
            "joined_at": m.joined_at,
            "remark": m.remark,
        }
        for m in members
    ]

    return ResponseModel(
        code=200,
        message="success",
        data={
            "team_id": team_id,
            "team_name": team.team_name,
            "members": items,
            "total": len(items),
        }
    )


@router.post("/sales-teams/{team_id}/members", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def add_team_member(
    *,
    db: Session = Depends(deps.get_db),
    team_id: int,
    request: TeamMemberAddRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """添加团队成员"""
    team = db.query(SalesTeam).filter(SalesTeam.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="团队不存在",
        )

    # 检查用户是否存在
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    # 检查是否已是成员
    existing = db.query(SalesTeamMember).filter(
        SalesTeamMember.team_id == team_id,
        SalesTeamMember.user_id == request.user_id,
    ).first()
    if existing:
        if existing.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该用户已是团队成员",
            )
        # 重新激活
        existing.is_active = True
        existing.role = request.role
        existing.is_primary = request.is_primary
        existing.remark = request.remark
        db.commit()
        db.refresh(existing)
        member = existing
    else:
        member = SalesTeamMember(
            team_id=team_id,
            user_id=request.user_id,
            role=request.role,
            is_primary=request.is_primary,
            remark=request.remark,
        )
        db.add(member)
        db.commit()
        db.refresh(member)

    # 如果设为主团队，清除其他团队的主团队标记
    if request.is_primary:
        db.query(SalesTeamMember).filter(
            SalesTeamMember.user_id == request.user_id,
            SalesTeamMember.id != member.id,
        ).update({"is_primary": False})
        db.commit()

    return ResponseModel(
        code=201,
        message="成员添加成功",
        data={
            "id": member.id,
            "team_id": team_id,
            "user_id": member.user_id,
            "user_name": user.real_name or user.username,
            "role": member.role,
            "is_primary": member.is_primary,
        }
    )


@router.post("/sales-teams/{team_id}/members/batch", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def batch_add_team_members(
    *,
    db: Session = Depends(deps.get_db),
    team_id: int,
    request: TeamMemberBatchAddRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """批量添加团队成员"""
    team = db.query(SalesTeam).filter(SalesTeam.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="团队不存在",
        )

    added = []
    skipped = []
    for user_id in request.user_ids:
        existing = db.query(SalesTeamMember).filter(
            SalesTeamMember.team_id == team_id,
            SalesTeamMember.user_id == user_id,
            SalesTeamMember.is_active == True,
        ).first()
        if existing:
            skipped.append(user_id)
            continue

        member = SalesTeamMember(
            team_id=team_id,
            user_id=user_id,
            role=request.role,
        )
        db.add(member)
        added.append(user_id)

    db.commit()

    return ResponseModel(
        code=201,
        message=f"成功添加 {len(added)} 人，跳过 {len(skipped)} 人（已存在）",
        data={
            "added": added,
            "skipped": skipped,
        }
    )


@router.put("/sales-teams/{team_id}/members/{member_id}", response_model=ResponseModel)
def update_team_member(
    *,
    db: Session = Depends(deps.get_db),
    team_id: int,
    member_id: int,
    request: TeamMemberUpdateRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新团队成员"""
    member = db.query(SalesTeamMember).filter(
        SalesTeamMember.id == member_id,
        SalesTeamMember.team_id == team_id,
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="成员不存在",
        )

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(member, field, value)

    # 如果设为主团队，清除其他团队的主团队标记
    if request.is_primary:
        db.query(SalesTeamMember).filter(
            SalesTeamMember.user_id == member.user_id,
            SalesTeamMember.id != member.id,
        ).update({"is_primary": False})

    db.commit()
    db.refresh(member)

    return ResponseModel(
        code=200,
        message="成员更新成功",
        data={
            "id": member.id,
            "user_id": member.user_id,
            "role": member.role,
            "is_primary": member.is_primary,
            "is_active": member.is_active,
        }
    )


@router.delete("/sales-teams/{team_id}/members/{member_id}", response_model=ResponseModel)
def remove_team_member(
    *,
    db: Session = Depends(deps.get_db),
    team_id: int,
    member_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """移除团队成员（软删除）"""
    member = db.query(SalesTeamMember).filter(
        SalesTeamMember.id == member_id,
        SalesTeamMember.team_id == team_id,
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="成员不存在",
        )

    member.is_active = False
    db.commit()

    return ResponseModel(
        code=200,
        message="成员已移除",
        data={"member_id": member_id},
    )


# ==================== 团队PK管理 ====================


@router.get("/team-pk", response_model=ResponseModel)
def list_team_pks(
    *,
    db: Session = Depends(deps.get_db),
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取团队PK列表"""
    query = db.query(TeamPKRecord)

    if status_filter:
        query = query.filter(TeamPKRecord.status == status_filter)

    total = query.count()
    pks = query.order_by(TeamPKRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for pk in pks:
        team_ids = json.loads(pk.team_ids) if pk.team_ids else []
        teams = db.query(SalesTeam).filter(SalesTeam.id.in_(team_ids)).all()
        team_info = [{"id": t.id, "team_code": t.team_code, "team_name": t.team_name} for t in teams]

        items.append({
            "id": pk.id,
            "pk_name": pk.pk_name,
            "pk_type": pk.pk_type,
            "team_ids": team_ids,
            "teams": team_info,
            "start_date": pk.start_date,
            "end_date": pk.end_date,
            "target_value": float(pk.target_value) if pk.target_value else None,
            "status": pk.status,
            "winner_team_id": pk.winner_team_id,
            "winner_team_name": pk.winner_team.team_name if pk.winner_team else None,
            "reward_description": pk.reward_description,
            "created_at": pk.created_at,
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@router.post("/team-pk", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_team_pk(
    *,
    db: Session = Depends(deps.get_db),
    request: TeamPKCreateRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建团队PK"""
    # 验证团队存在性
    teams = db.query(SalesTeam).filter(SalesTeam.id.in_(request.team_ids)).all()
    if len(teams) != len(request.team_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="部分团队不存在",
        )

    pk = TeamPKRecord(
        pk_name=request.pk_name,
        pk_type=request.pk_type,
        team_ids=json.dumps(request.team_ids),
        start_date=request.start_date,
        end_date=request.end_date,
        target_value=request.target_value,
        reward_description=request.reward_description,
        status="PENDING" if request.start_date > datetime.now() else "ONGOING",
        created_by=current_user.id,
    )
    db.add(pk)
    db.commit()
    db.refresh(pk)

    return ResponseModel(
        code=201,
        message="PK创建成功",
        data={
            "id": pk.id,
            "pk_name": pk.pk_name,
            "status": pk.status,
        }
    )


@router.get("/team-pk/{pk_id}", response_model=ResponseModel)
def get_team_pk(
    *,
    db: Session = Depends(deps.get_db),
    pk_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取团队PK详情"""
    pk = db.query(TeamPKRecord).filter(TeamPKRecord.id == pk_id).first()
    if not pk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PK记录不存在",
        )

    team_ids = json.loads(pk.team_ids) if pk.team_ids else []
    teams = db.query(SalesTeam).filter(SalesTeam.id.in_(team_ids)).all()

    # 获取各团队当前业绩数据
    team_data = []
    for team in teams:
        # 查询该团队在PK期间的业绩
        members = db.query(SalesTeamMember).filter(
            SalesTeamMember.team_id == team.id,
            SalesTeamMember.is_active == True,
        ).all()
        member_ids = [m.user_id for m in members]

        contract_amount = 0
        collection_amount = 0
        lead_count = 0

        if member_ids:
            contracts = db.query(Contract).filter(
                Contract.owner_id.in_(member_ids),
                Contract.created_at >= pk.start_date,
                Contract.created_at <= pk.end_date,
            ).all()
            contract_amount = sum(float(c.contract_amount or 0) for c in contracts)

            invoices = db.query(Invoice).join(Contract).filter(
                Contract.owner_id.in_(member_ids),
                Invoice.paid_date.isnot(None),
                Invoice.paid_date >= pk.start_date.date(),
                Invoice.paid_date <= pk.end_date.date(),
                Invoice.payment_status.in_(["PAID", "PARTIAL"]),
            ).all()
            collection_amount = sum(float(inv.paid_amount or 0) for inv in invoices)

            leads = db.query(Lead).filter(
                Lead.owner_id.in_(member_ids),
                Lead.created_at >= pk.start_date,
                Lead.created_at <= pk.end_date,
            ).all()
            lead_count = len(leads)

        team_data.append({
            "id": team.id,
            "team_code": team.team_code,
            "team_name": team.team_name,
            "member_count": len(member_ids),
            "contract_amount": contract_amount,
            "collection_amount": collection_amount,
            "lead_count": lead_count,
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "id": pk.id,
            "pk_name": pk.pk_name,
            "pk_type": pk.pk_type,
            "team_ids": team_ids,
            "teams": team_data,
            "start_date": pk.start_date,
            "end_date": pk.end_date,
            "target_value": float(pk.target_value) if pk.target_value else None,
            "status": pk.status,
            "winner_team_id": pk.winner_team_id,
            "winner_team_name": pk.winner_team.team_name if pk.winner_team else None,
            "result_summary": json.loads(pk.result_summary) if pk.result_summary else None,
            "reward_description": pk.reward_description,
            "creator_name": (pk.creator.real_name or pk.creator.username) if pk.creator else None,
            "created_at": pk.created_at,
        }
    )


@router.put("/team-pk/{pk_id}", response_model=ResponseModel)
def update_team_pk(
    *,
    db: Session = Depends(deps.get_db),
    pk_id: int,
    request: TeamPKUpdateRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新团队PK"""
    pk = db.query(TeamPKRecord).filter(TeamPKRecord.id == pk_id).first()
    if not pk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PK记录不存在",
        )

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "result_summary" and value:
            value = json.dumps(value) if isinstance(value, dict) else value
        setattr(pk, field, value)

    db.commit()
    db.refresh(pk)

    return ResponseModel(
        code=200,
        message="PK更新成功",
        data={"id": pk.id, "status": pk.status},
    )


@router.post("/team-pk/{pk_id}/complete", response_model=ResponseModel)
def complete_team_pk(
    *,
    db: Session = Depends(deps.get_db),
    pk_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """完成团队PK并计算结果"""
    pk = db.query(TeamPKRecord).filter(TeamPKRecord.id == pk_id).first()
    if not pk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PK记录不存在",
        )

    if pk.status == "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PK已完成",
        )

    team_ids = json.loads(pk.team_ids) if pk.team_ids else []
    teams = db.query(SalesTeam).filter(SalesTeam.id.in_(team_ids)).all()

    # 计算各团队业绩
    results = []
    for team in teams:
        members = db.query(SalesTeamMember).filter(
            SalesTeamMember.team_id == team.id,
            SalesTeamMember.is_active == True,
        ).all()
        member_ids = [m.user_id for m in members]

        value = 0
        if member_ids:
            if pk.pk_type == "CONTRACT_AMOUNT":
                contracts = db.query(Contract).filter(
                    Contract.owner_id.in_(member_ids),
                    Contract.created_at >= pk.start_date,
                    Contract.created_at <= pk.end_date,
                ).all()
                value = sum(float(c.contract_amount or 0) for c in contracts)
            elif pk.pk_type == "COLLECTION_AMOUNT":
                invoices = db.query(Invoice).join(Contract).filter(
                    Contract.owner_id.in_(member_ids),
                    Invoice.paid_date.isnot(None),
                    Invoice.paid_date >= pk.start_date.date(),
                    Invoice.paid_date <= pk.end_date.date(),
                    Invoice.payment_status.in_(["PAID", "PARTIAL"]),
                ).all()
                value = sum(float(inv.paid_amount or 0) for inv in invoices)
            elif pk.pk_type == "LEAD_COUNT":
                value = db.query(Lead).filter(
                    Lead.owner_id.in_(member_ids),
                    Lead.created_at >= pk.start_date,
                    Lead.created_at <= pk.end_date,
                ).count()

        results.append({
            "team_id": team.id,
            "team_name": team.team_name,
            "value": value,
        })

    # 找出获胜者
    results.sort(key=lambda x: x["value"], reverse=True)
    winner = results[0] if results else None

    pk.status = "COMPLETED"
    pk.winner_team_id = winner["team_id"] if winner else None
    pk.result_summary = json.dumps(results)
    db.commit()

    return ResponseModel(
        code=200,
        message="PK已完成",
        data={
            "id": pk.id,
            "winner_team_id": pk.winner_team_id,
            "winner_team_name": winner["team_name"] if winner else None,
            "results": results,
        }
    )


# ==================== 团队（SalesTeam）排名 ====================


@router.get("/sales-teams/ranking", response_model=ResponseModel)
def get_sales_teams_ranking(
    *,
    db: Session = Depends(deps.get_db),
    ranking_type: str = Query("contract_amount", description="排名类型：contract_amount/collection_amount/lead_count/opportunity_count"),
    period_type: str = Query("MONTHLY", description="周期类型：DAILY/WEEKLY/MONTHLY/QUARTERLY"),
    period_value: Optional[str] = Query(None, description="周期标识，如 2026-01（默认当前月）"),
    department_id: Optional[int] = Query(None, description="部门ID筛选"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取销售团队排名（按团队聚合业绩）

    与 /team/ranking 不同，这里是按 SalesTeam 实体排名，而非个人排名。
    """
    from datetime import timedelta

    # 默认当前月
    if not period_value:
        today = date.today()
        period_value = today.strftime("%Y-%m")

    # 计算时间范围
    if period_type == "MONTHLY":
        year, month = map(int, period_value.split("-"))
        start_date_value = date(year, month, 1)
        if month == 12:
            end_date_value = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date_value = date(year, month + 1, 1) - timedelta(days=1)
    elif period_type == "QUARTERLY":
        year, quarter = period_value.split("-Q")
        quarter = int(quarter)
        start_month = (quarter - 1) * 3 + 1
        start_date_value = date(int(year), start_month, 1)
        end_month = quarter * 3
        if end_month == 12:
            end_date_value = date(int(year) + 1, 1, 1) - timedelta(days=1)
        else:
            end_date_value = date(int(year), end_month + 1, 1) - timedelta(days=1)
    else:
        # 默认当月
        today = date.today()
        start_date_value = date(today.year, today.month, 1)
        end_date_value = today

    start_datetime = datetime.combine(start_date_value, datetime.min.time())
    end_datetime = datetime.combine(end_date_value, datetime.max.time())

    # 查询团队
    query = db.query(SalesTeam).filter(SalesTeam.is_active == True)
    if department_id:
        query = query.filter(SalesTeam.department_id == department_id)
    teams = query.all()

    # 计算各团队业绩
    rankings = []
    for team in teams:
        members = db.query(SalesTeamMember).filter(
            SalesTeamMember.team_id == team.id,
            SalesTeamMember.is_active == True,
        ).all()
        member_ids = [m.user_id for m in members]

        lead_count = 0
        opportunity_count = 0
        contract_count = 0
        contract_amount = 0
        collection_amount = 0

        if member_ids:
            # 线索数量
            lead_count = db.query(Lead).filter(
                Lead.owner_id.in_(member_ids),
                Lead.created_at >= start_datetime,
                Lead.created_at <= end_datetime,
            ).count()

            # 商机数量
            opportunity_count = db.query(Opportunity).filter(
                Opportunity.owner_id.in_(member_ids),
                Opportunity.created_at >= start_datetime,
                Opportunity.created_at <= end_datetime,
            ).count()

            # 合同数量和金额
            contracts = db.query(Contract).filter(
                Contract.owner_id.in_(member_ids),
                Contract.created_at >= start_datetime,
                Contract.created_at <= end_datetime,
            ).all()
            contract_count = len(contracts)
            contract_amount = sum(float(c.contract_amount or 0) for c in contracts)

            # 回款金额
            invoices = db.query(Invoice).join(Contract).filter(
                Contract.owner_id.in_(member_ids),
                Invoice.paid_date.isnot(None),
                Invoice.paid_date >= start_date_value,
                Invoice.paid_date <= end_date_value,
                Invoice.payment_status.in_(["PAID", "PARTIAL"]),
            ).all()
            collection_amount = sum(float(inv.paid_amount or 0) for inv in invoices)

        rankings.append({
            "team_id": team.id,
            "team_code": team.team_code,
            "team_name": team.team_name,
            "team_type": team.team_type,
            "leader_name": (team.leader.real_name or team.leader.username) if team.leader else None,
            "member_count": len(member_ids),
            "lead_count": lead_count,
            "opportunity_count": opportunity_count,
            "contract_count": contract_count,
            "contract_amount": contract_amount,
            "collection_amount": collection_amount,
        })

    # 按指定指标排序
    sort_key = ranking_type
    if sort_key not in ["contract_amount", "collection_amount", "lead_count", "opportunity_count", "contract_count"]:
        sort_key = "contract_amount"
    rankings.sort(key=lambda x: x.get(sort_key, 0), reverse=True)

    # 添加排名
    for idx, item in enumerate(rankings[:limit]):
        item["rank"] = idx + 1

    return ResponseModel(
        code=200,
        message="success",
        data={
            "ranking_type": ranking_type,
            "period_type": period_type,
            "period_value": period_value,
            "start_date": start_date_value.isoformat(),
            "end_date": end_date_value.isoformat(),
            "rankings": rankings[:limit],
            "total_count": len(rankings),
        }
    )
