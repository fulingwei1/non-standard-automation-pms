"""Tests for app/services/ppt_generator/config.py"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.ppt_generator.config import PresentationConfig
    from pptx.dml.color import RGBColor
    from pptx.util import Inches, Pt
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def test_color_constants_are_rgb():
    """颜色常量是 RGBColor 实例"""
    assert isinstance(PresentationConfig.DARK_BLUE, RGBColor)
    assert isinstance(PresentationConfig.TECH_BLUE, RGBColor)
    assert isinstance(PresentationConfig.SILVER, RGBColor)
    assert isinstance(PresentationConfig.ORANGE, RGBColor)
    assert isinstance(PresentationConfig.GREEN, RGBColor)
    assert isinstance(PresentationConfig.WHITE, RGBColor)
    assert isinstance(PresentationConfig.LIGHT_BLUE, RGBColor)


def test_dark_blue_value():
    """DARK_BLUE 颜色值正确"""
    assert PresentationConfig.DARK_BLUE == RGBColor(10, 22, 40)


def test_slide_dimensions():
    """幻灯片尺寸配置正确"""
    assert PresentationConfig.SLIDE_WIDTH == Inches(10)
    assert PresentationConfig.SLIDE_HEIGHT == Inches(7.5)


def test_font_sizes_are_pt():
    """字体大小是 Pt 类型"""
    assert PresentationConfig.TITLE_FONT_SIZE == Pt(44)
    assert PresentationConfig.SUBTITLE_FONT_SIZE == Pt(24)
    assert PresentationConfig.HEADING_FONT_SIZE == Pt(32)
    assert PresentationConfig.SECTION_TITLE_FONT_SIZE == Pt(40)
    assert PresentationConfig.CONTENT_FONT_SIZE == Pt(18)


def test_table_font_sizes():
    """表格字体大小正确"""
    assert PresentationConfig.TABLE_HEADER_FONT_SIZE == Pt(14)
    assert PresentationConfig.TABLE_CELL_FONT_SIZE == Pt(12)
    assert PresentationConfig.PAGE_NUMBER_FONT_SIZE == Pt(12)


def test_top_bar_height():
    """顶部装饰条高度正确"""
    assert PresentationConfig.TOP_BAR_HEIGHT == Inches(0.1)


def test_instantiation():
    """可以正常实例化"""
    config = PresentationConfig()
    assert config is not None
    assert config.WHITE == RGBColor(255, 255, 255)
