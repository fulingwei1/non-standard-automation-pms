# -*- coding: utf-8 -*-
"""Tests for procurement_analysis/quality_analysis.py"""
import pytest
from unittest.mock import MagicMock
from datetime import date


class TestQualityAnalyzer:
    def test_empty(self):
        from app.services.procurement_analysis.quality_analysis import QualityAnalyzer
        db = MagicMock()
        db.query.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.filter.return_value.group_by.return_value.all.return_value = []
        result = QualityAnalyzer.get_quality_rate_data(db, date(2025, 1, 1), date(2025, 12, 31))
        assert result['supplier_quality'] == []
        assert result['summary']['total_suppliers'] == 0

    def test_with_data(self):
        from app.services.procurement_analysis.quality_analysis import QualityAnalyzer
        db = MagicMock()
        row = MagicMock(
            supplier_id=1, supplier_name='Sup A',
            material_code='M001', material_name='Steel',
            total_qualified=90, total_rejected=10, total_inspected=100
        )
        db.query.return_value.join.return_value.join.return_value.join.return_value.filter.return_value.filter.return_value.group_by.return_value.all.return_value = [row]
        result = QualityAnalyzer.get_quality_rate_data(db, date(2025, 1, 1), date(2025, 12, 31))
        assert len(result['supplier_quality']) == 1
        assert result['supplier_quality'][0]['overall_pass_rate'] == 90.0
