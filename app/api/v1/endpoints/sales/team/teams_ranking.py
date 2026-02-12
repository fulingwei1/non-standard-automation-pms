# -*- coding: utf-8 -*-
"""
销售团队排名 API endpoints（按团队实体聚合）
"""

from datetime import date, datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.common.date_range import get_month_range_by_ym
from app.core import security
from app.models.sales import Contract, Invoice, Lead, Opportunity, SalesTeam, SalesTeamMember
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


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
    # 默认当前月
    if not period_value:
        today = date.today()
        period_value = today.strftime("%Y-%m")

    # 计算时间范围
    if period_type == "MONTHLY":
        year, month = map(int, period_value.split("-"))
        start_date_value, end_date_value = get_month_range_by_ym(year, month)
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
    query = db.query(SalesTeam).filter(SalesTeam.is_active)
    if department_id:
        query = query.filter(SalesTeam.department_id == department_id)
    teams = query.all()

    # 计算各团队业绩
    rankings = []
    for team in teams:
        members = db.query(SalesTeamMember).filter(
            SalesTeamMember.team_id == team.id,
            SalesTeamMember.is_active,
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
