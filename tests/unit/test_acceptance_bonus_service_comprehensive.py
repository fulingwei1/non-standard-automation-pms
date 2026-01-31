# -*- coding: utf-8 -*-
"""
acceptance_bonus_service 综合单元测试

测试覆盖:
- get_active_rules: 获取激活的奖金规则
- calculate_sales_bonus: 计算销售奖金总额
- calculate_presale_bonus: 计算售前技术奖金总额
- calculate_project_bonus: 计算项目奖金总额
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestGetActiveRules:
    """测试 get_active_rules 函数"""

    def test_returns_active_rules(self):
        """测试返回激活的规则"""
        from app.services.acceptance_bonus_service import get_active_rules

        mock_db = MagicMock()
        mock_rule1 = MagicMock()
        mock_rule1.id = 1
        mock_rule1.bonus_type = "SALES"
        mock_rule1.is_active = True

        mock_rule2 = MagicMock()
        mock_rule2.id = 2
        mock_rule2.bonus_type = "SALES"
        mock_rule2.is_active = True

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_rule1, mock_rule2]

        result = get_active_rules(mock_db, "SALES")

        assert len(result) == 2

    def test_returns_empty_when_no_rules(self):
        """测试无规则时返回空列表"""
        from app.services.acceptance_bonus_service import get_active_rules

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = get_active_rules(mock_db, "SALES")

        assert result == []

    def test_filters_by_bonus_type(self):
        """测试按奖金类型筛选"""
        from app.services.acceptance_bonus_service import get_active_rules

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        get_active_rules(mock_db, "PROJECT")

        # 验证filter被调用
        mock_db.query.return_value.filter.assert_called()


class TestCalculateSalesBonus:
    """测试 calculate_sales_bonus 函数"""

    def test_returns_none_when_no_contract(self):
        """测试无合同时返回None"""
        from app.services.acceptance_bonus_service import calculate_sales_bonus

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.contract_no = "CONTRACT001"

        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = calculate_sales_bonus(mock_db, mock_project, [])

        assert result is None

    def test_calculates_bonus_correctly(self):
        """测试正确计算奖金"""
        from app.services.acceptance_bonus_service import calculate_sales_bonus

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_no = "CONTRACT001"

        mock_contract = MagicMock()
        mock_contract.id = 10
        mock_contract.contract_amount = Decimal("100000")

        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.rule_name = "销售奖金规则"
        mock_rule.coefficient = Decimal("5")  # 5%
        mock_rule.trigger_condition = {"acceptance_completed": True}

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        result = calculate_sales_bonus(mock_db, mock_project, [mock_rule])

        assert result is not None
        assert result.total_bonus_amount == Decimal("5000")  # 100000 * 5%
        mock_db.add.assert_called_once()

    def test_handles_empty_trigger_condition(self):
        """测试处理空触发条件"""
        from app.services.acceptance_bonus_service import calculate_sales_bonus

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_no = "CONTRACT001"

        mock_contract = MagicMock()
        mock_contract.id = 10
        mock_contract.contract_amount = Decimal("100000")

        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.rule_name = "销售奖金规则"
        mock_rule.coefficient = Decimal("3")
        mock_rule.trigger_condition = {}  # 空条件

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        result = calculate_sales_bonus(mock_db, mock_project, [mock_rule])

        assert result is not None
        assert result.total_bonus_amount == Decimal("3000")

    def test_returns_none_when_bonus_is_zero(self):
        """测试奖金为零时返回None"""
        from app.services.acceptance_bonus_service import calculate_sales_bonus

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.contract_no = "CONTRACT001"

        mock_contract = MagicMock()
        mock_contract.contract_amount = Decimal("0")

        mock_rule = MagicMock()
        mock_rule.coefficient = Decimal("5")
        mock_rule.trigger_condition = {}

        mock_db.query.return_value.filter.return_value.first.return_value = mock_contract

        result = calculate_sales_bonus(mock_db, mock_project, [mock_rule])

        assert result is None

    def test_handles_exception_gracefully(self):
        """测试优雅处理异常"""
        from app.services.acceptance_bonus_service import calculate_sales_bonus

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.contract_no = "CONTRACT001"

        mock_db.query.return_value.filter.return_value.first.side_effect = Exception("数据库错误")

        result = calculate_sales_bonus(mock_db, mock_project, [])

        assert result is None


class TestCalculatePresaleBonus:
    """测试 calculate_presale_bonus 函数"""

    def test_returns_none_when_no_rules(self):
        """测试无规则时返回None"""
        from app.services.acceptance_bonus_service import calculate_presale_bonus

        mock_db = MagicMock()
        mock_project = MagicMock()

        result = calculate_presale_bonus(mock_db, mock_project, [])

        assert result is None

    def test_returns_none_when_no_tickets(self):
        """测试无售前工单时返回None"""
        from app.services.acceptance_bonus_service import calculate_presale_bonus

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1

        mock_rule = MagicMock()

        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = calculate_presale_bonus(mock_db, mock_project, [mock_rule])

        assert result is None

    def test_calculates_bonus_from_opportunity(self):
        """测试从商机计算奖金"""
        from app.services.acceptance_bonus_service import calculate_presale_bonus

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.status = "ST00"
        mock_project.contract_amount = None

        mock_ticket = MagicMock()
        mock_ticket.id = 100
        mock_ticket.opportunity_id = 10
        mock_ticket.assignee_id = 5

        mock_opportunity = MagicMock()
        mock_opportunity.id = 10
        mock_opportunity.stage = "WON"
        mock_opportunity.est_amount = Decimal("200000")

        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.rule_name = "售前奖金规则"
        mock_rule.coefficient = Decimal("2")  # 2%

        # Setup query chain
        def query_side_effect(model):
            query_mock = MagicMock()
            if model.__name__ == 'PresaleSupportTicket':
                query_mock.filter.return_value.all.return_value = [mock_ticket]
            elif model.__name__ == 'Opportunity':
                query_mock.filter.return_value.first.return_value = mock_opportunity
            return query_mock

        mock_db.query.side_effect = query_side_effect

        result = calculate_presale_bonus(mock_db, mock_project, [mock_rule])

        assert result is not None
        assert result.total_bonus_amount == Decimal("4000")  # 200000 * 2%

    def test_calculates_bonus_from_project(self):
        """测试从项目计算奖金"""
        from app.services.acceptance_bonus_service import calculate_presale_bonus

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.status = "ST01"  # 进行中
        mock_project.contract_amount = Decimal("150000")

        mock_ticket = MagicMock()
        mock_ticket.id = 100
        mock_ticket.opportunity_id = None
        mock_ticket.assignee_id = 5

        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.rule_name = "售前奖金规则"
        mock_rule.coefficient = Decimal("2")

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_ticket]

        result = calculate_presale_bonus(mock_db, mock_project, [mock_rule])

        assert result is not None
        assert result.total_bonus_amount == Decimal("3000")  # 150000 * 2%

    def test_handles_exception_gracefully(self):
        """测试优雅处理异常"""
        from app.services.acceptance_bonus_service import calculate_presale_bonus

        mock_db = MagicMock()
        mock_project = MagicMock()

        mock_rule = MagicMock()
        mock_db.query.return_value.filter.return_value.all.side_effect = Exception("数据库错误")

        result = calculate_presale_bonus(mock_db, mock_project, [mock_rule])

        assert result is None


class TestCalculateProjectBonus:
    """测试 calculate_project_bonus 函数"""

    def test_returns_none_when_no_rules(self):
        """测试无规则时返回None"""
        from app.services.acceptance_bonus_service import calculate_project_bonus

        mock_db = MagicMock()
        mock_project = MagicMock()

        result = calculate_project_bonus(mock_db, mock_project, [])

        assert result is None

    def test_calculates_bonus_with_coefficient(self):
        """测试使用系数计算奖金"""
        from app.services.acceptance_bonus_service import calculate_project_bonus

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal("500000")

        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.rule_name = "项目奖金规则"
        mock_rule.coefficient = Decimal("3")  # 3%

        # Mock evaluation service
        with patch('app.services.acceptance_bonus_service.ProjectEvaluationService') as mock_eval_service:
            mock_eval_instance = MagicMock()
            mock_eval_instance.get_difficulty_bonus_coefficient.return_value = Decimal("1.2")
            mock_eval_instance.get_new_tech_bonus_coefficient.return_value = Decimal("1.0")
            mock_eval_service.return_value = mock_eval_instance

            # Mock project members query
            mock_db.query.return_value.filter.return_value.all.return_value = []

            result = calculate_project_bonus(mock_db, mock_project, [mock_rule])

            # 500000 * 3% = 15000 * 1.2 (difficulty_coef) = 18000
            assert result is not None
            assert result.total_bonus_amount == Decimal("18000")

    def test_uses_max_coefficient(self):
        """测试使用最大系数"""
        from app.services.acceptance_bonus_service import calculate_project_bonus

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal("100000")

        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.rule_name = "项目奖金规则"
        mock_rule.coefficient = Decimal("5")

        with patch('app.services.acceptance_bonus_service.ProjectEvaluationService') as mock_eval_service:
            mock_eval_instance = MagicMock()
            mock_eval_instance.get_difficulty_bonus_coefficient.return_value = Decimal("1.1")
            mock_eval_instance.get_new_tech_bonus_coefficient.return_value = Decimal("1.5")  # 更大
            mock_eval_service.return_value = mock_eval_instance

            mock_db.query.return_value.filter.return_value.all.return_value = []

            result = calculate_project_bonus(mock_db, mock_project, [mock_rule])

            # 100000 * 5% = 5000 * 1.5 (new_tech_coef is max) = 7500
            assert result.total_bonus_amount == Decimal("7500")

    def test_includes_member_and_contribution_info(self):
        """测试包含成员和贡献信息"""
        from app.services.acceptance_bonus_service import calculate_project_bonus

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal("100000")

        mock_rule = MagicMock()
        mock_rule.id = 1
        mock_rule.rule_name = "项目奖金规则"
        mock_rule.coefficient = Decimal("5")

        mock_member = MagicMock()
        mock_contribution = MagicMock()

        with patch('app.services.acceptance_bonus_service.ProjectEvaluationService') as mock_eval_service:
            mock_eval_instance = MagicMock()
            mock_eval_instance.get_difficulty_bonus_coefficient.return_value = Decimal("1.0")
            mock_eval_instance.get_new_tech_bonus_coefficient.return_value = Decimal("1.0")
            mock_eval_service.return_value = mock_eval_instance

            # Setup query chain for members and contributions
            def query_side_effect(model):
                query_mock = MagicMock()
                if model.__name__ == 'ProjectMember':
                    query_mock.filter.return_value.all.return_value = [mock_member, mock_member]
                elif model.__name__ == 'ProjectContribution':
                    query_mock.filter.return_value.all.return_value = [mock_contribution]
                return query_mock

            mock_db.query.side_effect = query_side_effect

            result = calculate_project_bonus(mock_db, mock_project, [mock_rule])

            assert result.allocation_detail["member_count"] == 2
            assert result.allocation_detail["contribution_count"] == 1

    def test_handles_exception_gracefully(self):
        """测试优雅处理异常"""
        from app.services.acceptance_bonus_service import calculate_project_bonus

        mock_db = MagicMock()
        mock_project = MagicMock()

        mock_rule = MagicMock()
        mock_rule.coefficient = Decimal("5")

        with patch('app.services.acceptance_bonus_service.ProjectEvaluationService') as mock_eval_service:
            mock_eval_service.side_effect = Exception("服务错误")

            result = calculate_project_bonus(mock_db, mock_project, [mock_rule])

            assert result is None
