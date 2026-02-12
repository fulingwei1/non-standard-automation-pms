# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock, patch
from app.services.report_framework.adapters.rd_expense import RdExpenseReportAdapter


class TestRdExpenseReportAdapter:
    def test_get_report_code(self):
        db = MagicMock()
        adapter = RdExpenseReportAdapter(db, "RD_AUXILIARY_LEDGER")
        assert adapter.get_report_code() == "RD_AUXILIARY_LEDGER"

    def test_get_report_code_unknown(self):
        db = MagicMock()
        adapter = RdExpenseReportAdapter(db, "CUSTOM")
        assert adapter.get_report_code() == "CUSTOM"

    def test_generate_data_no_year(self):
        db = MagicMock()
        adapter = RdExpenseReportAdapter(db)
        with pytest.raises(ValueError, match="year"):
            adapter.generate_data({})

    @patch("app.services.report_framework.adapters.rd_expense.RdExpenseReportAdapter.generate_data")
    def test_generate_data_unsupported_type(self, mock_gen):
        mock_gen.side_effect = ValueError("不支持的报表类型")
        db = MagicMock()
        adapter = RdExpenseReportAdapter(db, "INVALID")
        with pytest.raises(ValueError):
            adapter.generate_data({"year": 2024})
