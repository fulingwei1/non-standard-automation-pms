# -*- coding: utf-8 -*-
"""
第十四批：验收奖金计算服务 单元测试
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

try:
    from app.services import acceptance_bonus_service as abs_svc
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_db():
    return MagicMock()


def make_project(**kwargs):
    p = MagicMock()
    p.id = kwargs.get("id", 1)
    p.contract_no = kwargs.get("contract_no", "CT-2025-001")
    return p


def make_rule(**kwargs):
    r = MagicMock()
    r.id = kwargs.get("id", 1)
    r.rule_name = "奖金规则"
    r.bonus_type = kwargs.get("bonus_type", "ACCEPTANCE")
    r.coefficient = kwargs.get("coefficient", Decimal("3"))
    r.trigger_condition = kwargs.get("trigger_condition", {})
    r.is_active = True
    return r


class TestAcceptanceBonusService:
    def test_get_active_rules(self):
        db = make_db()
        rules = [make_rule(), make_rule(id=2)]
        db.query.return_value.filter.return_value.all.return_value = rules
        result = abs_svc.get_active_rules(db, "ACCEPTANCE")
        assert result == rules

    def test_get_active_rules_empty(self):
        db = make_db()
        db.query.return_value.filter.return_value.all.return_value = []
        result = abs_svc.get_active_rules(db, "NONEXISTENT")
        assert result == []

    def test_calculate_sales_bonus_no_contract(self):
        db = make_db()
        project = make_project()
        db.query.return_value.filter.return_value.first.return_value = None
        rules = [make_rule(trigger_condition={"acceptance_completed": True})]
        result = abs_svc.calculate_sales_bonus(db, project, rules)
        assert result is None

    def test_calculate_sales_bonus_with_contract(self):
        db = make_db()
        project = make_project()
        contract = MagicMock()
        contract.id = 100
        contract.contract_amount = Decimal("1000000")
        db.query.return_value.filter.return_value.first.return_value = contract
        rule = make_rule(coefficient=Decimal("3"))
        result = abs_svc.calculate_sales_bonus(db, project, [rule])
        assert result is not None
        db.add.assert_called_once()
        # 检查 total_bonus = 1000000 * 3/100 = 30000
        assert result.total_bonus_amount == Decimal("30000")

    def test_calculate_sales_bonus_zero_ratio(self):
        db = make_db()
        project = make_project()
        contract = MagicMock()
        contract.id = 100
        contract.contract_amount = Decimal("1000000")
        db.query.return_value.filter.return_value.first.return_value = contract
        rule = make_rule(coefficient=Decimal("0"))
        result = abs_svc.calculate_sales_bonus(db, project, [rule])
        assert result is None  # 奖金为0，不创建记录

    def test_calculate_presale_bonus_no_rules(self):
        db = make_db()
        project = make_project()
        result = abs_svc.calculate_presale_bonus(db, project, [])
        assert result is None

    def test_calculate_presale_bonus_no_tickets(self):
        db = make_db()
        project = make_project()
        db.query.return_value.filter.return_value.all.return_value = []
        rules = [make_rule(bonus_type="PRESALE")]
        result = abs_svc.calculate_presale_bonus(db, project, rules)
        assert result is None
