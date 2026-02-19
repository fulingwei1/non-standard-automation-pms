# -*- coding: utf-8 -*-
"""
第四十七批覆盖测试 - ppt_generator/base_builder.py
"""
import pytest

pytest.importorskip("app.services.ppt_generator.base_builder")

from unittest.mock import MagicMock, patch

from app.services.ppt_generator.base_builder import BaseSlideBuilder


def _make_builder():
    prs = MagicMock()
    prs.slide_width = 9144000
    prs.slide_height = 6858000
    slide_layout = MagicMock()
    prs.slide_layouts.__getitem__.return_value = slide_layout
    slide = MagicMock()
    prs.slides.add_slide.return_value = slide

    # shapes.add_shape returns a mock with fill/line attrs
    shape = MagicMock()
    shape.fill = MagicMock()
    shape.line = MagicMock()
    shape.line.fill = MagicMock()
    slide.shapes.add_shape.return_value = shape

    # shapes.add_textbox returns textbox with text_frame
    textbox = MagicMock()
    para = MagicMock()
    textbox.text_frame.paragraphs = [para]
    textbox.text_frame.word_wrap = True
    slide.shapes.add_textbox.return_value = textbox

    builder = BaseSlideBuilder(prs)
    return builder, prs, slide


def test_init_sets_prs_and_config():
    builder, prs, _ = _make_builder()
    assert builder.prs is prs
    assert builder.config is not None


def test_add_title_slide_returns_slide():
    builder, _, slide = _make_builder()
    result = builder.add_title_slide("测试标题", "副标题")
    assert result is slide


def test_add_title_slide_no_subtitle():
    builder, _, slide = _make_builder()
    result = builder.add_title_slide("仅标题")
    assert result is slide


def test_add_section_slide_returns_slide():
    builder, _, slide = _make_builder()
    result = builder.add_section_slide("章节标题", "章节副标题")
    assert result is slide


def test_add_white_background_calls_add_shape():
    builder, _, slide = _make_builder()
    bg = builder._add_white_background(slide)
    slide.shapes.add_shape.assert_called()


def test_add_top_bar_calls_add_shape():
    builder, _, slide = _make_builder()
    builder._add_top_bar(slide)
    slide.shapes.add_shape.assert_called()


def test_add_slide_title_calls_add_textbox():
    builder, _, slide = _make_builder()
    builder._add_slide_title(slide, "页面标题")
    slide.shapes.add_textbox.assert_called()


def test_add_page_number():
    builder, _, slide = _make_builder()
    builder._add_page_number(slide, 5)
    slide.shapes.add_textbox.assert_called()
