# -*- coding: utf-8 -*-
"""Tests for procurement_analysis/price_analysis.py"""
import pytest
from unittest.mock import MagicMock
from datetime import date


class TestPriceAnalyzer:
    def test_empty_results(self):
        from app.services.procurement_analysis.price_analysis import PriceAnalyzer
        db = MagicMock()
        db.query.return_value.join.return_value.join.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        result = PriceAnalyzer.get_price_fluctuation_data(db)
        assert result['materials'] == []
        assert result['summary']['total_materials'] == 0

    def test_with_data(self):
        from app.services.procurement_analysis.price_analysis import PriceAnalyzer
        db = MagicMock()
        row = MagicMock(
            material_code='M001',
            material_name='Steel',
            unit_price=100,
            order_date=date(2025, 1, 1),
            supplier_name='Supplier A',
            supplier_id=1,
            category_name='Metal',
            standard_price=95
        )
        row2 = MagicMock(
            material_code='M001',
            material_name='Steel',
            unit_price=120,
            order_date=date(2025, 2, 1),
            supplier_name='Supplier B',
            supplier_id=2,
            category_name='Metal',
            standard_price=95
        )
        db.query.return_value.join.return_value.join.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [row, row2]
        result = PriceAnalyzer.get_price_fluctuation_data(db)
        assert result['summary']['total_materials'] == 1
        assert len(result['materials']) == 1
        m = result['materials'][0]
        assert m['min_price'] == 100
        assert m['max_price'] == 120
