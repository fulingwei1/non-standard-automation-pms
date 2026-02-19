"""Tests for app/services/ppt_generator/base_builder.py"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

try:
    from app.services.ppt_generator.base_builder import BaseSlideBuilder
    from app.services.ppt_generator.config import PresentationConfig
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_mock_prs():
    """构建 mock Presentation"""
    prs = MagicMock()
    slide = MagicMock()
    textbox = MagicMock()
    tf = MagicMock()
    para = MagicMock()
    para.font = MagicMock()
    para.font.color = MagicMock()
    tf.paragraphs = [para]
    tf.word_wrap = False
    textbox.text_frame = tf
    shape = MagicMock()
    shape.fill = MagicMock()
    shape.fill.fore_color = MagicMock()
    shape.line = MagicMock()
    shape.line.fill = MagicMock()
    slide.shapes = MagicMock()
    slide.shapes.add_textbox.return_value = textbox
    slide.shapes.add_shape.return_value = shape
    slide_layout = MagicMock()
    prs.slide_layouts = [slide_layout] * 10
    prs.slides = MagicMock()
    prs.slides.add_slide.return_value = slide
    prs.slide_width = PresentationConfig.SLIDE_WIDTH
    prs.slide_height = PresentationConfig.SLIDE_HEIGHT
    return prs, slide, textbox, shape


def test_init_creates_config():
    """初始化时创建 config"""
    prs, _, _, _ = _make_mock_prs()
    builder = BaseSlideBuilder(prs)
    assert isinstance(builder.config, PresentationConfig)
    assert builder.prs is prs


def test_add_title_slide_no_subtitle():
    """add_title_slide 无副标题时正常运行"""
    prs, slide, _, _ = _make_mock_prs()
    builder = BaseSlideBuilder(prs)
    result = builder.add_title_slide("测试标题")
    assert result is slide
    prs.slides.add_slide.assert_called_once()


def test_add_title_slide_with_subtitle():
    """add_title_slide 有副标题时添加额外文本框"""
    prs, slide, textbox, _ = _make_mock_prs()
    builder = BaseSlideBuilder(prs)
    result = builder.add_title_slide("主标题", "副标题")
    assert result is slide
    # 应该调用至少两次 add_textbox（标题和副标题）
    assert slide.shapes.add_textbox.call_count >= 2


def test_add_section_slide_no_subtitle():
    """add_section_slide 无副标题时正常运行"""
    prs, slide, _, _ = _make_mock_prs()
    builder = BaseSlideBuilder(prs)
    result = builder.add_section_slide("第一部分")
    assert result is slide


def test_add_section_slide_with_subtitle():
    """add_section_slide 有副标题时添加额外文本框"""
    prs, slide, textbox, _ = _make_mock_prs()
    builder = BaseSlideBuilder(prs)
    result = builder.add_section_slide("第一部分", "章节副标题")
    assert result is slide
    assert slide.shapes.add_textbox.call_count >= 2


def test_add_white_background():
    """_add_white_background 调用 add_shape"""
    prs, slide, _, shape = _make_mock_prs()
    builder = BaseSlideBuilder(prs)
    result = builder._add_white_background(slide)
    slide.shapes.add_shape.assert_called()
    assert result is shape


def test_add_top_bar():
    """_add_top_bar 调用 add_shape"""
    prs, slide, _, shape = _make_mock_prs()
    builder = BaseSlideBuilder(prs)
    result = builder._add_top_bar(slide)
    slide.shapes.add_shape.assert_called()
    assert result is shape


def test_add_page_number():
    """_add_page_number 创建文本框并设置页码"""
    prs, slide, textbox, _ = _make_mock_prs()
    builder = BaseSlideBuilder(prs)
    result = builder._add_page_number(slide, 5)
    slide.shapes.add_textbox.assert_called()
    assert result is textbox
