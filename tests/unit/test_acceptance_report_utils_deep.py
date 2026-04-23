# -*- coding: utf-8 -*-
"""Deep tests for app.services.acceptance.report_utils."""

from __future__ import annotations

import builtins
import sys
from datetime import date
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.acceptance import report_utils


pytestmark = pytest.mark.unit


def _make_order(**overrides):
    project = SimpleNamespace(project_name="测试项目")
    machine = SimpleNamespace(machine_name="测试设备")
    order = SimpleNamespace(
        id=1,
        order_no="ACC-001",
        acceptance_type="FAT",
        status="COMPLETED",
        actual_end_date=date(2026, 4, 11),
        pass_rate=95,
        total_items=20,
        passed_items=19,
        failed_items=1,
        qa_signer_id=8,
        customer_signer="客户代表",
        project=project,
        machine=machine,
    )
    for key, value in overrides.items():
        setattr(order, key, value)
    return order


def _install_fake_reportlab(monkeypatch: pytest.MonkeyPatch, *, fail_build: bool = False) -> None:
    reportlab = ModuleType("reportlab")
    lib = ModuleType("reportlab.lib")
    colors = ModuleType("reportlab.lib.colors")
    colors.grey = "grey"
    colors.black = "black"
    colors.beige = "beige"
    colors.HexColor = lambda value: value

    pagesizes = ModuleType("reportlab.lib.pagesizes")
    pagesizes.A4 = "A4"

    styles = ModuleType("reportlab.lib.styles")

    class ParagraphStyle:
        def __init__(self, name, parent=None, **kwargs):
            self.name = name
            self.parent = parent
            self.kwargs = kwargs

    styles.ParagraphStyle = ParagraphStyle
    styles.getSampleStyleSheet = lambda: {
        "Heading1": object(),
        "Heading2": object(),
        "Normal": object(),
    }

    units = ModuleType("reportlab.lib.units")
    units.inch = 72

    platypus = ModuleType("reportlab.platypus")

    class Paragraph:
        def __init__(self, text, style):
            self.text = text
            self.style = style

    class Spacer:
        def __init__(self, width, height):
            self.width = width
            self.height = height

    class TableStyle:
        def __init__(self, rows):
            self.rows = rows

    class Table:
        def __init__(self, data, colWidths=None):
            self.data = data
            self.colWidths = colWidths
            self.style = None

        def setStyle(self, style):
            self.style = style

    class SimpleDocTemplate:
        def __init__(self, buffer, pagesize=None):
            self.buffer = buffer
            self.pagesize = pagesize

        def build(self, story):
            if fail_build:
                raise RuntimeError("pdf build failed")
            self.buffer.write(b"%PDF-1.4 fake pdf bytes")

    platypus.Paragraph = Paragraph
    platypus.SimpleDocTemplate = SimpleDocTemplate
    platypus.Spacer = Spacer
    platypus.Table = Table
    platypus.TableStyle = TableStyle

    monkeypatch.setitem(sys.modules, "reportlab", reportlab)
    monkeypatch.setitem(sys.modules, "reportlab.lib", lib)
    monkeypatch.setitem(sys.modules, "reportlab.lib.colors", colors)
    monkeypatch.setitem(sys.modules, "reportlab.lib.pagesizes", pagesizes)
    monkeypatch.setitem(sys.modules, "reportlab.lib.styles", styles)
    monkeypatch.setitem(sys.modules, "reportlab.lib.units", units)
    monkeypatch.setitem(sys.modules, "reportlab.platypus", platypus)


def test_generate_report_no_for_fat(monkeypatch: pytest.MonkeyPatch):
    count_query = MagicMock()
    count_query.scalar.return_value = 5
    monkeypatch.setattr(report_utils, "apply_like_filter", lambda *args, **kwargs: count_query)

    db = MagicMock()
    result = report_utils.generate_report_no(db, "FAT")

    assert result.startswith("FAT-")
    assert result.endswith("-006")


def test_generate_report_no_defaults_to_ar_when_count_missing(monkeypatch: pytest.MonkeyPatch):
    count_query = MagicMock()
    count_query.scalar.return_value = None
    monkeypatch.setattr(report_utils, "apply_like_filter", lambda *args, **kwargs: count_query)

    db = MagicMock()
    result = report_utils.generate_report_no(db, "FINAL")

    assert result.startswith("AR-")
    assert result.endswith("-001")


def test_get_report_version_returns_next_version():
    report = SimpleNamespace(version=3)
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = report

    assert report_utils.get_report_version(db, 1, "FAT") == 4


def test_get_report_version_returns_one_when_missing():
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

    assert report_utils.get_report_version(db, 1, "FAT") == 1


def test_save_report_file_generates_pdf_with_fake_reportlab(tmp_path, monkeypatch: pytest.MonkeyPatch):
    _install_fake_reportlab(monkeypatch)
    monkeypatch.setattr(report_utils.settings, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(report_utils, "get_report_version", lambda *args, **kwargs: 2)

    db = MagicMock()
    current_user = SimpleNamespace(real_name="测试员", username="tester")
    order = _make_order()

    rel_path, size, digest = report_utils.save_report_file(
        report_content="hello report",
        report_no="FAT-20260411-001",
        report_type="FAT",
        include_signatures=False,
        order=order,
        db=db,
        current_user=current_user,
    )

    assert rel_path == "reports/FAT-20260411-001.pdf"
    assert size > 0
    assert len(digest) == 64
    assert (tmp_path / rel_path).exists()


def test_save_report_file_falls_back_to_text_when_pdf_build_fails(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    _install_fake_reportlab(monkeypatch, fail_build=True)
    monkeypatch.setattr(report_utils.settings, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(report_utils, "get_report_version", lambda *args, **kwargs: 1)

    db = MagicMock()
    current_user = SimpleNamespace(real_name="测试员", username="tester")
    order = _make_order(order_no="ACC-测试-001")

    rel_path, size, digest = report_utils.save_report_file(
        report_content="纯文本内容",
        report_no="FAT-20260411-002",
        report_type="FAT",
        include_signatures=False,
        order=order,
        db=db,
        current_user=current_user,
    )

    assert rel_path == "reports/FAT-20260411-002.txt"
    assert size == len("纯文本内容".encode("utf-8"))
    assert len(digest) == 64
    assert (tmp_path / rel_path).read_text(encoding="utf-8") == "纯文本内容"


def test_save_report_file_falls_back_to_text_when_reportlab_missing(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("reportlab"):
            raise ImportError("reportlab missing")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(report_utils.settings, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(report_utils, "get_report_version", lambda *args, **kwargs: 1)
    monkeypatch.setattr(builtins, "__import__", fake_import)

    db = MagicMock()
    current_user = SimpleNamespace(real_name="测试员", username="tester")
    order = _make_order()

    rel_path, _, _ = report_utils.save_report_file(
        report_content="缺依赖时的文本内容",
        report_no="FAT-20260411-003",
        report_type="FAT",
        include_signatures=False,
        order=order,
        db=db,
        current_user=current_user,
    )

    assert rel_path == "reports/FAT-20260411-003.txt"
    assert (tmp_path / rel_path).read_text(encoding="utf-8") == "缺依赖时的文本内容"


def test_build_report_content_includes_signer_and_issue_stats():
    signer = SimpleNamespace(real_name="质检签字人", username="qa_user")

    signer_query = MagicMock()
    signer_query.filter.return_value.first.return_value = signer

    total_query = MagicMock()
    total_query.filter.return_value.scalar.return_value = 5

    resolved_query = MagicMock()
    resolved_query.filter.return_value.scalar.return_value = 3

    db = MagicMock()
    db.query.side_effect = [signer_query, total_query, resolved_query]

    order = _make_order()
    current_user = SimpleNamespace(real_name="报告生成人", username="creator")

    content = report_utils.build_report_content(db, order, "FAT-20260411-003", 2, current_user)

    assert "报告编号：FAT-20260411-003" in content
    assert "项目名称：测试项目" in content
    assert "机台名称：测试设备" in content
    assert "总问题数：5" in content
    assert "已解决：3" in content
    assert "待解决：2" in content
    assert "质检签字：质检签字人" in content
    assert "生成人：报告生成人" in content


def test_build_report_content_uses_na_when_optional_fields_missing():
    total_query = MagicMock()
    total_query.filter.return_value.scalar.return_value = 0

    resolved_query = MagicMock()
    resolved_query.filter.return_value.scalar.return_value = 0

    db = MagicMock()
    db.query.side_effect = [total_query, resolved_query]

    order = _make_order(
        project=None,
        machine=None,
        qa_signer_id=None,
        customer_signer=None,
        actual_end_date=None,
        pass_rate=0,
    )
    current_user = SimpleNamespace(real_name=None, username="creator")

    content = report_utils.build_report_content(db, order, "AR-20260411-001", 1, current_user)

    assert "项目名称：N/A" in content
    assert "机台名称：N/A" in content
    assert "验收日期：N/A" in content
    assert "质检签字：N/A" in content
    assert "客户签字：None" in content
    assert "生成人：creator" in content
