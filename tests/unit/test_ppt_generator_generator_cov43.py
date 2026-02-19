# -*- coding: utf-8 -*-
"""
第四十三批覆盖率测试 - app/services/ppt_generator/generator.py
"""
import pytest

pytest.importorskip("app.services.ppt_generator.generator")

from unittest.mock import MagicMock, patch, call
import os


# ── 公共 patch 上下文 ─────────────────────────────────────────────────────────
PATCHES = [
    "app.services.ppt_generator.generator.Presentation",
    "app.services.ppt_generator.generator.BaseSlideBuilder",
    "app.services.ppt_generator.generator.ContentSlideBuilder",
    "app.services.ppt_generator.generator.TableSlideBuilder",
    "app.services.ppt_generator.generator.PresentationConfig",
]


def make_generator():
    """Create a PresentationGenerator with all heavy deps mocked."""
    mocks = {}
    patch_objs = []
    for p in PATCHES:
        patcher = patch(p)
        mock = patcher.start()
        patch_objs.append(patcher)
        mocks[p] = mock

    from app.services.ppt_generator.generator import PresentationGenerator
    gen = PresentationGenerator()

    # Stop patches after instantiation; further calls use mock attrs
    for patcher in patch_objs:
        patcher.stop()

    return gen


# ── 1. PresentationGenerator 可以正常实例化 ──────────────────────────────────
def test_generator_instantiation():
    with patch("app.services.ppt_generator.generator.Presentation"), \
         patch("app.services.ppt_generator.generator.BaseSlideBuilder"), \
         patch("app.services.ppt_generator.generator.ContentSlideBuilder"), \
         patch("app.services.ppt_generator.generator.TableSlideBuilder"), \
         patch("app.services.ppt_generator.generator.PresentationConfig"):
        from app.services.ppt_generator.generator import PresentationGenerator
        gen = PresentationGenerator()
        assert gen is not None
        assert hasattr(gen, "base_builder")
        assert hasattr(gen, "content_builder")
        assert hasattr(gen, "table_builder")


# ── 2. create_cover_slide 调用 base_builder.add_title_slide ──────────────────
def test_create_cover_slide():
    with patch("app.services.ppt_generator.generator.Presentation"), \
         patch("app.services.ppt_generator.generator.BaseSlideBuilder") as MockBase, \
         patch("app.services.ppt_generator.generator.ContentSlideBuilder"), \
         patch("app.services.ppt_generator.generator.TableSlideBuilder"), \
         patch("app.services.ppt_generator.generator.PresentationConfig"):
        from app.services.ppt_generator.generator import PresentationGenerator
        gen = PresentationGenerator()

        mock_slide = MagicMock()
        mock_textbox = MagicMock()
        mock_slide.shapes.add_textbox.return_value = mock_textbox
        gen.base_builder.add_title_slide.return_value = mock_slide

        gen.create_cover_slide()
        gen.base_builder.add_title_slide.assert_called_once()


# ── 3. create_toc_slide 调用 content_builder.add_content_slide ───────────────
def test_create_toc_slide():
    with patch("app.services.ppt_generator.generator.Presentation"), \
         patch("app.services.ppt_generator.generator.BaseSlideBuilder"), \
         patch("app.services.ppt_generator.generator.ContentSlideBuilder") as MockContent, \
         patch("app.services.ppt_generator.generator.TableSlideBuilder"), \
         patch("app.services.ppt_generator.generator.PresentationConfig"):
        from app.services.ppt_generator.generator import PresentationGenerator
        gen = PresentationGenerator()

        gen.create_toc_slide()
        gen.content_builder.add_content_slide.assert_called_once()


# ── 4. create_part1_industry_insights 调用 content/table builder ─────────────
def test_create_part1():
    with patch("app.services.ppt_generator.generator.Presentation"), \
         patch("app.services.ppt_generator.generator.BaseSlideBuilder"), \
         patch("app.services.ppt_generator.generator.ContentSlideBuilder"), \
         patch("app.services.ppt_generator.generator.TableSlideBuilder"), \
         patch("app.services.ppt_generator.generator.PresentationConfig"):
        from app.services.ppt_generator.generator import PresentationGenerator
        gen = PresentationGenerator()

        gen.create_part1_industry_insights()
        # Should call content_builder at least once (slides 3, 4, 6)
        assert gen.content_builder.add_content_slide.call_count >= 2
        # And table_builder for slide 5
        gen.table_builder.add_table_slide.assert_called_once()


# ── 5. create_part2_solution_overview 调用 section slide ─────────────────────
def test_create_part2():
    with patch("app.services.ppt_generator.generator.Presentation"), \
         patch("app.services.ppt_generator.generator.BaseSlideBuilder"), \
         patch("app.services.ppt_generator.generator.ContentSlideBuilder"), \
         patch("app.services.ppt_generator.generator.TableSlideBuilder"), \
         patch("app.services.ppt_generator.generator.PresentationConfig"):
        from app.services.ppt_generator.generator import PresentationGenerator
        gen = PresentationGenerator()

        gen.create_part2_solution_overview()
        gen.base_builder.add_section_slide.assert_called()


# ── 6. generate 调用 prs.save 并返回路径 ─────────────────────────────────────
def test_generate_saves_file():
    with patch("app.services.ppt_generator.generator.Presentation"), \
         patch("app.services.ppt_generator.generator.BaseSlideBuilder"), \
         patch("app.services.ppt_generator.generator.ContentSlideBuilder"), \
         patch("app.services.ppt_generator.generator.TableSlideBuilder"), \
         patch("app.services.ppt_generator.generator.PresentationConfig"):
        from app.services.ppt_generator.generator import PresentationGenerator
        gen = PresentationGenerator()

        out = gen.generate("test_output.pptx")
        gen.prs.save.assert_called_once_with("test_output.pptx")
        assert out == "test_output.pptx"


# ── 7. generate 默认输出路径 ─────────────────────────────────────────────────
def test_generate_default_path():
    with patch("app.services.ppt_generator.generator.Presentation"), \
         patch("app.services.ppt_generator.generator.BaseSlideBuilder"), \
         patch("app.services.ppt_generator.generator.ContentSlideBuilder"), \
         patch("app.services.ppt_generator.generator.TableSlideBuilder"), \
         patch("app.services.ppt_generator.generator.PresentationConfig"):
        from app.services.ppt_generator.generator import PresentationGenerator
        gen = PresentationGenerator()

        out = gen.generate()
        assert out == "完整PPT.pptx"
        gen.prs.save.assert_called_with("完整PPT.pptx")


# ── 8. 各 part 方法均可无异常调用 ────────────────────────────────────────────
def test_all_parts_no_exception():
    with patch("app.services.ppt_generator.generator.Presentation"), \
         patch("app.services.ppt_generator.generator.BaseSlideBuilder"), \
         patch("app.services.ppt_generator.generator.ContentSlideBuilder"), \
         patch("app.services.ppt_generator.generator.TableSlideBuilder"), \
         patch("app.services.ppt_generator.generator.PresentationConfig"):
        from app.services.ppt_generator.generator import PresentationGenerator
        gen = PresentationGenerator()

        gen.create_part3_core_features()
        gen.create_part4_customer_portal()
        gen.create_part5_ai_capabilities()
        gen.create_part6_customer_value()
        gen.create_part7_cooperation()
        # No assertions needed; just ensure they don't raise
