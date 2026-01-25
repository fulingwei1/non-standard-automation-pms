# -*- coding: utf-8 -*-
"""
验收奖金计算服务单元测试
测试 app/services/acceptance_bonus_service.py
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.acceptance import AcceptanceOrder
from app.models.bonus import BonusRule, TeamBonusAllocation
from app.models.presale import PresaleSupportTicket
from app.models.project import Project, ProjectMember
from app.models.sales import Contract, Opportunity
from app.services.acceptance_bonus_service import (
    calculate_presale_bonus,
    calculate_project_bonus,
    calculate_sales_bonus,
    get_active_rules,
)


class TestGetActiveRules:
    """测试 get_active_rules 函数"""

    def test_get_active_rules_returns_matching_rules(self):
        """测试获取激活的奖金规则"""
        mock_db = MagicMock(spec=Session)

        mock_rule1 = Mock(spec=BonusRule)
        mock_rule1.id = 1
        mock_rule1.bonus_type = "SALES_BASED"
        mock_rule1.is_active = True

        mock_rule2 = Mock(spec=BonusRule)
        mock_rule2.id = 2
        mock_rule2.bonus_type = "SALES_BASED"
        mock_rule2.is_active = True

        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_rule1,
            mock_rule2,
        ]

        result = get_active_rules(mock_db, "SALES_BASED")

        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2

    def test_get_active_rules_returns_empty_list(self):
        """测试没有匹配规则时返回空列表"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = get_active_rules(mock_db, "NON_EXISTENT_TYPE")

        assert result == []


class TestCalculateSalesBonus:
    """测试 calculate_sales_bonus 函数"""

    def test_calculate_sales_bonus_no_contract(self):
        """测试没有合同时返回 None"""
        mock_db = MagicMock(spec=Session)
        mock_project = Mock(spec=Project)
        mock_project.contract_no = "CT-001"

        # Contract not found
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_rules = [Mock(spec=BonusRule)]

        result = calculate_sales_bonus(mock_db, mock_project, mock_rules)

        assert result is None

    def test_calculate_sales_bonus_successfully(self):
        """测试成功计算销售奖金"""
        mock_db = MagicMock(spec=Session)

        mock_project = Mock(spec=Project)
        mock_project.id = 1
        mock_project.contract_no = "CT-001"

        mock_contract = Mock(spec=Contract)
        mock_contract.id = 10
        mock_contract.contract_amount = Decimal("100000")

        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_contract
        )

        mock_rule = Mock(spec=BonusRule)
        mock_rule.id = 5
        mock_rule.rule_name = "销售奖金规则"
        mock_rule.coefficient = Decimal("5")  # 5%
        mock_rule.trigger_condition = {"acceptance_completed": True}

        result = calculate_sales_bonus(mock_db, mock_project, [mock_rule])

        assert result is not None
        assert result.project_id == 1
        # 100000 * 5% = 5000
        assert result.total_bonus_amount == Decimal("5000")
        assert result.status == "PENDING"
        assert result.allocation_detail["bonus_type"] == "SALES_BASED"
        assert result.allocation_detail["rule_id"] == 5

    def test_calculate_sales_bonus_zero_amount(self):
        """测试合同金额为0时返回 None"""
        mock_db = MagicMock(spec=Session)

        mock_project = Mock(spec=Project)
        mock_project.id = 1
        mock_project.contract_no = "CT-001"

        mock_contract = Mock(spec=Contract)
        mock_contract.id = 10
        mock_contract.contract_amount = Decimal("0")

        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_contract
        )

        mock_rule = Mock(spec=BonusRule)
        mock_rule.id = 5
        mock_rule.coefficient = Decimal("5")
        mock_rule.trigger_condition = {}

        result = calculate_sales_bonus(mock_db, mock_project, [mock_rule])

        assert result is None

    def test_calculate_sales_bonus_handles_exception(self):
        """测试异常处理"""
        mock_db = MagicMock(spec=Session)

        mock_project = Mock(spec=Project)
        mock_project.contract_no = "CT-001"

        # Simulate database error
        mock_db.query.side_effect = Exception("Database error")

        mock_rules = [Mock(spec=BonusRule)]

        result = calculate_sales_bonus(mock_db, mock_project, mock_rules)

        assert result is None


class TestCalculatePresaleBonus:
    """测试 calculate_presale_bonus 函数"""

    def test_calculate_presale_bonus_no_rules(self):
        """测试没有规则时返回 None"""
        mock_db = MagicMock(spec=Session)
        mock_project = Mock(spec=Project)

        result = calculate_presale_bonus(mock_db, mock_project, [])

        assert result is None

    def test_calculate_presale_bonus_no_tickets(self):
        """测试没有售前工单时返回 None"""
        mock_db = MagicMock(spec=Session)
        mock_project = Mock(spec=Project)
        mock_project.id = 1

        mock_db.query.return_value.filter.return_value.all.return_value = []

        mock_rule = Mock(spec=BonusRule)

        result = calculate_presale_bonus(mock_db, mock_project, [mock_rule])

        assert result is None

    def test_calculate_presale_bonus_from_opportunity(self):
        """测试基于商机计算售前奖金"""
        mock_db = MagicMock(spec=Session)

        mock_project = Mock(spec=Project)
        mock_project.id = 1
        mock_project.status = "ST01"
        mock_project.contract_amount = Decimal("0")

        mock_ticket = Mock(spec=PresaleSupportTicket)
        mock_ticket.id = 10
        mock_ticket.opportunity_id = 100
        mock_ticket.assignee_id = 1
        mock_ticket.status = "COMPLETED"

        mock_opportunity = Mock(spec=Opportunity)
        mock_opportunity.id = 100
        mock_opportunity.stage = "WON"
        mock_opportunity.est_amount = Decimal("200000")

        # First call returns tickets, second returns opportunity
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_ticket]
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_opportunity
        )

        mock_rule = Mock(spec=BonusRule)
        mock_rule.id = 5
        mock_rule.rule_name = "售前奖金规则"
        mock_rule.coefficient = Decimal("2")  # 2%

        result = calculate_presale_bonus(mock_db, mock_project, [mock_rule])

        assert result is not None
        assert result.project_id == 1
        # 200000 * 2% = 4000
        assert result.total_bonus_amount == Decimal("4000")
        assert result.allocation_detail["bonus_type"] == "PRESALE_BASED"
        assert result.allocation_detail["ticket_count"] == 1

    def test_calculate_presale_bonus_from_project(self):
        """测试基于项目金额计算售前奖金（无商机时）"""
        mock_db = MagicMock(spec=Session)

        mock_project = Mock(spec=Project)
        mock_project.id = 1
        mock_project.status = "ST02"
        mock_project.contract_amount = Decimal("150000")

        mock_ticket = Mock(spec=PresaleSupportTicket)
        mock_ticket.id = 10
        mock_ticket.opportunity_id = None  # 无商机
        mock_ticket.assignee_id = 2
        mock_ticket.status = "COMPLETED"

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_ticket]
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_rule = Mock(spec=BonusRule)
        mock_rule.id = 5
        mock_rule.rule_name = "售前奖金规则"
        mock_rule.coefficient = Decimal("3")  # 3%

        result = calculate_presale_bonus(mock_db, mock_project, [mock_rule])

        assert result is not None
        # 150000 * 3% = 4500
        assert result.total_bonus_amount == Decimal("4500")

    def test_calculate_presale_bonus_handles_exception(self):
        """测试异常处理"""
        mock_db = MagicMock(spec=Session)

        mock_project = Mock(spec=Project)
        mock_project.id = 1

        # Simulate error
        mock_db.query.side_effect = Exception("Query error")

        mock_rule = Mock(spec=BonusRule)

        result = calculate_presale_bonus(mock_db, mock_project, [mock_rule])

        assert result is None


class TestCalculateProjectBonus:
    """测试 calculate_project_bonus 函数"""

    def test_calculate_project_bonus_no_rules(self):
        """测试没有规则时返回 None"""
        mock_db = MagicMock(spec=Session)
        mock_project = Mock(spec=Project)

        result = calculate_project_bonus(mock_db, mock_project, [])

        assert result is None

    @patch("app.services.acceptance_bonus_service.ProjectEvaluationService")
    def test_calculate_project_bonus_successfully(self, mock_eval_service_class):
        """测试成功计算项目奖金"""
        mock_db = MagicMock(spec=Session)

        mock_project = Mock(spec=Project)
        mock_project.id = 1
        mock_project.contract_amount = Decimal("500000")

        # Setup evaluation service mock
        mock_eval_service = MagicMock()
        mock_eval_service.get_difficulty_bonus_coefficient.return_value = Decimal("1.2")
        mock_eval_service.get_new_tech_bonus_coefficient.return_value = Decimal("1.1")
        mock_eval_service_class.return_value = mock_eval_service

        # Members query
        mock_member = Mock(spec=ProjectMember)
        mock_member.id = 1
        mock_member.is_active = True

        # Contributions query mock
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [mock_member],  # members
            [],  # contributions
        ]

        mock_rule = Mock(spec=BonusRule)
        mock_rule.id = 5
        mock_rule.rule_name = "项目奖金规则"
        mock_rule.coefficient = Decimal("10")  # 10%

        result = calculate_project_bonus(mock_db, mock_project, [mock_rule])

        assert result is not None
        assert result.project_id == 1
        # 500000 * 10% * 1.2 (difficulty coefficient) = 60000
        assert result.total_bonus_amount == Decimal("60000")
        assert result.allocation_detail["bonus_type"] == "PROJECT_BASED"
        assert result.allocation_detail["difficulty_coefficient"] == 1.2
        assert result.allocation_detail["final_coefficient"] == 1.2
        assert result.allocation_detail["member_count"] == 1

    @patch("app.services.acceptance_bonus_service.ProjectEvaluationService")
    def test_calculate_project_bonus_zero_amount(self, mock_eval_service_class):
        """测试项目金额为0时返回 None"""
        mock_db = MagicMock(spec=Session)

        mock_project = Mock(spec=Project)
        mock_project.id = 1
        mock_project.contract_amount = Decimal("0")

        mock_eval_service = MagicMock()
        mock_eval_service.get_difficulty_bonus_coefficient.return_value = Decimal("1.0")
        mock_eval_service.get_new_tech_bonus_coefficient.return_value = Decimal("1.0")
        mock_eval_service_class.return_value = mock_eval_service

        mock_rule = Mock(spec=BonusRule)
        mock_rule.id = 5
        mock_rule.coefficient = Decimal("10")

        result = calculate_project_bonus(mock_db, mock_project, [mock_rule])

        assert result is None

    @patch("app.services.acceptance_bonus_service.ProjectEvaluationService")
    def test_calculate_project_bonus_with_new_tech_coefficient(
        self, mock_eval_service_class
    ):
        """测试使用新技术系数计算奖金"""
        mock_db = MagicMock(spec=Session)

        mock_project = Mock(spec=Project)
        mock_project.id = 1
        mock_project.contract_amount = Decimal("100000")

        # New tech coefficient is higher than difficulty
        mock_eval_service = MagicMock()
        mock_eval_service.get_difficulty_bonus_coefficient.return_value = Decimal("1.1")
        mock_eval_service.get_new_tech_bonus_coefficient.return_value = Decimal("1.5")
        mock_eval_service_class.return_value = mock_eval_service

        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [],  # members
            [],  # contributions
        ]

        mock_rule = Mock(spec=BonusRule)
        mock_rule.id = 5
        mock_rule.coefficient = Decimal("5")

        result = calculate_project_bonus(mock_db, mock_project, [mock_rule])

        assert result is not None
        # 100000 * 5% * 1.5 = 7500
        assert result.total_bonus_amount == Decimal("7500")
        assert result.allocation_detail["final_coefficient"] == 1.5

    def test_calculate_project_bonus_handles_exception(self):
        """测试异常处理"""
        mock_db = MagicMock(spec=Session)

        mock_project = Mock(spec=Project)
        mock_project.id = 1

        # Simulate error
        mock_db.query.side_effect = Exception("Database error")

        mock_rule = Mock(spec=BonusRule)

        result = calculate_project_bonus(mock_db, mock_project, [mock_rule])

        assert result is None


class TestIntegration:
    """集成测试"""

    def test_get_and_calculate_sales_bonus(self):
        """测试获取规则并计算销售奖金的完整流程"""
        mock_db = MagicMock(spec=Session)

        # Setup rules
        mock_rule = Mock(spec=BonusRule)
        mock_rule.id = 1
        mock_rule.rule_name = "销售奖金"
        mock_rule.bonus_type = "SALES_BASED"
        mock_rule.is_active = True
        mock_rule.coefficient = Decimal("5")
        mock_rule.trigger_condition = {}

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_rule]

        # Get active rules
        rules = get_active_rules(mock_db, "SALES_BASED")
        assert len(rules) == 1

        # Setup project and contract
        mock_project = Mock(spec=Project)
        mock_project.id = 1
        mock_project.contract_no = "CT-001"

        mock_contract = Mock(spec=Contract)
        mock_contract.id = 10
        mock_contract.contract_amount = Decimal("200000")

        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_contract
        )

        # Calculate bonus
        result = calculate_sales_bonus(mock_db, mock_project, rules)

        assert result is not None
        assert result.total_bonus_amount == Decimal("10000")  # 200000 * 5%

    @patch("app.services.acceptance_bonus_service.ProjectEvaluationService")
    def test_multiple_bonus_types(self, mock_eval_service_class):
        """测试计算多种类型奖金"""
        mock_db = MagicMock(spec=Session)

        mock_project = Mock(spec=Project)
        mock_project.id = 1
        mock_project.contract_no = "CT-001"
        mock_project.contract_amount = Decimal("100000")
        mock_project.status = "ST01"

        # Mock evaluation service
        mock_eval_service = MagicMock()
        mock_eval_service.get_difficulty_bonus_coefficient.return_value = Decimal("1.0")
        mock_eval_service.get_new_tech_bonus_coefficient.return_value = Decimal("1.0")
        mock_eval_service_class.return_value = mock_eval_service

        # Sales bonus
        mock_contract = Mock(spec=Contract)
        mock_contract.id = 10
        mock_contract.contract_amount = Decimal("100000")

        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_contract
        )

        sales_rule = Mock(spec=BonusRule)
        sales_rule.id = 1
        sales_rule.coefficient = Decimal("5")
        sales_rule.trigger_condition = {}

        sales_bonus = calculate_sales_bonus(mock_db, mock_project, [sales_rule])
        assert sales_bonus.total_bonus_amount == Decimal("5000")

        # Project bonus
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [],  # members
            [],  # contributions
        ]

        project_rule = Mock(spec=BonusRule)
        project_rule.id = 2
        project_rule.coefficient = Decimal("10")

        project_bonus = calculate_project_bonus(mock_db, mock_project, [project_rule])
        assert project_bonus.total_bonus_amount == Decimal("10000")
