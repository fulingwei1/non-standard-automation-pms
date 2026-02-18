# -*- coding: utf-8 -*-
"""质量管理服务单元测试 (QualityService)"""
import pytest
import statistics
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, call


def _make_db():
    return MagicMock()


def _make_inspection(**kw):
    insp = MagicMock()
    defaults = dict(
        id=1,
        inspection_no="QI202401010001",
        inspection_date=datetime(2024, 1, 15),
        inspection_qty=100,
        qualified_qty=95,
        defect_qty=5,
        defect_rate=Decimal("5.0"),
        defect_type="尺寸偏差",
        batch_no="BATCH-001",
        material_id=10,
        inspection_type="进货检验",
        measured_value=Decimal("10.5"),
        spec_upper_limit=Decimal("11.0"),
        spec_lower_limit=Decimal("10.0"),
        status="PASS",
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(insp, k, v)
    return insp


class TestCalculateSPCControlLimits:
    def test_insufficient_samples_raises_error(self):
        from app.services.quality_service import QualityService
        db = _make_db()
        # 返回少于5个样本
        db.query.return_value.filter.return_value.all.return_value = [
            _make_inspection(measured_value=Decimal("10.1")),
            _make_inspection(measured_value=Decimal("10.2")),
        ]
        with pytest.raises(ValueError, match="样本数量不足"):
            QualityService.calculate_spc_control_limits(
                db=db,
                material_id=10,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 12, 31)
            )

    def test_spc_with_enough_samples(self):
        from app.services.quality_service import QualityService
        db = _make_db()
        # 返回6个样本
        inspections = [
            _make_inspection(measured_value=Decimal(str(v)))
            for v in [10.0, 10.1, 10.2, 10.3, 10.4, 10.5]
        ]
        db.query.return_value.filter.return_value.all.return_value = inspections
        result = QualityService.calculate_spc_control_limits(
            db=db,
            material_id=10,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )
        assert "control_limits" in result
        assert "data_points" in result
        assert result["control_limits"].ucl > result["control_limits"].cl
        assert result["control_limits"].cl > result["control_limits"].lcl


class TestGetQualityTrend:
    def test_empty_inspections_returns_zero_stats(self):
        from app.services.quality_service import QualityService
        db = _make_db()
        db.query.return_value.filter.return_value.all.return_value = []
        start = datetime(2024, 1, 1)
        end = datetime(2024, 3, 31)
        result = QualityService.get_quality_trend(db, start, end)
        assert result["total_inspections"] == 0
        assert result["total_qty"] == 0
        assert result["avg_defect_rate"] == 0

    def test_with_inspections_calculates_avg_defect_rate(self):
        from app.services.quality_service import QualityService
        db = _make_db()
        insp1 = _make_inspection(inspection_qty=100, defect_qty=5)
        insp2 = _make_inspection(inspection_qty=200, defect_qty=10)
        db.query.return_value.filter.return_value.all.return_value = [insp1, insp2]
        start = datetime(2024, 1, 1)
        end = datetime(2024, 3, 31)
        result = QualityService.get_quality_trend(db, start, end)
        assert result["total_qty"] == 300
        assert result["total_defects"] == 15
        assert result["total_inspections"] == 2
        # avg defect rate = 15/300 * 100 = 5%
        assert abs(result["avg_defect_rate"] - 5.0) < 0.01


class TestGetQualityStatistics:
    def test_returns_statistics_dict_structure(self):
        from app.services.quality_service import QualityService
        db = _make_db()
        # 模拟 inspections 查询
        insp1 = _make_inspection(inspection_qty=100, qualified_qty=95, defect_qty=5)
        insp2 = _make_inspection(inspection_qty=200, qualified_qty=190, defect_qty=10)
        # 主查询返回检验记录
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value.all.return_value = [insp1, insp2]
        query_mock.filter.return_value.count.return_value = 0
        query_mock.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = QualityService.get_quality_statistics(db)
        assert "total_inspections" in result
        assert "overall_defect_rate" in result
        assert "pass_rate" in result
        assert "top_defect_types" in result

    def test_empty_data_returns_zero_rates(self):
        from app.services.quality_service import QualityService
        db = _make_db()
        query_mock = MagicMock()
        db.query.return_value = query_mock
        query_mock.filter.return_value.all.return_value = []
        query_mock.filter.return_value.count.return_value = 0
        query_mock.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = QualityService.get_quality_statistics(db)
        assert result["overall_defect_rate"] == 0
        assert result["pass_rate"] == 0


class TestBatchTracing:
    def test_no_records_raises_value_error(self):
        from app.services.quality_service import QualityService
        db = _make_db()
        db.query.return_value.filter.return_value.all.return_value = []
        with pytest.raises(ValueError, match="未找到批次号"):
            QualityService.batch_tracing(db, "BATCH-NOTEXIST")

    def test_existing_batch_returns_tracing_dict(self):
        from app.services.quality_service import QualityService
        db = _make_db()
        insp = _make_inspection(id=1, batch_no="BATCH-001")
        db.query.return_value.filter.return_value.all.side_effect = [
            [insp],   # inspection 查询
            [],       # defect analysis 查询
            [],       # rework orders 查询
        ]
        result = QualityService.batch_tracing(db, "BATCH-001")
        assert "batch_no" in result
        assert result["batch_no"] == "BATCH-001"


class TestAggregateByTime:
    def test_aggregate_by_day(self):
        from app.services.quality_service import QualityService
        insp1 = _make_inspection(
            inspection_date=datetime(2024, 1, 1),
            inspection_qty=100, qualified_qty=95, defect_qty=5, defect_rate=Decimal("5.0")
        )
        insp2 = _make_inspection(
            inspection_date=datetime(2024, 1, 1),
            inspection_qty=50, qualified_qty=48, defect_qty=2, defect_rate=Decimal("4.0")
        )
        result = QualityService._aggregate_by_time([insp1, insp2], "day")
        assert len(result) == 1  # 同一天合并
        assert result[0].total_qty == 150

    def test_aggregate_by_month(self):
        from app.services.quality_service import QualityService
        insp1 = _make_inspection(
            inspection_date=datetime(2024, 1, 15),
            inspection_qty=100, qualified_qty=95, defect_qty=5, defect_rate=Decimal("5.0")
        )
        insp2 = _make_inspection(
            inspection_date=datetime(2024, 2, 10),
            inspection_qty=80, qualified_qty=76, defect_qty=4, defect_rate=Decimal("5.0")
        )
        result = QualityService._aggregate_by_time([insp1, insp2], "month")
        assert len(result) == 2  # 不同月份
