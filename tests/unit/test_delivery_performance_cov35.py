# -*- coding: utf-8 -*-
"""
第三十五批 - delivery_performance.py 单元测试
"""
import pytest
from datetime import date
from unittest.mock import MagicMock

try:
    from app.services.procurement_analysis.delivery_performance import DeliveryPerformanceAnalyzer
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="导入失败，跳过")


def _make_row(supplier_id, supplier_name, supplier_code,
              receipt_id, receipt_date, receipt_no,
              promised_date, order_no, order_id):
    row = MagicMock()
    row.supplier_id = supplier_id
    row.supplier_name = supplier_name
    row.supplier_code = supplier_code
    row.receipt_id = receipt_id
    row.receipt_date = receipt_date
    row.receipt_no = receipt_no
    row.promised_date = promised_date
    row.order_no = order_no
    row.order_id = order_id
    return row


def _make_db(rows):
    db = MagicMock()
    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = rows
    db.query.return_value = mock_query
    return db


@pytest.mark.skipif(not IMPORT_OK, reason="导入失败")
class TestDeliveryPerformanceAnalyzer:

    def test_on_time_delivery(self):
        """准时交货正确统计"""
        row = _make_row(
            1, "供应商A", "SUP001",
            101, date(2024, 3, 10), "REC001",
            date(2024, 3, 15), "PO001", 201
        )
        db = _make_db([row])
        result = DeliveryPerformanceAnalyzer.get_delivery_performance_data(
            db, date(2024, 1, 1), date(2024, 12, 31)
        )
        perf = result["supplier_performance"][0]
        assert perf["on_time_deliveries"] == 1
        assert perf["delayed_deliveries"] == 0
        assert perf["on_time_rate"] == 100.0

    def test_delayed_delivery(self):
        """延期交货正确统计"""
        row = _make_row(
            2, "供应商B", "SUP002",
            102, date(2024, 3, 20), "REC002",
            date(2024, 3, 10), "PO002", 202
        )
        db = _make_db([row])
        result = DeliveryPerformanceAnalyzer.get_delivery_performance_data(
            db, date(2024, 1, 1), date(2024, 12, 31)
        )
        perf = result["supplier_performance"][0]
        assert perf["delayed_deliveries"] == 1
        assert perf["on_time_rate"] == 0.0
        assert len(result["delayed_orders"]) == 1

    def test_empty_results(self):
        """无记录时返回空汇总"""
        db = _make_db([])
        result = DeliveryPerformanceAnalyzer.get_delivery_performance_data(
            db, date(2024, 1, 1), date(2024, 12, 31)
        )
        assert result["supplier_performance"] == []
        assert result["summary"]["total_suppliers"] == 0
        assert result["summary"]["avg_on_time_rate"] == 0

    def test_multiple_suppliers_sorted(self):
        """多供应商按准时率降序排列"""
        row_a = _make_row(1, "A", "A001", 1, date(2024, 3, 5), "R1",
                          date(2024, 3, 10), "P1", 1)  # on-time
        row_b = _make_row(2, "B", "B001", 2, date(2024, 3, 20), "R2",
                          date(2024, 3, 10), "P2", 2)  # delayed
        db = _make_db([row_a, row_b])
        result = DeliveryPerformanceAnalyzer.get_delivery_performance_data(
            db, date(2024, 1, 1), date(2024, 12, 31)
        )
        perfs = result["supplier_performance"]
        assert perfs[0]["on_time_rate"] >= perfs[-1]["on_time_rate"]

    def test_summary_contains_required_keys(self):
        """汇总包含必要字段"""
        db = _make_db([])
        result = DeliveryPerformanceAnalyzer.get_delivery_performance_data(
            db, date(2024, 1, 1), date(2024, 12, 31)
        )
        assert "total_suppliers" in result["summary"]
        assert "avg_on_time_rate" in result["summary"]
        assert "total_delayed_orders" in result["summary"]

    def test_delayed_orders_capped_at_50(self):
        """延期记录最多返回50条"""
        rows = []
        for i in range(60):
            rows.append(_make_row(
                i, f"供应商{i}", f"SUP{i:03d}",
                i, date(2024, 3, 20), f"REC{i}",
                date(2024, 3, 10), f"PO{i}", i
            ))
        db = _make_db(rows)
        result = DeliveryPerformanceAnalyzer.get_delivery_performance_data(
            db, date(2024, 1, 1), date(2024, 12, 31)
        )
        assert len(result["delayed_orders"]) <= 50

    def test_null_promised_date(self):
        """promised_date 为 None 时不计入延期"""
        row = _make_row(
            3, "供应商C", "SUP003",
            103, date(2024, 3, 20), "REC003",
            None, "PO003", 203
        )
        db = _make_db([row])
        result = DeliveryPerformanceAnalyzer.get_delivery_performance_data(
            db, date(2024, 1, 1), date(2024, 12, 31)
        )
        perf = result["supplier_performance"][0]
        assert perf["delayed_deliveries"] == 0
