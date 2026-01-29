# -*- coding: utf-8 -*-
"""
PPT生成器单元测试

测试内容：
- PresentationConfig: 配置常量验证
- BaseSlideBuilder: 基础幻灯片创建功能
- ContentSlideBuilder: 内容幻灯片构建
- TableSlideBuilder: 表格幻灯片构建
- PresentationGenerator: 完整PPT生成流程
"""

import os
import tempfile

import pytest

# Skip this module if python-pptx is not installed
pptx = pytest.importorskip("pptx")
from pptx import Presentation
from pptx.dml.color import RGBColor as RgbColor  # python-pptx 使用 RGBColor
from pptx.util import Inches, Pt

from app.services.ppt_generator import PresentationGenerator
from app.services.ppt_generator.base_builder import BaseSlideBuilder
from app.services.ppt_generator.config import PresentationConfig
from app.services.ppt_generator.content_builder import ContentSlideBuilder
from app.services.ppt_generator.table_builder import TableSlideBuilder


# ============================================================================
# PresentationConfig 测试
# ============================================================================


@pytest.mark.unit
class TestPresentationConfig:
    """测试PPT配置类"""

    def test_color_definitions(self):
        """测试颜色定义"""
        config = PresentationConfig()

        # 验证颜色是 RgbColor 类型
        assert isinstance(config.DARK_BLUE, RgbColor)
        assert isinstance(config.TECH_BLUE, RgbColor)
        assert isinstance(config.SILVER, RgbColor)
        assert isinstance(config.ORANGE, RgbColor)
        assert isinstance(config.GREEN, RgbColor)
        assert isinstance(config.WHITE, RgbColor)
        assert isinstance(config.LIGHT_BLUE, RgbColor)

    def test_font_size_definitions(self):
        """测试字体大小定义"""
        config = PresentationConfig()

        # 验证字体大小设置
        assert config.TITLE_FONT_SIZE == Pt(44)
        assert config.SUBTITLE_FONT_SIZE == Pt(24)
        assert config.HEADING_FONT_SIZE == Pt(32)
        assert config.SECTION_TITLE_FONT_SIZE == Pt(40)
        assert config.CONTENT_FONT_SIZE == Pt(18)
        assert config.TABLE_HEADER_FONT_SIZE == Pt(14)
        assert config.TABLE_CELL_FONT_SIZE == Pt(12)
        assert config.PAGE_NUMBER_FONT_SIZE == Pt(12)

    def test_slide_dimensions(self):
        """测试幻灯片尺寸"""
        assert PresentationConfig.SLIDE_WIDTH == Inches(10)
        assert PresentationConfig.SLIDE_HEIGHT == Inches(7.5)
        assert PresentationConfig.TOP_BAR_HEIGHT == Inches(0.1)

    def test_color_values(self):
        """测试具体颜色值"""
        # 验证 DARK_BLUE 是 RGB(10, 22, 40)
        assert PresentationConfig.DARK_BLUE == RgbColor(10, 22, 40)
        # 验证 TECH_BLUE 是 RGB(0, 212, 255)
        assert PresentationConfig.TECH_BLUE == RgbColor(0, 212, 255)
        # 验证 WHITE 是 RGB(255, 255, 255)
        assert PresentationConfig.WHITE == RgbColor(255, 255, 255)


# ============================================================================
# BaseSlideBuilder 测试
# ============================================================================


@pytest.mark.unit
class TestBaseSlideBuilder:
    """测试基础幻灯片构建器"""

    @pytest.fixture
    def presentation(self):
        """创建测试用的Presentation对象"""
        prs = Presentation()
        prs.slide_width = PresentationConfig.SLIDE_WIDTH
        prs.slide_height = PresentationConfig.SLIDE_HEIGHT
        return prs

    @pytest.fixture
    def builder(self, presentation):
        """创建BaseSlideBuilder实例"""
        return BaseSlideBuilder(presentation)

    def test_init(self, presentation):
        """测试初始化"""
        builder = BaseSlideBuilder(presentation)
        assert builder.prs == presentation
        assert isinstance(builder.config, PresentationConfig)

    def test_add_title_slide(self, builder, presentation):
        """测试添加标题幻灯片"""
        slide = builder.add_title_slide("测试标题", "测试副标题")

        assert slide is not None
        assert len(presentation.slides) == 1

    def test_add_title_slide_without_subtitle(self, builder, presentation):
        """测试添加不带副标题的标题幻灯片"""
        slide = builder.add_title_slide("测试标题")

        assert slide is not None
        assert len(presentation.slides) == 1

    def test_add_section_slide(self, builder, presentation):
        """测试添加章节分隔页"""
        slide = builder.add_section_slide("第一章", "章节说明")

        assert slide is not None
        assert len(presentation.slides) == 1

    def test_add_section_slide_without_subtitle(self, builder, presentation):
        """测试添加不带副标题的章节页"""
        slide = builder.add_section_slide("第一章")

        assert slide is not None
        assert len(presentation.slides) == 1

    def test_add_white_background(self, builder, presentation):
        """测试添加白色背景"""
        slide_layout = presentation.slide_layouts[6]
        slide = presentation.slides.add_slide(slide_layout)

        background = builder._add_white_background(slide)

        assert background is not None

    def test_add_top_bar(self, builder, presentation):
        """测试添加顶部装饰条"""
        slide_layout = presentation.slide_layouts[6]
        slide = presentation.slides.add_slide(slide_layout)

        top_bar = builder._add_top_bar(slide)

        assert top_bar is not None

    def test_add_slide_title(self, builder, presentation):
        """测试添加幻灯片标题"""
        slide_layout = presentation.slide_layouts[6]
        slide = presentation.slides.add_slide(slide_layout)

        title_box = builder._add_slide_title(slide, "测试标题")

        assert title_box is not None

    def test_add_page_number(self, builder, presentation):
        """测试添加页码"""
        slide_layout = presentation.slide_layouts[6]
        slide = presentation.slides.add_slide(slide_layout)

        page_box = builder._add_page_number(slide, 1)

        assert page_box is not None


# ============================================================================
# ContentSlideBuilder 测试
# ============================================================================


@pytest.mark.unit
class TestContentSlideBuilder:
    """测试内容幻灯片构建器"""

    @pytest.fixture
    def presentation(self):
        """创建测试用的Presentation对象"""
        prs = Presentation()
        prs.slide_width = PresentationConfig.SLIDE_WIDTH
        prs.slide_height = PresentationConfig.SLIDE_HEIGHT
        return prs

    @pytest.fixture
    def builder(self, presentation):
        """创建ContentSlideBuilder实例"""
        return ContentSlideBuilder(presentation)

    def test_init(self, presentation):
        """测试初始化"""
        builder = ContentSlideBuilder(presentation)
        assert builder.prs == presentation

    def test_add_content_slide_with_string_list(self, builder, presentation):
        """测试使用字符串列表添加内容幻灯片"""
        content = ["第一行内容", "第二行内容", "第三行内容"]
        slide = builder.add_content_slide("测试标题", content, page_num=1)

        assert slide is not None
        assert len(presentation.slides) == 1

    def test_add_content_slide_with_dict_list(self, builder, presentation):
        """测试使用字典列表添加内容幻灯片"""
        config = PresentationConfig()
        content = [
        {"text": "标题行", "size": 24, "bold": True, "color": config.TECH_BLUE},
        {"text": "普通行", "size": 18},
        "字符串行",
        ]
        slide = builder.add_content_slide("测试标题", content, page_num=2)

        assert slide is not None
        assert len(presentation.slides) == 1

    def test_add_content_slide_without_page_num(self, builder, presentation):
        """测试不带页码的内容幻灯片"""
        content = ["内容"]
        slide = builder.add_content_slide("标题", content)

        assert slide is not None

    def test_add_two_column_slide(self, builder, presentation):
        """测试添加两栏内容幻灯片"""
        left = ["左栏第一行", "左栏第二行"]
        right = ["右栏第一行", "右栏第二行"]
        slide = builder.add_two_column_slide("双栏标题", left, right, page_num=3)

        assert slide is not None
        assert len(presentation.slides) == 1

    def test_add_two_column_slide_without_page_num(self, builder, presentation):
        """测试不带页码的两栏幻灯片"""
        left = ["左"]
        right = ["右"]
        slide = builder.add_two_column_slide("标题", left, right)

        assert slide is not None

    def test_fill_textbox(self, builder, presentation):
        """测试填充文本框"""
        slide_layout = presentation.slide_layouts[6]
        slide = presentation.slides.add_slide(slide_layout)

        textbox = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(3))
        content = ["第一行", "第二行", "第三行"]

        builder._fill_textbox(textbox, content)

        # 验证文本框已填充
        assert textbox.text_frame is not None


# ============================================================================
# TableSlideBuilder 测试
# ============================================================================


@pytest.mark.unit
class TestTableSlideBuilder:
    """测试表格幻灯片构建器"""

    @pytest.fixture
    def presentation(self):
        """创建测试用的Presentation对象"""
        prs = Presentation()
        prs.slide_width = PresentationConfig.SLIDE_WIDTH
        prs.slide_height = PresentationConfig.SLIDE_HEIGHT
        return prs

    @pytest.fixture
    def builder(self, presentation):
        """创建TableSlideBuilder实例"""
        return TableSlideBuilder(presentation)

    def test_init(self, presentation):
        """测试初始化"""
        builder = TableSlideBuilder(presentation)
        assert builder.prs == presentation

    def test_add_table_slide(self, builder, presentation):
        """测试添加表格幻灯片"""
        headers = ["列A", "列B", "列C"]
        rows = [["A1", "B1", "C1"], ["A2", "B2", "C2"], ["A3", "B3", "C3"]]

        slide = builder.add_table_slide("表格标题", headers, rows, page_num=1)

        assert slide is not None
        assert len(presentation.slides) == 1

    def test_add_table_slide_single_row(self, builder, presentation):
        """测试添加单行表格"""
        headers = ["名称", "值"]
        rows = [["测试", "100"]]

        slide = builder.add_table_slide("单行表格", headers, rows)

        assert slide is not None

    def test_add_table_slide_many_rows(self, builder, presentation):
        """测试添加多行表格"""
        headers = ["ID", "名称"]
        rows = [[str(i), f"项目{i}"] for i in range(10)]

        slide = builder.add_table_slide("多行表格", headers, rows, page_num=5)

        assert slide is not None

    def test_add_table_slide_without_page_num(self, builder, presentation):
        """测试不带页码的表格幻灯片"""
        headers = ["A", "B"]
        rows = [["1", "2"]]

        slide = builder.add_table_slide("标题", headers, rows)

        assert slide is not None


# ============================================================================
# PresentationGenerator 测试
# ============================================================================


@pytest.mark.unit
class TestPresentationGenerator:
    """测试PPT生成器主类"""

    def test_init(self):
        """测试初始化"""
        generator = PresentationGenerator()

        assert generator.prs is not None
        assert generator.prs.slide_width == PresentationConfig.SLIDE_WIDTH
        assert generator.prs.slide_height == PresentationConfig.SLIDE_HEIGHT
        assert isinstance(generator.base_builder, BaseSlideBuilder)
        assert isinstance(generator.content_builder, ContentSlideBuilder)
        assert isinstance(generator.table_builder, TableSlideBuilder)
        assert isinstance(generator.config, PresentationConfig)

    def test_create_cover_slide(self):
        """测试创建封面"""
        generator = PresentationGenerator()
        generator.create_cover_slide()

        assert len(generator.prs.slides) == 1

    def test_create_toc_slide(self):
        """测试创建目录"""
        generator = PresentationGenerator()
        generator.create_toc_slide()

        assert len(generator.prs.slides) == 1

    def test_create_part1_industry_insights(self):
        """测试创建第一部分"""
        generator = PresentationGenerator()
        generator.create_part1_industry_insights()

        # 应该创建多张幻灯片
        assert len(generator.prs.slides) > 0

    def test_create_part2_solution_overview(self):
        """测试创建第二部分"""
        generator = PresentationGenerator()
        generator.create_part2_solution_overview()

        assert len(generator.prs.slides) > 0

    def test_create_part3_core_features(self):
        """测试创建第三部分"""
        generator = PresentationGenerator()
        generator.create_part3_core_features()

        assert len(generator.prs.slides) > 0

    def test_create_part4_customer_portal(self):
        """测试创建第四部分"""
        generator = PresentationGenerator()
        generator.create_part4_customer_portal()

        assert len(generator.prs.slides) > 0

    def test_create_part5_ai_capabilities(self):
        """测试创建第五部分"""
        generator = PresentationGenerator()
        generator.create_part5_ai_capabilities()

        assert len(generator.prs.slides) > 0

    def test_create_part6_customer_value(self):
        """测试创建第六部分"""
        generator = PresentationGenerator()
        generator.create_part6_customer_value()

        assert len(generator.prs.slides) > 0

    def test_create_part7_cooperation(self):
        """测试创建第七部分"""
        generator = PresentationGenerator()
        generator.create_part7_cooperation()

        assert len(generator.prs.slides) > 0

    def test_generate_creates_file(self):
        """测试生成PPT文件"""
        generator = PresentationGenerator()

        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
            output_path = tmp.name

            try:
                result = generator.generate(output_path)

                assert result == output_path
                assert os.path.exists(output_path)
                assert os.path.getsize(output_path) > 0
            finally:
                if os.path.exists(output_path):
                    os.unlink(output_path)

    def test_generate_default_path(self):
        """测试使用默认路径生成PPT"""
        generator = PresentationGenerator()
        default_path = "完整PPT.pptx"

        try:
            result = generator.generate()

            assert result == default_path
            assert os.path.exists(default_path)
        finally:
            if os.path.exists(default_path):
                os.unlink(default_path)


@pytest.mark.unit
class TestPresentationGeneratorIntegration:
    """测试PPT生成器集成场景"""

    def test_full_presentation_generation(self):
        """测试完整PPT生成流程"""
        generator = PresentationGenerator()

        # 创建所有部分
        generator.create_cover_slide()
        generator.create_toc_slide()
        generator.create_part1_industry_insights()
        generator.create_part2_solution_overview()
        generator.create_part3_core_features()
        generator.create_part4_customer_portal()
        generator.create_part5_ai_capabilities()
        generator.create_part6_customer_value()
        generator.create_part7_cooperation()

        # 验证生成了多张幻灯片
        total_slides = len(generator.prs.slides)
        assert total_slides > 10  # 应该有很多幻灯片

    def test_builder_composition(self):
        """测试构建器组合"""
        generator = PresentationGenerator()

        # 验证所有构建器共享同一个 Presentation
        assert generator.base_builder.prs is generator.prs
        assert generator.content_builder.prs is generator.prs
        assert generator.table_builder.prs is generator.prs

    def test_config_consistency(self):
        """测试配置一致性"""
        generator = PresentationGenerator()

        # 验证配置对象类型
        assert isinstance(generator.config, PresentationConfig)
        assert isinstance(generator.base_builder.config, PresentationConfig)
        assert isinstance(generator.content_builder.config, PresentationConfig)
        assert isinstance(generator.table_builder.config, PresentationConfig)
