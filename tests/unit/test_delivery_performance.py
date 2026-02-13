# -*- coding: utf-8 -*-
"""Tests for procurement_analysis/delivery_performance.py"""
import pytest
from unittest.mock import MagicMock
from datetime import date


class TestDeliveryPerformanceAnalyzer:
    def test_empty_results(self):
        from app.services.procurement_analysis.delivery_performance import DeliveryPerformanceAnalyzer
        db = MagicMock()
        db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = []
        result = DeliveryPerformanceAnalyzer.get_delivery_performance_data(
            db, date(2025, 1, 1), date(2025, 12, 31)
        )
        assert result['supplier_performance'] == []
        assert result['summary']['total_suppliers'] == 0

    def test_with_on_time_delivery(self):
        from app.services.procurement_analysis.delivery_performance import DeliveryPerformanceAnalyzer
        db = MagicMock()
        row = MagicMock(
            supplier_id=1, supplier_name='Sup A', supplier_code='S001',
            receipt_id=1, receipt_date=date(2025, 3, 1), receipt_no='R001',
            promised_date=date(2025, 3, 5), order_no='PO001', order_id=1
        )
        db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = [row]
        result = DeliveryPerformanceAnalyzer.get_delivery_performance_data(
            db, date(2025, 1, 1), date(2025, 12, 31)
        )
        assert result['supplier_performance'][0]['on_time_rate'] == 100.0

    def test_with_delayed_delivery(self):
        from app.services.procurement_analysis.delivery_performance import DeliveryPerformanceAnalyzer
        db = MagicMock()
        row = MagicMock(
            supplier_id=1, supplier_name='Sup A', supplier_code='S001',
            receipt_id=1, receipt_date=date(2025, 3, 10), receipt_no='R001',
            promised_date=date(2025, 3, 1), order_no='PO001', order_id=1
        )
        db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = [row]
        result = DeliveryPerformanceAnalyzer.get_delivery_performance_data(
            db, date(2025, 1, 1), date(2025, 12, 31)
        )
        assert result['supplier_performance'][0]['on_time_rate'] == 0.0
        assert len(result['delayed_orders']) == 1
