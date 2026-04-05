# -*- coding: utf-8 -*-
"""
Schema 模型测试
"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from pydantic import ValidationError

from app.schemas.bonus import (
    BonusRuleBase,
    BonusRuleCreate,
    BonusRuleUpdate,
    BonusRuleResponse,
    BonusCalculationBase,
    BonusCalculationCreate,
    BonusCalculationResponse,
)
from app.schemas.common import PageParams, PaginatedResponse



class TestBonusRuleSchemas:
    """奖金规则 Schema 测试"""

    def test_bonus_rule_base_valid(self):
        """测试奖金规则基础模型 - 有效数据"""
        data = {
            "rule_code": "BR001",
            "rule_name": "销售业绩奖金",
            "bonus_type": "PERFORMANCE",
            "calculation_formula": "销售额 * 5%",
            "base_amount": Decimal("1000.00"),
            "coefficient": Decimal("1.5"),
            "is_active": True,
            "priority": 1,
            "require_approval": True,
        }
        rule = BonusRuleBase(**data)
        assert rule.rule_code == "BR001"
        assert rule.rule_name == "销售业绩奖金"
        assert rule.bonus_type == "PERFORMANCE"

    def test_bonus_rule_base_optional_fields(self):
        """测试奖金规则基础模型 - 可选字段"""
        data = {
            "rule_code": "BR002",
            "rule_name": "项目奖金",
            "bonus_type": "PROJECT",
        }
        rule = BonusRuleBase(**data)
        assert rule.rule_code == "BR002"
        assert rule.calculation_formula is None
        assert rule.base_amount is None

    def test_bonus_rule_create(self):
        """测试创建奖金规则"""
        data = {
            "rule_code": "BR003",
            "rule_name": "里程碑奖金",
            "bonus_type": "MILESTONE",
            "trigger_condition": {"milestone_type": "FAT", "status": "COMPLETED"},
            "apply_to_roles": ["sales", "engineer"],
        }
        rule = BonusRuleCreate(**data)
        assert rule.rule_code == "BR003"
        assert rule.trigger_condition == {"milestone_type": "FAT", "status": "COMPLETED"}

    def test_bonus_rule_update(self):
        """测试更新奖金规则"""
        data = {
            "rule_name": "更新后的奖金规则",
            "bonus_type": "PROJECT",
            "is_active": False,
        }
        update = BonusRuleUpdate(**data)
        assert update.rule_name == "更新后的奖金规则"
        assert update.is_active is False


class TestBonusCalculationSchemas:
    """奖金计算 Schema 测试"""

    def test_bonus_calculation_base(self):
        """测试奖金计算基础模型"""
        data = {
            "rule_id": 1,
            "user_id": 100,
            "calculated_amount": Decimal("5000.00"),
            "calculation_detail": {"sales": 100000, "rate": 0.05},
        }
        calc = BonusCalculationBase(**data)
        assert calc.rule_id == 1
        assert calc.user_id == 100
        assert calc.calculated_amount == Decimal("5000.00")

    def test_bonus_calculation_with_optional(self):
        """测试奖金计算 - 包含可选字段"""
        data = {
            "rule_id": 2,
            "period_id": 1,
            "project_id": 10,
            "milestone_id": 5,
            "user_id": 101,
            "performance_result_id": 3,
            "calculated_amount": Decimal("3000.00"),
        }
        calc = BonusCalculationBase(**data)
        assert calc.period_id == 1
        assert calc.project_id == 10
        assert calc.milestone_id == 5

    def test_bonus_calculation_create(self):
        """测试创建奖金计算"""
        data = {
            "rule_id": 1,
            "user_id": 100,
            "calculated_amount": Decimal("2000.00"),
        }
        calc = BonusCalculationCreate(**data)
        assert calc.calculated_amount == Decimal("2000.00")


class TestCommonSchemas:
    """通用 Schema 测试"""

    def test_page_params_default(self):
        """测试分页参数默认值"""
        params = PageParams()
        assert params.page == 1
        assert params.page_size == 20

    def test_page_params_custom(self):
        """测试分页参数自定义"""
        params = PageParams(page=3, page_size=50)
        assert params.page == 3
        assert params.page_size == 50

    def test_paginated_response(self):
        """测试分页响应"""
        data = {"items": [1, 2, 3], "total": 100, "page": 1, "page_size": 20}
        response = PaginatedResponse(**data)
        assert response.items == [1, 2, 3]
        assert response.total == 100
        assert response.page == 1


class TestSchemaValidation:
    """Schema 验证测试"""

    def test_bonus_rule_required_fields(self):
        """测试必填字段验证"""
        with pytest.raises(ValidationError):
            BonusRuleCreate()

    def test_bonus_calculation_required_fields(self):
        """测试必填字段验证"""
        with pytest.raises(ValidationError):
            BonusCalculationCreate()

    def test_decimal_precision(self):
        """测试小数精度"""
        data = {
            "rule_code": "BR004",
            "rule_name": "测试精度",
            "bonus_type": "PERFORMANCE",
            "base_amount": Decimal("12345678.90"),
            "coefficient": Decimal("1.25"),
        }
        rule = BonusRuleBase(**data)
        assert rule.base_amount == Decimal("12345678.90")
        assert rule.coefficient == Decimal("1.25")

    def test_date_field(self):
        """测试日期字段"""
        data = {
            "rule_code": "BR005",
            "rule_name": "日期测试",
            "bonus_type": "PROJECT",
            "effective_start_date": date(2025, 1, 1),
            "effective_end_date": date(2025, 12, 31),
        }
        rule = BonusRuleBase(**data)
        assert rule.effective_start_date == date(2025, 1, 1)
        assert rule.effective_end_date == date(2025, 12, 31)

    def test_list_fields(self):
        """测试列表字段"""
        data = {
            "rule_code": "BR006",
            "rule_name": "列表测试",
            "bonus_type": "PERFORMANCE",
            "apply_to_roles": ["manager", "engineer", "sales"],
            "apply_to_depts": [1, 2, 3],
            "apply_to_projects": ["PROJECT_A", "PROJECT_B"],
        }
        rule = BonusRuleBase(**data)
        assert len(rule.apply_to_roles) == 3
        assert len(rule.apply_to_depts) == 3
        assert "PROJECT_A" in rule.apply_to_projects