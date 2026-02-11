# -*- coding: utf-8 -*-
"""Tests for acceptance/report_utils.py"""
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.services.acceptance.report_utils import (
    generate_report_no,
    get_report_version,
    build_report_content,
)


class TestGenerateReportNo:
    def test_first_report(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.scalar.return_value = 0
        result = generate_report_no(db, "FAT")
        today = datetime.now().strftime("%Y%m%d")
        assert result == f"FAT-{today}-001"

    def test_second_report(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.scalar.return_value = 3
        result = generate_report_no(db, "SAT")
        assert result.startswith("SAT-")
        assert result.endswith("-004")

    def test_final_type(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.scalar.return_value = 0
        result = generate_report_no(db, "FINAL")
        assert result.startswith("AR-")


class TestGetReportVersion:
    def test_first_version(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        assert get_report_version(db, 1, "FAT") == 1

    def test_increment_version(self):
        db = MagicMock()
        existing = MagicMock(version=3)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = existing
        assert get_report_version(db, 1, "FAT") == 4


class TestBuildReportContent:
    def test_basic_content(self):
        db = MagicMock()
        order = MagicMock()
        order.order_no = "ACC-001"
        order.status = "PASSED"
        order.actual_end_date = datetime(2025, 6, 15)
        order.pass_rate = 95
        order.total_items = 100
        order.passed_items = 95
        order.failed_items = 5
        order.qa_signer_id = 1
        order.project = MagicMock(project_name="项目A")
        order.machine = MagicMock(machine_name="机台1")
        order.acceptance_type = "FAT"
        order.id = 1

        qa_user = MagicMock(real_name="质检员", username="qa1")
        db.query.return_value.filter.return_value.first.return_value = qa_user
        db.query.return_value.filter.return_value.scalar.side_effect = [10, 8]

        user = MagicMock(real_name="管理员", username="admin")

        result = build_report_content(db, order, "FAT-20250101-001", 1, user)
        assert "FAT-20250101-001" in result
        assert "项目A" in result
        assert "95%" in result

    def test_no_project_or_machine(self):
        db = MagicMock()
        order = MagicMock()
        order.order_no = "ACC-002"
        order.status = "PENDING"
        order.actual_end_date = None
        order.pass_rate = 0
        order.total_items = 0
        order.passed_items = 0
        order.failed_items = 0
        order.qa_signer_id = None
        order.project = None
        order.machine = None
        order.acceptance_type = "SAT"
        order.id = 2

        db.query.return_value.filter.return_value.scalar.side_effect = [0, 0]

        user = MagicMock(real_name="管理员", username="admin")
        result = build_report_content(db, order, "SAT-20250101-001", 1, user)
        assert "N/A" in result
