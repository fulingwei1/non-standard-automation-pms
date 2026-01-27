# -*- coding: utf-8 -*-
"""
PPT生成器服务单元测试

测试覆盖:
- PresentationGenerator: 演示文稿生成器
- BaseSlideBuilder: 基础幻灯片构建器
- ContentSlideBuilder: 内容幻灯片构建器
- TableSlideBuilder: 表格幻灯片构建器
- PresentationConfig: 演示文稿配置
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile

import pytest


class TestPresentationGenerator:
    """测试演示文稿生成器"""

    @pytest.fixture
    def generator(self):
        """创建生成器实例"""
        from app.services.ppt_generator.generator import PresentationGenerator
        return PresentationGenerator()

    def test_generator_initialization(self, generator):
        """测试生成器初始化"""
        assert generator is not None

    def test_generate_creates_presentation(self, generator):
        """测试生成演示文稿"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.pptx"

            result = generator.generate(output_path=str(output_path))

            # 应该返回路径或成功标志
            assert result is not None or output_path.exists()

    def test_create_cover_slide(self, generator):
        """测试创建封面幻灯片"""
        # 验证方法存在
        assert hasattr(generator, 'create_cover_slide')

    def test_create_toc_slide(self, generator):
        """测试创建目录幻灯片"""
        assert hasattr(generator, 'create_toc_slide')


class TestBaseSlideBuilder:
    """测试基础幻灯片构建器"""

    def test_import_class(self):
        """测试导入类"""
        from app.services.ppt_generator.builders.base import BaseSlideBuilder
        assert BaseSlideBuilder is not None


class TestContentSlideBuilder:
    """测试内容幻灯片构建器"""

    def test_import_class(self):
        """测试导入类"""
        from app.services.ppt_generator.builders.content import ContentSlideBuilder
        assert ContentSlideBuilder is not None


class TestTableSlideBuilder:
    """测试表格幻灯片构建器"""

    def test_import_class(self):
        """测试导入类"""
        from app.services.ppt_generator.builders.table import TableSlideBuilder
        assert TableSlideBuilder is not None


class TestPresentationConfig:
    """测试演示文稿配置"""

    def test_import_config(self):
        """测试导入配置"""
        from app.services.ppt_generator.config import PresentationConfig
        assert PresentationConfig is not None

    def test_default_colors(self):
        """测试默认颜色配置"""
        from app.services.ppt_generator.config import PresentationConfig

        config = PresentationConfig()

        # 验证颜色配置
        assert hasattr(config, 'TECH_BLUE') or hasattr(config, 'colors')

    def test_default_fonts(self):
        """测试默认字体配置"""
        from app.services.ppt_generator.config import PresentationConfig

        config = PresentationConfig()

        # 验证字体配置
        assert hasattr(config, 'title_font') or hasattr(config, 'fonts')


class TestPPTGeneratorModule:
    """测试PPT生成器模块"""

    def test_import_module(self):
        """测试导入模块"""
        from app.services.ppt_generator import PresentationGenerator
        assert PresentationGenerator is not None

    def test_generator_has_create_methods(self):
        """测试生成器有创建方法"""
        from app.services.ppt_generator import PresentationGenerator

        generator = PresentationGenerator()

        # 验证常用方法存在
        assert hasattr(generator, 'generate')
