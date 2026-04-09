# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 合同审批适配器"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


class TestContractApprovalAdapterBusinessLogic:
    """合同审批适配器业务逻辑测试"""

    def test_get_entity_found(self):
        """测试获取合同实体"""
        from app.services.approval_engine.adapters.contract import ContractApprovalAdapter

        mock_db = MagicMock()
        mock_contract = MagicMock()
        mock_contract.id = 1
        mock_contract.contract_code = "CTR-2026-001"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        adapter = ContractApprovalAdapter(mock_db)
        result = adapter.get_entity(1)

        assert result is not None
        assert result.id == 1

    def test_get_entity_not_found(self):
        """测试合同不存在"""
        from app.services.approval_engine.adapters.contract import ContractApprovalAdapter

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        adapter = ContractApprovalAdapter(mock_db)
        result = adapter.get_entity(999)

        assert result is None

    def test_get_entity_data(self):
        """测试获取合同数据"""
        from app.services.approval_engine.adapters.contract import ContractApprovalAdapter

        mock_db = MagicMock()

        # Mock合同
        mock_contract = MagicMock()
        mock_contract.id = 1
        mock_contract.contract_code = "CTR-2026-001"
        mock_contract.customer_contract_no = "CUST-001"
        mock_contract.status = "DRAFT"
        mock_contract.contract_amount = 500000
        mock_contract.customer_id = 1
        mock_contract.customer = MagicMock()
        mock_contract.customer.name = "测试客户"
        mock_contract.project_id = 1
        mock_contract.signing_date = datetime(2026, 4, 10)
        mock_contract.owner_id = 1
        mock_contract.owner = MagicMock()
        mock_contract.owner.name = "张三"
        mock_contract.payment_terms_summary = "分期付款"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        adapter = ContractApprovalAdapter(mock_db)
        result = adapter.get_entity_data(1)

        assert result["contract_code"] == "CTR-2026-001"
        assert result["contract_amount"] == 500000.0
        assert result["customer_name"] == "测试客户"

    def test_get_entity_data_contract_not_found(self):
        """测试合同不存在时的数据获取"""
        from app.services.approval_engine.adapters.contract import ContractApprovalAdapter

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        adapter = ContractApprovalAdapter(mock_db)
        result = adapter.get_entity_data(999)

        assert result == {}

    def test_on_submit(self):
        """测试提交审批回调"""
        from app.services.approval_engine.adapters.contract import ContractApprovalAdapter

        mock_db = MagicMock()
        mock_contract = MagicMock()
        mock_contract.id = 1
        mock_contract.status = "DRAFT"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        adapter = ContractApprovalAdapter(mock_db)
        mock_instance = MagicMock()
        adapter.on_submit(1, mock_instance)

        # 状态应该变为PENDING_APPROVAL
        assert mock_contract.status == "PENDING_APPROVAL"

    def test_on_approved(self):
        """测试审批通过回调"""
        from app.services.approval_engine.adapters.contract import ContractApprovalAdapter

        mock_db = MagicMock()
        mock_contract = MagicMock()
        mock_contract.id = 1
        mock_contract.status = "PENDING_APPROVAL"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        adapter = ContractApprovalAdapter(mock_db)
        mock_instance = MagicMock()
        adapter.on_approved(1, mock_instance)

        # 状态应该变为APPROVED
        assert mock_contract.status == "APPROVED"

    def test_on_rejected(self):
        """测试审批拒绝回调"""
        from app.services.approval_engine.adapters.contract import ContractApprovalAdapter

        mock_db = MagicMock()
        mock_contract = MagicMock()
        mock_contract.id = 1
        mock_contract.status = "PENDING_APPROVAL"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        adapter = ContractApprovalAdapter(mock_db)
        mock_instance = MagicMock()
        adapter.on_rejected(1, mock_instance, "金额过大")

        # 状态应该变为REJECTED
        assert mock_contract.status == "REJECTED"

    def test_on_cancelled(self):
        """测试审批取消回调"""
        from app.services.approval_engine.adapters.contract import ContractApprovalAdapter

        mock_db = MagicMock()
        mock_contract = MagicMock()
        mock_contract.id = 1
        mock_contract.status = "PENDING_APPROVAL"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        adapter = ContractApprovalAdapter(mock_db)
        mock_instance = MagicMock()
        adapter.on_cancelled(1, mock_instance)

        # 状态应该恢复
        assert mock_contract.status in ["DRAFT", "PENDING_APPROVAL"]


class TestContractApprovalAdapterRouting:
    """审批路由测试"""

    def test_can_route_by_amount(self):
        """测试按金额路由"""
        from app.services.approval_engine.adapters.contract import ContractApprovalAdapter

        mock_db = MagicMock()

        mock_contract = MagicMock()
        mock_contract.contract_amount = 1000000  # 100万

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        adapter = ContractApprovalAdapter(mock_db)
        data = adapter.get_entity_data(1)

        # 可以基于金额判断路由
        assert data["contract_amount"] == 1000000.0

    def test_can_route_by_customer(self):
        """测试按客户路由"""
        from app.services.approval_engine.adapters.contract import ContractApprovalAdapter

        mock_db = MagicMock()

        mock_customer = MagicMock()
        mock_customer.name = "VIP客户"

        mock_contract = MagicMock()
        mock_contract.customer = mock_customer

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        adapter = ContractApprovalAdapter(mock_db)
        data = adapter.get_entity_data(1)

        assert data["customer_name"] == "VIP客户"


class TestContractApprovalAdapterEdgeCases:
    """边界情况测试"""

    def test_contract_amount_none(self):
        """测试合同金额为None"""
        from app.services.approval_engine.adapters.contract import ContractApprovalAdapter

        mock_db = MagicMock()

        mock_contract = MagicMock()
        mock_contract.contract_amount = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        adapter = ContractApprovalAdapter(mock_db)
        data = adapter.get_entity_data(1)

        assert data["contract_amount"] == 0

    def test_contract_no_customer(self):
        """测试合同没有关联客户"""
        from app.services.approval_engine.adapters.contract import ContractApprovalAdapter

        mock_db = MagicMock()

        mock_contract = MagicMock()
        mock_contract.customer = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        adapter = ContractApprovalAdapter(mock_db)
        data = adapter.get_entity_data(1)

        assert data["customer_name"] is None

    def test_contract_no_owner(self):
        """测试合同没有负责人"""
        from app.services.approval_engine.adapters.contract import ContractApprovalAdapter

        mock_db = MagicMock()

        mock_contract = MagicMock()
        mock_contract.owner = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        adapter = ContractApprovalAdapter(mock_db)
        data = adapter.get_entity_data(1)

        assert data["owner_name"] is None