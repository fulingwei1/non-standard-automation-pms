# -*- coding: utf-8 -*-
"""
PDF 共享样式与字体工具

所有 PDF 导出服务共用的样式定义和中文字体注册。
"""

import os
import logging
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

logger = logging.getLogger(__name__)

# ── 中文字体路径 ─────────────────────────────────────
FONT_PATHS = [
    "/System/Library/Fonts/PingFang.ttc",     # macOS
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # Linux
    "C:/Windows/Fonts/msyh.ttc",              # Windows
]

_font_registered = False
CHINESE_FONT_NAME: Optional[str] = None


def register_chinese_font() -> Optional[str]:
    """
    注册中文字体，返回字体名称。多次调用幂等。
    """
    global _font_registered, CHINESE_FONT_NAME
    if _font_registered:
        return CHINESE_FONT_NAME

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    for path in FONT_PATHS:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("Chinese", path))
                CHINESE_FONT_NAME = "Chinese"
                _font_registered = True
                return CHINESE_FONT_NAME
            except Exception as e:
                logger.debug(f"字体注册失败 {path}: {e}")

    _font_registered = True
    return None


# ── 颜色常量 ─────────────────────────────────────────
HEADER_BG = colors.HexColor("#336699")
HEADER_TEXT = colors.white
ALT_ROW_BG = colors.HexColor("#F5F5F5")
BORDER_COLOR = colors.HexColor("#CCCCCC")
