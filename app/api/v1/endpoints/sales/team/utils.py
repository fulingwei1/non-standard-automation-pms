# -*- coding: utf-8 -*-
"""
销售团队管理工具函数
"""

from datetime import date, datetime
from typing import Dict, List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core import security
from app.models.sales import Contract, Invoice, Lead, Opportunity
from app.models.user import User, UserRole
from app.services.sales_team_service import SalesTeamService



def ensure_sales_director_permission(current_user: User, db: Session):
    """检查是否为销售总监（数据范围 ALL）"""
    if current_user.is_superuser:
        return
    scope = security.get_sales_data_scope(current_user, db)
    if scope != 'ALL':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅销售总监可以调整排名权重配置",
        )


def collect_sales_team_members(
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


def build_team_response(team, db: Session, include_members: bool = True) -> dict:
    """构建团队响应数据"""
    from app.models.sales import SalesTeamMember

    # 获取成员数量
    member_count = db.query(SalesTeamMember).filter(
        SalesTeamMember.team_id == team.id,
        SalesTeamMember.is_active,
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
            SalesTeamMember.is_active,
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
