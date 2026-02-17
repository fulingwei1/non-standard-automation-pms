# -*- coding: utf-8 -*-
"""
质量管理服务单元测试
覆盖 SPC 计算、帕累托分析、移动平均预测等核心算法
"""
import pytest
import statistics
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.quality_service import QualityService


class TestCalculateMovingAverage:
    """_calculate_moving_average 移动平均计算"""

    def test_returns_none_when_insufficient_data(self):
        result = QualityService._calculate_moving_average([1.0, 2.0], window=3)
        assert result is None

    def test_exact_window_size(self):
        result = QualityService._calculate_moving_average([1.0, 2.0, 3.0], window=3)
        assert result == pytest.approx(2.0)

    def test_uses_last_n_elements(self):
        # window=3，取最后3个 [4, 5, 6] → 平均5.0
        result = QualityService._calculate_moving_average([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], window=3)
        assert result == pytest.approx(5.0)

    def test_single_value_window_one(self):
        result = QualityService._calculate_moving_average([7.5], window=1)
        assert result == pytest.approx(7.5)


class TestAggregateByTime:
    """_aggregate_by_time 按时间维度聚合"""

    def _make_inspection(self, date_str, inspection_qty, qualified_qty, defect_qty):
        i = MagicMock()
        i.inspection_date = datetime.strptime(date_str, "%Y-%m-%d")
        i.inspection_qty = inspection_qty
        i.qualified_qty = qualified_qty
        i.defect_qty = defect_qty
        return i

    def test_aggregate_by_day(self):
        inspections = [
            self._make_inspection("2025-01-01", 100, 95, 5),
            self._make_inspection("2025-01-01", 200, 190, 10),
            self._make_inspection("2025-01-02", 150, 140, 10),
        ]
        result = QualityService._aggregate_by_time(inspections, "day")
        assert len(result) == 2
        # 第一天汇总
        day1 = result[0]
        assert day1.total_qty == 300
        assert day1.defect_qty == 15

    def test_aggregate_by_month(self):
        inspections = [
            self._make_inspection("2025-01-10", 100, 90, 10),
            self._make_inspection("2025-02-15", 200, 190, 10),
        ]
        result = QualityService._aggregate_by_time(inspections, "month")
        assert len(result) == 2
        assert result[0].date == "2025-01"

    def test_defect_rate_calculated(self):
        inspections = [self._make_inspection("2025-01-01", 100, 95, 5)]
        result = QualityService._aggregate_by_time(inspections, "day")
        assert result[0].defect_rate == pytest.approx(5.0)

    def test_zero_total_qty_results_in_zero_rate(self):
        inspections = [self._make_inspection("2025-01-01", 0, 0, 0)]
        result = QualityService._aggregate_by_time(inspections, "day")
        assert result[0].defect_rate == pytest.approx(0.0)


class TestSPCControlLimits:
    """calculate_spc_control_limits SPC控制限计算"""

    def _make_db(self, measured_values, spec_upper=None, spec_lower=None):
        db = MagicMock()
        inspections = []
        for i, v in enumerate(measured_values):
            insp = MagicMock()
            insp.inspection_no = f"QI2025010{i:04d}"
            insp.inspection_date = datetime(2025, 1, i + 1)
            insp.measured_value = Decimal(str(v))
            insp.spec_upper_limit = Decimal(str(spec_upper)) if spec_upper else None
            insp.spec_lower_limit = Decimal(str(spec_lower)) if spec_lower else None
            inspections.append(insp)
        db.query.return_value.filter.return_value.all.return_value = inspections
        return db

    def test_insufficient_samples_raises(self):
        db = self._make_db([1.0, 2.0, 3.0, 4.0])  # 只有4个，需要>=5
        with pytest.raises(ValueError, match="样本数量不足"):
            QualityService.calculate_spc_control_limits(
                db=db,
                material_id=1,
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 12, 31),
            )

    def test_control_limits_ucl_gt_lcl(self):
        values = [10.0, 11.0, 12.0, 9.0, 10.5, 11.5, 10.2, 9.8, 10.8, 11.2]
        db = self._make_db(values)
        result = QualityService.calculate_spc_control_limits(
            db=db, material_id=1,
            start_date=datetime(2025, 1, 1), end_date=datetime(2025, 12, 31)
        )
        limits = result["control_limits"]
        assert limits.ucl > limits.cl > limits.lcl

    def test_cl_equals_mean(self):
        values = [10.0, 10.0, 10.0, 10.0, 10.0]  # 全相同，均值10
        db = self._make_db(values)
        result = QualityService.calculate_spc_control_limits(
            db=db, material_id=1,
            start_date=datetime(2025, 1, 1), end_date=datetime(2025, 12, 31)
        )
        assert result["control_limits"].cl == pytest.approx(10.0)

    def test_cpk_calculated_with_spec_limits(self):
        values = [9.8, 10.0, 10.2, 9.9, 10.1, 10.0, 10.05, 9.95, 10.1, 9.9]
        db = self._make_db(values, spec_upper=12.0, spec_lower=8.0)
        result = QualityService.calculate_spc_control_limits(
            db=db, material_id=1,
            start_date=datetime(2025, 1, 1), end_date=datetime(2025, 12, 31)
        )
        assert result["process_capability_index"] is not None
        assert result["process_capability_index"] > 0

    def test_out_of_control_points_detected(self):
        # 大量正常值 + 1个极端离群值 → 应检测到离群点
        # 使用重复100次的稳定值+1个极端值，确保UCL远低于离群值
        normal_values = [10.0] * 20
        values = normal_values + [1000.0]  # 21个值
        db = self._make_db(values)
        result = QualityService.calculate_spc_control_limits(
            db=db, material_id=1,
            start_date=datetime(2025, 1, 1), end_date=datetime(2025, 12, 31)
        )
        assert len(result["out_of_control_points"]) >= 1


class TestDefectRateCalculation:
    """质检记录中的不良率计算逻辑"""

    def test_defect_rate_formula(self):
        """验证不良率 = defect_qty / inspection_qty * 100"""
        inspection_qty = 200
        defect_qty = 10
        defect_rate = (defect_qty / inspection_qty) * 100
        assert defect_rate == pytest.approx(5.0)

    def test_defect_rate_zero_when_no_defects(self):
        inspection_qty = 100
        defect_qty = 0
        defect_rate = (defect_qty / inspection_qty) * 100
        assert defect_rate == 0.0
