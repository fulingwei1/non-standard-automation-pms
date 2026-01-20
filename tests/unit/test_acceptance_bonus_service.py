# -*- coding: utf-8 -*-
"""
acceptance_bonus_service 单元测试

测试验收奖金计算服务的各个方法
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.acceptance_bonus_service import (
    calculate_presale_bonus,
    calculate_project_bonus,
    calculate_sales_bonus,
    get_active_rules,
)


@pytest.mark.unit
class TestGetActiveRules:
    """测试 get_active_rules 函数"""

    def test_get_active_rules_found(self):
        """测试获取激活的规则"""
        mock_db = MagicMock()
        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.bonus_type = "SALES"
        mock_rule.is_active = True

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_rule]

        result = get_active_rules(mock_db, "SALES")

        assert len(result) == 1
        assert result[0].bonus_type == "SALES"

    def test_get_active_rules_empty(self):
        """测试没有激活的规则"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = get_active_rules(mock_db, "NONEXISTENT")

        assert result == []

    def test_get_active_rules_multiple(self):
        """测试多个激活的规则"""
        mock_db = MagicMock()
        mock_rules = [MagicMock(id=i, bonus_type="PROJECT") for i in range(3)]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_rules

        result = get_active_rules(mock_db, "PROJECT")

        assert len(result) == 3


@pytest.mark.unit
class TestCalculateSalesBonus:
    """测试 calculate_sales_bonus 函数"""

    def test_no_contract_found(self):
        """测试找不到合同"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_project = MagicMock()
        mock_project.contract_no = "C001"

        result = calculate_sales_bonus(mock_db, mock_project, [])

        assert result is None

    def test_empty_rules(self):
        """测试空规则列表"""
        mock_db = MagicMock()
        mock_contract = MagicMock()
        mock_contract.contract_amount = Decimal('100000')
        mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        mock_project = MagicMock()
        mock_project.contract_no = "C001"

        result = calculate_sales_bonus(mock_db, mock_project, [])

        assert result is None

    @patch('app.services.acceptance_bonus_service.Contract')
    def test_calculate_bonus_success(self, mock_contract_class):
        """测试成功计算销售奖金"""
        mock_db = MagicMock()

        mock_contract = MagicMock()
        mock_contract.id = 1
        mock_contract.contract_amount = Decimal('100000')
        mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_no = "C001"

        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.rule_name = "Sales Bonus"
        mock_rule.coefficient = Decimal('5')  # 5%
        mock_rule.trigger_condition = {"acceptance_completed": True}

        result = calculate_sales_bonus(mock_db, mock_project, [mock_rule])

        assert result is not None
        assert result.total_bonus_amount == Decimal('5000')  # 100000 * 5%
        assert mock_db.add.called

    @patch('app.services.acceptance_bonus_service.Contract')
    def test_calculate_bonus_no_trigger_condition(self, mock_contract_class):
        """测试没有触发条件时也计算"""
        mock_db = MagicMock()

        mock_contract = MagicMock()
        mock_contract.id = 1
        mock_contract.contract_amount = Decimal('50000')
        mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_no = "C001"

        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.rule_name = "Sales Bonus"
        mock_rule.coefficient = Decimal('10')  # 10%
        mock_rule.trigger_condition = None

        result = calculate_sales_bonus(mock_db, mock_project, [mock_rule])

        assert result is not None
        assert result.total_bonus_amount == Decimal('5000')  # 50000 * 10%

    @patch('app.services.acceptance_bonus_service.Contract')
    def test_calculate_bonus_zero_amount(self, mock_contract_class):
        """测试零奖金"""
        mock_db = MagicMock()

        mock_contract = MagicMock()
        mock_contract.id = 1
        mock_contract.contract_amount = Decimal('0')
        mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_no = "C001"

        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.coefficient = Decimal('5')
        mock_rule.trigger_condition = {}

        result = calculate_sales_bonus(mock_db, mock_project, [mock_rule])

        assert result is None  # Zero bonus, no allocation created

    def test_exception_handling(self):
        """测试异常处理"""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")

        mock_project = MagicMock()
        mock_project.contract_no = "C001"

        result = calculate_sales_bonus(mock_db, mock_project, [])

        assert result is None


@pytest.mark.unit
class TestCalculatePresaleBonus:
    """测试 calculate_presale_bonus 函数"""

    def test_empty_rules(self):
        """测试空规则列表"""
        mock_db = MagicMock()
        mock_project = MagicMock()

        result = calculate_presale_bonus(mock_db, mock_project, [])

        assert result is None

    def test_no_presale_tickets(self):
        """测试没有售前工单"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        mock_project = MagicMock()
        mock_project.id = 1

        mock_rule = MagicMock()

        result = calculate_presale_bonus(mock_db, mock_project, [mock_rule])

        assert result is None

    def test_calculate_bonus_with_opportunity(self):
        """测试基于商机计算售前奖金"""
        mock_db = MagicMock()

        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.opportunity_id = 1
        mock_ticket.assignee_id = 10
        mock_ticket.status = 'COMPLETED'

        mock_opportunity = MagicMock()
        mock_opportunity.id = 1
        mock_opportunity.stage = 'WON'
        mock_opportunity.est_amount = Decimal('200000')

        def query_side_effect(model):
            query_mock = MagicMock()
            model_name = model.__name__
            if model_name == 'PresaleSupportTicket':
                query_mock.filter.return_value.all.return_value = [mock_ticket]
            elif model_name == 'Opportunity':
                query_mock.filter.return_value.first.return_value = mock_opportunity
            return query_mock

        mock_db.query.side_effect = query_side_effect

        mock_project = MagicMock()
        mock_project.id = 1

        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.rule_name = "Presale Bonus"
        mock_rule.coefficient = Decimal('2')  # 2%

        result = calculate_presale_bonus(mock_db, mock_project, [mock_rule])

        assert result is not None
        assert result.total_bonus_amount == Decimal('4000')  # 200000 * 2%
        assert mock_db.add.called

    def test_calculate_bonus_with_project_status(self):
        """测试基于项目状态计算售前奖金"""
        mock_db = MagicMock()

        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.opportunity_id = None
        mock_ticket.assignee_id = 10

        def query_side_effect(model):
            query_mock = MagicMock()
            model_name = model.__name__
            if model_name == 'PresaleSupportTicket':
                query_mock.filter.return_value.all.return_value = [mock_ticket]
            return query_mock

        mock_db.query.side_effect = query_side_effect

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.status = 'ST01'  # Won status
        mock_project.contract_amount = Decimal('150000')

        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.rule_name = "Presale Bonus"
        mock_rule.coefficient = Decimal('3')  # 3%

        result = calculate_presale_bonus(mock_db, mock_project, [mock_rule])

        assert result is not None
        assert result.total_bonus_amount == Decimal('4500')  # 150000 * 3%

    def test_exception_handling(self):
        """测试异常处理"""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")

        mock_project = MagicMock()

        mock_rule = MagicMock()

        result = calculate_presale_bonus(mock_db, mock_project, [mock_rule])

        assert result is None


@pytest.mark.unit
class TestCalculateProjectBonus:
    """测试 calculate_project_bonus 函数"""

    def test_empty_rules(self):
        """测试空规则列表"""
        mock_db = MagicMock()
        mock_project = MagicMock()

        result = calculate_project_bonus(mock_db, mock_project, [])

        assert result is None

    @patch('app.services.acceptance_bonus_service.ProjectEvaluationService')
    def test_calculate_bonus_success(self, mock_eval_service_class):
        """测试成功计算项目奖金"""
        mock_db = MagicMock()

        # Mock evaluation service
        mock_eval_service = MagicMock()
        mock_eval_service.get_difficulty_bonus_coefficient.return_value = Decimal('1.2')
        mock_eval_service.get_new_tech_bonus_coefficient.return_value = Decimal('1.1')
        mock_eval_service_class.return_value = mock_eval_service

        # Mock project members
        mock_member = MagicMock()
        mock_member.id = 1

        # Mock contributions
        mock_contribution = MagicMock()

        def query_side_effect(model):
            query_mock = MagicMock()
            model_name = model.__name__
            if model_name == 'ProjectMember':
                query_mock.filter.return_value.all.return_value = [mock_member]
            elif model_name == 'ProjectContribution':
                query_mock.filter.return_value.all.return_value = [mock_contribution]
            return query_mock

        mock_db.query.side_effect = query_side_effect

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal('100000')

        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.rule_name = "Project Bonus"
        mock_rule.coefficient = Decimal('5')  # 5%

        result = calculate_project_bonus(mock_db, mock_project, [mock_rule])

        assert result is not None
        # 100000 * 5% * 1.2 (max of 1.2 and 1.1) = 6000
        assert result.total_bonus_amount == Decimal('6000')
        assert mock_db.add.called

    @patch('app.services.acceptance_bonus_service.ProjectEvaluationService')
    def test_calculate_bonus_zero_amount(self, mock_eval_service_class):
        """测试零项目金额"""
        mock_db = MagicMock()

        mock_eval_service = MagicMock()
        mock_eval_service.get_difficulty_bonus_coefficient.return_value = Decimal('1.0')
        mock_eval_service.get_new_tech_bonus_coefficient.return_value = Decimal('1.0')
        mock_eval_service_class.return_value = mock_eval_service

        mock_db.query.return_value.filter.return_value.all.return_value = []

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal('0')

        mock_rule = MagicMock()
        mock_rule.coefficient = Decimal('5')

        result = calculate_project_bonus(mock_db, mock_project, [mock_rule])

        assert result is None

    def test_exception_handling(self):
        """测试异常处理"""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")

        mock_project = MagicMock()

        mock_rule = MagicMock()

        result = calculate_project_bonus(mock_db, mock_project, [mock_rule])

        assert result is None


@pytest.mark.unit
class TestAcceptanceBonusIntegration:
    """集成测试"""

    def test_all_functions_importable(self):
        """测试所有函数可导入"""
        from app.services.acceptance_bonus_service import (
            calculate_presale_bonus,
            calculate_project_bonus,
            calculate_sales_bonus,
            get_active_rules,
        )

        assert get_active_rules is not None
        assert calculate_sales_bonus is not None
        assert calculate_presale_bonus is not None
        assert calculate_project_bonus is not None

    @patch('app.services.acceptance_bonus_service.Contract')
    def test_multiple_rules_first_match(self, mock_contract_class):
        """测试多个规则时使用第一个匹配的"""
        mock_db = MagicMock()

        mock_contract = MagicMock()
        mock_contract.id = 1
        mock_contract.contract_amount = Decimal('100000')
        mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_no = "C001"

        mock_rule1 = MagicMock()
        mock_rule1.id = 1
        mock_rule1.rule_name = "Rule 1"
        mock_rule1.coefficient = Decimal('3')
        mock_rule1.trigger_condition = {}

        mock_rule2 = MagicMock()
        mock_rule2.id = 2
        mock_rule2.rule_name = "Rule 2"
        mock_rule2.coefficient = Decimal('5')
        mock_rule2.trigger_condition = {}

        result = calculate_sales_bonus(mock_db, mock_project, [mock_rule1, mock_rule2])

        assert result is not None
        # Should use first rule (3%)
        assert result.total_bonus_amount == Decimal('3000')

    @patch('app.services.acceptance_bonus_service.ProjectEvaluationService')
    def test_bonus_coefficient_applied(self, mock_eval_service_class):
        """测试奖金系数正确应用"""
        mock_db = MagicMock()

        mock_eval_service = MagicMock()
        mock_eval_service.get_difficulty_bonus_coefficient.return_value = Decimal('1.5')
        mock_eval_service.get_new_tech_bonus_coefficient.return_value = Decimal('1.3')
        mock_eval_service_class.return_value = mock_eval_service

        mock_db.query.return_value.filter.return_value.all.return_value = []

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal('100000')

        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.rule_name = "Project Bonus"
        mock_rule.coefficient = Decimal('10')  # 10%

        result = calculate_project_bonus(mock_db, mock_project, [mock_rule])

        assert result is not None
        # 100000 * 10% * 1.5 (max coefficient) = 15000
        assert result.total_bonus_amount == Decimal('15000')
