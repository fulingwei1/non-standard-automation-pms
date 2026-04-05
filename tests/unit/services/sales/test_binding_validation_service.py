# -*- coding: utf-8 -*-
"""
绑定验证服务测试
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.sales.binding_validation_service import (
    BindingIssueCode,
    BindingIssueLevel,
    BindingValidationService,
)


class TestBindingValidationService:
    """BindingValidationService 测试"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = MagicMock()
        db.commit = MagicMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """创建服务实例"""
        return BindingValidationService(mock_db)

    # ========== 绑定验证测试 ==========
    @pytest.mark.asyncio
    async def test_validate_missing_solution_binding(self, service, mock_db):
        """测试缺少方案绑定"""
        # 模拟报价版本
        mock_qv = MagicMock()
        mock_qv.id = 1
        mock_qv.solution_version_id = None
        mock_qv.cost_estimation_id = 1
        mock_qv.cost_estimation = MagicMock(
            status="approved",
            solution_version_id=1,
            total_cost=Decimal("10000"),
        )
        mock_qv.cost_total = Decimal("10000")

        mock_db.query.return_value.get.return_value = mock_qv

        result = await service.validate_quote_binding(1)

        assert result.status == "invalid"
        assert any(i.code == BindingIssueCode.SOLUTION_NOT_BOUND for i in result.issues)

    @pytest.mark.asyncio
    async def test_validate_missing_cost_binding(self, service, mock_db):
        """测试缺少成本绑定"""
        mock_sv = MagicMock()
        mock_sv.id = 1
        mock_sv.status = "approved"

        mock_qv = MagicMock()
        mock_qv.id = 1
        mock_qv.solution_version_id = 1
        mock_qv.solution_version = mock_sv
        mock_qv.cost_estimation_id = None
        mock_qv.cost_estimation = None

        mock_db.query.return_value.get.return_value = mock_qv
        service._get_latest_approved_solution_version = MagicMock(return_value=mock_sv)

        result = await service.validate_quote_binding(1)

        assert result.status == "invalid"
        assert any(i.code == BindingIssueCode.COST_NOT_BOUND for i in result.issues)

    @pytest.mark.asyncio
    async def test_validate_solution_not_approved(self, service, mock_db):
        """测试方案未审批"""
        mock_sv = MagicMock()
        mock_sv.id = 1
        mock_sv.version_no = "V1.0"
        mock_sv.status = "draft"
        mock_sv.solution_id = 1

        mock_ce = MagicMock()
        mock_ce.id = 1
        mock_ce.status = "approved"
        mock_ce.solution_version_id = 1
        mock_ce.total_cost = Decimal("10000")

        mock_qv = MagicMock()
        mock_qv.id = 1
        mock_qv.solution_version_id = 1
        mock_qv.solution_version = mock_sv
        mock_qv.cost_estimation_id = 1
        mock_qv.cost_estimation = mock_ce
        mock_qv.cost_total = Decimal("10000")

        mock_db.query.return_value.get.return_value = mock_qv
        service._get_latest_approved_solution_version = MagicMock(return_value=None)

        result = await service.validate_quote_binding(1)

        # 应该是 outdated（有警告但无错误）
        assert result.status == "outdated"
        assert any(i.code == BindingIssueCode.SOLUTION_NOT_APPROVED for i in result.issues)

    @pytest.mark.asyncio
    async def test_validate_cost_solution_mismatch(self, service, mock_db):
        """测试成本与方案版本不匹配"""
        mock_sv = MagicMock()
        mock_sv.id = 1
        mock_sv.version_no = "V1.0"
        mock_sv.status = "approved"
        mock_sv.solution_id = 1

        mock_ce = MagicMock()
        mock_ce.id = 1
        mock_ce.status = "approved"
        mock_ce.solution_version_id = 2  # 不匹配
        mock_ce.total_cost = Decimal("10000")

        mock_qv = MagicMock()
        mock_qv.id = 1
        mock_qv.solution_version_id = 1
        mock_qv.solution_version = mock_sv
        mock_qv.cost_estimation_id = 1
        mock_qv.cost_estimation = mock_ce
        mock_qv.cost_total = Decimal("10000")

        mock_db.query.return_value.get.return_value = mock_qv
        service._get_latest_approved_solution_version = MagicMock(return_value=mock_sv)

        result = await service.validate_quote_binding(1)

        assert result.status == "invalid"
        assert any(i.code == BindingIssueCode.COST_SOLUTION_MISMATCH for i in result.issues)

    @pytest.mark.asyncio
    async def test_validate_cost_amount_mismatch(self, service, mock_db):
        """测试成本金额不一致"""
        mock_sv = MagicMock()
        mock_sv.id = 1
        mock_sv.version_no = "V1.0"
        mock_sv.status = "approved"
        mock_sv.solution_id = 1

        mock_ce = MagicMock()
        mock_ce.id = 1
        mock_ce.status = "approved"
        mock_ce.solution_version_id = 1
        mock_ce.total_cost = Decimal("10000")

        mock_qv = MagicMock()
        mock_qv.id = 1
        mock_qv.solution_version_id = 1
        mock_qv.solution_version = mock_sv
        mock_qv.cost_estimation_id = 1
        mock_qv.cost_estimation = mock_ce
        mock_qv.cost_total = Decimal("12000")  # 不一致

        mock_db.query.return_value.get.return_value = mock_qv
        service._get_latest_approved_solution_version = MagicMock(return_value=mock_sv)

        result = await service.validate_quote_binding(1)

        assert result.status == "invalid"
        assert any(i.code == BindingIssueCode.COST_AMOUNT_MISMATCH for i in result.issues)

    @pytest.mark.asyncio
    async def test_validate_valid_binding(self, service, mock_db):
        """测试完整有效绑定"""
        mock_sv = MagicMock()
        mock_sv.id = 1
        mock_sv.version_no = "V1.0"
        mock_sv.status = "approved"
        mock_sv.solution_id = 1

        mock_ce = MagicMock()
        mock_ce.id = 1
        mock_ce.status = "approved"
        mock_ce.solution_version_id = 1
        mock_ce.total_cost = Decimal("10000")

        mock_qv = MagicMock()
        mock_qv.id = 1
        mock_qv.solution_version_id = 1
        mock_qv.solution_version = mock_sv
        mock_qv.cost_estimation_id = 1
        mock_qv.cost_estimation = mock_ce
        mock_qv.cost_total = Decimal("10000")

        mock_db.query.return_value.get.return_value = mock_qv
        service._get_latest_approved_solution_version = MagicMock(return_value=mock_sv)

        result = await service.validate_quote_binding(1)

        assert result.status == "valid"
        assert len(result.issues) == 0
        assert result.is_valid is True


class TestBindingIssueLevel:
    """绑定问题级别测试"""

    def test_error_level(self):
        """ERROR 级别存在"""
        assert BindingIssueLevel.ERROR == "error"

    def test_warning_level(self):
        """WARNING 级别存在"""
        assert BindingIssueLevel.WARNING == "warning"

    def test_info_level(self):
        """INFO 级别存在"""
        assert BindingIssueLevel.INFO == "info"


class TestBindingIssueCode:
    """绑定问题代码测试"""

    def test_all_codes_exist(self):
        """所有问题代码都存在"""
        expected_codes = [
            "SOLUTION_NOT_BOUND",
            "SOLUTION_NOT_APPROVED",
            "SOLUTION_VERSION_OUTDATED",
            "COST_NOT_BOUND",
            "COST_NOT_APPROVED",
            "COST_SOLUTION_MISMATCH",
            "COST_AMOUNT_MISMATCH",
            "QUOTE_BINDING_INCOMPLETE",
        ]
        for code in expected_codes:
            assert hasattr(BindingIssueCode, code)
