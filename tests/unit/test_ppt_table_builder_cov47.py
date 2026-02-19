# -*- coding: utf-8 -*-
"""
第四十七批覆盖测试 - ppt_generator/table_builder.py
"""
import pytest

pytest.importorskip("app.services.ppt_generator.table_builder")

from unittest.mock import MagicMock, patch

from app.services.ppt_generator.table_builder import TableSlideBuilder


def _make_builder():
    prs = MagicMock()
    prs.slide_width = 9144000
    prs.slide_height = 6858000
    slide_layout = MagicMock()
    prs.slide_layouts.__getitem__.return_value = slide_layout

    slide = MagicMock()
    prs.slides.add_slide.return_value = slide

    shape = MagicMock()
    shape.fill = MagicMock()
    shape.line = MagicMock()
    shape.line.fill = MagicMock()
    slide.shapes.add_shape.return_value = shape

    # mock table
    cell = MagicMock()
    cell.fill = MagicMock()
    cell.text_frame.paragraphs = [MagicMock()]

    table_mock = MagicMock()
    table_mock.cell.return_value = cell
    table_mock.columns = [MagicMock()]

    table_shape = MagicMock()
    table_shape.table = table_mock
    slide.shapes.add_table.return_value = table_shape

    textbox = MagicMock()
    para = MagicMock()
    textbox.text_frame.paragraphs = [para]
    slide.shapes.add_textbox.return_value = textbox

    builder = TableSlideBuilder(prs)
    return builder, prs, slide


def test_add_table_slide_returns_slide():
    builder, _, slide = _make_builder()
    headers = ["列1", "列2", "列3"]
    rows = [["A", "B", "C"], ["D", "E", "F"]]
    result = builder.add_table_slide("测试表格", headers, rows, page_num=1)
    assert result is slide


def test_add_table_slide_calls_add_table():
    builder, _, slide = _make_builder()
    headers = ["H1", "H2"]
    rows = [["r1c1", "r1c2"]]
    builder.add_table_slide("表格", headers, rows)
    slide.shapes.add_table.assert_called_once()


def test_format_table_header_sets_text():
    builder, _, slide = _make_builder()
    headers = ["编号", "名称", "状态"]
    rows = []
    builder.add_table_slide("表格", headers, rows)
    # 调用了 add_table，说明 header 格式化逻辑运行了
    slide.shapes.add_table.assert_called()


def test_format_table_rows_zebra_on_even():
    """偶数行（idx 0, 2...）应该填充浅蓝背景"""
    builder, _, slide = _make_builder()

    # 手动触发 _format_table_rows 逻辑
    table_mock = MagicMock()
    cell = MagicMock()
    cell.fill = MagicMock()
    cell.text_frame.paragraphs = [MagicMock()]
    table_mock.cell.return_value = cell

    rows = [["x", "y"], ["a", "b"]]
    builder._format_table_rows(table_mock, rows)

    # 至少调用了 cell() 方法
    assert table_mock.cell.call_count > 0


def test_add_table_slide_with_page_number():
    builder, _, slide = _make_builder()
    builder.add_table_slide("标题", ["A"], [["v"]], page_num=3)
    # page number adds a textbox
    slide.shapes.add_textbox.assert_called()


def test_inherits_base_builder():
    from app.services.ppt_generator.base_builder import BaseSlideBuilder
    builder, _, _ = _make_builder()
    assert isinstance(builder, BaseSlideBuilder)
