# -*- coding: utf-8 -*-
"""
第四十七批覆盖测试 - ppt_generator/config.py
"""
import pytest

pytest.importorskip("app.services.ppt_generator.config")

from app.services.ppt_generator.config import PresentationConfig


def test_config_instantiable():
    cfg = PresentationConfig()
    assert cfg is not None


def test_colors_are_rgb():
    from pptx.dml.color import RGBColor as RgbColor
    cfg = PresentationConfig()
    for attr in ("DARK_BLUE", "TECH_BLUE", "SILVER", "ORANGE", "GREEN", "WHITE", "LIGHT_BLUE"):
        val = getattr(cfg, attr)
        assert isinstance(val, RgbColor), f"{attr} should be RGBColor"


def test_font_sizes_positive():
    from pptx.util import Pt
    cfg = PresentationConfig()
    sizes = [
        cfg.TITLE_FONT_SIZE,
        cfg.SUBTITLE_FONT_SIZE,
        cfg.HEADING_FONT_SIZE,
        cfg.SECTION_TITLE_FONT_SIZE,
        cfg.CONTENT_FONT_SIZE,
        cfg.TABLE_HEADER_FONT_SIZE,
        cfg.TABLE_CELL_FONT_SIZE,
        cfg.PAGE_NUMBER_FONT_SIZE,
    ]
    for sz in sizes:
        assert sz > 0, f"Expected positive size, got {sz}"


def test_title_larger_than_content():
    cfg = PresentationConfig()
    assert cfg.TITLE_FONT_SIZE > cfg.CONTENT_FONT_SIZE


def test_slide_dimensions_positive():
    cfg = PresentationConfig()
    assert cfg.SLIDE_WIDTH > 0
    assert cfg.SLIDE_HEIGHT > 0


def test_dark_blue_rgb_values():
    cfg = PresentationConfig()
    # DARK_BLUE = (10, 22, 40)
    assert cfg.DARK_BLUE[0] == 10
    assert cfg.DARK_BLUE[1] == 22
    assert cfg.DARK_BLUE[2] == 40


def test_white_rgb_values():
    cfg = PresentationConfig()
    assert cfg.WHITE[0] == 255
    assert cfg.WHITE[1] == 255
    assert cfg.WHITE[2] == 255
