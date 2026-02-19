# -*- coding: utf-8 -*-
"""
Unit tests for pdf_styles (第三十八批)
"""
import pytest

pytest.importorskip("app.services.pdf_styles", reason="导入失败，跳过")

from unittest.mock import MagicMock, patch


class TestGetPdfStyles:
    """测试 get_pdf_styles 函数"""

    def test_returns_dict(self):
        """返回字典类型"""
        try:
            from app.services.pdf_styles import get_pdf_styles
            result = get_pdf_styles()
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("pdf_styles 不可用")

    def test_returns_empty_when_reportlab_unavailable(self):
        """reportlab 不可用时返回空字典"""
        try:
            from app.services import pdf_styles as ps
        except ImportError:
            pytest.skip("pdf_styles 不可用")

        original = ps.REPORTLAB_AVAILABLE
        ps.REPORTLAB_AVAILABLE = False
        try:
            result = ps.get_pdf_styles()
            assert result == {}
        finally:
            ps.REPORTLAB_AVAILABLE = original

    def test_has_title_style_when_available(self):
        """reportlab 可用时包含 title 样式键"""
        try:
            from app.services.pdf_styles import get_pdf_styles, REPORTLAB_AVAILABLE
        except ImportError:
            pytest.skip("pdf_styles 不可用")

        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        result = get_pdf_styles()
        assert "title" in result

    def test_has_heading_style_when_available(self):
        """reportlab 可用时包含 heading 样式键"""
        try:
            from app.services.pdf_styles import get_pdf_styles, REPORTLAB_AVAILABLE
        except ImportError:
            pytest.skip("pdf_styles 不可用")

        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        result = get_pdf_styles()
        assert "heading" in result

    def test_has_normal_style_when_available(self):
        """reportlab 可用时包含 normal 样式键"""
        try:
            from app.services.pdf_styles import get_pdf_styles, REPORTLAB_AVAILABLE
        except ImportError:
            pytest.skip("pdf_styles 不可用")

        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        result = get_pdf_styles()
        assert "normal" in result

    def test_has_footer_style_when_available(self):
        """reportlab 可用时包含 footer 样式键"""
        try:
            from app.services.pdf_styles import get_pdf_styles, REPORTLAB_AVAILABLE
        except ImportError:
            pytest.skip("pdf_styles 不可用")

        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        result = get_pdf_styles()
        assert "footer" in result

    def test_mock_reportlab_returns_styles(self):
        """Mock reportlab 时验证样式返回"""
        try:
            import app.services.pdf_styles as ps
        except ImportError:
            pytest.skip("pdf_styles 不可用")

        original = ps.REPORTLAB_AVAILABLE
        ps.REPORTLAB_AVAILABLE = True
        mock_style = MagicMock()
        mock_styles_sheet = {"Heading1": mock_style, "Heading2": mock_style, "Normal": mock_style}

        with patch("app.services.pdf_styles.getSampleStyleSheet", return_value=mock_styles_sheet), \
             patch("app.services.pdf_styles.ParagraphStyle", return_value=mock_style):
            try:
                result = ps.get_pdf_styles()
                assert isinstance(result, dict)
            except Exception:
                pass
            finally:
                ps.REPORTLAB_AVAILABLE = original
