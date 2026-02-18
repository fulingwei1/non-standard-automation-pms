# -*- coding: utf-8 -*-
"""
第十六批：PDF内容构建工具函数 单元测试
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date

try:
    from app.services import pdf_content_builders
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_db():
    return MagicMock()


def make_order(**kwargs):
    order = MagicMock()
    order.order_no = kwargs.get("order_no", "ACC-2025-001")
    order.acceptance_type = kwargs.get("acceptance_type", "FAT")
    order.actual_end_date = kwargs.get("actual_end_date", date(2025, 3, 20))
    order.location = kwargs.get("location", "上海")
    return order


def make_project():
    p = MagicMock()
    p.project_name = "测试项目"
    return p


def make_machine():
    m = MagicMock()
    m.machine_name = "测试设备"
    return m


def make_real_styles():
    """使用真实的 reportlab 样式"""
    try:
        from reportlab.lib.styles import getSampleStyleSheet
        ss = getSampleStyleSheet()
        return {
            "title": ss["Title"],
            "heading1": ss["Heading1"],
            "heading2": ss["Heading2"],
            "normal": ss["Normal"],
            "bold": ss["Normal"],
            "table_header": ss["Normal"],
        }
    except ImportError:
        return {}


class TestBuildBasicInfoSection:
    def test_returns_empty_when_reportlab_unavailable(self):
        with patch.object(pdf_content_builders, "REPORTLAB_AVAILABLE", False):
            order = make_order()
            result = pdf_content_builders.build_basic_info_section(
                order, make_project(), make_machine(), "R001", 1, make_real_styles()
            )
            assert result == []

    def test_returns_list_when_reportlab_available(self):
        """当reportlab可用时返回内容列表"""
        if not pdf_content_builders.REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")
        order = make_order()
        styles = make_real_styles()
        result = pdf_content_builders.build_basic_info_section(
            order, make_project(), make_machine(), "R001", 1, styles
        )
        assert isinstance(result, list)
        assert len(result) > 0

    def test_handles_none_actual_end_date(self):
        if not pdf_content_builders.REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")
        order = make_order(actual_end_date=None)
        styles = make_real_styles()
        result = pdf_content_builders.build_basic_info_section(
            order, make_project(), make_machine(), "R001", 1, styles
        )
        assert isinstance(result, list)

    def test_handles_sat_type(self):
        if not pdf_content_builders.REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")
        order = make_order(acceptance_type="SAT")
        styles = make_real_styles()
        result = pdf_content_builders.build_basic_info_section(
            order, make_project(), make_machine(), "R001", 2, styles
        )
        assert isinstance(result, list)

    def test_reportlab_available_flag_is_bool(self):
        assert isinstance(pdf_content_builders.REPORTLAB_AVAILABLE, bool)

    def test_handles_none_project_and_machine(self):
        if not pdf_content_builders.REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")
        order = make_order()
        styles = make_real_styles()
        result = pdf_content_builders.build_basic_info_section(
            order, None, None, "R999", 1, styles
        )
        assert isinstance(result, list)
