# -*- coding: utf-8 -*-
"""binding_validation_service 深度测试"""

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.sales.binding_validation_service import (
    BindingIssueCode,
    BindingIssueLevel,
    BindingValidationResult,
    BindingValidationService,
)


class FakeQuery:
    def __init__(self, get_map=None, first_value=None, all_value=None):
        self._get_map = get_map or {}
        self._first_value = first_value
        self._all_value = all_value or []

    def get(self, key):
        return self._get_map.get(key)

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self._first_value

    def all(self):
        return self._all_value


class TestBindingValidationServiceDeep:
    def test_validation_result_properties(self):
        result = BindingValidationResult(
            quote_version_id=1,
            status="outdated",
            issues=[
                SimpleNamespace(level=BindingIssueLevel.WARNING),
                SimpleNamespace(level=BindingIssueLevel.ERROR),
            ],
            validated_at=datetime(2026, 4, 12, 11, 0, 0),
        )

        assert result.is_valid is False
        assert result.has_errors is True
        assert result.has_warnings is True

    @pytest.mark.asyncio
    async def test_validate_quote_binding_raises_when_missing(self):
        db = MagicMock()
        db.query.return_value = FakeQuery(get_map={})
        service = BindingValidationService(db)

        with pytest.raises(ValueError, match="报价版本不存在: 99"):
            await service.validate_quote_binding(99)

    @pytest.mark.asyncio
    async def test_validate_quote_binding_outdated_with_multiple_warnings(self):
        db = MagicMock()
        solution = SimpleNamespace(id=10, solution_id=1, version_no="V1.0", status="draft")
        latest = SimpleNamespace(id=11, solution_id=1, version_no="V1.1", status="approved")
        cost = SimpleNamespace(id=20, status="draft", solution_version_id=10, total_cost=Decimal("100"))
        qv = SimpleNamespace(
            id=3,
            solution_version_id=10,
            solution_version=solution,
            cost_estimation_id=20,
            cost_estimation=cost,
            cost_total=Decimal("100"),
            binding_status=None,
            binding_validated_at=None,
            binding_warning=None,
        )
        db.query.return_value = FakeQuery(get_map={3: qv})
        service = BindingValidationService(db)
        service._get_latest_approved_solution_version = MagicMock(return_value=latest)

        result = await service.validate_quote_binding(3)

        assert result.status == "outdated"
        assert {i.code for i in result.issues} == {
            BindingIssueCode.SOLUTION_NOT_APPROVED,
            BindingIssueCode.SOLUTION_VERSION_OUTDATED,
            BindingIssueCode.COST_NOT_APPROVED,
        }
        assert qv.binding_status == "outdated"
        assert "方案版本 V1.0 未审批" in qv.binding_warning
        assert "成本估算未审批" in qv.binding_warning
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_cost_to_quote_updates_margin_and_binding(self):
        db = MagicMock()
        cost = SimpleNamespace(
            id=8,
            total_cost=Decimal("80"),
            is_bound_to_quote=False,
            bound_quote_version_id=None,
        )
        qv = SimpleNamespace(
            id=5,
            cost_estimation=cost,
            total_price=Decimal("200"),
            cost_total=None,
            gross_margin=None,
            binding_status=None,
            binding_validated_at=None,
            binding_warning="x",
        )
        db.query.return_value = FakeQuery(get_map={5: qv})
        service = BindingValidationService(db)

        updated = await service.sync_cost_to_quote(5)

        assert updated is qv
        assert qv.cost_total == Decimal("80")
        assert qv.gross_margin == Decimal("60.00")
        assert qv.binding_status == "valid"
        assert qv.binding_warning is None
        assert cost.is_bound_to_quote is True
        assert cost.bound_quote_version_id == 5
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_cost_to_quote_missing_quote_or_cost(self):
        db = MagicMock()
        service = BindingValidationService(db)
        db.query.side_effect = [FakeQuery(get_map={}), FakeQuery(get_map={6: SimpleNamespace(id=6, cost_estimation=None)})]

        with pytest.raises(ValueError, match="报价版本不存在: 6"):
            await service.sync_cost_to_quote(6)
        with pytest.raises(ValueError, match="报价未绑定成本估算，无法同步"):
            await service.sync_cost_to_quote(6)

    @pytest.mark.asyncio
    async def test_validate_binding_before_submit_blocks_on_errors(self):
        service = BindingValidationService(MagicMock())
        fail = BindingValidationResult(
            quote_version_id=1,
            status="invalid",
            issues=[
                SimpleNamespace(level=BindingIssueLevel.ERROR, message="A"),
                SimpleNamespace(level=BindingIssueLevel.WARNING, message="B"),
                SimpleNamespace(level=BindingIssueLevel.ERROR, message="C"),
            ],
            validated_at=datetime.now(),
        )
        ok = BindingValidationResult(
            quote_version_id=2,
            status="outdated",
            issues=[SimpleNamespace(level=BindingIssueLevel.WARNING, message="W")],
            validated_at=datetime.now(),
        )
        async def fake_validate(_quote_version_id):
            return {1: fail, 2: ok}[_quote_version_id]

        service.validate_quote_binding = fake_validate

        with pytest.raises(ValueError, match="报价绑定验证失败：A; C"):
            await service.validate_binding_before_submit(1)
        result = await service.validate_binding_before_submit(2)

        assert result is ok

    @pytest.mark.asyncio
    async def test_check_solution_update_impact_and_latest_version(self):
        db = MagicMock()
        solution = SimpleNamespace(id=4)
        costs = [SimpleNamespace(id=1, version_no="C1", status="approved")]
        quotes = [SimpleNamespace(id=2, quote_id=9, version_no="Q1")]
        latest = SimpleNamespace(id=10, version_no="V2.0")
        db.query.side_effect = [
            FakeQuery(get_map={4: solution}),
            FakeQuery(all_value=costs),
            FakeQuery(all_value=quotes),
            FakeQuery(first_value=latest),
            FakeQuery(get_map={}),
        ]
        service = BindingValidationService(db)

        impact = await service.check_solution_update_impact(4)
        latest_result = service._get_latest_approved_solution_version(4)
        empty = await service.check_solution_update_impact(99)

        assert impact == [
            {"type": "cost_estimation", "id": 1, "version_no": "C1", "status": "approved", "impact": "需要重新评估成本"},
            {"type": "quote_version", "id": 2, "quote_id": 9, "version_no": "Q1", "impact": "需要更新绑定或重新报价"},
        ]
        assert latest_result is latest
        assert empty == []
