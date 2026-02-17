# -*- coding: utf-8 -*-
"""
ContractEnhancedService 单元测试 - G2组覆盖率提升

覆盖:
- ContractEnhancedService.create_contract
- ContractEnhancedService._generate_contract_code
- ContractEnhancedService.get_contract
- ContractEnhancedService.get_contracts (筛选)
- ContractEnhancedService.update_contract (成功 & 非草稿拒绝)
- ContractEnhancedService.delete_contract
- ContractEnhancedService.submit_for_approval
- ContractEnhancedService._create_approval_flow (金额分级)
"""

from decimal import Decimal
from datetime import datetime
from unittest.mock import MagicMock, patch, call

import pytest


class TestCreateContract:
    """测试 create_contract"""

    def test_creates_contract_in_draft_status(self):
        from app.services.sales.contract_enhanced import ContractEnhancedService

        db = MagicMock()
        db.flush = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        contract_data = MagicMock()
        contract_data.contract_code = "HT-20260217-001"
        contract_data.total_amount = Decimal("100000")
        contract_data.received_amount = Decimal("20000")
        contract_data.terms = []
        contract_data.model_dump.return_value = {
            "contract_code": "HT-20260217-001",
            "total_amount": Decimal("100000"),
            "received_amount": Decimal("20000"),
        }

        result = ContractEnhancedService.create_contract(db, contract_data, user_id=1)

        # Should call db.add and commit
        db.add.assert_called()
        db.commit.assert_called_once()

    def test_auto_generates_contract_code_when_missing(self):
        from app.services.sales.contract_enhanced import ContractEnhancedService

        db = MagicMock()
        db.flush = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        contract_data = MagicMock()
        contract_data.contract_code = None
        contract_data.total_amount = Decimal("50000")
        contract_data.received_amount = Decimal("0")
        contract_data.terms = []
        contract_data.model_dump.return_value = {
            "contract_code": None,
            "total_amount": Decimal("50000"),
            "received_amount": Decimal("0"),
        }

        # Mock _generate_contract_code
        with patch.object(
            ContractEnhancedService, "_generate_contract_code", return_value="HT-20260217-001"
        ):
            ContractEnhancedService.create_contract(db, contract_data, user_id=1)

        # code should be set
        assert contract_data.contract_code == "HT-20260217-001"

    def test_creates_terms_when_provided(self):
        from app.services.sales.contract_enhanced import ContractEnhancedService

        db = MagicMock()
        db.flush = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        term1 = MagicMock()
        term1.model_dump.return_value = {"term_content": "条款1"}

        contract_data = MagicMock()
        contract_data.contract_code = "HT-001"
        contract_data.total_amount = Decimal("100000")
        contract_data.received_amount = Decimal("0")
        contract_data.terms = [term1]
        contract_data.model_dump.return_value = {
            "contract_code": "HT-001",
            "total_amount": Decimal("100000"),
            "received_amount": Decimal("0"),
        }

        ContractEnhancedService.create_contract(db, contract_data, user_id=1)
        # db.add should be called at least twice (contract + term)
        assert db.add.call_count >= 2


class TestGenerateContractCode:
    """测试 _generate_contract_code"""

    def test_generates_first_code_when_no_prior(self):
        from app.services.sales.contract_enhanced import ContractEnhancedService

        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        code = ContractEnhancedService._generate_contract_code(db)

        today = datetime.now().strftime("%Y%m%d")
        assert code == f"HT-{today}-001"

    def test_increments_from_last_code(self):
        from app.services.sales.contract_enhanced import ContractEnhancedService

        db = MagicMock()
        last = MagicMock()
        last.contract_code = "HT-20260217-005"
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = last

        code = ContractEnhancedService._generate_contract_code(db)
        # Should produce 006
        assert code.endswith("006")


class TestGetContract:
    """测试 get_contract"""

    def test_returns_contract_when_found(self):
        from app.services.sales.contract_enhanced import ContractEnhancedService

        db = MagicMock()
        mock_contract = MagicMock()
        (db.query.return_value
           .options.return_value
           .filter.return_value
           .first.return_value) = mock_contract

        result = ContractEnhancedService.get_contract(db, 1)
        assert result == mock_contract

    def test_returns_none_when_not_found(self):
        from app.services.sales.contract_enhanced import ContractEnhancedService

        db = MagicMock()
        (db.query.return_value
           .options.return_value
           .filter.return_value
           .first.return_value) = None

        result = ContractEnhancedService.get_contract(db, 999)
        assert result is None


class TestGetContracts:
    """测试 get_contracts"""

    def test_returns_list_and_total(self):
        from app.services.sales.contract_enhanced import ContractEnhancedService

        db = MagicMock()
        mock_contracts = [MagicMock(), MagicMock()]
        # Simulate query chain
        q = MagicMock()
        q.count.return_value = 2
        q.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_contracts
        # Also need filter to return chainable mock
        q.filter.return_value = q
        db.query.return_value = q

        contracts, total = ContractEnhancedService.get_contracts(db)
        assert total == 2
        assert len(contracts) == 2

    def test_filters_by_status(self):
        from app.services.sales.contract_enhanced import ContractEnhancedService

        db = MagicMock()
        q = MagicMock()
        q.count.return_value = 0
        q.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        q.filter.return_value = q
        db.query.return_value = q

        contracts, total = ContractEnhancedService.get_contracts(db, status="draft")
        q.filter.assert_called()


class TestUpdateContract:
    """测试 update_contract"""

    def test_raises_when_not_draft(self):
        from app.services.sales.contract_enhanced import ContractEnhancedService

        db = MagicMock()
        mock_contract = MagicMock()
        mock_contract.status = "approving"
        db.query.return_value.filter.return_value.first.return_value = mock_contract

        contract_data = MagicMock()
        contract_data.model_dump.return_value = {}
        contract_data.total_amount = None
        contract_data.received_amount = None

        with pytest.raises(ValueError, match="只能更新草稿状态"):
            ContractEnhancedService.update_contract(db, 1, contract_data)

    def test_returns_none_when_not_found(self):
        from app.services.sales.contract_enhanced import ContractEnhancedService

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = ContractEnhancedService.update_contract(db, 999, MagicMock())
        assert result is None

    def test_updates_fields_on_draft_contract(self):
        from app.services.sales.contract_enhanced import ContractEnhancedService

        db = MagicMock()
        mock_contract = MagicMock()
        mock_contract.status = "draft"
        mock_contract.total_amount = Decimal("100000")
        mock_contract.received_amount = Decimal("0")
        db.query.return_value.filter.return_value.first.return_value = mock_contract

        contract_data = MagicMock()
        contract_data.model_dump.return_value = {"contract_name": "新合同名称"}
        contract_data.total_amount = None
        contract_data.received_amount = None

        result = ContractEnhancedService.update_contract(db, 1, contract_data)
        assert mock_contract.contract_name == "新合同名称"
        db.commit.assert_called_once()


class TestDeleteContract:
    """测试 delete_contract"""

    def test_returns_false_when_not_found(self):
        from app.services.sales.contract_enhanced import ContractEnhancedService

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = ContractEnhancedService.delete_contract(db, 999)
        assert result is False

    def test_raises_when_not_draft(self):
        from app.services.sales.contract_enhanced import ContractEnhancedService

        db = MagicMock()
        mock_contract = MagicMock()
        mock_contract.status = "approved"
        db.query.return_value.filter.return_value.first.return_value = mock_contract

        with pytest.raises(ValueError, match="只能删除草稿状态"):
            ContractEnhancedService.delete_contract(db, 1)

    @patch("app.services.sales.contract_enhanced.delete_obj")
    def test_deletes_draft_contract(self, mock_delete):
        from app.services.sales.contract_enhanced import ContractEnhancedService

        db = MagicMock()
        mock_contract = MagicMock()
        mock_contract.status = "draft"
        db.query.return_value.filter.return_value.first.return_value = mock_contract

        result = ContractEnhancedService.delete_contract(db, 1)
        assert result is True
        mock_delete.assert_called_once_with(db, mock_contract)


class TestCreateApprovalFlow:
    """测试 _create_approval_flow 金额分级逻辑"""

    def test_small_amount_one_approver(self):
        from app.services.sales.contract_enhanced import ContractEnhancedService

        db = MagicMock()
        approvals = ContractEnhancedService._create_approval_flow(
            db, contract_id=1, amount=Decimal("50000")
        )
        # < 100000: sales_manager only
        assert len(approvals) == 1
        assert approvals[0].approval_role == "sales_manager"

    def test_medium_amount_one_approver(self):
        from app.services.sales.contract_enhanced import ContractEnhancedService

        db = MagicMock()
        approvals = ContractEnhancedService._create_approval_flow(
            db, contract_id=1, amount=Decimal("200000")
        )
        # 100000-500000: sales_director
        assert len(approvals) == 1
        assert approvals[0].approval_role == "sales_director"

    def test_large_amount_three_approvers(self):
        from app.services.sales.contract_enhanced import ContractEnhancedService

        db = MagicMock()
        approvals = ContractEnhancedService._create_approval_flow(
            db, contract_id=1, amount=Decimal("1000000")
        )
        # > 500000: sales_director + finance_director + general_manager
        assert len(approvals) == 3
        roles = {a.approval_role for a in approvals}
        assert "sales_director" in roles
        assert "finance_director" in roles
        assert "general_manager" in roles


class TestSubmitForApproval:
    """测试 submit_for_approval"""

    def test_raises_when_contract_not_found(self):
        from app.services.sales.contract_enhanced import ContractEnhancedService

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="合同不存在"):
            ContractEnhancedService.submit_for_approval(db, 999, user_id=1)

    def test_raises_when_not_draft(self):
        from app.services.sales.contract_enhanced import ContractEnhancedService

        db = MagicMock()
        mock_contract = MagicMock()
        mock_contract.status = "approving"
        db.query.return_value.filter.return_value.first.return_value = mock_contract

        with pytest.raises(ValueError, match="只能提交草稿状态"):
            ContractEnhancedService.submit_for_approval(db, 1, user_id=1)

    def test_sets_status_approving_when_approvals_exist(self):
        from app.services.sales.contract_enhanced import ContractEnhancedService

        db = MagicMock()
        mock_contract = MagicMock()
        mock_contract.status = "draft"
        mock_contract.total_amount = Decimal("200000")
        db.query.return_value.filter.return_value.first.return_value = mock_contract

        with patch.object(
            ContractEnhancedService,
            "_create_approval_flow",
            return_value=[MagicMock()],
        ):
            ContractEnhancedService.submit_for_approval(db, 1, user_id=1)

        assert mock_contract.status == "approving"
        db.commit.assert_called_once()
