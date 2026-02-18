# -*- coding: utf-8 -*-
"""第五批：quality_service.py 单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime, date

try:
    from app.services.quality_service import QualityService
    HAS_MODULE = True
except ImportError:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="quality_service not importable")


def make_db():
    return MagicMock()


class TestGenerateInspectionNo:
    def test_returns_string(self):
        db = make_db()
        db.query.return_value.filter.return_value.count.return_value = 0
        no = QualityService._generate_inspection_no(db)
        assert isinstance(no, str)
        assert len(no) > 0


class TestCreateInspection:
    def test_defect_rate_calculation(self):
        db = make_db()
        db.query.return_value.filter.return_value.count.return_value = 5
        # 模拟 alert rules 查询返回空
        db.query.return_value.filter.return_value.all.return_value = []

        inspection_data = MagicMock()
        inspection_data.inspection_qty = 100
        inspection_data.defect_qty = 5
        inspection_data.model_dump.return_value = {
            "inspection_qty": 100,
            "defect_qty": 5,
        }

        with patch("app.services.quality_service.save_obj") as mock_save:
            inspection = QualityService.create_inspection(db, inspection_data, current_user_id=1)
            assert mock_save.called

    def test_zero_inspection_qty(self):
        db = make_db()
        db.query.return_value.filter.return_value.count.return_value = 0
        db.query.return_value.filter.return_value.all.return_value = []

        inspection_data = MagicMock()
        inspection_data.inspection_qty = 0
        inspection_data.defect_qty = 0
        inspection_data.model_dump.return_value = {
            "inspection_qty": 0,
            "defect_qty": 0,
        }

        with patch("app.services.quality_service.save_obj"):
            # 不应抛出除以零错误
            inspection = QualityService.create_inspection(db, inspection_data, current_user_id=1)


class TestCalculateMovingAverage:
    def test_normal(self):
        data = [10.0, 20.0, 30.0, 40.0, 50.0]
        result = QualityService._calculate_moving_average(data, window=3)
        assert result == pytest.approx(40.0)

    def test_insufficient_data(self):
        data = [10.0, 20.0]
        result = QualityService._calculate_moving_average(data, window=3)
        assert result is None

    def test_empty(self):
        result = QualityService._calculate_moving_average([], window=3)
        assert result is None


class TestParetoAnalysis:
    def test_returns_dict(self):
        db = make_db()
        stats = []
        for name, cnt in [("裂纹", 50), ("气孔", 30), ("变形", 20)]:
            s = MagicMock()
            s.defect_type = name
            s.total_qty = cnt
            stats.append(s)
        # Mock the query chain for group_by/order_by/limit/all
        q = MagicMock()
        q.filter.return_value = q
        q.group_by.return_value = q
        q.order_by.return_value = q
        q.limit.return_value = q
        q.all.return_value = stats
        db.query.return_value = q

        result = QualityService.pareto_analysis(
            db, start_date=datetime(2024, 1, 1), end_date=datetime(2024, 12, 31)
        )
        assert isinstance(result, dict)
        assert "data_points" in result

    def test_empty_data(self):
        db = make_db()
        q = MagicMock()
        q.filter.return_value = q
        q.group_by.return_value = q
        q.order_by.return_value = q
        q.limit.return_value = q
        q.all.return_value = []
        db.query.return_value = q

        result = QualityService.pareto_analysis(
            db, start_date=datetime(2024, 1, 1), end_date=datetime(2024, 12, 31)
        )
        assert result["data_points"] == []
        assert result["total_defects"] == 0


class TestGetQualityStatistics:
    def test_returns_dict(self):
        db = make_db()
        db.query.return_value.filter.return_value.count.return_value = 10
        db.query.return_value.filter.return_value.scalar.return_value = 5.0
        db.query.return_value.scalar.return_value = 100

        result = QualityService.get_quality_statistics(db)
        assert isinstance(result, dict)
