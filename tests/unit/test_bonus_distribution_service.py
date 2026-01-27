# -*- coding: utf-8 -*-
"""
奖金发放服务单元测试
测试 app/services/bonus_distribution_service.py
"""

from datetime import datetime, date
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.bonus import (
    BonusAllocationSheet,
    BonusCalculation,
    BonusDistribution,
    BonusRule,
    TeamBonusAllocation,
)
from app.services.bonus_distribution_service import (
    check_distribution_exists,
    create_calculation_from_team_allocation,
    create_distribution_record,
    validate_sheet_for_distribution,
)


class TestValidateSheetForDistribution:
    """测试 validate_sheet_for_distribution 函数"""

    def test_sheet_already_distributed(self):
        """测试明细表已发放的情况"""
        sheet = Mock(spec=BonusAllocationSheet)
        sheet.status = "DISTRIBUTED"

        is_valid, error = validate_sheet_for_distribution(sheet)

        assert is_valid is False
        assert "已发放" in error

    def test_sheet_missing_finance_confirmation(self):
        """测试缺少财务确认的情况"""
        sheet = Mock(spec=BonusAllocationSheet)
        sheet.status = "PENDING"
        sheet.finance_confirmed = False
        sheet.hr_confirmed = True
        sheet.manager_confirmed = True

        is_valid, error = validate_sheet_for_distribution(sheet)

        assert is_valid is False
        assert "线下确认未完成" in error

    def test_sheet_missing_hr_confirmation(self):
        """测试缺少人力资源确认的情况"""
        sheet = Mock(spec=BonusAllocationSheet)
        sheet.status = "PENDING"
        sheet.finance_confirmed = True
        sheet.hr_confirmed = False
        sheet.manager_confirmed = True

        is_valid, error = validate_sheet_for_distribution(sheet)

        assert is_valid is False
        assert "线下确认未完成" in error

    def test_sheet_missing_manager_confirmation(self):
        """测试缺少总经理确认的情况"""
        sheet = Mock(spec=BonusAllocationSheet)
        sheet.status = "PENDING"
        sheet.finance_confirmed = True
        sheet.hr_confirmed = True
        sheet.manager_confirmed = False

        is_valid, error = validate_sheet_for_distribution(sheet)

        assert is_valid is False
        assert "线下确认未完成" in error

    def test_sheet_missing_parse_result(self):
        """测试明细表数据无效的情况"""
        sheet = Mock(spec=BonusAllocationSheet)
        sheet.status = "PENDING"
        sheet.finance_confirmed = True
        sheet.hr_confirmed = True
        sheet.manager_confirmed = True
        sheet.parse_result = None

        is_valid, error = validate_sheet_for_distribution(sheet)

        assert is_valid is False
        assert "明细表数据无效" in error

    def test_sheet_missing_valid_rows_key(self):
        """测试明细表缺少 valid_rows 键的情况"""
        sheet = Mock(spec=BonusAllocationSheet)
        sheet.status = "PENDING"
        sheet.finance_confirmed = True
        sheet.hr_confirmed = True
        sheet.manager_confirmed = True
        sheet.parse_result = {"other_key": []}

        is_valid, error = validate_sheet_for_distribution(sheet)

        assert is_valid is False
        assert "明细表数据无效" in error

    def test_sheet_empty_valid_rows(self):
        """测试明细表没有有效数据的情况"""
        sheet = Mock(spec=BonusAllocationSheet)
        sheet.status = "PENDING"
        sheet.finance_confirmed = True
        sheet.hr_confirmed = True
        sheet.manager_confirmed = True
        sheet.parse_result = {"valid_rows": []}

        is_valid, error = validate_sheet_for_distribution(sheet)

        assert is_valid is False
        assert "没有有效数据" in error

    def test_sheet_valid_for_distribution(self):
        """测试明细表可以发放的情况"""
        sheet = Mock(spec=BonusAllocationSheet)
        sheet.status = "PENDING"
        sheet.finance_confirmed = True
        sheet.hr_confirmed = True
        sheet.manager_confirmed = True
        sheet.parse_result = {
        "valid_rows": [
        {"user_id": 1, "amount": 1000},
        {"user_id": 2, "amount": 2000},
        ]
        }

        is_valid, error = validate_sheet_for_distribution(sheet)

        assert is_valid is True
        assert error is None


class TestCreateCalculationFromTeamAllocation:
    """测试 create_calculation_from_team_allocation 函数"""

    def test_allocation_not_found(self):
        """测试团队奖金分配不存在的情况"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_calculator = MagicMock()

        with pytest.raises(ValueError, match="不存在"):
            create_calculation_from_team_allocation(
            mock_db,
            team_allocation_id=999,
            user_id=1,
            calculated_amount=Decimal("1000"),
            calculator=mock_calculator,
            )

    def test_allocation_missing_rule_id(self):
        """测试分配明细缺少规则ID的情况"""
        mock_db = MagicMock(spec=Session)

        mock_allocation = Mock(spec=TeamBonusAllocation)
        mock_allocation.id = 1
        mock_allocation.allocation_detail = {}  # 缺少 rule_id

        mock_db.query.return_value.filter.return_value.first.return_value = (
        mock_allocation
        )

        mock_calculator = MagicMock()

        with pytest.raises(ValueError, match="缺少规则ID"):
            create_calculation_from_team_allocation(
            mock_db,
            team_allocation_id=1,
            user_id=1,
            calculated_amount=Decimal("1000"),
            calculator=mock_calculator,
            )

    def test_rule_not_found(self):
        """测试规则不存在的情况"""
        mock_db = MagicMock(spec=Session)

        mock_allocation = Mock(spec=TeamBonusAllocation)
        mock_allocation.id = 1
        mock_allocation.allocation_detail = {"rule_id": 999}
        mock_allocation.project_id = 1

        # First query returns allocation, second returns None for rule
        mock_db.query.return_value.filter.return_value.first.side_effect = [
        mock_allocation,
        None,  # Rule not found
        ]

        mock_calculator = MagicMock()

        with pytest.raises(ValueError, match="规则ID.*不存在"):
            create_calculation_from_team_allocation(
            mock_db,
            team_allocation_id=1,
            user_id=1,
            calculated_amount=Decimal("1000"),
            calculator=mock_calculator,
            )

    def test_create_calculation_successfully(self):
        """测试成功创建个人计算记录"""
        mock_db = MagicMock(spec=Session)

        mock_allocation = Mock(spec=TeamBonusAllocation)
        mock_allocation.id = 1
        mock_allocation.project_id = 10
        mock_allocation.allocation_detail = {
        "rule_id": 5,
        "bonus_type": "PROJECT_BASED",
        }

        mock_rule = Mock(spec=BonusRule)
        mock_rule.id = 5

        # Setup query returns
        mock_db.query.return_value.filter.return_value.first.side_effect = [
        mock_allocation,
        mock_rule,
        ]

        mock_calculator = MagicMock()
        mock_calculator.generate_calculation_code.return_value = "CALC-001"

        result = create_calculation_from_team_allocation(
        mock_db,
        team_allocation_id=1,
        user_id=100,
        calculated_amount=Decimal("5000"),
        calculator=mock_calculator,
        )

        # Verify the calculation was created correctly
        assert result.calculation_code == "CALC-001"
        assert result.rule_id == 5
        assert result.project_id == 10
        assert result.user_id == 100
        assert result.calculated_amount == Decimal("5000")
        assert result.status == "APPROVED"
        assert result.calculation_detail["from_team_allocation"] is True
        assert result.calculation_detail["team_allocation_id"] == 1

        # Verify db operations
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()


class TestCreateDistributionRecord:
    """测试 create_distribution_record 函数"""

    def test_create_distribution_record_successfully(self):
        """测试成功创建发放记录"""
        mock_db = MagicMock(spec=Session)

        row_data = {
        "distributed_amount": "5000.00",
        "distribution_date": "2024-06-15",
        "payment_method": "BANK_TRANSFER",
        "voucher_no": "VCH-001",
        "payment_account": "6222****1234",
        "payment_remark": "项目奖金发放",
        }

        def mock_generate_code():
            return "DIST-001"

            result = create_distribution_record(
            mock_db,
            calculation_id=10,
            user_id=100,
            row_data=row_data,
            current_user_id=1,
            generate_distribution_code_func=mock_generate_code,
            )

            # Verify the distribution was created correctly
            assert result.distribution_code == "DIST-001"
            assert result.calculation_id == 10
            assert result.user_id == 100
            assert result.distributed_amount == Decimal("5000.00")
            assert result.distribution_date == date(2024, 6, 15)
            assert result.payment_method == "BANK_TRANSFER"
            assert result.voucher_no == "VCH-001"
            assert result.payment_account == "6222****1234"
            assert result.payment_remark == "项目奖金发放"
            assert result.status == "PAID"
            assert result.paid_by == 1

            # Verify db.add was called
            mock_db.add.assert_called_once()

    def test_create_distribution_record_minimal_data(self):
        """测试使用最少数据创建发放记录"""
        mock_db = MagicMock(spec=Session)

        row_data = {
        "distributed_amount": "1000.00",
        "distribution_date": "2024-01-01",
        }

        def mock_generate_code():
            return "DIST-002"

            result = create_distribution_record(
            mock_db,
            calculation_id=20,
            user_id=200,
            row_data=row_data,
            current_user_id=2,
            generate_distribution_code_func=mock_generate_code,
            )

            assert result.distribution_code == "DIST-002"
            assert result.distributed_amount == Decimal("1000.00")
            assert result.payment_method is None
            assert result.voucher_no is None


class TestCheckDistributionExists:
    """测试 check_distribution_exists 函数"""

    def test_distribution_exists(self):
        """测试已存在发放记录的情况"""
        mock_db = MagicMock(spec=Session)

        mock_distribution = Mock(spec=BonusDistribution)
        mock_distribution.id = 1
        mock_distribution.status = "PAID"

        mock_db.query.return_value.filter.return_value.first.return_value = (
        mock_distribution
        )

        result = check_distribution_exists(mock_db, calculation_id=10, user_id=100)

        assert result is True

    def test_distribution_not_exists(self):
        """测试不存在发放记录的情况"""
        mock_db = MagicMock(spec=Session)

        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = check_distribution_exists(mock_db, calculation_id=10, user_id=100)

        assert result is False

    def test_distribution_exists_different_user(self):
        """测试查询不同用户的发放记录"""
        mock_db = MagicMock(spec=Session)

        # User 100 has distribution, user 200 doesn't
        mock_db.query.return_value.filter.return_value.first.side_effect = [
        Mock(spec=BonusDistribution),  # User 100
        None,  # User 200
        ]

        result1 = check_distribution_exists(mock_db, calculation_id=10, user_id=100)
        result2 = check_distribution_exists(mock_db, calculation_id=10, user_id=200)

        assert result1 is True
        assert result2 is False


class TestIntegration:
    """集成测试"""

    def test_full_distribution_workflow(self):
        """测试完整的发放流程"""
        # 1. 验证明细表
        sheet = Mock(spec=BonusAllocationSheet)
        sheet.status = "PENDING"
        sheet.finance_confirmed = True
        sheet.hr_confirmed = True
        sheet.manager_confirmed = True
        sheet.parse_result = {
        "valid_rows": [
        {
        "user_id": 1,
        "distributed_amount": "5000.00",
        "distribution_date": "2024-06-15",
        }
        ]
        }

        is_valid, error = validate_sheet_for_distribution(sheet)
        assert is_valid is True

        # 2. 检查是否已发放
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        exists = check_distribution_exists(mock_db, calculation_id=1, user_id=1)
        assert exists is False

        # 3. 创建发放记录
        row_data = sheet.parse_result["valid_rows"][0]
        distribution = create_distribution_record(
        mock_db,
        calculation_id=1,
        user_id=1,
        row_data=row_data,
        current_user_id=999,
        generate_distribution_code_func=lambda: "DIST-TEST-001",
        )

        assert distribution.distributed_amount == Decimal("5000.00")
        assert distribution.status == "PAID"
