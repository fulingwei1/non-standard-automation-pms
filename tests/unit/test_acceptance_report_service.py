# -*- coding: utf-8 -*-
"""Tests for app.services.acceptance_report_service."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services import acceptance_report_service as service


pytestmark = pytest.mark.unit


@pytest.fixture
def mock_order():
    return SimpleNamespace(
        id=1,
        order_no="AO-TEST-001",
        acceptance_type="FAT",
        status="COMPLETED",
        actual_end_date=None,
        pass_rate=95.0,
        total_items=20,
        passed_items=19,
        failed_items=1,
        customer_signer="客户签字人",
        project=SimpleNamespace(project_name="测试项目"),
        machine=SimpleNamespace(machine_name="测试设备"),
    )


@pytest.fixture
def mock_user():
    return SimpleNamespace(id=1, username="test_user", real_name="测试用户")


def test_generate_report_no_fat(monkeypatch: pytest.MonkeyPatch):
    count_query = MagicMock()
    count_query.scalar.return_value = 5
    monkeypatch.setattr(service, "apply_like_filter", lambda *args, **kwargs: count_query)

    db = MagicMock()
    report_no = service.generate_report_no(db, "FAT")

    assert report_no.startswith("FAT-")
    assert report_no.endswith("-006")


def test_generate_report_no_other_keeps_original_prefix(monkeypatch: pytest.MonkeyPatch):
    count_query = MagicMock()
    count_query.scalar.return_value = 0
    monkeypatch.setattr(service, "apply_like_filter", lambda *args, **kwargs: count_query)

    db = MagicMock()
    report_no = service.generate_report_no(db, "OTHER")

    assert report_no.startswith("OTHER-")
    assert report_no.endswith("-001")


def test_generate_report_no_non_integer_count_resets_to_one(monkeypatch: pytest.MonkeyPatch):
    count_query = MagicMock()
    count_query.scalar.return_value = "weird"
    monkeypatch.setattr(service, "apply_like_filter", lambda *args, **kwargs: count_query)

    db = MagicMock()
    report_no = service.generate_report_no(db, "SAT")

    assert report_no.startswith("SAT-")
    assert report_no.endswith("-001")


def test_get_report_version_returns_next_version():
    latest = SimpleNamespace(version=2)
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = latest

    assert service.get_report_version(db, order_id=1, report_type="FAT") == 3


def test_get_report_version_returns_one_when_missing():
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

    assert service.get_report_version(db, order_id=1, report_type="FAT") == 1


def test_build_report_content_includes_customer_and_user(mock_order, mock_user):
    content = service.build_report_content(
        db=MagicMock(),
        order=mock_order,
        report_no="FAT-TEST-001",
        version=2,
        user=mock_user,
    )

    assert "验收报告: FAT-TEST-001" in content
    assert "版本: V2" in content
    assert "验收单号: AO-TEST-001" in content
    assert "验收类型: FAT" in content
    assert "客户签字: 客户签字人" in content
    assert "生成人: 测试用户" in content


def test_build_report_content_omits_optional_lines_when_missing(mock_order):
    mock_order.customer_signer = None

    content = service.build_report_content(
        db=MagicMock(),
        order=mock_order,
        report_no="SAT-TEST-001",
        version=1,
        user=None,
    )

    assert "客户签字:" not in content
    assert "生成人:" not in content


def test_reportlab_available_flag_is_boolean():
    assert isinstance(service.REPORTLAB_AVAILABLE, bool)


def test_save_report_file_uses_txt_when_pdf_unavailable(tmp_path, mock_order, mock_user, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(service, "REPORTLAB_AVAILABLE", False)

    relative_path, filename = service.save_report_file(
        content="测试报告内容",
        order_no=mock_order.order_no,
        report_type="FAT",
        use_pdf=True,
        order=mock_order,
        db=MagicMock(),
        user=mock_user,
    )

    assert relative_path == f"reports/{mock_order.order_no}_FAT.txt"
    assert filename == f"{mock_order.order_no}_FAT.txt"
    assert (tmp_path / "uploads" / "reports" / filename).read_text(encoding="utf-8") == "测试报告内容"


def test_save_report_file_uses_pdf_extension_when_available(tmp_path, mock_order, mock_user, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(service, "REPORTLAB_AVAILABLE", True)

    relative_path, filename = service.save_report_file(
        content="pdf content",
        order_no=mock_order.order_no,
        report_type="SAT",
        use_pdf=True,
        order=mock_order,
        db=MagicMock(),
        user=mock_user,
    )

    assert relative_path == f"reports/{mock_order.order_no}_SAT.pdf"
    assert filename == f"{mock_order.order_no}_SAT.pdf"
    assert (tmp_path / "uploads" / "reports" / filename).read_text(encoding="utf-8") == "pdf content"
