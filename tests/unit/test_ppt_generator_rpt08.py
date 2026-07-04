# -*- coding: utf-8 -*-
"""RPT-08: PPT generation must be data-driven, not hardcoded demo content."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.ppt_generator.generator import PresentationGenerator


@pytest.fixture
def generator_with_mocked_builders():
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

        yield PresentationGenerator(), prs, base_builder, content_builder, table_builder


def test_generate_requires_explicit_deck_spec(generator_with_mocked_builders):
    generator, *_ = generator_with_mocked_builders

    with pytest.raises(ValueError, match="deck_spec"):
        generator.generate(output_path="demo.pptx")


def test_generate_uses_supplied_deck_spec_without_demo_content(generator_with_mocked_builders):
    generator, prs, base_builder, content_builder, table_builder = generator_with_mocked_builders
    deck_spec = {
        "title": "真实项目经营复盘",
        "subtitle": "2026-07",
        "slogan": "仅使用本次传入数据",
        "toc": ["经营摘要", "风险闭环"],
        "slides": [
            {
                "type": "content",
                "title": "经营摘要",
                "content": ["合同额 800 万", {"text": "毛利率 32%", "bold": True}],
            },
            {
                "type": "table",
                "title": "风险闭环",
                "headers": ["风险", "状态"],
                "rows": [["交期", "已缓解"]],
            },
        ],
    }

    result = generator.generate(output_path="review.pptx", deck_spec=deck_spec)

    assert result == "review.pptx"
    base_builder.add_title_slide.assert_called_once_with("真实项目经营复盘", "2026-07")
    content_builder.add_content_slide.assert_any_call(
        "内容导览",
        [
            {"text": "经营摘要", "size": 24, "bold": True},
            {"text": "风险闭环", "size": 24, "bold": True},
        ],
        page_num=2,
    )
    content_builder.add_content_slide.assert_any_call(
        "经营摘要",
        ["合同额 800 万", {"text": "毛利率 32%", "bold": True}],
        page_num=3,
    )
    table_builder.add_table_slide.assert_called_once_with(
        "风险闭环",
        ["风险", "状态"],
        [["交期", "已缓解"]],
        page_num=4,
    )
    prs.save.assert_called_once_with("review.pptx")
