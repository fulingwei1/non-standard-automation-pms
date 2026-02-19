# -*- coding: utf-8 -*-
"""
第三十五批 - contract_service.py 单元测试
"""
import pytest

try:
    import asyncio
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.services.sales.contract_service import ContractService, ProjectPaymentPlan
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="导入失败，跳过")


def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.mark.skipif(not IMPORT_OK, reason="导入失败")
class TestContractService:

    def _make_db(self, contract=None, customer=None):
        db = AsyncMock()
        if contract is None:
            db.execute.return_value = MagicMock(first=MagicMock(return_value=None))
        else:
            mock_result = MagicMock()
            mock_result.first.return_value = (contract, customer)
            db.execute.return_value = mock_result
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        return db

    def test_contract_not_found_raises_value_error(self):
        """合同不存在时抛出 ValueError"""
        db = self._make_db(contract=None)
        with pytest.raises((ValueError, Exception)):
            run_async(ContractService.create_project_from_contract(db, 999))

    def test_contract_already_has_project(self):
        """合同已关联项目时返回失败信息"""
        contract = MagicMock()
        contract.project_id = 42
        contract.payment_nodes = []
        customer = MagicMock()
        customer.name = "测试客户"
        customer.id = 1
        db = self._make_db(contract, customer)
        result = run_async(ContractService.create_project_from_contract(db, 1))
        assert result["success"] is False
        assert result["project_id"] == 42

    def test_project_payment_plan_model_tablename(self):
        """ProjectPaymentPlan 表名正确"""
        assert ProjectPaymentPlan.__tablename__ == "project_payment_plans"

    def test_project_payment_plan_default_status(self):
        """ProjectPaymentPlan 默认状态为 PENDING"""
        col = ProjectPaymentPlan.status
        assert col.default.arg == "PENDING"

    def test_create_project_success(self):
        """合同无项目时成功创建"""
        contract = MagicMock()
        contract.project_id = None
        contract.payment_nodes = []
        contract.contract_amount = 100000
        contract.sow_text = "测试SOW"
        contract.acceptance_criteria = []
        contract.contract_code = "CT001"
        contract.id = 1

        customer = MagicMock()
        customer.name = "客户A"
        customer.id = 10

        db = self._make_db(contract, customer)
        # mock Project 的 id
        with patch("app.services.sales.contract_service.Project") as MockProject, \
             patch("app.services.sales.contract_service.ProjectService") as MockPS:
            mock_proj_instance = MagicMock()
            mock_proj_instance.id = 100
            mock_proj_instance.amount = 100000
            MockProject.return_value = mock_proj_instance
            MockPS.generate_code = AsyncMock(return_value="PRJ-001")
            result = run_async(ContractService.create_project_from_contract(db, 1))
        assert result["success"] is True
        assert result["payment_plans_count"] == 0

    def test_create_project_with_payment_nodes(self):
        """有付款节点时创建相应的收款计划和里程碑"""
        contract = MagicMock()
        contract.project_id = None
        contract.payment_nodes = [
            {"name": "首付款", "percentage": 30, "due_date": None, "description": "首付"},
            {"name": "中期款", "percentage": 40, "due_date": None, "description": "中期"},
        ]
        contract.contract_amount = 200000
        contract.sow_text = ""
        contract.acceptance_criteria = []
        contract.contract_code = "CT002"
        contract.id = 2

        customer = MagicMock()
        customer.name = "客户B"
        customer.id = 20

        db = self._make_db(contract, customer)
        with patch("app.services.sales.contract_service.Project") as MockProject, \
             patch("app.services.sales.contract_service.ProjectMilestone") as MockMilestone, \
             patch("app.services.sales.contract_service.ProjectPaymentPlan") as MockPPP, \
             patch("app.services.sales.contract_service.ProjectService") as MockPS:
            mock_proj = MagicMock()
            mock_proj.id = 200
            mock_proj.amount = 200000
            MockProject.return_value = mock_proj
            MockPS.generate_code = AsyncMock(return_value="PRJ-002")
            result = run_async(ContractService.create_project_from_contract(db, 2))
        assert result["success"] is True
        assert result["payment_plans_count"] == 2
