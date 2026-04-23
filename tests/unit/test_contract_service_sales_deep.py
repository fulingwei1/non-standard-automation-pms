# -*- coding: utf-8 -*-
"""sales.contract_service 深度测试"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.sales.contract_service import ContractService


class DummySelect:
    def where(self, *args, **kwargs):
        return self

    def options(self, *args, **kwargs):
        return self


class DummyNested:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeResult:
    def __init__(self, first_value):
        self._first_value = first_value

    def first(self):
        return self._first_value


class FakeProject:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.id = None


class FakePaymentPlan:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.id = None


class FakeMilestone:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.id = None


class TestSalesContractServiceDeep:
    def _make_db(self):
        db = MagicMock()
        db.execute = AsyncMock()
        db.begin_nested = MagicMock(return_value=DummyNested())
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        added = []

        def add(obj):
            if getattr(obj, "id", None) is None:
                obj.id = len(added) + 100
            added.append(obj)

        db.add.side_effect = add
        db._added = added
        return db

    @pytest.mark.asyncio
    async def test_create_project_from_contract_not_found(self):
        db = self._make_db()
        db.execute.return_value = FakeResult(None)

        with patch("app.services.sales.contract_service.select", return_value=DummySelect()), \
             patch("app.services.sales.contract_service.selectinload", return_value=None):
            with pytest.raises(ValueError, match="合同不存在: 999"):
                await ContractService.create_project_from_contract(db, 999)

    @pytest.mark.asyncio
    async def test_create_project_from_contract_invalid_status_and_already_linked(self):
        db = self._make_db()
        customer = SimpleNamespace(id=3, name="客户A")
        invalid_contract = SimpleNamespace(
            id=1,
            contract_code="HT-1",
            status="draft",
            project_id=None,
            payment_nodes="[]",
        )
        db.execute.return_value = FakeResult((invalid_contract, customer))

        with patch("app.services.sales.contract_service.select", return_value=DummySelect()), \
             patch("app.services.sales.contract_service.selectinload", return_value=None):
            with pytest.raises(ValueError, match="只有已签署"):
                await ContractService.create_project_from_contract(db, 1)

        linked_contract = SimpleNamespace(
            id=2,
            contract_code="HT-2",
            status="SIGNED",
            project_id=88,
            payment_nodes="[]",
        )
        db.execute.return_value = FakeResult((linked_contract, customer))
        with patch("app.services.sales.contract_service.select", return_value=DummySelect()), \
             patch("app.services.sales.contract_service.selectinload", return_value=None):
            result = await ContractService.create_project_from_contract(db, 2)

        assert result == {
            "success": False,
            "message": "该合同已关联项目ID 88，无需重复创建项目",
            "project_id": 88,
        }

    @pytest.mark.asyncio
    async def test_create_project_from_contract_success_with_payment_nodes(self):
        db = self._make_db()
        customer = SimpleNamespace(id=5, name="客户B")
        contract = SimpleNamespace(
            id=10,
            contract_code="HT-10",
            contract_amount=500000,
            status="signed",
            project_id=None,
            payment_nodes="json",
            sow_text="SOW",
            acceptance_criteria=["AC1"],
        )
        db.execute.return_value = FakeResult((contract, customer))

        with patch("app.services.sales.contract_service.select", return_value=DummySelect()), \
             patch("app.services.sales.contract_service.selectinload", return_value=None), \
             patch("app.services.sales.contract_service.safe_json_loads", return_value=[
                 {"name": "首款", "percentage": 30, "due_date": "2026-05-01", "description": "首款说明"},
                 {"name": "尾款", "percentage": 70, "due_date": "2026-06-01", "description": "尾款说明"},
             ]), \
             patch("app.services.sales.contract_service.Project", FakeProject), \
             patch("app.services.sales.contract_service.ProjectPaymentPlan", FakePaymentPlan), \
             patch("app.services.sales.contract_service.ProjectMilestone", FakeMilestone), \
             patch("app.services.sales.contract_service.ProjectService.generate_code", AsyncMock(return_value="PRJ-001")):
            result = await ContractService.create_project_from_contract(db, 10)

        assert result == {
            "success": True,
            "message": "项目创建成功，付款节点已关联到里程碑",
            "project_id": 100,
            "payment_plans_count": 2,
            "milestones_count": 2,
        }
        project = db._added[0]
        payment_plan1 = db._added[1]
        milestone1 = db._added[2]
        payment_plan2 = db._added[3]
        milestone2 = db._added[4]
        assert project.code == "PRJ-001"
        assert project.name == "HT-10-客户B"
        assert project.amount == 500000
        assert project.stage == "S1"
        assert payment_plan1.amount == 150000
        assert payment_plan1.milestone_id == milestone1.id
        assert payment_plan2.amount == 350000
        assert payment_plan2.milestone_id == milestone2.id
        assert milestone1.name == "M2"
        assert milestone2.name == "M3"
        db.commit.assert_awaited_once()
        db.rollback.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_project_from_contract_success_without_payment_nodes(self):
        db = self._make_db()
        customer = SimpleNamespace(id=6, name="客户C")
        contract = SimpleNamespace(
            id=11,
            contract_code="HT-11",
            contract_amount=100000,
            status="EXECUTING",
            project_id=None,
            payment_nodes=None,
            sow_text=None,
            acceptance_criteria=None,
        )
        db.execute.return_value = FakeResult((contract, customer))

        with patch("app.services.sales.contract_service.select", return_value=DummySelect()), \
             patch("app.services.sales.contract_service.selectinload", return_value=None), \
             patch("app.services.sales.contract_service.safe_json_loads", return_value=[]), \
             patch("app.services.sales.contract_service.Project", FakeProject), \
             patch("app.services.sales.contract_service.ProjectPaymentPlan", FakePaymentPlan), \
             patch("app.services.sales.contract_service.ProjectMilestone", FakeMilestone), \
             patch("app.services.sales.contract_service.ProjectService.generate_code", AsyncMock(return_value="PRJ-002")):
            result = await ContractService.create_project_from_contract(db, 11)

        assert result["success"] is True
        assert result["payment_plans_count"] == 0
        assert result["milestones_count"] == 0
        assert len(db._added) == 1
        assert db._added[0].sow_text == ""
        assert db._added[0].acceptance_criteria == []

    @pytest.mark.asyncio
    async def test_create_project_from_contract_rolls_back_on_error(self):
        db = self._make_db()
        customer = SimpleNamespace(id=7, name="客户D")
        contract = SimpleNamespace(
            id=12,
            contract_code="HT-12",
            contract_amount=200000,
            status="signed",
            project_id=None,
            payment_nodes="json",
            sow_text="SOW",
            acceptance_criteria=[],
        )
        db.execute.return_value = FakeResult((contract, customer))
        db.add.side_effect = RuntimeError("db boom")

        with patch("app.services.sales.contract_service.select", return_value=DummySelect()), \
             patch("app.services.sales.contract_service.selectinload", return_value=None), \
             patch("app.services.sales.contract_service.safe_json_loads", return_value=[]), \
             patch("app.services.sales.contract_service.Project", FakeProject), \
             patch("app.services.sales.contract_service.ProjectService.generate_code", AsyncMock(return_value="PRJ-003")):
            with pytest.raises(ValueError, match="创建项目失败: db boom"):
                await ContractService.create_project_from_contract(db, 12)

        db.rollback.assert_awaited_once()
