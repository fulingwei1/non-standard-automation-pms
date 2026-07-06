# -*- coding: utf-8 -*-
"""
评分规则管理 API endpoints

包含评分规则的查询、创建、激活等端点
"""

from __future__ import annotations

import json
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import ScoringRule
from app.models.sales.operation_log import SalesEntityType, SalesOperationType
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.sales import ScoringRuleCreate, ScoringRuleResponse
from app.services.sales.operation_log_service import SalesOperationLogService
from app.utils.db_helpers import get_or_404

router = APIRouter()


def _json_audit_value(value: str | None) -> Any:
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _scoring_rule_audit_value(rule: ScoringRule) -> dict[str, Any]:
    return {
        "id": rule.id,
        "version": rule.version,
        "rules_json": _json_audit_value(rule.rules_json),
        "is_active": bool(rule.is_active),
        "description": rule.description,
        "created_by": rule.created_by,
    }


def _changed_fields(old_value: dict[str, Any], new_value: dict[str, Any]) -> list[str]:
    return [
        field
        for field, value in new_value.items()
        if old_value.get(field) != value
    ]


def _log_scoring_rule_operation(
    db: Session,
    rule: ScoringRule,
    operation_type: str,
    current_user: User,
    *,
    old_value: dict[str, Any] | None,
    new_value: dict[str, Any] | None,
    changed_fields: list[str] | None,
    operation_desc: str,
    remark: str | None = None,
) -> None:
    SalesOperationLogService.log_operation(
        db,
        entity_type=SalesEntityType.SCORING_RULE,
        entity_id=rule.id,
        entity_code=rule.version,
        operation_type=operation_type,
        operator=current_user,
        operation_desc=operation_desc,
        old_value=old_value,
        new_value=new_value,
        changed_fields=changed_fields,
        remark=remark,
    )


@router.get("/scoring-rules", response_model=List[ScoringRuleResponse])
def list_scoring_rules(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取评分规则列表"""
    rules = db.query(ScoringRule).order_by(desc(ScoringRule.created_at)).all()

    result = []
    for rule in rules:
        creator_name = None
        if rule.created_by:
            creator = db.query(User).filter(User.id == rule.created_by).first()
            creator_name = creator.real_name if creator else None

        result.append(
            ScoringRuleResponse(
                id=rule.id,
                version=rule.version,
                is_active=rule.is_active,
                description=rule.description,
                created_by=rule.created_by,
                created_at=rule.created_at,
                updated_at=rule.updated_at,
                creator_name=creator_name,
            )
        )

    return result


@router.post("/scoring-rules", response_model=ScoringRuleResponse, status_code=201)
def create_scoring_rule(
    *,
    db: Session = Depends(deps.get_db),
    request: ScoringRuleCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建评分规则"""
    # 检查版本号是否已存在
    existing = db.query(ScoringRule).filter(ScoringRule.version == request.version).first()
    if existing:
        raise HTTPException(status_code=400, detail="版本号已存在")

    rule = ScoringRule(
        version=request.version,
        rules_json=request.rules_json,
        description=request.description,
        created_by=current_user.id,
    )

    db.add(rule)
    db.flush()
    _log_scoring_rule_operation(
        db,
        rule,
        SalesOperationType.CREATE,
        current_user,
        old_value={},
        new_value=_scoring_rule_audit_value(rule),
        changed_fields=[],
        operation_desc="创建评分规则",
        remark=rule.description,
    )
    db.commit()
    db.refresh(rule)

    return ScoringRuleResponse(
        id=rule.id,
        version=rule.version,
        is_active=rule.is_active,
        description=rule.description,
        created_by=rule.created_by,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
        creator_name=current_user.real_name,
    )


@router.put("/scoring-rules/{rule_id}/activate", response_model=ResponseModel)
def activate_scoring_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """激活评分规则版本"""
    rule = get_or_404(db, ScoringRule, rule_id, detail="评分规则不存在")

    active_rules = (
        db.query(ScoringRule)
        .filter(ScoringRule.is_active.is_(True), ScoringRule.id != rule.id)
        .all()
    )
    active_rule_old_values = {
        active_rule.id: _scoring_rule_audit_value(active_rule)
        for active_rule in active_rules
    }
    old_value = _scoring_rule_audit_value(rule)

    # 取消其他规则的激活状态
    for active_rule in active_rules:
        active_rule.is_active = False

    # 激活当前规则
    rule.is_active = True
    db.flush()

    for active_rule in active_rules:
        active_old_value = active_rule_old_values[active_rule.id]
        active_new_value = _scoring_rule_audit_value(active_rule)
        _log_scoring_rule_operation(
            db,
            active_rule,
            SalesOperationType.STATUS_CHANGE,
            current_user,
            old_value=active_old_value,
            new_value=active_new_value,
            changed_fields=_changed_fields(active_old_value, active_new_value),
            operation_desc="停用评分规则",
        )

    new_value = _scoring_rule_audit_value(rule)
    _log_scoring_rule_operation(
        db,
        rule,
        SalesOperationType.STATUS_CHANGE,
        current_user,
        old_value=old_value,
        new_value=new_value,
        changed_fields=_changed_fields(old_value, new_value),
        operation_desc="激活评分规则",
    )
    db.commit()

    return ResponseModel(message="评分规则已激活")
