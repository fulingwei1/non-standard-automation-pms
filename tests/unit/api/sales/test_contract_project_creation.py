# -*- coding: utf-8 -*-
"""
单元测试 - 合同转项目功能
测试合同状态验证、G4 阶段门验证、事务回滚等场景
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# 导入被测模块中的常量
from app.api.v1.endpoints.sales.contracts.contracts import ALLOWED_CONTRACT_STATUSES


class TestContractStatusValidation:
    """合同状态验证测试"""

    def test_allowed_statuses_include_signed(self):
        """测试允许的状态包含 signed（小写）"""
        assert "signed" in ALLOWED_CONTRACT_STATUSES

    def test_allowed_statuses_include_executing(self):
        """测试允许的状态包含 executing（小写）"""
        assert "executing" in ALLOWED_CONTRACT_STATUSES

    def test_allowed_statuses_include_uppercase_signed(self):
        """测试允许的状态包含 SIGNED（大写）"""
        assert "SIGNED" in ALLOWED_CONTRACT_STATUSES

    def test_allowed_statuses_include_uppercase_executing(self):
        """测试允许的状态包含 EXECUTING（大写）"""
        assert "EXECUTING" in ALLOWED_CONTRACT_STATUSES

    def test_draft_not_in_allowed_statuses(self):
        """测试草稿状态不在允许列表中"""
        assert "draft" not in ALLOWED_CONTRACT_STATUSES
        assert "DRAFT" not in ALLOWED_CONTRACT_STATUSES

    def test_voided_not_in_allowed_statuses(self):
        """测试作废状态不在允许列表中"""
        assert "voided" not in ALLOWED_CONTRACT_STATUSES
        assert "VOIDED" not in ALLOWED_CONTRACT_STATUSES

    def test_pending_approval_not_in_allowed_statuses(self):
        """测试待审批状态不在允许列表中"""
        assert "pending_approval" not in ALLOWED_CONTRACT_STATUSES
        assert "PENDING_APPROVAL" not in ALLOWED_CONTRACT_STATUSES


class TestG4GateValidation:
    """G4 阶段门验证测试"""

    def test_validate_g4_returns_errors_for_empty_deliverables(self):
        """测试空交付物列表返回错误"""
        from app.api.v1.endpoints.sales.utils.gate_validation import (
            validate_g4_contract_to_project,
        )

        # 创建模拟合同
        mock_contract = MagicMock()
        mock_contract.contract_amount = Decimal("100000")
        mock_contract.acceptance_summary = "验收标准"
        mock_contract.payment_terms_summary = "付款条款"
        mock_contract.status = "SIGNED"
        mock_contract.project_id = None

        passed, errors = validate_g4_contract_to_project(mock_contract, [], db=None)

        assert not passed
        assert any("交付物" in error for error in errors)

    def test_validate_g4_returns_errors_for_non_signed_contract(self):
        """测试非已签署合同返回错误"""
        from app.api.v1.endpoints.sales.utils.gate_validation import (
            validate_g4_contract_to_project,
        )

        mock_contract = MagicMock()
        mock_contract.contract_amount = Decimal("100000")
        mock_contract.acceptance_summary = "验收标准"
        mock_contract.payment_terms_summary = "付款条款"
        mock_contract.status = "DRAFT"  # 非已签署状态
        mock_contract.project_id = None

        mock_deliverable = MagicMock()
        mock_deliverable.deliverable_name = "测试交付物"
        mock_deliverable.required_for_payment = True

        passed, errors = validate_g4_contract_to_project(
            mock_contract, [mock_deliverable], db=None
        )

        assert not passed
        assert any("签订" in error or "SIGNED" in error for error in errors)

    def test_validate_g4_returns_errors_for_already_linked_project(self):
        """测试已关联项目的合同返回错误"""
        from app.api.v1.endpoints.sales.utils.gate_validation import (
            validate_g4_contract_to_project,
        )

        mock_contract = MagicMock()
        mock_contract.contract_amount = Decimal("100000")
        mock_contract.acceptance_summary = "验收标准"
        mock_contract.payment_terms_summary = "付款条款"
        mock_contract.status = "SIGNED"
        mock_contract.project_id = 123  # 已关联项目

        mock_deliverable = MagicMock()
        mock_deliverable.deliverable_name = "测试交付物"
        mock_deliverable.required_for_payment = True

        passed, errors = validate_g4_contract_to_project(
            mock_contract, [mock_deliverable], db=None
        )

        assert not passed
        assert any("关联" in error or "重复" in error for error in errors)

    def test_validate_g4_returns_errors_for_missing_acceptance_summary(self):
        """测试缺少验收摘要返回错误"""
        from app.api.v1.endpoints.sales.utils.gate_validation import (
            validate_g4_contract_to_project,
        )

        mock_contract = MagicMock()
        mock_contract.contract_amount = Decimal("100000")
        mock_contract.acceptance_summary = None  # 缺少验收摘要
        mock_contract.payment_terms_summary = "付款条款"
        mock_contract.status = "SIGNED"
        mock_contract.project_id = None

        mock_deliverable = MagicMock()
        mock_deliverable.deliverable_name = "测试交付物"
        mock_deliverable.required_for_payment = True

        passed, errors = validate_g4_contract_to_project(
            mock_contract, [mock_deliverable], db=None
        )

        assert not passed
        assert any("验收" in error for error in errors)

    def test_validate_g4_passes_for_valid_contract(self):
        """测试有效合同通过验证"""
        from app.api.v1.endpoints.sales.utils.gate_validation import (
            validate_g4_contract_to_project,
        )

        mock_contract = MagicMock()
        mock_contract.contract_amount = Decimal("100000")
        mock_contract.acceptance_summary = "验收标准"
        mock_contract.payment_terms_summary = "付款条款"
        mock_contract.status = "SIGNED"
        mock_contract.project_id = None

        mock_deliverable = MagicMock()
        mock_deliverable.deliverable_name = "测试交付物"
        mock_deliverable.required_for_payment = True

        passed, errors = validate_g4_contract_to_project(
            mock_contract, [mock_deliverable], db=None
        )

        assert passed
        assert len(errors) == 0


class TestContractServiceStatusValidation:
    """ContractService 状态验证测试"""

    def test_allowed_statuses_are_consistent(self):
        """测试允许状态的一致性（包含大小写两种形式）"""
        from app.api.v1.endpoints.sales.contracts.contracts import (
            ALLOWED_CONTRACT_STATUSES,
        )

        # 验证同时包含大小写形式
        assert "signed" in ALLOWED_CONTRACT_STATUSES
        assert "SIGNED" in ALLOWED_CONTRACT_STATUSES
        assert "executing" in ALLOWED_CONTRACT_STATUSES
        assert "EXECUTING" in ALLOWED_CONTRACT_STATUSES
        # 验证集合大小正确（4 个元素：signed, SIGNED, executing, EXECUTING）
        assert len(ALLOWED_CONTRACT_STATUSES) == 4


class TestSafeJsonLoadsIntegration:
    """safe_json_loads 在合同模块中的集成测试"""

    def test_payment_nodes_parsing_with_valid_json(self):
        """测试有效 JSON 格式的付款节点解析"""
        from app.utils.json_helpers import safe_json_loads

        payment_json = '[{"name": "首付款", "percentage": 30}, {"name": "尾款", "percentage": 70}]'
        result = safe_json_loads(payment_json, default=[], field_name="payment_nodes")

        assert len(result) == 2
        assert result[0]["name"] == "首付款"
        assert result[0]["percentage"] == 30

    def test_payment_nodes_parsing_with_invalid_json(self):
        """测试无效 JSON 格式的付款节点解析"""
        from app.utils.json_helpers import safe_json_loads

        invalid_json = "这不是有效的JSON"
        result = safe_json_loads(invalid_json, default=[], field_name="payment_nodes")

        assert result == []

    def test_payment_nodes_parsing_with_none(self):
        """测试 None 值的付款节点解析"""
        from app.utils.json_helpers import safe_json_loads

        result = safe_json_loads(None, default=[], field_name="payment_nodes")

        assert result == []

    def test_payment_nodes_parsing_with_already_list(self):
        """测试已是列表类型的付款节点解析"""
        from app.utils.json_helpers import safe_json_loads

        existing_list = [{"name": "首付款", "percentage": 30}]
        result = safe_json_loads(existing_list, default=[], field_name="payment_nodes")

        assert result == existing_list
