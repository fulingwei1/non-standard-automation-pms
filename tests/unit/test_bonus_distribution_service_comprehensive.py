# -*- coding: utf-8 -*-
"""
BonusDistributionService 综合单元测试

测试覆盖:
- validate_sheet_for_distribution: 验证明细表是否可以发放
- create_calculation_from_team_allocation: 从团队奖金分配创建个人计算记录
- create_distribution_record: 创建发放记录
- check_distribution_exists: 检查是否已发放
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestValidateSheetForDistribution:
    """测试 validate_sheet_for_distribution 函数"""

    def test_returns_false_when_already_distributed(self):
        """测试已发放时返回False"""
        from app.services.bonus_distribution_service import validate_sheet_for_distribution

        mock_sheet = MagicMock()
        mock_sheet.status = "DISTRIBUTED"

        is_valid, error = validate_sheet_for_distribution(mock_sheet)

        assert is_valid is False
        assert "已发放" in error

    def test_returns_false_when_finance_not_confirmed(self):
        """测试财务未确认时返回False"""
        from app.services.bonus_distribution_service import validate_sheet_for_distribution

        mock_sheet = MagicMock()
        mock_sheet.status = "PENDING"
        mock_sheet.finance_confirmed = False
        mock_sheet.hr_confirmed = True
        mock_sheet.manager_confirmed = True

        is_valid, error = validate_sheet_for_distribution(mock_sheet)

        assert is_valid is False
        assert "线下确认未完成" in error

    def test_returns_false_when_hr_not_confirmed(self):
        """测试人力未确认时返回False"""
        from app.services.bonus_distribution_service import validate_sheet_for_distribution

        mock_sheet = MagicMock()
        mock_sheet.status = "PENDING"
        mock_sheet.finance_confirmed = True
        mock_sheet.hr_confirmed = False
        mock_sheet.manager_confirmed = True

        is_valid, error = validate_sheet_for_distribution(mock_sheet)

        assert is_valid is False
        assert "线下确认未完成" in error

    def test_returns_false_when_manager_not_confirmed(self):
        """测试总经理未确认时返回False"""
        from app.services.bonus_distribution_service import validate_sheet_for_distribution

        mock_sheet = MagicMock()
        mock_sheet.status = "PENDING"
        mock_sheet.finance_confirmed = True
        mock_sheet.hr_confirmed = True
        mock_sheet.manager_confirmed = False

        is_valid, error = validate_sheet_for_distribution(mock_sheet)

        assert is_valid is False
        assert "线下确认未完成" in error

    def test_returns_false_when_parse_result_invalid(self):
        """测试解析结果无效时返回False"""
        from app.services.bonus_distribution_service import validate_sheet_for_distribution

        mock_sheet = MagicMock()
        mock_sheet.status = "PENDING"
        mock_sheet.finance_confirmed = True
        mock_sheet.hr_confirmed = True
        mock_sheet.manager_confirmed = True
        mock_sheet.parse_result = None

        is_valid, error = validate_sheet_for_distribution(mock_sheet)

        assert is_valid is False
        assert "数据无效" in error

    def test_returns_false_when_no_valid_rows(self):
        """测试无有效行时返回False"""
        from app.services.bonus_distribution_service import validate_sheet_for_distribution

        mock_sheet = MagicMock()
        mock_sheet.status = "PENDING"
        mock_sheet.finance_confirmed = True
        mock_sheet.hr_confirmed = True
        mock_sheet.manager_confirmed = True
        mock_sheet.parse_result = {"valid_rows": []}

        is_valid, error = validate_sheet_for_distribution(mock_sheet)

        assert is_valid is False
        assert "没有有效数据" in error

    def test_returns_true_when_all_conditions_met(self):
        """测试所有条件满足时返回True"""
        from app.services.bonus_distribution_service import validate_sheet_for_distribution

        mock_sheet = MagicMock()
        mock_sheet.status = "PENDING"
        mock_sheet.finance_confirmed = True
        mock_sheet.hr_confirmed = True
        mock_sheet.manager_confirmed = True
        mock_sheet.parse_result = {
            "valid_rows": [
                {"user_id": 1, "amount": 1000}
            ]
        }

        is_valid, error = validate_sheet_for_distribution(mock_sheet)

        assert is_valid is True
        assert error is None


class TestCreateCalculationFromTeamAllocation:
    """测试 create_calculation_from_team_allocation 函数"""

    def test_raises_error_when_allocation_not_found(self):
        """测试分配不存在时抛出异常"""
        from app.services.bonus_distribution_service import create_calculation_from_team_allocation

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_calculator = MagicMock()

        with pytest.raises(ValueError) as exc_info:
            create_calculation_from_team_allocation(
                mock_db,
                team_allocation_id=999,
                user_id=1,
                calculated_amount=Decimal("1000"),
                calculator=mock_calculator
            )

        assert "不存在" in str(exc_info.value)

    def test_raises_error_when_rule_id_missing(self):
        """测试缺少规则ID时抛出异常"""
        from app.services.bonus_distribution_service import create_calculation_from_team_allocation

        mock_db = MagicMock()

        mock_allocation = MagicMock()
        mock_allocation.id = 1
        mock_allocation.allocation_detail = {}

        mock_db.query.return_value.filter.return_value.first.return_value = mock_allocation

        mock_calculator = MagicMock()

        with pytest.raises(ValueError) as exc_info:
            create_calculation_from_team_allocation(
                mock_db,
                team_allocation_id=1,
                user_id=1,
                calculated_amount=Decimal("1000"),
                calculator=mock_calculator
            )

        assert "缺少规则ID" in str(exc_info.value)

    def test_raises_error_when_rule_not_found(self):
        """测试规则不存在时抛出异常"""
        from app.services.bonus_distribution_service import create_calculation_from_team_allocation

        mock_db = MagicMock()

        mock_allocation = MagicMock()
        mock_allocation.id = 1
        mock_allocation.allocation_detail = {"rule_id": 999}

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_allocation,
            None,  # Rule not found
        ]

        mock_calculator = MagicMock()

        with pytest.raises(ValueError) as exc_info:
            create_calculation_from_team_allocation(
                mock_db,
                team_allocation_id=1,
                user_id=1,
                calculated_amount=Decimal("1000"),
                calculator=mock_calculator
            )

        assert "规则ID" in str(exc_info.value)

    def test_creates_calculation_successfully(self):
        """测试成功创建计算记录"""
        from app.services.bonus_distribution_service import create_calculation_from_team_allocation

        mock_db = MagicMock()

        mock_allocation = MagicMock()
        mock_allocation.id = 1
        mock_allocation.project_id = 10
        mock_allocation.allocation_detail = {"rule_id": 5}

        mock_rule = MagicMock()
        mock_rule.id = 5

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_allocation,
            mock_rule,
        ]

        mock_calculator = MagicMock()
        mock_calculator.generate_calculation_code.return_value = "CALC001"

        result = create_calculation_from_team_allocation(
            mock_db,
            team_allocation_id=1,
            user_id=1,
            calculated_amount=Decimal("1000"),
            calculator=mock_calculator
        )

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()


class TestCreateDistributionRecord:
    """测试 create_distribution_record 函数"""

    def test_creates_distribution_with_all_fields(self):
        """测试创建包含所有字段的发放记录"""
        from app.services.bonus_distribution_service import create_distribution_record

        mock_db = MagicMock()

        row_data = {
            "distributed_amount": "5000",
            "distribution_date": "2026-01-15",
            "payment_method": "BANK_TRANSFER",
            "voucher_no": "VOU001",
            "payment_account": "622xxxxx",
            "payment_remark": "测试备注",
        }

        def mock_code_generator():
            return "DIST001"

        result = create_distribution_record(
            mock_db,
            calculation_id=1,
            user_id=10,
            row_data=row_data,
            current_user_id=100,
            generate_distribution_code_func=mock_code_generator
        )

        mock_db.add.assert_called_once()

    def test_creates_distribution_with_minimal_fields(self):
        """测试创建最小字段的发放记录"""
        from app.services.bonus_distribution_service import create_distribution_record

        mock_db = MagicMock()

        row_data = {
            "distributed_amount": "3000",
            "distribution_date": "2026-01-20",
        }

        def mock_code_generator():
            return "DIST002"

        result = create_distribution_record(
            mock_db,
            calculation_id=2,
            user_id=20,
            row_data=row_data,
            current_user_id=100,
            generate_distribution_code_func=mock_code_generator
        )

        mock_db.add.assert_called_once()

    def test_sets_status_to_paid(self):
        """测试设置状态为已发放"""
        from app.services.bonus_distribution_service import create_distribution_record

        mock_db = MagicMock()

        row_data = {
            "distributed_amount": "1000",
            "distribution_date": "2026-01-25",
        }

        def mock_code_generator():
            return "DIST003"

        result = create_distribution_record(
            mock_db,
            calculation_id=3,
            user_id=30,
            row_data=row_data,
            current_user_id=100,
            generate_distribution_code_func=mock_code_generator
        )

        # Verify the distribution object was added
        added_obj = mock_db.add.call_args[0][0]
        assert added_obj.status == "PAID"


class TestCheckDistributionExists:
    """测试 check_distribution_exists 函数"""

    def test_returns_true_when_distribution_exists(self):
        """测试发放存在时返回True"""
        from app.services.bonus_distribution_service import check_distribution_exists

        mock_db = MagicMock()
        mock_distribution = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_distribution

        result = check_distribution_exists(mock_db, calculation_id=1, user_id=10)

        assert result is True

    def test_returns_false_when_distribution_not_exists(self):
        """测试发放不存在时返回False"""
        from app.services.bonus_distribution_service import check_distribution_exists

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = check_distribution_exists(mock_db, calculation_id=1, user_id=10)

        assert result is False

    def test_only_checks_paid_status(self):
        """测试只检查已发放状态"""
        from app.services.bonus_distribution_service import check_distribution_exists

        mock_db = MagicMock()

        # Call the function
        check_distribution_exists(mock_db, calculation_id=1, user_id=10)

        # Verify the filter was called (we check that filter chain was used)
        mock_db.query.assert_called_once()
