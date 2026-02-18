# -*- coding: utf-8 -*-
"""第十三批 - 交期校验服务 单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta

try:
    from app.services.delivery_validation_service import DeliveryValidationService
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


@pytest.fixture
def db():
    return MagicMock()


class TestGetMaterialLeadTime:
    def test_by_material_id_found(self, db):
        """通过material_id找到交期"""
        mock_material = MagicMock()
        mock_material.lead_time_days = 15
        mock_material.material_name = "螺丝"
        db.query.return_value.filter.return_value.first.return_value = mock_material

        days, note = DeliveryValidationService.get_material_lead_time(
            db, material_id=1
        )
        assert days == 15
        assert "螺丝" in note

    def test_by_material_code_found(self, db):
        """通过material_code找到交期"""
        mock_material = MagicMock()
        mock_material.lead_time_days = 10
        mock_material.material_name = "轴承"
        db.query.return_value.filter.return_value.first.return_value = mock_material

        days, note = DeliveryValidationService.get_material_lead_time(
            db, material_code="M001"
        )
        assert days == 10

    def test_fallback_to_type_default(self, db):
        """物料不存在时使用类型默认值"""
        db.query.return_value.filter.return_value.first.return_value = None

        days, note = DeliveryValidationService.get_material_lead_time(
            db, material_type="标准件"
        )
        assert days == 7
        assert "标准件" in note

    def test_fallback_unknown_type_default(self, db):
        """未知类型时使用默认14天"""
        db.query.return_value.filter.return_value.first.return_value = None

        days, note = DeliveryValidationService.get_material_lead_time(
            db, material_type="未知类型"
        )
        assert days == 14

    def test_default_stage_durations_defined(self):
        """默认阶段工期已定义"""
        assert 'S1' in DeliveryValidationService.DEFAULT_STAGE_DURATION
        assert 'S4' in DeliveryValidationService.DEFAULT_STAGE_DURATION
        assert DeliveryValidationService.DEFAULT_STAGE_DURATION['S4'] == 30

    def test_default_material_lead_times_defined(self):
        """默认物料交期已定义"""
        assert '标准件' in DeliveryValidationService.DEFAULT_MATERIAL_LEAD_TIME
        assert '定制件' in DeliveryValidationService.DEFAULT_MATERIAL_LEAD_TIME
        assert DeliveryValidationService.DEFAULT_MATERIAL_LEAD_TIME['定制件'] == 30

    def test_material_id_no_lead_time_falls_through(self, db):
        """物料存在但无lead_time_days时继续查找"""
        mock_material = MagicMock()
        mock_material.lead_time_days = None
        db.query.return_value.filter.return_value.first.return_value = mock_material

        days, note = DeliveryValidationService.get_material_lead_time(
            db, material_id=1, material_type="机械件"
        )
        # 应该回退到类型默认
        assert days == 14
