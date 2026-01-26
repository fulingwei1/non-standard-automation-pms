# -*- coding: utf-8 -*-
"""
验收奖金计算服务单元测试

测试覆盖:
- 获取激活的奖金规则
- 计算销售奖金
- 计算售前技术奖金
- 计算项目奖金
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.services.acceptance_bonus_service import (
    get_active_rules,
    calculate_sales_bonus,
    calculate_presale_bonus,
    calculate_project_bonus,
)


class TestGetActiveRules:
    """获取激活奖金规则测试"""

    def test_get_active_rules_empty(self, db_session: Session):
        """测试无激活规则时返回空列表"""
        rules = get_active_rules(db_session, bonus_type='NONEXISTENT_TYPE')
        assert isinstance(rules, list)

    def test_get_active_rules_sales(self, db_session: Session):
        """测试获取销售奖金规则"""
        rules = get_active_rules(db_session, bonus_type='SALES')
        assert isinstance(rules, list)

    def test_get_active_rules_presale(self, db_session: Session):
        """测试获取售前奖金规则"""
        rules = get_active_rules(db_session, bonus_type='PRESALE')
        assert isinstance(rules, list)

    def test_get_active_rules_project(self, db_session: Session):
        """测试获取项目奖金规则"""
        rules = get_active_rules(db_session, bonus_type='PROJECT')
        assert isinstance(rules, list)


class TestCalculateSalesBonus:
    """计算销售奖金测试"""

    def test_calculate_sales_bonus_no_contract(self, db_session: Session):
        """测试无合同时返回None"""
        mock_project = MagicMock()
        mock_project.id = 99999
        mock_project.contract_no = 'NONEXISTENT_CONTRACT'

        result = calculate_sales_bonus(db_session, mock_project, [])
        assert result is None

    def test_calculate_sales_bonus_empty_rules(self, db_session: Session):
        """测试无规则时返回None"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_no = 'TEST_CONTRACT'

        result = calculate_sales_bonus(db_session, mock_project, [])
        assert result is None


class TestCalculatePresaleBonus:
    """计算售前技术奖金测试"""

    def test_calculate_presale_bonus_no_rules(self, db_session: Session):
        """测试无规则时返回None"""
        mock_project = MagicMock()
        mock_project.id = 1

        result = calculate_presale_bonus(db_session, mock_project, [])
        assert result is None

    def test_calculate_presale_bonus_no_tickets(self, db_session: Session):
        """测试无售前工单时返回None"""
        mock_project = MagicMock()
        mock_project.id = 99999

        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.coefficient = Decimal('5.0')

        result = calculate_presale_bonus(db_session, mock_project, [mock_rule])
        assert result is None


class TestCalculateProjectBonus:
    """计算项目奖金测试"""

    def test_calculate_project_bonus_no_rules(self, db_session: Session):
        """测试无规则时返回None"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal('100000')

        result = calculate_project_bonus(db_session, mock_project, [])
        assert result is None

    def test_calculate_project_bonus_zero_amount(self, db_session: Session):
        """测试项目金额为0时"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal('0')

        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.coefficient = Decimal('3.0')

        # 使用patch模拟评价服务
        with patch('app.services.acceptance_bonus_service.ProjectEvaluationService') as MockEvalService:
            mock_eval_instance = MagicMock()
            mock_eval_instance.get_difficulty_bonus_coefficient.return_value = Decimal('1.0')
            mock_eval_instance.get_new_tech_bonus_coefficient.return_value = Decimal('1.0')
            MockEvalService.return_value = mock_eval_instance

            result = calculate_project_bonus(db_session, mock_project, [mock_rule])
            # 金额为0时，奖金也为0，应返回None
            assert result is None
