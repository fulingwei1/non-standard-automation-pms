# -*- coding: utf-8 -*-
"""
团队PK管理 API endpoints
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.core import security
from app.models.sales import Contract, Invoice, Lead, SalesTeam, SalesTeamMember, TeamPKRecord
from app.models.sales.operation_log import SalesEntityType, SalesOperationType
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.sales import TeamPKCreateRequest, TeamPKUpdateRequest
from app.services.sales.operation_log_service import SalesOperationLogService

router = APIRouter()


def _safe_parse_id_list(raw_value: Optional[Any]) -> list[int]:
    """Parse legacy team_ids payload safely."""
    if raw_value in (None, "", []):
        return []
    if isinstance(raw_value, list):
        return [int(x) for x in raw_value if str(x).strip().isdigit()]
    if isinstance(raw_value, (int, float)):
        return [int(raw_value)]

    raw_str = str(raw_value).strip()
    if not raw_str:
        return []

    try:
        parsed = json.loads(raw_str)
        if isinstance(parsed, list):
            return [int(x) for x in parsed if str(x).strip().isdigit()]
        if isinstance(parsed, (int, float)):
            return [int(parsed)]
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    # Legacy fallback: "1,2,3" / "1 2 3" / "1"
    normalized = raw_str.replace(";", ",").replace("|", ",").replace(" ", ",")
    return [int(x) for x in normalized.split(",") if x.strip().isdigit()]


def _safe_parse_json(raw_value: Optional[Any]) -> Optional[Any]:
    """Parse optional JSON text safely."""
    if raw_value in (None, ""):
        return None
    if isinstance(raw_value, (dict, list)):
        return raw_value
    try:
        return json.loads(str(raw_value))
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def _audit_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "value"):
        return value.value
    return value


def _team_pk_audit_value(pk: TeamPKRecord) -> dict[str, Any]:
    return {
        "team_pk_id": pk.id,
        "pk_name": pk.pk_name,
        "pk_type": pk.pk_type,
        "team_ids": _safe_parse_id_list(pk.team_ids),
        "start_date": _audit_value(pk.start_date),
        "end_date": _audit_value(pk.end_date),
        "target_value": _audit_value(pk.target_value),
        "status": pk.status,
        "winner_team_id": pk.winner_team_id,
        "result_summary": _safe_parse_json(pk.result_summary),
        "reward_description": pk.reward_description,
        "created_by": pk.created_by,
    }


def _changed_fields(old_value: dict[str, Any], new_value: dict[str, Any]) -> list[str]:
    return [
        field
        for field, value in new_value.items()
        if field in old_value and old_value[field] != value
    ]


def _log_team_pk_operation(
    db: Session,
    pk: TeamPKRecord,
    operation_type: str,
    operator: User,
    *,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    operation_desc: str,
) -> None:
    old_snapshot = old_value or {}
    new_snapshot = new_value or {}
    SalesOperationLogService.log_operation(
        db,
        entity_type=SalesEntityType.TEAM_PK,
        entity_id=pk.id,
        entity_code=f"TEAM-PK-{pk.id}",
        operation_type=operation_type,
        operator=operator,
        operation_desc=operation_desc,
        old_value=old_snapshot,
        new_value=new_snapshot,
        changed_fields=_changed_fields(old_snapshot, new_snapshot),
        remark="team_pk",
    )


@router.get("/team-pk", response_model=ResponseModel)
def list_team_pks(
    *,
    db: Session = Depends(deps.get_db),
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    pagination: PaginationParams = Depends(get_pagination_query),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取团队PK列表"""
    query = db.query(TeamPKRecord)

    if status_filter:
        query = query.filter(TeamPKRecord.status == status_filter)

    total = query.count()
    pks = apply_pagination(
        query.order_by(TeamPKRecord.created_at.desc()), pagination.offset, pagination.limit
    ).all()

    items = []
    for pk in pks:
        team_ids = _safe_parse_id_list(pk.team_ids)
        teams = db.query(SalesTeam).filter(SalesTeam.id.in_(team_ids)).all()
        team_info = [
            {"id": t.id, "team_code": t.team_code, "team_name": t.team_name} for t in teams
        ]

        items.append(
            {
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
            }
        )

    return ResponseModel(
        code=200,
        message="success",
        data={
            "items": items,
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
        },
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
    db.flush()
    _log_team_pk_operation(
        db,
        pk,
        SalesOperationType.CREATE,
        current_user,
        new_value=_team_pk_audit_value(pk),
        operation_desc="创建团队PK",
    )
    db.commit()
    db.refresh(pk)

    return ResponseModel(
        code=201,
        message="PK创建成功",
        data={
            "id": pk.id,
            "pk_name": pk.pk_name,
            "status": pk.status,
        },
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

    team_ids = _safe_parse_id_list(pk.team_ids)
    teams = db.query(SalesTeam).filter(SalesTeam.id.in_(team_ids)).all()

    # 获取各团队当前业绩数据
    team_data = []
    for team in teams:
        # 查询该团队在PK期间的业绩
        members = (
            db.query(SalesTeamMember)
            .filter(
                SalesTeamMember.team_id == team.id,
                SalesTeamMember.is_active,
            )
            .all()
        )
        member_ids = [m.user_id for m in members]

        contract_amount = 0
        collection_amount = 0
        lead_count = 0

        if member_ids:
            contracts = (
                db.query(Contract)
                .filter(
                    Contract.sales_owner_id.in_(member_ids),
                    Contract.created_at >= pk.start_date,
                    Contract.created_at <= pk.end_date,
                )
                .all()
            )
            contract_amount = sum(float(c.contract_amount or 0) for c in contracts)

            invoices = (
                db.query(Invoice)
                .join(Contract)
                .filter(
                    Contract.sales_owner_id.in_(member_ids),
                    Invoice.paid_date.isnot(None),
                    Invoice.paid_date >= pk.start_date.date(),
                    Invoice.paid_date <= pk.end_date.date(),
                    Invoice.payment_status.in_(["PAID", "PARTIAL"]),
                )
                .all()
            )
            collection_amount = sum(float(inv.paid_amount or 0) for inv in invoices)

            leads = (
                db.query(Lead)
                .filter(
                    Lead.owner_id.in_(member_ids),
                    Lead.created_at >= pk.start_date,
                    Lead.created_at <= pk.end_date,
                )
                .all()
            )
            lead_count = len(leads)

        team_data.append(
            {
                "id": team.id,
                "team_code": team.team_code,
                "team_name": team.team_name,
                "member_count": len(member_ids),
                "contract_amount": contract_amount,
                "collection_amount": collection_amount,
                "lead_count": lead_count,
            }
        )

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
            "result_summary": _safe_parse_json(pk.result_summary),
            "reward_description": pk.reward_description,
            "creator_name": (pk.creator.real_name or pk.creator.username) if pk.creator else None,
            "created_at": pk.created_at,
        },
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

    old_value = _team_pk_audit_value(pk)
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "result_summary" and value:
            value = json.dumps(value) if isinstance(value, dict) else value
        setattr(pk, field, value)

    db.flush()
    _log_team_pk_operation(
        db,
        pk,
        SalesOperationType.UPDATE,
        current_user,
        old_value=old_value,
        new_value=_team_pk_audit_value(pk),
        operation_desc="更新团队PK",
    )
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

    team_ids = _safe_parse_id_list(pk.team_ids)
    teams = db.query(SalesTeam).filter(SalesTeam.id.in_(team_ids)).all()

    # 计算各团队业绩
    results = []
    for team in teams:
        members = (
            db.query(SalesTeamMember)
            .filter(
                SalesTeamMember.team_id == team.id,
                SalesTeamMember.is_active,
            )
            .all()
        )
        member_ids = [m.user_id for m in members]

        value = 0
        if member_ids:
            if pk.pk_type == "CONTRACT_AMOUNT":
                contracts = (
                    db.query(Contract)
                    .filter(
                        Contract.sales_owner_id.in_(member_ids),
                        Contract.created_at >= pk.start_date,
                        Contract.created_at <= pk.end_date,
                    )
                    .all()
                )
                value = sum(float(c.contract_amount or 0) for c in contracts)
            elif pk.pk_type == "COLLECTION_AMOUNT":
                invoices = (
                    db.query(Invoice)
                    .join(Contract)
                    .filter(
                        Contract.sales_owner_id.in_(member_ids),
                        Invoice.paid_date.isnot(None),
                        Invoice.paid_date >= pk.start_date.date(),
                        Invoice.paid_date <= pk.end_date.date(),
                        Invoice.payment_status.in_(["PAID", "PARTIAL"]),
                    )
                    .all()
                )
                value = sum(float(inv.paid_amount or 0) for inv in invoices)
            elif pk.pk_type == "LEAD_COUNT":
                value = (
                    db.query(Lead)
                    .filter(
                        Lead.owner_id.in_(member_ids),
                        Lead.created_at >= pk.start_date,
                        Lead.created_at <= pk.end_date,
                    )
                    .count()
                )

        results.append(
            {
                "team_id": team.id,
                "team_name": team.team_name,
                "value": value,
            }
        )

    # 找出获胜者
    results.sort(key=lambda x: x["value"], reverse=True)
    winner = results[0] if results else None

    old_value = _team_pk_audit_value(pk)
    pk.status = "COMPLETED"
    pk.winner_team_id = winner["team_id"] if winner else None
    pk.result_summary = json.dumps(results)
    db.flush()
    _log_team_pk_operation(
        db,
        pk,
        SalesOperationType.STATUS_CHANGE,
        current_user,
        old_value=old_value,
        new_value=_team_pk_audit_value(pk),
        operation_desc="完成团队PK",
    )
    db.commit()

    return ResponseModel(
        code=200,
        message="PK已完成",
        data={
            "id": pk.id,
            "winner_team_id": pk.winner_team_id,
            "winner_team_name": winner["team_name"] if winner else None,
            "results": results,
        },
    )
