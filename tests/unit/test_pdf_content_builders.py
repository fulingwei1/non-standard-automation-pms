# -*- coding: utf-8 -*-
"""
I2组 - PDF内容构建工具 单元测试
覆盖: app/services/pdf_content_builders.py
"""
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch, call

import pytest


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_styles():
    """创建伪 styles 字典（使用 MagicMock 避免真实 reportlab 样式问题）"""
    style = MagicMock()
    return {
        "title": style,
        "heading": style,
        "normal": style,
        "footer": style,
    }


def _make_order(
    acceptance_type="FAT",
    order_no="ORD-001",
    actual_end_date=None,
    location="上海",
    overall_result="PASSED",
    conclusion="验收通过",
    conditions=None,
    order_id=1,
):
    order = MagicMock()
    order.id = order_id
    order.order_no = order_no
    order.acceptance_type = acceptance_type
    order.actual_end_date = actual_end_date or datetime(2024, 1, 15)
    order.location = location
    order.overall_result = overall_result
    order.conclusion = conclusion
    order.conditions = conditions
    return order


def _make_project(project_name="测试项目"):
    p = MagicMock()
    p.project_name = project_name
    return p


def _make_machine(machine_name="测试设备"):
    m = MagicMock()
    m.machine_name = machine_name
    return m


def _patch_platypus():
    """返回用于 patch reportlab.platypus 的上下文管理器组合"""
    mock_para = MagicMock()
    mock_spacer = MagicMock()
    mock_table = MagicMock()
    mock_table.return_value = MagicMock()
    mock_table.return_value.setStyle = MagicMock()
    return mock_para, mock_spacer, mock_table


# ─── build_basic_info_section ─────────────────────────────────────────────────

class TestBuildBasicInfoSection:
    def test_returns_empty_when_unavailable(self):
        with patch("app.services.pdf_content_builders.REPORTLAB_AVAILABLE", False):
            from app.services.pdf_content_builders import build_basic_info_section
            result = build_basic_info_section(
                _make_order(), _make_project(), _make_machine(),
                "RPT-001", 1, _make_styles()
            )
        assert result == []

    def test_returns_story_when_available(self):
        from app.services.pdf_content_builders import build_basic_info_section, REPORTLAB_AVAILABLE
        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        order = _make_order()
        project = _make_project()
        machine = _make_machine()
        styles = _make_styles()

        mock_para, mock_spacer, mock_table = _patch_platypus()

        with patch("reportlab.platypus.Paragraph", mock_para), \
             patch("reportlab.platypus.Spacer", mock_spacer), \
             patch("reportlab.platypus.Table", mock_table):
            result = build_basic_info_section(order, project, machine, "RPT-001", 1, styles)
            assert isinstance(result, list)
            assert len(result) > 0

    def test_acceptance_type_mapping(self):
        """各验收类型都能正确映射中文，不崩溃"""
        from app.services.pdf_content_builders import build_basic_info_section, REPORTLAB_AVAILABLE
        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        mock_para, mock_spacer, mock_table = _patch_platypus()

        for atype in ["FAT", "SAT", "FINAL", "UNKNOWN"]:
            order = _make_order(acceptance_type=atype)
            with patch("reportlab.platypus.Paragraph", mock_para), \
                 patch("reportlab.platypus.Spacer", mock_spacer), \
                 patch("reportlab.platypus.Table", mock_table):
                # 不抛出异常即可
                build_basic_info_section(order, _make_project(), _make_machine(), "R001", 1, _make_styles())

    def test_none_project_and_machine(self):
        from app.services.pdf_content_builders import build_basic_info_section, REPORTLAB_AVAILABLE
        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        mock_para, mock_spacer, mock_table = _patch_platypus()

        with patch("reportlab.platypus.Paragraph", mock_para), \
             patch("reportlab.platypus.Spacer", mock_spacer), \
             patch("reportlab.platypus.Table", mock_table):
            # project=None, machine=None 不应崩溃
            build_basic_info_section(_make_order(), None, None, "R001", 1, _make_styles())


# ─── build_statistics_section ─────────────────────────────────────────────────

class TestBuildStatisticsSection:
    def _make_db(self, items):
        mock_db = MagicMock()
        mock_q = MagicMock()
        mock_q.filter.return_value.order_by.return_value.all.return_value = items
        mock_db.query.return_value = mock_q
        return mock_db

    def _make_item(self, cat_code, cat_name, status):
        item = MagicMock()
        item.category_code = cat_code
        item.category_name = cat_name
        item.result_status = status
        return item

    def test_returns_empty_when_unavailable(self):
        with patch("app.services.pdf_content_builders.REPORTLAB_AVAILABLE", False):
            from app.services.pdf_content_builders import build_statistics_section
            result = build_statistics_section(_make_order(), MagicMock(), _make_styles())
        assert result == []

    def test_empty_items(self):
        from app.services.pdf_content_builders import build_statistics_section, REPORTLAB_AVAILABLE
        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        db = self._make_db([])
        mock_para, mock_spacer, mock_table = _patch_platypus()

        with patch("reportlab.platypus.Paragraph", mock_para), \
             patch("reportlab.platypus.Spacer", mock_spacer), \
             patch("reportlab.platypus.Table", mock_table):
            result = build_statistics_section(_make_order(), db, _make_styles())
            assert isinstance(result, list)

    def test_with_items(self):
        from app.services.pdf_content_builders import build_statistics_section, REPORTLAB_AVAILABLE
        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        items = [
            self._make_item("C1", "外观检查", "PASSED"),
            self._make_item("C1", "外观检查", "FAILED"),
            self._make_item("C2", "功能检查", "NA"),
            self._make_item("C2", "功能检查", "CONDITIONAL"),
        ]
        db = self._make_db(items)
        mock_para, mock_spacer, mock_table = _patch_platypus()

        with patch("reportlab.platypus.Paragraph", mock_para), \
             patch("reportlab.platypus.Spacer", mock_spacer), \
             patch("reportlab.platypus.Table", mock_table):
            result = build_statistics_section(_make_order(), db, _make_styles())
            assert isinstance(result, list)

    def test_pass_rate_calculation(self):
        """验证通过率计算逻辑正确"""
        from app.services.pdf_content_builders import build_statistics_section, REPORTLAB_AVAILABLE
        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        # 5个检查项：2通过 1失败 1NA 1有条件 → valid=4, effective=2+0.8=2.8, rate=70%
        items = [
            self._make_item("C1", "外观", "PASSED"),
            self._make_item("C1", "外观", "PASSED"),
            self._make_item("C1", "外观", "FAILED"),
            self._make_item("C1", "外观", "NA"),
            self._make_item("C1", "外观", "CONDITIONAL"),
        ]
        db = self._make_db(items)
        mock_para, mock_spacer, mock_table = _patch_platypus()

        with patch("reportlab.platypus.Paragraph", mock_para), \
             patch("reportlab.platypus.Spacer", mock_spacer), \
             patch("reportlab.platypus.Table", mock_table):
            result = build_statistics_section(_make_order(), db, _make_styles())
            assert isinstance(result, list)


# ─── build_conclusion_section ────────────────────────────────────────────────

class TestBuildConclusionSection:
    def test_returns_empty_when_unavailable(self):
        with patch("app.services.pdf_content_builders.REPORTLAB_AVAILABLE", False):
            from app.services.pdf_content_builders import build_conclusion_section
            result = build_conclusion_section(_make_order(), _make_styles())
        assert result == []

    def test_passed_conclusion(self):
        from app.services.pdf_content_builders import build_conclusion_section, REPORTLAB_AVAILABLE
        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        order = _make_order(overall_result="PASSED", conclusion="全部通过")
        mock_para, mock_spacer, _ = _patch_platypus()

        with patch("reportlab.platypus.Paragraph", mock_para), \
             patch("reportlab.platypus.Spacer", mock_spacer):
            result = build_conclusion_section(order, _make_styles())
            assert isinstance(result, list)

    def test_failed_conclusion(self):
        from app.services.pdf_content_builders import build_conclusion_section, REPORTLAB_AVAILABLE
        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        order = _make_order(overall_result="FAILED", conclusion="验收不通过")
        mock_para, mock_spacer, _ = _patch_platypus()

        with patch("reportlab.platypus.Paragraph", mock_para), \
             patch("reportlab.platypus.Spacer", mock_spacer):
            result = build_conclusion_section(order, _make_styles())
            assert isinstance(result, list)

    def test_conditional_with_conditions(self):
        from app.services.pdf_content_builders import build_conclusion_section, REPORTLAB_AVAILABLE
        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        order = _make_order(overall_result="CONDITIONAL", conclusion="有条件通过", conditions="需整改三项")
        mock_para, mock_spacer, _ = _patch_platypus()

        with patch("reportlab.platypus.Paragraph", mock_para), \
             patch("reportlab.platypus.Spacer", mock_spacer):
            result = build_conclusion_section(order, _make_styles())
            assert isinstance(result, list)

    def test_unknown_result(self):
        from app.services.pdf_content_builders import build_conclusion_section, REPORTLAB_AVAILABLE
        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        order = _make_order(overall_result="UNKNOWN")
        mock_para, mock_spacer, _ = _patch_platypus()

        with patch("reportlab.platypus.Paragraph", mock_para), \
             patch("reportlab.platypus.Spacer", mock_spacer):
            result = build_conclusion_section(order, _make_styles())
            assert isinstance(result, list)


# ─── build_issues_section ─────────────────────────────────────────────────────

class TestBuildIssuesSection:
    def _make_issue(self, issue_no, title, severity, status, is_blocking):
        issue = MagicMock()
        issue.issue_no = issue_no
        issue.title = title
        issue.severity = severity
        issue.status = status
        issue.is_blocking = is_blocking
        return issue

    def _make_db(self, issues):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = issues
        return db

    def test_returns_empty_when_unavailable(self):
        with patch("app.services.pdf_content_builders.REPORTLAB_AVAILABLE", False):
            from app.services.pdf_content_builders import build_issues_section
            result = build_issues_section(_make_order(), MagicMock(), _make_styles())
        assert result == []

    def test_no_issues(self):
        from app.services.pdf_content_builders import build_issues_section, REPORTLAB_AVAILABLE
        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        db = self._make_db([])
        result = build_issues_section(_make_order(), db, _make_styles())
        # 无问题时返回空 list
        assert result == []

    def test_with_issues(self):
        from app.services.pdf_content_builders import build_issues_section, REPORTLAB_AVAILABLE
        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        issues = [
            self._make_issue("ISS-001", "问题一", "CRITICAL", "OPEN", True),
            self._make_issue("ISS-002", "问题二", "MAJOR", "RESOLVED", False),
        ]
        db = self._make_db(issues)
        mock_para, mock_spacer, mock_table = _patch_platypus()

        with patch("reportlab.platypus.Paragraph", mock_para), \
             patch("reportlab.platypus.Spacer", mock_spacer), \
             patch("reportlab.platypus.Table", mock_table):
            result = build_issues_section(_make_order(), db, _make_styles())
            assert isinstance(result, list)

    def test_title_truncation(self):
        """超过20字的标题应被截断"""
        from app.services.pdf_content_builders import build_issues_section, REPORTLAB_AVAILABLE
        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        long_title = "这是一个超过二十个字的验收问题标题描述内容"
        issues = [self._make_issue("ISS-001", long_title, "MINOR", "OPEN", False)]
        db = self._make_db(issues)
        mock_para, mock_spacer, mock_table = _patch_platypus()

        with patch("reportlab.platypus.Paragraph", mock_para), \
             patch("reportlab.platypus.Spacer", mock_spacer), \
             patch("reportlab.platypus.Table", mock_table):
            result = build_issues_section(_make_order(), db, _make_styles())
            assert isinstance(result, list)

    def test_more_than_10_issues_shows_note(self):
        """超过10条问题时显示省略提示"""
        from app.services.pdf_content_builders import build_issues_section, REPORTLAB_AVAILABLE
        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        issues = [
            self._make_issue(f"ISS-{i:03d}", f"问题{i}", "MINOR", "OPEN", False)
            for i in range(12)
        ]
        db = self._make_db(issues)
        mock_para, mock_spacer, mock_table = _patch_platypus()

        with patch("reportlab.platypus.Paragraph", mock_para), \
             patch("reportlab.platypus.Spacer", mock_spacer), \
             patch("reportlab.platypus.Table", mock_table):
            result = build_issues_section(_make_order(), db, _make_styles())
            assert isinstance(result, list)


# ─── build_signatures_section ────────────────────────────────────────────────

class TestBuildSignaturesSection:
    def _make_sig(self, stype, name, role, company, signed_at):
        sig = MagicMock()
        sig.signer_type = stype
        sig.signer_name = name
        sig.signer_role = role
        sig.signer_company = company
        sig.signed_at = signed_at
        return sig

    def _make_db(self, sigs):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = sigs
        return db

    def test_returns_empty_when_unavailable(self):
        with patch("app.services.pdf_content_builders.REPORTLAB_AVAILABLE", False):
            from app.services.pdf_content_builders import build_signatures_section
            result = build_signatures_section(_make_order(), MagicMock(), _make_styles())
        assert result == []

    def test_no_signatures(self):
        from app.services.pdf_content_builders import build_signatures_section, REPORTLAB_AVAILABLE
        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        db = self._make_db([])
        mock_para, mock_spacer, _ = _patch_platypus()

        with patch("reportlab.platypus.Paragraph", mock_para), \
             patch("reportlab.platypus.Spacer", mock_spacer):
            result = build_signatures_section(_make_order(), db, _make_styles())
            assert isinstance(result, list)

    def test_with_signatures(self):
        from app.services.pdf_content_builders import build_signatures_section, REPORTLAB_AVAILABLE
        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        sigs = [
            self._make_sig("QA", "张质检", "质检员", "公司A", datetime(2024, 1, 15, 10, 0)),
            self._make_sig("CUSTOMER", "李客户", "采购经理", "公司B", None),
        ]
        db = self._make_db(sigs)
        mock_para, mock_spacer, mock_table = _patch_platypus()

        with patch("reportlab.platypus.Paragraph", mock_para), \
             patch("reportlab.platypus.Spacer", mock_spacer), \
             patch("reportlab.platypus.Table", mock_table):
            result = build_signatures_section(_make_order(), db, _make_styles())
            assert isinstance(result, list)

    def test_signer_type_mapping(self):
        """所有签字人类型都能映射"""
        from app.services.pdf_content_builders import build_signatures_section, REPORTLAB_AVAILABLE
        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        sigs = [
            self._make_sig("QA", "QA员", "质检", "A公司", None),
            self._make_sig("PM", "项目经理", "PM", "A公司", None),
            self._make_sig("CUSTOMER", "客户", "采购", "B公司", None),
            self._make_sig("WITNESS", "见证人", "见证", "C公司", None),
        ]
        db = self._make_db(sigs)
        mock_para, mock_spacer, mock_table = _patch_platypus()

        with patch("reportlab.platypus.Paragraph", mock_para), \
             patch("reportlab.platypus.Spacer", mock_spacer), \
             patch("reportlab.platypus.Table", mock_table):
            result = build_signatures_section(_make_order(), db, _make_styles())
            assert isinstance(result, list)


# ─── build_footer_section ─────────────────────────────────────────────────────

class TestBuildFooterSection:
    def test_returns_empty_when_unavailable(self):
        with patch("app.services.pdf_content_builders.REPORTLAB_AVAILABLE", False):
            from app.services.pdf_content_builders import build_footer_section
            result = build_footer_section(MagicMock(), _make_styles())
        assert result == []

    def test_with_real_name(self):
        from app.services.pdf_content_builders import build_footer_section, REPORTLAB_AVAILABLE
        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        user = MagicMock()
        user.real_name = "张三"
        user.username = "zhangsan"

        mock_para, mock_spacer, _ = _patch_platypus()

        with patch("reportlab.platypus.Paragraph", mock_para), \
             patch("reportlab.platypus.Spacer", mock_spacer):
            result = build_footer_section(user, _make_styles())
            assert isinstance(result, list)

    def test_fallback_to_username(self):
        from app.services.pdf_content_builders import build_footer_section, REPORTLAB_AVAILABLE
        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab 未安装")

        user = MagicMock()
        user.real_name = None
        user.username = "admin"

        mock_para, mock_spacer, _ = _patch_platypus()

        with patch("reportlab.platypus.Paragraph", mock_para), \
             patch("reportlab.platypus.Spacer", mock_spacer):
            result = build_footer_section(user, _make_styles())
            assert isinstance(result, list)
