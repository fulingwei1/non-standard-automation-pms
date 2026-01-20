"""
PPT配置文件 - 颜色和样式定义
"""

from pptx.dml.color import RgbColor
from pptx.util import Inches, Pt


class PresentationConfig:
    """PPT配置类 - 统一管理颜色、尺寸等配置"""

    # 颜色定义
    DARK_BLUE = RgbColor(10, 22, 40)  # #0A1628
    TECH_BLUE = RgbColor(0, 212, 255)  # #00D4FF
    SILVER = RgbColor(192, 192, 192)  # #C0C0C0
    ORANGE = RgbColor(255, 107, 53)  # #FF6B35
    GREEN = RgbColor(0, 196, 140)  # #00C48C
    WHITE = RgbColor(255, 255, 255)
    LIGHT_BLUE = RgbColor(230, 247, 255)

    # 字体大小
    TITLE_FONT_SIZE = Pt(44)
    SUBTITLE_FONT_SIZE = Pt(24)
    HEADING_FONT_SIZE = Pt(32)
    SECTION_TITLE_FONT_SIZE = Pt(40)
    CONTENT_FONT_SIZE = Pt(18)
    TABLE_HEADER_FONT_SIZE = Pt(14)
    TABLE_CELL_FONT_SIZE = Pt(12)
    PAGE_NUMBER_FONT_SIZE = Pt(12)

    # 尺寸
    SLIDE_WIDTH = Inches(10)
    SLIDE_HEIGHT = Inches(7.5)
    TOP_BAR_HEIGHT = Inches(0.1)
