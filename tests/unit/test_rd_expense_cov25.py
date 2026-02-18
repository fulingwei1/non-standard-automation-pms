# -*- coding: utf-8 -*-
"""第二十五批 - report_framework/adapters/rd_expense 单元测试"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.report_framework.adapters.rd_expense")

from app.services.report_framework.adapters.rd_expense import RdExpenseReportAdapter


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def adapter(db):
    with patch("app.services.report_framework.adapters.rd_expense.BaseReportAdapter.__init__", return_value=None):
        svc = RdExpenseReportAdapter.__new__(RdExpenseReportAdapter)
        svc.db = db
        svc.report_type = "RD_AUXILIARY_LEDGER"
    return svc


# ── get_report_code ───────────────────────────────────────────────────────────

class TestGetReportCode:
    def test_known_type_returns_mapped_code(self, db):
        with patch("app.services.report_framework.adapters.rd_expense.BaseReportAdapter.__init__", return_value=None):
            svc = RdExpenseReportAdapter.__new__(RdExpenseReportAdapter)
            svc.db = db
            svc.report_type = "RD_AUXILIARY_LEDGER"
        assert svc.get_report_code() == "RD_AUXILIARY_LEDGER"

    def test_all_known_types_map_to_themselves(self, db):
        known_types = [
            "RD_AUXILIARY_LEDGER",
            "RD_DEDUCTION_DETAIL",
            "RD_HIGH_TECH",
            "RD_INTENSITY",
            "RD_PERSONNEL",
        ]
        for rtype in known_types:
            with patch("app.services.report_framework.adapters.rd_expense.BaseReportAdapter.__init__", return_value=None):
                svc = RdExpenseReportAdapter.__new__(RdExpenseReportAdapter)
                svc.db = db
                svc.report_type = rtype
            assert svc.get_report_code() == rtype

    def test_unknown_type_returns_itself(self, db):
        with patch("app.services.report_framework.adapters.rd_expense.BaseReportAdapter.__init__", return_value=None):
            svc = RdExpenseReportAdapter.__new__(RdExpenseReportAdapter)
            svc.db = db
            svc.report_type = "CUSTOM_TYPE"
        assert svc.get_report_code() == "CUSTOM_TYPE"


# ── REPORT_TYPE_MAP ───────────────────────────────────────────────────────────

class TestReportTypeMap:
    def test_map_contains_all_expected_types(self):
        expected = {
            "RD_AUXILIARY_LEDGER",
            "RD_DEDUCTION_DETAIL",
            "RD_HIGH_TECH",
            "RD_INTENSITY",
            "RD_PERSONNEL",
        }
        assert set(RdExpenseReportAdapter.REPORT_TYPE_MAP.keys()) == expected

    def test_map_values_equal_keys(self):
        for k, v in RdExpenseReportAdapter.REPORT_TYPE_MAP.items():
            assert k == v


# ── generate_data ─────────────────────────────────────────────────────────────

class TestGenerateData:
    def _make_adapter(self, db, report_type):
        with patch("app.services.report_framework.adapters.rd_expense.BaseReportAdapter.__init__", return_value=None):
            svc = RdExpenseReportAdapter.__new__(RdExpenseReportAdapter)
            svc.db = db
            svc.report_type = report_type
        return svc

    def test_raises_when_year_missing(self, db):
        svc = self._make_adapter(db, "RD_AUXILIARY_LEDGER")
        with pytest.raises(ValueError, match="year"):
            svc.generate_data({})

    def test_auxiliary_ledger_calls_build_function(self, db):
        svc = self._make_adapter(db, "RD_AUXILIARY_LEDGER")
        with patch("app.services.rd_report_data_service.build_auxiliary_ledger_data") as mock_fn:
            mock_fn.return_value = {"data": []}
            result = svc.generate_data({"year": 2025})
        mock_fn.assert_called_once_with(db, 2025, None)

    def test_auxiliary_ledger_passes_project_id(self, db):
        svc = self._make_adapter(db, "RD_AUXILIARY_LEDGER")
        with patch("app.services.rd_report_data_service.build_auxiliary_ledger_data") as mock_fn:
            mock_fn.return_value = {}
            svc.generate_data({"year": 2025, "project_id": 7})
        mock_fn.assert_called_once_with(db, 2025, 7)

    def test_deduction_detail_calls_build_function(self, db):
        svc = self._make_adapter(db, "RD_DEDUCTION_DETAIL")
        with patch("app.services.rd_report_data_service.build_deduction_detail_data") as mock_fn:
            mock_fn.return_value = {}
            svc.generate_data({"year": 2025})
        mock_fn.assert_called_once()

    def test_high_tech_calls_build_function(self, db):
        svc = self._make_adapter(db, "RD_HIGH_TECH")
        with patch("app.services.rd_report_data_service.build_high_tech_data") as mock_fn:
            mock_fn.return_value = {}
            svc.generate_data({"year": 2025})
        mock_fn.assert_called_once_with(db, 2025)

    def test_intensity_single_year(self, db):
        svc = self._make_adapter(db, "RD_INTENSITY")
        with patch("app.services.rd_report_data_service.build_intensity_data") as mock_fn:
            mock_fn.return_value = {}
            svc.generate_data({"year": 2025, "start_year": 2025, "end_year": 2025})
        mock_fn.assert_called_once_with(db, 2025)

    def test_intensity_multi_year_raises(self, db):
        svc = self._make_adapter(db, "RD_INTENSITY")
        with patch("app.services.rd_report_data_service.build_intensity_data"):
            with pytest.raises(ValueError, match="多年度"):
                svc.generate_data({"year": 2024, "start_year": 2023, "end_year": 2025})

    def test_personnel_calls_build_function(self, db):
        svc = self._make_adapter(db, "RD_PERSONNEL")
        with patch("app.services.rd_report_data_service.build_personnel_data") as mock_fn:
            mock_fn.return_value = {}
            svc.generate_data({"year": 2025})
        mock_fn.assert_called_once_with(db, 2025)

    def test_unknown_type_raises(self, db):
        svc = self._make_adapter(db, "UNKNOWN_TYPE")
        with pytest.raises(ValueError, match="不支持的报表类型"):
            svc.generate_data({"year": 2025})
