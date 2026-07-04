# -*- coding: utf-8 -*-
"""HR-17 契约：奖金审批主链路加固。

1. 审批端点必须挂 bonus:manage 权限（不再任意登录用户可批）。
2. 受益人不得审批自己的奖金（防自审）。
3. 只有 CALCULATED 状态可审批（防重复审批/终态翻案）。
4. Excel 分配表导入的计算记录必须带审批留痕（审批人/时间/意见），不再无痕直批。
"""
import uuid
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.bonus import BonusCalculation, BonusRule
from tests.conftest import _get_or_create_user


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _seed_rule(db, user_id):
    rule = BonusRule(
        rule_code=_unique("BR"),
        rule_name="测试奖金规则",
        bonus_type="PROJECT",
    )
    db.add(rule)
    db.flush()
    return rule


def _seed_calc(db, rule_id, beneficiary_id, status="CALCULATED"):
    calc = BonusCalculation(
        calculation_code=_unique("BC"),
        rule_id=rule_id,
        user_id=beneficiary_id,
        calculated_amount=Decimal("8000"),
        status=status,
    )
    db.add(calc)
    db.commit()
    db.refresh(calc)
    return calc


def _users(db):
    approver = _get_or_create_user(
        db,
        username=_unique("appr").lower(),
        password="test123",
        real_name="奖金审批人",
        department="人事部",
    )
    beneficiary = _get_or_create_user(
        db,
        username=_unique("benef").lower(),
        password="test123",
        real_name="奖金受益人",
        department="销售部",
    )
    return approver, beneficiary


def test_approve_endpoint_requires_bonus_manage_permission():
    import inspect

    from app.api.v1.endpoints.bonus import sales_calc

    src = inspect.getsource(sales_calc.approve_bonus_calculation)
    assert 'require_permission("bonus:manage")' in src, "审批端点未挂 bonus:manage 权限"


def test_self_approval_is_rejected(db_session):
    from app.api.v1.endpoints.bonus.sales_calc import approve_bonus_calculation
    from app.schemas.bonus import BonusCalculationApprove

    approver, _ = _users(db_session)
    rule = _seed_rule(db_session, approver.id)
    calc = _seed_calc(db_session, rule.id, beneficiary_id=approver.id)

    with pytest.raises(HTTPException) as exc:
        approve_bonus_calculation(
            db=db_session,
            calc_id=calc.id,
            approve_in=BonusCalculationApprove(approved=True, comment="给自己批"),
            current_user=approver,
        )
    assert exc.value.status_code == 403
    db_session.expire_all()
    assert db_session.get(BonusCalculation, calc.id).status == "CALCULATED"


def test_only_calculated_status_can_be_approved(db_session):
    from app.api.v1.endpoints.bonus.sales_calc import approve_bonus_calculation
    from app.schemas.bonus import BonusCalculationApprove

    approver, beneficiary = _users(db_session)
    rule = _seed_rule(db_session, approver.id)
    approved_calc = _seed_calc(db_session, rule.id, beneficiary.id, status="APPROVED")

    with pytest.raises(HTTPException) as exc:
        approve_bonus_calculation(
            db=db_session,
            calc_id=approved_calc.id,
            approve_in=BonusCalculationApprove(approved=False, comment="翻案"),
            current_user=approver,
        )
    assert exc.value.status_code == 400, "已审批记录不得重复流转"

    # 正常路径：CALCULATED 可批
    fresh = _seed_calc(db_session, rule.id, beneficiary.id)
    result = approve_bonus_calculation(
        db=db_session,
        calc_id=fresh.id,
        approve_in=BonusCalculationApprove(approved=True, comment="ok"),
        current_user=approver,
    )
    assert result.data.status == "APPROVED"
    assert result.data.approved_by == approver.id


def test_excel_import_calculation_carries_approval_trace(db_session):
    from app.services.bonus import BonusCalculator
    from app.services.bonus.bonus_distribution_service import (
        create_calculation_from_team_allocation,
    )
    from app.models.bonus import TeamBonusAllocation
    from app.models.project import Project

    approver, beneficiary = _users(db_session)
    rule = _seed_rule(db_session, approver.id)
    project = Project(
        project_code=_unique("PJ-BONUS"),
        project_name="奖金测试项目",
        stage="S4",
        status="ST04",
        health="H1",
    )
    db_session.add(project)
    db_session.flush()
    allocation = TeamBonusAllocation(
        project_id=project.id,
        total_bonus_amount=Decimal("50000"),
        allocation_detail={"rule_id": rule.id},
        status="CONFIRMED",
    )
    db_session.add(allocation)
    db_session.flush()

    calc = create_calculation_from_team_allocation(
        db_session,
        allocation.id,
        beneficiary.id,
        Decimal("8000"),
        BonusCalculator(db_session),
        approved_by=approver.id,
    )

    assert calc.status == "APPROVED"
    assert calc.approved_by == approver.id, "导入直批必须留审批人痕迹"
    assert calc.approved_at is not None
    assert "线下确认" in (calc.approval_comment or "")
