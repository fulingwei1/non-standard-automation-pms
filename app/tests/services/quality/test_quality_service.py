# -*- coding: utf-8 -*-
"""
质量管理服务测试
目标覆盖率: 60%+
测试用例数: 8个
"""
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from app.services.quality_service import QualityService


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = Mock()
    return db


@pytest.fixture
def sample_inspection_data():
    """创建示例质检数据"""
    from app.schemas.production.quality import QualityInspectionCreate

    return QualityInspectionCreate(
        work_order_id=1,
        material_id=1,
        batch_no="BATCH001",
        inspection_type="IPQC",
        inspection_date=datetime.now(),
        inspector_id=1,
        inspection_qty=100,
        qualified_qty=95,
        defect_qty=5,
        inspection_result="PASS",
        notes="正常检验",
    )


@pytest.fixture
def sample_inspection():
    """创建示例质检记录"""
    inspection = Mock()
    inspection.id = 1
    inspection.inspection_no = "QI202404010001"
    inspection.inspection_date = datetime(2024, 4, 1)
    inspection.inspection_qty = 100
    inspection.qualified_qty = 95
    inspection.defect_qty = 5
    inspection.defect_rate = Decimal("5.00")
    inspection.inspection_type = "IPQC"
    inspection.material_id = 1
    inspection.work_order_id = 1
    return inspection


class TestQualityService:
    """质量管理服务测试类"""

    def test_create_inspection_success(self, mock_db, sample_inspection_data):
        """测试创建质检记录成功"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.order_by.return_value.first.return_value = None

        with patch("app.services.quality_service.save_obj") as mock_save:
            with patch("app.services.quality_service.QualityService._check_quality_alerts"):
                result = QualityService.create_inspection(
                    mock_db, sample_inspection_data, current_user_id=1
                )
                assert result is not None
                mock_save.assert_called_once()

    def test_create_inspection_calculate_defect_rate(self, mock_db, sample_inspection_data):
        """测试创建质检记录时不良率计算"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.order_by.return_value.first.return_value = None

        with patch("app.services.quality_service.save_obj") as mock_save:
            with patch("app.services.quality_service.QualityService._check_quality_alerts"):
                result = QualityService.create_inspection(
                    mock_db, sample_inspection_data, current_user_id=1
                )
                saved_obj = mock_save.call_args[0][1]
                assert saved_obj.defect_rate == Decimal("5.00")

    def test_generate_inspection_no_first_record(self, mock_db):
        """测试生成质检单号-首条记录"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.order_by.return_value.first.return_value = None

        result = QualityService._generate_inspection_no(mock_db)
        today = datetime.now().strftime("%Y%m%d")
        assert result == f"QI{today}0001"

    def test_generate_inspection_no_existing_records(self, mock_db):
        """测试生成质检单号-已有记录"""
        today = datetime.now().strftime("%Y%m%d")
        mock_last = Mock()
        mock_last.inspection_no = f"QI{today}0005"

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.order_by.return_value.first.return_value = mock_last

        result = QualityService._generate_inspection_no(mock_db)
        assert result == f"QI{today}0006"

    def test_get_quality_trend_basic(self, mock_db, sample_inspection):
        """测试质量趋势分析-基本功能"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 4, 30)

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.all.return_value = [sample_inspection]

        result = QualityService.get_quality_trend(
            mock_db, start_date, end_date, group_by="day"
        )

        assert "trend_data" in result
        assert "avg_defect_rate" in result
        assert "total_inspections" in result

    def test_get_quality_trend_with_material_filter(self, mock_db, sample_inspection):
        """测试质量趋势分析-物料筛选"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 4, 30)
        material_id = 1

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.all.return_value = [sample_inspection]

        result = QualityService.get_quality_trend(
            mock_db, start_date, end_date, material_id=material_id, group_by="day"
        )

        assert result is not None
        assert result["total_inspections"] == 1


class TestReworkOrder:
    """返工单测试类"""

    def test_generate_rework_order_no_first(self, mock_db):
        """测试生成返工单号-首条"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.order_by.return_value.first.return_value = None

        result = QualityService._generate_rework_order_no(mock_db)
        today = datetime.now().strftime("%Y%m%d")
        assert result == f"RW{today}0001"

    def test_generate_rework_order_no_existing(self, mock_db):
        """测试生成返工单号-已有"""
        today = datetime.now().strftime("%Y%m%d")
        mock_last = Mock()
        mock_last.rework_order_no = f"RW{today}0003"

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.order_by.return_value.first.return_value = mock_last

        result = QualityService._generate_rework_order_no(mock_db)
        assert result == f"RW{today}0004"