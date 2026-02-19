# -*- coding: utf-8 -*-
"""
第三十九批覆盖率测试 - procurement_analysis/quality_analysis.py
"""
import pytest
from datetime import date
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.procurement_analysis.quality_analysis",
                    reason="import failed, skip")


@pytest.fixture
def mock_db():
    return MagicMock()


class TestQualityAnalyzerEmptyResult:
    """无数据时返回结构正确"""

    def test_empty_supplier_quality(self, mock_db):
        from app.services.procurement_analysis.quality_analysis import QualityAnalyzer

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []

        result = QualityAnalyzer.get_quality_rate_data(
            mock_db, date(2024, 1, 1), date(2024, 12, 31)
        )

        assert result["supplier_quality"] == []
        assert result["summary"]["total_suppliers"] == 0
        assert result["summary"]["avg_pass_rate"] == 0
        assert result["summary"]["high_quality_suppliers"] == 0
        assert result["summary"]["low_quality_suppliers"] == 0


class TestQualityAnalyzerWithData:
    """有数据时统计结果正确"""

    def _make_row(self, sid, sname, mcode, mname, qualified, rejected, inspected):
        row = MagicMock()
        row.supplier_id = sid
        row.supplier_name = sname
        row.material_code = mcode
        row.material_name = mname
        row.total_qualified = qualified
        row.total_rejected = rejected
        row.total_inspected = inspected
        return row

    def test_pass_rate_calculation(self, mock_db):
        from app.services.procurement_analysis.quality_analysis import QualityAnalyzer

        rows = [
            self._make_row(1, "供应商A", "M001", "物料A", 90, 10, 100),
        ]
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = rows

        result = QualityAnalyzer.get_quality_rate_data(
            mock_db, date(2024, 1, 1), date(2024, 12, 31)
        )

        assert len(result["supplier_quality"]) == 1
        supplier = result["supplier_quality"][0]
        assert supplier["overall_pass_rate"] == 90.0
        assert supplier["total_qualified"] == 90.0
        assert supplier["total_rejected"] == 10.0

    def test_pass_rate_zero_total(self, mock_db):
        from app.services.procurement_analysis.quality_analysis import QualityAnalyzer

        rows = [
            self._make_row(1, "供应商A", "M001", "物料A", 0, 0, 0),
        ]
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = rows

        result = QualityAnalyzer.get_quality_rate_data(
            mock_db, date(2024, 1, 1), date(2024, 12, 31)
        )

        # 0/0 时默认100%
        assert result["supplier_quality"][0]["overall_pass_rate"] == 100

    def test_multiple_suppliers_sorted(self, mock_db):
        from app.services.procurement_analysis.quality_analysis import QualityAnalyzer

        rows = [
            self._make_row(1, "供应商A", "M001", "物料A", 80, 20, 100),
            self._make_row(2, "供应商B", "M002", "物料B", 99, 1, 100),
        ]
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = rows

        result = QualityAnalyzer.get_quality_rate_data(
            mock_db, date(2024, 1, 1), date(2024, 12, 31)
        )

        # 按合格率降序排列
        rates = [s["overall_pass_rate"] for s in result["supplier_quality"]]
        assert rates == sorted(rates, reverse=True)

    def test_supplier_filter(self, mock_db):
        from app.services.procurement_analysis.quality_analysis import QualityAnalyzer

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = []

        result = QualityAnalyzer.get_quality_rate_data(
            mock_db, date(2024, 1, 1), date(2024, 12, 31), supplier_id=5
        )

        assert result["summary"]["total_suppliers"] == 0

    def test_summary_high_low_quality(self, mock_db):
        from app.services.procurement_analysis.quality_analysis import QualityAnalyzer

        rows = [
            self._make_row(1, "供应商A", "M001", "物料A", 98, 2, 100),  # 98% >= 98 -> high
            self._make_row(2, "供应商B", "M002", "物料B", 85, 15, 100), # 85% < 90 -> low
        ]
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = rows

        result = QualityAnalyzer.get_quality_rate_data(
            mock_db, date(2024, 1, 1), date(2024, 12, 31)
        )
        assert result["summary"]["high_quality_suppliers"] == 1
        assert result["summary"]["low_quality_suppliers"] == 1

    def test_material_count_per_supplier(self, mock_db):
        from app.services.procurement_analysis.quality_analysis import QualityAnalyzer

        rows = [
            self._make_row(1, "供应商A", "M001", "物料A", 90, 10, 100),
            self._make_row(1, "供应商A", "M002", "物料B", 90, 10, 100),
        ]
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = rows

        result = QualityAnalyzer.get_quality_rate_data(
            mock_db, date(2024, 1, 1), date(2024, 12, 31)
        )
        assert result["supplier_quality"][0]["material_count"] == 2
