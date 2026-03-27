# -*- coding: utf-8 -*-
"""
销售团队组织架构 API
GET /sales/team/org — 返回销售团队层级树、各节点业绩、汇报关系
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import Contract, Lead, Opportunity, SalesTeam, SalesTeamMember
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


def _build_user_metrics(
    db: Session,
    user_id: int,
    start_dt: datetime,
    end_dt: datetime,
) -> Dict[str, Any]:
    """计算单个用户的业绩指标"""
    lead_count = (
        db.query(func.count(Lead.id))
        .filter(Lead.owner_id == user_id, Lead.created_at >= start_dt, Lead.created_at <= end_dt)
        .scalar() or 0
    )
    opp_count = (
        db.query(func.count(Opportunity.id))
        .filter(Opportunity.owner_id == user_id, Opportunity.created_at >= start_dt, Opportunity.created_at <= end_dt)
        .scalar() or 0
    )
    contract_rows = (
        db.query(Contract)
        .filter(Contract.sales_owner_id == user_id, Contract.created_at >= start_dt, Contract.created_at <= end_dt)
        .all()
    )
    contract_count = len(contract_rows)
    contract_amount = sum(float(c.contract_amount or 0) for c in contract_rows)

    return {
        "lead_count": lead_count,
        "opportunity_count": opp_count,
        "contract_count": contract_count,
        "contract_amount": contract_amount,
    }


def _build_team_node(
    db: Session,
    team: SalesTeam,
    start_dt: datetime,
    end_dt: datetime,
    children_map: Dict[int, List[SalesTeam]],
) -> Dict[str, Any]:
    """递归构建团队树节点"""
    # 获取团队成员
    members = (
        db.query(SalesTeamMember)
        .filter(SalesTeamMember.team_id == team.id, SalesTeamMember.is_active.is_(True))
        .all()
    )

    member_nodes = []
    team_total_amount = 0.0
    team_total_contracts = 0
    team_total_opps = 0

    for m in members:
        user = m.user
        if not user:
            continue
        metrics = _build_user_metrics(db, user.id, start_dt, end_dt)
        team_total_amount += metrics["contract_amount"]
        team_total_contracts += metrics["contract_count"]
        team_total_opps += metrics["opportunity_count"]

        member_nodes.append({
            "id": user.id,
            "name": user.real_name or user.username,
            "level": "Sales",
            "role": m.role,
            "metrics": metrics,
        })

    # 递归处理子团队
    child_teams = children_map.get(team.id, [])
    child_nodes = []
    for child in child_teams:
        child_node = _build_team_node(db, child, start_dt, end_dt, children_map)
        team_total_amount += child_node.get("metrics", {}).get("contract_amount", 0)
        team_total_contracts += child_node.get("metrics", {}).get("contract_count", 0)
        team_total_opps += child_node.get("metrics", {}).get("opportunity_count", 0)
        child_nodes.append(child_node)

    # 确定节点层级
    if team.parent_team_id is None:
        level = "GM"
    elif not children_map.get(team.id):
        level = "Manager"
    else:
        level = "Director"

    # 负责人信息
    person = None
    if team.leader:
        person = {
            "id": team.leader.id,
            "name": team.leader.real_name or team.leader.username,
            "title": team.team_name,
        }

    total_members = len(member_nodes) + sum(
        c.get("metrics", {}).get("team_size", 0) for c in child_nodes
    )

    node = {
        "id": team.id,
        "name": team.team_name,
        "level": level,
        "person": person,
        "metrics": {
            "team_size": total_members or len(member_nodes),
            "contract_amount": team_total_amount,
            "contract_count": team_total_contracts,
            "opportunity_count": team_total_opps,
        },
        "children": child_nodes + member_nodes,
    }
    return node


@router.get("/team/org", response_model=ResponseModel, summary="销售团队组织架构")
def get_team_org(
    start_date: Optional[date] = Query(None, description="统计开始日期"),
    end_date: Optional[date] = Query(None, description="统计结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取销售团队组织架构树

    返回：
    - 层级树结构（GM → Director → Manager → Sales）
    - 各节点业绩指标
    - 汇报关系
    """
    start_dt_date = start_date or date(date.today().year, 1, 1)
    end_dt_date = end_date or date.today()
    start_dt = datetime.combine(start_dt_date, datetime.min.time())
    end_dt = datetime.combine(end_dt_date, datetime.max.time())

    # 获取所有活跃团队
    all_teams = db.query(SalesTeam).filter(SalesTeam.is_active.is_(True)).order_by(SalesTeam.sort_order).all()

    if not all_teams:
        return ResponseModel(code=200, message="success", data={"organization_tree": None, "total_members": 0})

    # 构建 parent → children 映射
    children_map: Dict[int, List[SalesTeam]] = {}
    root_teams: List[SalesTeam] = []
    for t in all_teams:
        if t.parent_team_id is None:
            root_teams.append(t)
        else:
            children_map.setdefault(t.parent_team_id, []).append(t)

    # 构建树
    if len(root_teams) == 1:
        tree = _build_team_node(db, root_teams[0], start_dt, end_dt, children_map)
    else:
        # 多个根团队时包装为虚拟根节点
        child_nodes = [_build_team_node(db, rt, start_dt, end_dt, children_map) for rt in root_teams]
        tree = {
            "id": 0,
            "name": "销售总部",
            "level": "GM",
            "person": None,
            "metrics": {
                "team_size": sum(c.get("metrics", {}).get("team_size", 0) for c in child_nodes),
                "contract_amount": sum(c.get("metrics", {}).get("contract_amount", 0) for c in child_nodes),
                "contract_count": sum(c.get("metrics", {}).get("contract_count", 0) for c in child_nodes),
                "opportunity_count": sum(c.get("metrics", {}).get("opportunity_count", 0) for c in child_nodes),
            },
            "children": child_nodes,
        }

    # 统计总成员数
    total_members = (
        db.query(func.count(func.distinct(SalesTeamMember.user_id)))
        .filter(SalesTeamMember.is_active.is_(True))
        .scalar() or 0
    )

    return ResponseModel(
        code=200,
        message="success",
        data={
            "organization_tree": tree,
            "total_members": total_members,
            "period": {
                "start": start_dt_date.isoformat(),
                "end": end_dt_date.isoformat(),
            },
        },
    )
