# -*- coding: utf-8 -*-
"""
DeliveryValidationService 综合单元测试

测试覆盖:
- get_material_lead_time: 获取物料交期
- get_max_material_lead_time: 获取报价单中最长物料交期
- estimate_project_cycle: 估算项目周期
- validate_delivery_date: 校验报价交期的合理性
- _get_suggestions: 生成优化建议
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestGetMaterialLeadTime:
    """测试 get_material_lead_time 方法"""

    def test_returns_lead_time_from_material_id(self):
        """测试通过物料ID获取交期"""
        from app.services.delivery_validation_service import DeliveryValidationService

        mock_db = MagicMock()
        mock_material = MagicMock()
        mock_material.material_name = "测试物料"
        mock_material.lead_time_days = 21

        mock_db.query.return_value.filter.return_value.first.return_value = mock_material

        days, remark = DeliveryValidationService.get_material_lead_time(
            mock_db, material_id=1
        )

        assert days == 21
        assert "物料档案" in remark

    def test_returns_lead_time_from_material_code(self):
        """测试通过物料编码获取交期"""
        from app.services.delivery_validation_service import DeliveryValidationService

        mock_db = MagicMock()
        mock_material = MagicMock()
        mock_material.material_name = "测试物料"
        mock_material.lead_time_days = 14

        # First query returns None (by id), second returns material (by code)
        mock_db.query.return_value.filter.return_value.first.side_effect = [None, mock_material]

        days, remark = DeliveryValidationService.get_material_lead_time(
            mock_db, material_code="MAT001"
        )

        assert days == 14

    def test_returns_default_by_material_type(self):
        """测试按物料类型返回默认值"""
        from app.services.delivery_validation_service import DeliveryValidationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        days, remark = DeliveryValidationService.get_material_lead_time(
            mock_db, material_type="标准件"
        )

        assert days == 7
        assert "默认值" in remark

    def test_returns_default_when_no_info(self):
        """测试无任何信息时返回默认值"""
        from app.services.delivery_validation_service import DeliveryValidationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        days, remark = DeliveryValidationService.get_material_lead_time(mock_db)

        assert days == 14
        assert "默认值14天" in remark

    def test_returns_correct_default_for_each_type(self):
        """测试各类型物料的默认交期"""
        from app.services.delivery_validation_service import DeliveryValidationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        test_cases = [
            ("标准件", 7),
            ("机械件", 14),
            ("电气件", 10),
            ("气动件", 7),
            ("外购件", 21),
            ("定制件", 30),
        ]

        for material_type, expected_days in test_cases:
            days, _ = DeliveryValidationService.get_material_lead_time(
                mock_db, material_type=material_type
            )
            assert days == expected_days, f"{material_type} 应该是 {expected_days} 天"


class TestGetMaxMaterialLeadTime:
    """测试 get_max_material_lead_time 方法"""

    def test_returns_max_lead_time(self):
        """测试返回最长交期"""
        from app.services.delivery_validation_service import DeliveryValidationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_item1 = MagicMock()
        mock_item1.id = 1
        mock_item1.item_name = "物料1"
        mock_item1.item_type = "标准件"  # 7天
        mock_item1.material_code = None
        mock_item1.quantity = 10
        mock_item1.is_critical = False

        mock_item2 = MagicMock()
        mock_item2.id = 2
        mock_item2.item_name = "物料2"
        mock_item2.item_type = "定制件"  # 30天
        mock_item2.material_code = None
        mock_item2.quantity = 5
        mock_item2.is_critical = False

        max_days, details = DeliveryValidationService.get_max_material_lead_time(
            mock_db, [mock_item1, mock_item2]
        )

        assert max_days == 30

    def test_prioritizes_critical_items(self):
        """测试优先考虑关键物料"""
        from app.services.delivery_validation_service import DeliveryValidationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_item1 = MagicMock()
        mock_item1.id = 1
        mock_item1.item_name = "普通物料"
        mock_item1.item_type = "定制件"  # 30天
        mock_item1.material_code = None
        mock_item1.quantity = 10
        mock_item1.is_critical = False

        mock_item2 = MagicMock()
        mock_item2.id = 2
        mock_item2.item_name = "关键物料"
        mock_item2.item_type = "标准件"  # 7天
        mock_item2.material_code = None
        mock_item2.quantity = 5
        mock_item2.is_critical = True

        max_days, details = DeliveryValidationService.get_max_material_lead_time(
            mock_db, [mock_item1, mock_item2]
        )

        # 关键物料优先，所以返回关键物料的7天
        assert max_days == 7

    def test_returns_zero_when_no_purchasable_items(self):
        """测试无需采购物料时返回零"""
        from app.services.delivery_validation_service import DeliveryValidationService

        mock_db = MagicMock()

        mock_item = MagicMock()
        mock_item.item_type = "服务"  # 不需要采购

        max_days, details = DeliveryValidationService.get_max_material_lead_time(
            mock_db, [mock_item]
        )

        assert max_days == 0
        assert details == []


class TestEstimateProjectCycle:
    """测试 estimate_project_cycle 方法"""

    def test_estimates_simple_project(self):
        """测试估算简单项目"""
        from app.services.delivery_validation_service import DeliveryValidationService

        mock_db = MagicMock()

        result = DeliveryValidationService.estimate_project_cycle(
            mock_db, complexity_level="SIMPLE"
        )

        assert result["estimated_total_days"] == 45
        assert result["complexity_level"] == "SIMPLE"

    def test_estimates_medium_project(self):
        """测试估算中等项目"""
        from app.services.delivery_validation_service import DeliveryValidationService

        mock_db = MagicMock()

        result = DeliveryValidationService.estimate_project_cycle(
            mock_db, complexity_level="MEDIUM"
        )

        assert result["estimated_total_days"] == 75

    def test_estimates_complex_project(self):
        """测试估算复杂项目"""
        from app.services.delivery_validation_service import DeliveryValidationService

        mock_db = MagicMock()

        result = DeliveryValidationService.estimate_project_cycle(
            mock_db, complexity_level="COMPLEX"
        )

        assert result["estimated_total_days"] == 105

    def test_applies_type_multiplier(self):
        """测试应用类型系数"""
        from app.services.delivery_validation_service import DeliveryValidationService

        mock_db = MagicMock()

        result = DeliveryValidationService.estimate_project_cycle(
            mock_db, project_type="线体类", complexity_level="MEDIUM"
        )

        # 75 * 1.3 = 97.5 -> 97
        assert result["estimated_total_days"] == 97

    def test_applies_amount_multiplier_high(self):
        """测试应用高金额系数"""
        from app.services.delivery_validation_service import DeliveryValidationService

        mock_db = MagicMock()

        result = DeliveryValidationService.estimate_project_cycle(
            mock_db, contract_amount=6000000, complexity_level="MEDIUM"
        )

        # 75 * 1.2 = 90
        assert result["estimated_total_days"] == 90

    def test_applies_amount_multiplier_low(self):
        """测试应用低金额系数"""
        from app.services.delivery_validation_service import DeliveryValidationService

        mock_db = MagicMock()

        result = DeliveryValidationService.estimate_project_cycle(
            mock_db, contract_amount=400000, complexity_level="MEDIUM"
        )

        # 75 * 0.85 = 63.75 -> 63
        assert result["estimated_total_days"] == 63

    def test_includes_stage_details(self):
        """测试包含阶段详情"""
        from app.services.delivery_validation_service import DeliveryValidationService

        mock_db = MagicMock()

        result = DeliveryValidationService.estimate_project_cycle(
            mock_db, complexity_level="MEDIUM"
        )

        assert "stage_details" in result
        assert len(result["stage_details"]) == 8  # S1-S8

    def test_includes_date_estimates(self):
        """测试包含日期估算"""
        from app.services.delivery_validation_service import DeliveryValidationService

        mock_db = MagicMock()

        result = DeliveryValidationService.estimate_project_cycle(
            mock_db, complexity_level="MEDIUM"
        )

        assert "estimated_start_date" in result
        assert "estimated_end_date" in result
        assert result["estimated_start_date"] == date.today().isoformat()


class TestValidateDeliveryDate:
    """测试 validate_delivery_date 方法"""

    def test_returns_error_when_no_lead_time(self):
        """测试无交期时返回错误"""
        from app.services.delivery_validation_service import DeliveryValidationService

        mock_db = MagicMock()
        mock_quote = MagicMock()
        mock_quote.opportunity = None

        mock_version = MagicMock()
        mock_version.lead_time_days = 0
        mock_version.total_price = Decimal("100000")

        result = DeliveryValidationService.validate_delivery_date(
            mock_db, mock_quote, mock_version, []
        )

        assert result["status"] == "ERROR"
        assert len(result["errors"]) > 0

    def test_returns_pass_for_valid_delivery(self):
        """测试有效交期返回通过"""
        from app.services.delivery_validation_service import DeliveryValidationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_quote = MagicMock()
        mock_quote.opportunity = None

        mock_version = MagicMock()
        mock_version.lead_time_days = 90
        mock_version.total_price = Decimal("100000")

        result = DeliveryValidationService.validate_delivery_date(
            mock_db, mock_quote, mock_version, []
        )

        assert result["status"] in ["PASS", "WARNING"]
        assert result["quoted_lead_time"] == 90

    def test_warns_when_shorter_than_material_lead_time(self):
        """测试短于物料交期时警告"""
        from app.services.delivery_validation_service import DeliveryValidationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_quote = MagicMock()
        mock_quote.opportunity = None

        mock_version = MagicMock()
        mock_version.lead_time_days = 20  # 短于定制件的30天
        mock_version.total_price = Decimal("100000")

        mock_item = MagicMock()
        mock_item.id = 1
        mock_item.item_name = "定制物料"
        mock_item.item_type = "定制件"  # 30天
        mock_item.material_code = None
        mock_item.quantity = 1
        mock_item.is_critical = False

        result = DeliveryValidationService.validate_delivery_date(
            mock_db, mock_quote, mock_version, [mock_item]
        )

        assert result["status"] == "WARNING"
        assert any("物料交期" in w["message"] for w in result["warnings"])

    def test_includes_suggestions(self):
        """测试包含建议"""
        from app.services.delivery_validation_service import DeliveryValidationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_quote = MagicMock()
        mock_quote.opportunity = None

        mock_version = MagicMock()
        mock_version.lead_time_days = 60
        mock_version.total_price = Decimal("100000")

        result = DeliveryValidationService.validate_delivery_date(
            mock_db, mock_quote, mock_version, []
        )

        assert "suggestions" in result
        assert len(result["suggestions"]) > 0


class TestGetSuggestions:
    """测试 _get_suggestions 方法"""

    def test_suggests_increase_when_shorter_than_material(self):
        """测试短于物料交期时建议增加"""
        from app.services.delivery_validation_service import DeliveryValidationService

        suggestions = DeliveryValidationService._get_suggestions(
            quoted_days=20,
            material_days=30,
            estimated_days=60
        )

        assert any("至少" in s for s in suggestions)

    def test_suggests_increase_when_shorter_than_estimated(self):
        """测试短于估算周期时建议增加"""
        from app.services.delivery_validation_service import DeliveryValidationService

        suggestions = DeliveryValidationService._get_suggestions(
            quoted_days=40,
            material_days=20,
            estimated_days=60
        )

        assert any("60" in s for s in suggestions)

    def test_suggests_range_when_no_quoted_days(self):
        """测试无报价交期时建议范围"""
        from app.services.delivery_validation_service import DeliveryValidationService

        suggestions = DeliveryValidationService._get_suggestions(
            quoted_days=None,
            material_days=30,
            estimated_days=60
        )

        assert any("建议交期" in s for s in suggestions)


class TestDefaultConstants:
    """测试默认常量"""

    def test_default_stage_duration_defined(self):
        """测试默认阶段工期已定义"""
        from app.services.delivery_validation_service import DeliveryValidationService

        assert len(DeliveryValidationService.DEFAULT_STAGE_DURATION) == 9
        assert DeliveryValidationService.DEFAULT_STAGE_DURATION["S1"] == 7
        assert DeliveryValidationService.DEFAULT_STAGE_DURATION["S4"] == 30

    def test_default_material_lead_time_defined(self):
        """测试默认物料交期已定义"""
        from app.services.delivery_validation_service import DeliveryValidationService

        assert len(DeliveryValidationService.DEFAULT_MATERIAL_LEAD_TIME) == 6
        assert DeliveryValidationService.DEFAULT_MATERIAL_LEAD_TIME["定制件"] == 30


class TestSingleton:
    """测试单例"""

    def test_singleton_exists(self):
        """测试单例存在"""
        from app.services.delivery_validation_service import delivery_validation_service

        assert delivery_validation_service is not None

    def test_singleton_is_instance(self):
        """测试单例是正确的实例"""
        from app.services.delivery_validation_service import (
            DeliveryValidationService,
            delivery_validation_service,
        )

        assert isinstance(delivery_validation_service, DeliveryValidationService)
