# -*- coding: utf-8 -*-
"""
库存盘点服务单元测试
覆盖任务状态流转、差异计算、统计更新等
"""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

from app.services.stock_count_service import StockCountService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    with patch("app.services.stock_count_service.InventoryManagementService"):
        svc = StockCountService(db=mock_db, tenant_id=1)
    return svc


def make_task(id=1, status="PENDING", total_items=5, counted_items=0, **kwargs):
    t = MagicMock()
    t.id = id
    t.status = status
    t.total_items = total_items
    t.counted_items = counted_items
    t.matched_items = 0
    t.diff_items = 0
    t.total_diff_value = Decimal("0")
    for k, v in kwargs.items():
        setattr(t, k, v)
    return t


def make_detail(id=1, task_id=1, system_quantity=Decimal("100"), unit_price=Decimal("10"), status="PENDING"):
    d = MagicMock()
    d.id = id
    d.task_id = task_id
    d.system_quantity = system_quantity
    d.unit_price = unit_price
    d.status = status
    d.actual_quantity = None
    d.difference = None
    d.difference_rate = None
    d.diff_value = None
    return d


class TestStartCountTask:
    def test_start_pending_task(self, service, mock_db):
        task = make_task(status="PENDING")
        service.get_count_task = MagicMock(return_value=task)
        result = service.start_count_task(task_id=1)
        assert result.status == "IN_PROGRESS"
        mock_db.commit.assert_called_once()

    def test_start_non_pending_raises(self, service):
        task = make_task(status="IN_PROGRESS")
        service.get_count_task = MagicMock(return_value=task)
        with pytest.raises(ValueError, match="状态不允许开始"):
            service.start_count_task(task_id=1)

    def test_start_nonexistent_task_raises(self, service):
        service.get_count_task = MagicMock(return_value=None)
        with pytest.raises(ValueError, match="盘点任务不存在"):
            service.start_count_task(task_id=999)


class TestCancelCountTask:
    def test_cancel_pending_task(self, service, mock_db):
        task = make_task(status="PENDING")
        service.get_count_task = MagicMock(return_value=task)
        result = service.cancel_count_task(task_id=1)
        assert result.status == "CANCELLED"
        mock_db.commit.assert_called_once()

    def test_cancel_completed_raises(self, service):
        task = make_task(status="COMPLETED")
        service.get_count_task = MagicMock(return_value=task)
        with pytest.raises(ValueError, match="已完成"):
            service.cancel_count_task(task_id=1)

    def test_cancel_nonexistent_raises(self, service):
        service.get_count_task = MagicMock(return_value=None)
        with pytest.raises(ValueError, match="盘点任务不存在"):
            service.cancel_count_task(task_id=999)


class TestRecordActualQuantity:
    def _setup_detail_query(self, mock_db, detail):
        mock_db.query.return_value.filter.return_value.first.return_value = detail

    def test_difference_calculated_correctly(self, service, mock_db):
        detail = make_detail(system_quantity=Decimal("100"))
        self._setup_detail_query(mock_db, detail)
        service._update_task_statistics = MagicMock()

        result = service.record_actual_quantity(
            detail_id=1,
            actual_quantity=Decimal("90"),
        )
        assert result.difference == Decimal("-10")

    def test_difference_rate_calculated(self, service, mock_db):
        detail = make_detail(system_quantity=Decimal("100"))
        self._setup_detail_query(mock_db, detail)
        service._update_task_statistics = MagicMock()

        result = service.record_actual_quantity(
            detail_id=1,
            actual_quantity=Decimal("90"),
        )
        # (-10 / 100) * 100 = -10%
        assert result.difference_rate == Decimal("-10")

    def test_diff_value_calculated_with_unit_price(self, service, mock_db):
        detail = make_detail(system_quantity=Decimal("100"), unit_price=Decimal("5"))
        self._setup_detail_query(mock_db, detail)
        service._update_task_statistics = MagicMock()

        result = service.record_actual_quantity(
            detail_id=1,
            actual_quantity=Decimal("90"),
        )
        # difference=-10, unit_price=5 → diff_value=-50
        assert result.diff_value == Decimal("-50")

    def test_zero_system_quantity_difference_rate_is_zero(self, service, mock_db):
        detail = make_detail(system_quantity=Decimal("0"))
        self._setup_detail_query(mock_db, detail)
        service._update_task_statistics = MagicMock()

        result = service.record_actual_quantity(
            detail_id=1,
            actual_quantity=Decimal("5"),
        )
        assert result.difference_rate == Decimal("0")

    def test_nonexistent_detail_raises(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="盘点明细不存在"):
            service.record_actual_quantity(detail_id=999, actual_quantity=Decimal("10"))


class TestUpdateTaskStatistics:
    def test_statistics_updated_correctly(self, service):
        task = make_task(id=1)
        service.get_count_task = MagicMock(return_value=task)

        details = [
            make_detail(id=1, status="COUNTED", system_quantity=Decimal("100")),
            make_detail(id=2, status="COUNTED", system_quantity=Decimal("50")),
            make_detail(id=3, status="PENDING", system_quantity=Decimal("30")),
        ]
        # d1 差异为0，d2 差异不为0
        details[0].difference = Decimal("0")
        details[0].diff_value = Decimal("0")
        details[1].difference = Decimal("5")
        details[1].diff_value = Decimal("25")
        details[2].difference = None
        details[2].diff_value = None

        service.get_count_details = MagicMock(return_value=details)

        service._update_task_statistics(task_id=1)

        assert task.total_items == 3
        assert task.counted_items == 2  # COUNTED 状态
        assert task.matched_items == 1  # difference == 0
        assert task.diff_items == 1    # difference != 0 且 not None
