# -*- coding: utf-8 -*-
"""
quality_service.py 单元测试（第二批）
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, call


# ─── 1. 纯逻辑：_calculate_moving_average ───────────────────────────────────
def test_calculate_moving_average_normal():
    from app.services.quality_service import QualityService
    data = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = QualityService._calculate_moving_average(data, window=3)
    assert result == round((3.0 + 4.0 + 5.0) / 3, 2)


def test_calculate_moving_average_insufficient_data():
    from app.services.quality_service import QualityService
    data = [1.0, 2.0]
    result = QualityService._calculate_moving_average(data, window=3)
    assert result is None


def test_calculate_moving_average_exact_window():
    from app.services.quality_service import QualityService
    data = [10.0, 20.0, 30.0]
    result = QualityService._calculate_moving_average(data, window=3)
    assert result == 20.0


# ─── 2. _aggregate_by_time ───────────────────────────────────────────────────
def test_aggregate_by_time_daily():
    from app.services.quality_service import QualityService

    def make_inspection(date_str, insp_qty, qual_qty, defect_qty):
        m = MagicMock()
        m.inspection_date = datetime.strptime(date_str, "%Y-%m-%d")
        m.inspection_qty = insp_qty
        m.qualified_qty = qual_qty
        m.defect_qty = defect_qty
        return m

    inspections = [
        make_inspection("2024-01-01", 100, 95, 5),
        make_inspection("2024-01-01", 50, 45, 5),
        make_inspection("2024-01-02", 80, 78, 2),
    ]
    result = QualityService._aggregate_by_time(inspections, "day")
    assert len(result) == 2
    # 第一天合并
    assert result[0].total_qty == 150
    assert result[0].defect_qty == 10
    assert result[0].defect_rate == round(10 / 150 * 100, 2)


def test_aggregate_by_time_month():
    from app.services.quality_service import QualityService

    m1 = MagicMock()
    m1.inspection_date = datetime(2024, 1, 15)
    m1.inspection_qty = 100
    m1.qualified_qty = 90
    m1.defect_qty = 10

    m2 = MagicMock()
    m2.inspection_date = datetime(2024, 2, 10)
    m2.inspection_qty = 200
    m2.qualified_qty = 195
    m2.defect_qty = 5

    result = QualityService._aggregate_by_time([m1, m2], "month")
    assert len(result) == 2
    assert result[0].date == "2024-01"
    assert result[1].date == "2024-02"


# ─── 3. _generate_inspection_no ──────────────────────────────────────────────
def test_generate_inspection_no_first_of_day():
    from app.services.quality_service import QualityService

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

    # 不 patch datetime，直接运行（序号以0001结尾）
    no = QualityService._generate_inspection_no(mock_db)
    assert no.startswith("QI")
    assert no.endswith("0001")


def test_generate_inspection_no_increments():
    from app.services.quality_service import QualityService

    today_str = datetime.now().strftime("%Y%m%d")
    last = MagicMock()
    last.inspection_no = f"QI{today_str}0005"

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = last

    no = QualityService._generate_inspection_no(mock_db)
    assert no.endswith("0006")


# ─── 4. complete_rework_order ────────────────────────────────────────────────
def test_complete_rework_order_not_found():
    from app.services.quality_service import QualityService

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError, match="返工单不存在"):
        QualityService.complete_rework_order(mock_db, 999, {})


def test_complete_rework_order_already_completed():
    from app.services.quality_service import QualityService

    mock_rw = MagicMock()
    mock_rw.status = "COMPLETED"

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_rw

    with pytest.raises(ValueError, match="返工单已完成"):
        QualityService.complete_rework_order(mock_db, 1, {})


def test_complete_rework_order_success():
    from app.services.quality_service import QualityService

    mock_rw = MagicMock()
    mock_rw.status = "IN_PROGRESS"

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_rw

    result = QualityService.complete_rework_order(
        mock_db, 1,
        {"completed_qty": 10, "qualified_qty": 9, "scrap_qty": 1,
         "actual_hours": 2, "rework_cost": 500, "completion_note": "done"}
    )
    assert mock_rw.status == "COMPLETED"
    assert mock_rw.completed_qty == 10
    mock_db.commit.assert_called_once()


# ─── 5. calculate_spc_control_limits 样本不足 ────────────────────────────────
def test_spc_insufficient_samples():
    from app.services.quality_service import QualityService

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = [MagicMock(), MagicMock()]

    with pytest.raises(ValueError, match="至少需要5个"):
        QualityService.calculate_spc_control_limits(
            mock_db, 1, datetime(2024, 1, 1), datetime(2024, 12, 31)
        )
