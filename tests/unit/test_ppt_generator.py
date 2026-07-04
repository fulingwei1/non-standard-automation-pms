# -*- coding: utf-8 -*-
"""Tests for the data-driven PPT generator."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.ppt_generator.generator import PresentationGenerator


@pytest.fixture
def generator_context():
    with (
        patch("app.services.ppt_generator.generator.Presentation") as presentation_cls,
        patch("app.services.ppt_generator.generator.BaseSlideBuilder") as base_cls,
        patch("app.services.ppt_generator.generator.ContentSlideBuilder") as content_cls,
        patch("app.services.ppt_generator.generator.TableSlideBuilder") as table_cls,
    ):
        prs = MagicMock()
        presentation_cls.return_value = prs
        base_builder = MagicMock()
        content_builder = MagicMock()
        table_builder = MagicMock()
        base_cls.return_value = base_builder
        content_cls.return_value = content_builder
        table_cls.return_value = table_builder

        generator = PresentationGenerator()
        yield generator, prs, base_builder, content_builder, table_builder


def test_init_creates_presentation_and_builders(generator_context):
    generator, prs, base_builder, content_builder, table_builder = generator_context

    assert generator.prs is prs
    assert generator.base_builder is base_builder
    assert generator.content_builder is content_builder
    assert generator.table_builder is table_builder


def test_create_cover_slide_uses_supplied_text(generator_context):
    generator, _, base_builder, _, _ = generator_context
    slide = MagicMock()
    base_builder.add_title_slide.return_value = slide

    result = generator.create_cover_slide("复盘标题", "7 月", "仅本次数据")

    assert result is slide
    base_builder.add_title_slide.assert_called_once_with("复盘标题", "7 月")
    slide.shapes.add_textbox.assert_called_once()
    paragraph = slide.shapes.add_textbox.return_value.text_frame.paragraphs[0]
    assert paragraph.text == "仅本次数据"


def test_create_toc_slide_uses_supplied_items(generator_context):
    generator, _, _, content_builder, _ = generator_context

    generator.create_toc_slide(["摘要", "风险"], page_num=9)

    content_builder.add_content_slide.assert_called_once_with(
        "内容导览",
        [
            {"text": "摘要", "size": 24, "bold": True},
            {"text": "风险", "size": 24, "bold": True},
        ],
        page_num=9,
    )


def test_generate_requires_explicit_deck_spec(generator_context):
    generator, *_ = generator_context

    with pytest.raises(ValueError, match="deck_spec"):
        generator.generate("demo.pptx")


def test_generate_creates_slides_from_deck_spec(generator_context):
    generator, prs, base_builder, content_builder, table_builder = generator_context
    deck_spec = {
        "title": "经营复盘",
        "subtitle": "2026-07",
        "slides": [
            {"type": "section", "title": "第一部分", "subtitle": "摘要"},
            {"type": "content", "title": "摘要", "content": ["真实指标"]},
            {"type": "table", "title": "风险", "headers": ["项", "状态"], "rows": [["交付", "正常"]]},
        ],
    }

    result = generator.generate("路径/中文PPT文件.pptx", deck_spec=deck_spec)

    assert result == "路径/中文PPT文件.pptx"
    base_builder.add_title_slide.assert_called_once_with("经营复盘", "2026-07")
    base_builder.add_section_slide.assert_called_once_with("第一部分", "摘要")
    content_builder.add_content_slide.assert_any_call(
        "内容导览",
        [
            {"text": "第一部分", "size": 24, "bold": True},
            {"text": "摘要", "size": 24, "bold": True},
            {"text": "风险", "size": 24, "bold": True},
        ],
        page_num=2,
    )
    content_builder.add_content_slide.assert_any_call("摘要", ["真实指标"], page_num=4)
    table_builder.add_table_slide.assert_called_once_with(
        "风险",
        ["项", "状态"],
        [["交付", "正常"]],
        page_num=5,
    )
    prs.save.assert_called_once_with("路径/中文PPT文件.pptx")
