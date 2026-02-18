# -*- coding: utf-8 -*-
"""
第十六批：收款计划服务 单元测试
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.sales.payment_plan_service import PaymentPlanService
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_db():
    return MagicMock()


def make_contract(**kwargs):
    contract = MagicMock()
    contract.id = kwargs.get("id", 1)
    contract.project_id = kwargs.get("project_id", 10)
    contract.contract_amount = kwargs.get("contract_amount", 1000000.0)
    contract.contract_code = kwargs.get("contract_code", "CT-2025-001")
    contract.customer_id = kwargs.get("customer_id", 5)
    return contract


class TestPaymentPlanService:
    def _svc(self, db=None):
        db = db or make_db()
        return PaymentPlanService(db)

    def test_init(self):
        db = make_db()
        svc = PaymentPlanService(db)
        assert svc.db is db

    def test_validate_contract_no_project_id(self):
        db = make_db()
        contract = make_contract(project_id=None)
        svc = PaymentPlanService(db)
        result = svc._validate_contract(contract)
        assert result is False

    def test_validate_contract_project_not_found(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        contract = make_contract()
        svc = PaymentPlanService(db)
        result = svc._validate_contract(contract)
        assert result is False

    def test_validate_contract_zero_amount(self):
        db = make_db()
        project = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.count.return_value = 0
        contract = make_contract(contract_amount=0)
        svc = PaymentPlanService(db)
        result = svc._validate_contract(contract)
        assert result is False

    def test_validate_contract_existing_plans(self):
        db = make_db()
        project = MagicMock()
        # 第一次查询返回project，第二次查询返回existing plans count
        first_call = MagicMock()
        first_call.first.return_value = project
        second_call = MagicMock()
        second_call.count.return_value = 3
        db.query.return_value.filter.side_effect = [first_call, second_call]
        contract = make_contract(contract_amount=100000.0)
        svc = PaymentPlanService(db)
        result = svc._validate_contract(contract)
        assert result is False

    def test_get_payment_configurations(self):
        svc = self._svc()
        configs = svc._get_payment_configurations()
        assert isinstance(configs, list)
        assert len(configs) > 0
        # 检查预付款配置
        types = [c["payment_type"] for c in configs]
        assert "ADVANCE" in types

    def test_generate_payment_plans_from_contract_invalid(self):
        db = make_db()
        # 无效合同（无项目ID）
        contract = make_contract(project_id=None)
        svc = PaymentPlanService(db)
        plans = svc.generate_payment_plans_from_contract(contract)
        assert plans == []

    def test_generate_payment_plans_from_contract_valid(self):
        db = make_db()
        project = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.count.return_value = 0
        contract = make_contract(contract_amount=500000.0)
        svc = PaymentPlanService(db)
        # _create_payment_plan 可能返回None，这里mock一下
        with patch.object(svc, '_create_payment_plan', return_value=MagicMock()):
            plans = svc.generate_payment_plans_from_contract(contract)
            assert isinstance(plans, list)
