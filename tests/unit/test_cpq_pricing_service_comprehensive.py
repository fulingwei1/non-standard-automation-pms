# -*- coding: utf-8 -*-
"""
CpqPricingService 综合单元测试

测试覆盖:
- preview_price: 预览价格计算
- _resolve_rule_set: 解析规则集
- _calculate_adjustment: 计算价格调整
- _evaluate_approvals: 评估审批要求
- _calculate_confidence: 计算置信度
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestResolveRuleSet:
    """测试 _resolve_rule_set 方法"""

    def test_returns_rule_set_by_id(self):
        """测试通过ID返回规则集"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        mock_rule_set = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_rule_set

        service = CpqPricingService(mock_db)

        result = service._resolve_rule_set(rule_set_id=1, template_version_id=None)

        assert result == mock_rule_set

    def test_returns_rule_set_from_template_version(self):
        """测试从模板版本返回规则集"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        mock_version = MagicMock()
        mock_version.rule_set_id = 5
        mock_rule_set = MagicMock()

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = mock_version
            else:
                result.first.return_value = mock_rule_set
            return result

        mock_db.query.return_value.filter = filter_side_effect

        service = CpqPricingService(mock_db)

        result = service._resolve_rule_set(rule_set_id=None, template_version_id=1)

        assert result == mock_rule_set

    def test_returns_none_when_no_ids_provided(self):
        """测试无ID时返回None"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        service = CpqPricingService(mock_db)

        result = service._resolve_rule_set(rule_set_id=None, template_version_id=None)

        assert result is None

    def test_returns_none_when_version_has_no_rule_set(self):
        """测试版本无规则集时返回None"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        mock_version = MagicMock()
        mock_version.rule_set_id = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_version

        service = CpqPricingService(mock_db)

        result = service._resolve_rule_set(rule_set_id=None, template_version_id=1)

        assert result is None


class TestCalculateAdjustment:
    """测试 _calculate_adjustment 方法"""

    def test_returns_zero_when_no_pricing_matrix(self):
        """测试无定价矩阵时返回0"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        service = CpqPricingService(mock_db)

        delta, reason = service._calculate_adjustment("key", "value", {})

        assert delta == Decimal("0")
        assert reason is None

    def test_returns_zero_when_key_not_in_matrix(self):
        """测试键不在矩阵中时返回0"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        service = CpqPricingService(mock_db)

        pricing_matrix = {"other_key": 100}

        delta, reason = service._calculate_adjustment("key", "value", pricing_matrix)

        assert delta == Decimal("0")

    def test_handles_numeric_rule(self):
        """测试处理数值型规则"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        service = CpqPricingService(mock_db)

        pricing_matrix = {"quantity": 500}

        delta, reason = service._calculate_adjustment("quantity", 10, pricing_matrix)

        assert delta == Decimal("500")

    def test_handles_dict_rule_with_value_match(self):
        """测试处理字典规则的值匹配"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        service = CpqPricingService(mock_db)

        pricing_matrix = {
            "size": {
                "small": 100,
                "medium": 200,
                "large": 300
            }
        }

        delta, reason = service._calculate_adjustment("size", "medium", pricing_matrix)

        assert delta == Decimal("200")

    def test_handles_dict_rule_with_object_value(self):
        """测试处理字典规则的对象值"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        service = CpqPricingService(mock_db)

        pricing_matrix = {
            "feature": {
                "premium": {
                    "amount": 1000,
                    "reason": "高级功能加价"
                }
            }
        }

        delta, reason = service._calculate_adjustment("feature", "premium", pricing_matrix)

        assert delta == Decimal("1000")
        assert reason == "高级功能加价"

    def test_uses_default_when_value_not_found(self):
        """测试值未找到时使用默认值"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        service = CpqPricingService(mock_db)

        pricing_matrix = {
            "color": {
                "red": 50,
                "default": 25
            }
        }

        delta, reason = service._calculate_adjustment("color", "blue", pricing_matrix)

        assert delta == Decimal("25")
        assert reason == "默认调价"


class TestEvaluateApprovals:
    """测试 _evaluate_approvals 方法"""

    def test_returns_false_when_no_threshold(self):
        """测试无阈值时返回False"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        service = CpqPricingService(mock_db)

        requires, reason = service._evaluate_approvals(
            {},
            base_price=Decimal("1000"),
            final_price=Decimal("800"),
            manual_discount_pct=None
        )

        assert requires is False
        assert reason is None

    def test_requires_approval_when_discount_exceeds_threshold(self):
        """测试折扣超过阈值时需要审批"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        service = CpqPricingService(mock_db)

        threshold = {"max_discount_pct": 10}

        requires, reason = service._evaluate_approvals(
            threshold,
            base_price=Decimal("1000"),
            final_price=Decimal("800"),
            manual_discount_pct=Decimal("15")
        )

        assert requires is True
        assert "15%" in reason
        assert "10%" in reason

    def test_requires_approval_when_below_floor_price(self):
        """测试低于底价时需要审批"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        service = CpqPricingService(mock_db)

        threshold = {"min_floor_price": 900}

        requires, reason = service._evaluate_approvals(
            threshold,
            base_price=Decimal("1000"),
            final_price=Decimal("800"),
            manual_discount_pct=None
        )

        assert requires is True
        assert "底价" in reason

    def test_requires_approval_when_margin_below_target(self):
        """测试毛利率低于目标时需要审批"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        service = CpqPricingService(mock_db)

        threshold = {"min_margin_pct": 20}

        requires, reason = service._evaluate_approvals(
            threshold,
            base_price=Decimal("1000"),
            final_price=Decimal("1050"),  # 5% margin
            manual_discount_pct=None
        )

        assert requires is True
        assert "毛利率" in reason


class TestCalculateConfidence:
    """测试 _calculate_confidence 方法"""

    def test_returns_medium_when_no_schema(self):
        """测试无schema时返回MEDIUM"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        service = CpqPricingService(mock_db)

        result = service._calculate_confidence({}, {})

        assert result == "MEDIUM"

    def test_returns_high_when_no_required_keys(self):
        """测试无必填项时返回HIGH"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        service = CpqPricingService(mock_db)

        config_schema = {
            "option1": {"required": False},
            "option2": {}
        }

        result = service._calculate_confidence(config_schema, {})

        assert result == "HIGH"

    def test_returns_high_when_all_required_provided(self):
        """测试所有必填项都提供时返回HIGH"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        service = CpqPricingService(mock_db)

        config_schema = {
            "field1": {"required": True},
            "field2": {"required": True}
        }
        selections = {"field1": "a", "field2": "b"}

        result = service._calculate_confidence(config_schema, selections)

        assert result == "HIGH"

    def test_returns_medium_when_partial_required_provided(self):
        """测试部分必填项提供时返回MEDIUM"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        service = CpqPricingService(mock_db)

        config_schema = {
            "field1": {"required": True},
            "field2": {"required": True},
            "field3": {"required": True},
            "field4": {"required": True}
        }
        selections = {"field1": "a", "field2": "b"}  # 50%

        result = service._calculate_confidence(config_schema, selections)

        assert result == "MEDIUM"

    def test_returns_low_when_few_required_provided(self):
        """测试很少必填项提供时返回LOW"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        service = CpqPricingService(mock_db)

        config_schema = {
            "field1": {"required": True},
            "field2": {"required": True},
            "field3": {"required": True},
            "field4": {"required": True},
            "field5": {"required": True}
        }
        selections = {"field1": "a"}  # 20%

        result = service._calculate_confidence(config_schema, selections)

        assert result == "LOW"


class TestPreviewPrice:
    """测试 preview_price 方法"""

    def test_returns_base_price_when_no_selections(self):
        """测试无选择时返回基础价格"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        mock_rule_set = MagicMock()
        mock_rule_set.config_schema = {}
        mock_rule_set.pricing_matrix = {}
        mock_rule_set.approval_threshold = {}
        mock_rule_set.currency = "CNY"
        mock_rule_set.base_price = "1000"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_rule_set

        service = CpqPricingService(mock_db)

        result = service.preview_price(rule_set_id=1)

        assert result['base_price'] == Decimal("1000")
        assert result['final_price'] == Decimal("1000")
        assert result['adjustment_total'] == Decimal("0")
        assert result['currency'] == "CNY"

    def test_applies_selections_adjustments(self):
        """测试应用选择调整"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        mock_rule_set = MagicMock()
        mock_rule_set.config_schema = {}
        mock_rule_set.pricing_matrix = {"size": {"large": 500}}
        mock_rule_set.approval_threshold = {}
        mock_rule_set.currency = "CNY"
        mock_rule_set.base_price = "1000"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_rule_set

        service = CpqPricingService(mock_db)

        result = service.preview_price(
            rule_set_id=1,
            selections={"size": "large"}
        )

        assert result['final_price'] == Decimal("1500")
        assert result['adjustment_total'] == Decimal("500")
        assert len(result['adjustments']) == 1

    def test_applies_manual_markup(self):
        """测试应用人工加成"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        mock_rule_set = MagicMock()
        mock_rule_set.config_schema = {}
        mock_rule_set.pricing_matrix = {}
        mock_rule_set.approval_threshold = {}
        mock_rule_set.currency = "CNY"
        mock_rule_set.base_price = "1000"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_rule_set

        service = CpqPricingService(mock_db)

        result = service.preview_price(
            rule_set_id=1,
            manual_markup_pct=Decimal("10")
        )

        assert result['final_price'] == Decimal("1100")  # 1000 + 10%

    def test_applies_manual_discount(self):
        """测试应用人工折扣"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        mock_rule_set = MagicMock()
        mock_rule_set.config_schema = {}
        mock_rule_set.pricing_matrix = {}
        mock_rule_set.approval_threshold = {}
        mock_rule_set.currency = "CNY"
        mock_rule_set.base_price = "1000"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_rule_set

        service = CpqPricingService(mock_db)

        result = service.preview_price(
            rule_set_id=1,
            manual_discount_pct=Decimal("20")
        )

        assert result['final_price'] == Decimal("800")  # 1000 - 20%

    def test_includes_approval_info(self):
        """测试包含审批信息"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()
        mock_rule_set = MagicMock()
        mock_rule_set.config_schema = {}
        mock_rule_set.pricing_matrix = {}
        mock_rule_set.approval_threshold = {"max_discount_pct": 10}
        mock_rule_set.currency = "CNY"
        mock_rule_set.base_price = "1000"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_rule_set

        service = CpqPricingService(mock_db)

        result = service.preview_price(
            rule_set_id=1,
            manual_discount_pct=Decimal("15")
        )

        assert result['requires_approval'] is True
        assert result['approval_reason'] is not None

    def test_uses_template_version_when_no_rule_set(self):
        """测试无规则集时使用模板版本"""
        from app.services.cpq_pricing_service import CpqPricingService

        mock_db = MagicMock()

        mock_version = MagicMock()
        mock_version.rule_set_id = None
        mock_version.config_schema = {}
        mock_version.pricing_rules = {"base_price": 2000}

        call_count = [0]
        def filter_side_effect(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.first.return_value = None  # No rule set
            else:
                result.first.return_value = mock_version
            return result

        mock_db.query.return_value.filter = filter_side_effect

        service = CpqPricingService(mock_db)

        result = service.preview_price(template_version_id=1)

        assert result['base_price'] == Decimal("2000")
