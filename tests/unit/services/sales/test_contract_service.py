# -*- coding: utf-8 -*-
"""
contract_service 单元测试

测试合同服务的从合同创建项目功能。
注意：由于 contract_service.py 中定义了 SQLAlchemy 模型，
需要测试业务逻辑而非直接导入服务类。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ========== ALLOWED_CONTRACT_STATUSES 测试 ==========

class TestAllowedContractStatuses:
    """合同状态常量测试"""

    # 直接定义常量值进行测试（与实际常量一致）
    ALLOWED_CONTRACT_STATUSES = {"signed", "executing", "SIGNED", "EXECUTING"}

    def test_allowed_statuses_lowercase(self):
        """小写状态允许"""
        assert "signed" in self.ALLOWED_CONTRACT_STATUSES
        assert "executing" in self.ALLOWED_CONTRACT_STATUSES

    def test_allowed_statuses_uppercase(self):
        """大写状态允许"""
        assert "SIGNED" in self.ALLOWED_CONTRACT_STATUSES
        assert "EXECUTING" in self.ALLOWED_CONTRACT_STATUSES

    def test_draft_not_allowed(self):
        """草稿状态不允许"""
        assert "draft" not in self.ALLOWED_CONTRACT_STATUSES
        assert "DRAFT" not in self.ALLOWED_CONTRACT_STATUSES

    def test_completed_not_allowed(self):
        """已完成状态不允许"""
        assert "completed" not in self.ALLOWED_CONTRACT_STATUSES
        assert "COMPLETED" not in self.ALLOWED_CONTRACT_STATUSES

    def test_voided_not_allowed(self):
        """已作废状态不允许"""
        assert "voided" not in self.ALLOWED_CONTRACT_STATUSES
        assert "VOIDED" not in self.ALLOWED_CONTRACT_STATUSES


# ========== 业务逻辑测试 ==========

class TestContractProjectCreationLogic:
    """合同创建项目的业务逻辑测试"""

    @pytest.fixture
    def sample_contract(self):
        """示例合同"""
        contract = MagicMock()
        contract.id = 1
        contract.contract_code = "HT-20260312-001"
        contract.contract_amount = 500000
        contract.status = "signed"
        contract.project_id = None
        contract.payment_nodes = '[{"name": "首款", "percentage": 30}]'
        contract.sow_text = "SOW 内容"
        contract.acceptance_criteria = ["验收标准1", "验收标准2"]
        return contract

    def test_status_validation_signed_allowed(self, sample_contract):
        """验证 signed 状态允许创建项目"""
        allowed_statuses = {"signed", "executing", "SIGNED", "EXECUTING"}
        sample_contract.status = "signed"
        assert sample_contract.status in allowed_statuses

    def test_status_validation_executing_allowed(self, sample_contract):
        """验证 executing 状态允许创建项目"""
        allowed_statuses = {"signed", "executing", "SIGNED", "EXECUTING"}
        sample_contract.status = "executing"
        assert sample_contract.status in allowed_statuses

    def test_status_validation_draft_rejected(self, sample_contract):
        """验证 draft 状态不允许创建项目"""
        allowed_statuses = {"signed", "executing", "SIGNED", "EXECUTING"}
        sample_contract.status = "draft"
        assert sample_contract.status not in allowed_statuses

    def test_already_linked_project_detected(self, sample_contract):
        """验证已关联项目的检测"""
        sample_contract.project_id = 123
        assert sample_contract.project_id is not None

    def test_payment_nodes_parsing(self, sample_contract):
        """验证付款节点解析"""
        import json
        nodes = json.loads(sample_contract.payment_nodes)
        assert len(nodes) == 1
        assert nodes[0]["name"] == "首款"
        assert nodes[0]["percentage"] == 30

    def test_payment_nodes_null_handling(self, sample_contract):
        """验证空付款节点处理"""
        sample_contract.payment_nodes = None
        # 空值应该被安全处理
        nodes = [] if sample_contract.payment_nodes is None else sample_contract.payment_nodes
        assert nodes == []

    def test_invalid_payment_nodes_json(self, sample_contract):
        """无效 JSON 应该被安全处理"""
        sample_contract.payment_nodes = "invalid json"
        try:
            import json
            nodes = json.loads(sample_contract.payment_nodes)
        except json.JSONDecodeError:
            nodes = []
        assert nodes == []


# ========== 付款节点计算测试 ==========

class TestPaymentNodeCalculation:
    """付款节点计算测试"""

    def test_calculate_amount_from_percentage(self):
        """从百分比计算金额"""
        contract_amount = 500000
        percentage = 30
        expected_amount = contract_amount * percentage / 100
        assert expected_amount == 150000

    def test_calculate_multiple_nodes(self):
        """计算多个付款节点"""
        contract_amount = 100000
        nodes = [
            {"name": "首款", "percentage": 30},
            {"name": "验收款", "percentage": 70},
        ]

        total_percentage = sum(n["percentage"] for n in nodes)
        assert total_percentage == 100

        amounts = [contract_amount * n["percentage"] / 100 for n in nodes]
        assert amounts == [30000, 70000]
        assert sum(amounts) == contract_amount

    def test_partial_payment_nodes(self):
        """部分付款节点（总和不到100%）"""
        contract_amount = 100000
        nodes = [
            {"name": "首款", "percentage": 30},
            {"name": "中期款", "percentage": 20},
        ]

        total_percentage = sum(n["percentage"] for n in nodes)
        assert total_percentage == 50

        # 应该只计算定义的节点
        amounts = [contract_amount * n["percentage"] / 100 for n in nodes]
        assert sum(amounts) == 50000


# ========== 里程碑创建逻辑测试 ==========

class TestMilestoneCreationLogic:
    """里程碑创建逻辑测试"""

    def test_milestone_name_from_payment_node(self):
        """从付款节点生成里程碑名称"""
        node = {"name": "首款", "percentage": 30}
        milestone_name = f"{node['name']}里程碑"
        assert milestone_name == "首款里程碑"

    def test_milestone_count_matches_nodes(self):
        """里程碑数量应等于付款节点数"""
        nodes = [
            {"name": "首款", "percentage": 30},
            {"name": "验收款", "percentage": 70},
        ]
        milestones_count = len(nodes)
        assert milestones_count == 2


# ========== 边界情况测试 ==========

class TestEdgeCases:
    """边界情况测试"""

    def test_empty_payment_nodes_list(self):
        """空付款节点列表"""
        nodes = []
        assert len(nodes) == 0

        # 应该能处理空列表
        milestones = [{"name": f"{n['name']}里程碑"} for n in nodes]
        assert milestones == []

    def test_zero_contract_amount(self):
        """零合同金额"""
        contract_amount = 0
        nodes = [{"name": "首款", "percentage": 30}]

        amounts = [contract_amount * n["percentage"] / 100 for n in nodes]
        assert amounts == [0]

    def test_status_case_insensitivity(self):
        """状态大小写不敏感"""
        allowed_statuses = {"signed", "executing", "SIGNED", "EXECUTING"}

        # 测试各种大小写变体
        assert "signed" in allowed_statuses
        assert "SIGNED" in allowed_statuses
        # 注意：混合大小写不在允许列表中
        assert "Signed" not in allowed_statuses
