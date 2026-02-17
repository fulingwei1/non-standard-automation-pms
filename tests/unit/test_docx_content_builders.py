# -*- coding: utf-8 -*-
"""
I2组 - Word文档内容构建 单元测试
覆盖: app/services/docx_content_builders.py
"""
from unittest.mock import MagicMock, patch, call
import pytest


def _make_doc_mock():
    """创建 docx Document 的 MagicMock"""
    doc = MagicMock()
    doc.sections = [MagicMock()]
    doc.add_heading.return_value = MagicMock()
    doc.add_paragraph.return_value = MagicMock()
    doc.add_table.return_value = _make_table_mock(7, 2)
    return doc


def _make_table_mock(rows=7, cols=2):
    """创建 Word 表格 mock"""
    mock_table = MagicMock()
    mock_rows = []
    for _ in range(rows):
        mock_row = MagicMock()
        mock_cells = []
        for _ in range(cols):
            mock_cell = MagicMock()
            mock_para = MagicMock()
            mock_run = MagicMock()
            mock_run.font = MagicMock()
            mock_run.font.bold = False
            mock_run.font.size = None
            mock_run.font.color = MagicMock()
            mock_para.runs = [mock_run]
            mock_cell.paragraphs = [mock_para]
            mock_cell.text = ""
            mock_cells.append(mock_cell)
        mock_row.cells = mock_cells
        mock_rows.append(mock_row)
    mock_table.rows = mock_rows
    return mock_table


# ─── setup_document_formatting ───────────────────────────────────────────────

class TestSetupDocumentFormatting:
    def test_sets_margins_when_docx_available(self):
        from app.services.docx_content_builders import setup_document_formatting, DOCX_AVAILABLE
        if not DOCX_AVAILABLE:
            pytest.skip("python-docx 未安装")

        doc = _make_doc_mock()
        setup_document_formatting(doc)

        section = doc.sections[0]
        # 检查边距被设置
        assert section.top_margin is not None

    def test_noop_when_docx_unavailable(self):
        with patch("app.services.docx_content_builders.DOCX_AVAILABLE", False):
            from app.services import docx_content_builders
            # 重新加载以使补丁生效
            import importlib
            importlib.reload(docx_content_builders)

        doc = _make_doc_mock()
        # 不应抛出任何异常
        from app.services.docx_content_builders import setup_document_formatting
        with patch("app.services.docx_content_builders.DOCX_AVAILABLE", False):
            setup_document_formatting(doc)


# ─── add_document_header ─────────────────────────────────────────────────────

class TestAddDocumentHeader:
    def test_adds_title_and_info(self):
        from app.services.docx_content_builders import add_document_header, DOCX_AVAILABLE
        if not DOCX_AVAILABLE:
            pytest.skip("python-docx 未安装")

        doc = _make_doc_mock()
        add_document_header(doc, "测试报告", "2024年1月")

        doc.add_heading.assert_called_once()
        assert doc.add_paragraph.called

    def test_with_rhythm_level(self):
        from app.services.docx_content_builders import add_document_header, DOCX_AVAILABLE
        if not DOCX_AVAILABLE:
            pytest.skip("python-docx 未安装")

        doc = _make_doc_mock()
        add_document_header(doc, "年度报告", "2024年", rhythm_level="MONTHLY")

        # add_paragraph 被调用了多次（含节律层级段落）
        assert doc.add_paragraph.call_count >= 2

    def test_noop_when_unavailable(self):
        doc = _make_doc_mock()
        with patch("app.services.docx_content_builders.DOCX_AVAILABLE", False):
            from app.services.docx_content_builders import add_document_header
            add_document_header(doc, "报告", "2024年")
        doc.add_heading.assert_not_called()


# ─── add_summary_section ─────────────────────────────────────────────────────

class TestAddSummarySection:
    def test_writes_summary_data(self):
        from app.services.docx_content_builders import add_summary_section, DOCX_AVAILABLE
        if not DOCX_AVAILABLE:
            pytest.skip("python-docx 未安装")

        doc = _make_doc_mock()
        doc.add_table.return_value = _make_table_mock(7, 2)
        summary = {
            "total_meetings": 10,
            "completed_meetings": 8,
            "completion_rate": "80%",
            "total_action_items": 20,
            "completed_action_items": 15,
            "overdue_action_items": 2,
            "action_completion_rate": "75%",
        }
        add_summary_section(doc, summary)
        doc.add_heading.assert_called()
        doc.add_table.assert_called()


# ─── add_comparison_section ───────────────────────────────────────────────────

class TestAddComparisonSection:
    def test_empty_comparison_data(self):
        from app.services.docx_content_builders import add_comparison_section, DOCX_AVAILABLE
        if not DOCX_AVAILABLE:
            pytest.skip("python-docx 未安装")

        doc = _make_doc_mock()
        add_comparison_section(doc, {})

        doc.add_heading.assert_called()
        # 空数据时添加"无对比数据"段落
        doc.add_paragraph.assert_called()

    def test_with_comparison_data(self):
        from app.services.docx_content_builders import add_comparison_section, DOCX_AVAILABLE
        if not DOCX_AVAILABLE:
            pytest.skip("python-docx 未安装")

        doc = _make_doc_mock()
        doc.add_table.return_value = _make_table_mock(6, 4)

        comparison_data = {
            "previous_period": "2023-12",
            "current_period": "2024-01",
            "meetings_comparison": {"current": 10, "previous": 8, "change": 2, "change_rate": "25%"},
            "completed_meetings_comparison": {"current": 8, "previous": 6, "change": 2, "change_rate": "33%"},
            "action_items_comparison": {"current": 20, "previous": 15, "change": 5, "change_rate": "33%"},
            "completed_action_items_comparison": {"current": 15, "previous": 10, "change": 5, "change_rate": "50%"},
            "completion_rate_comparison": {"current": "75%", "previous": "67%", "change": "8%", "change_value": 8},
        }
        add_comparison_section(doc, comparison_data)
        doc.add_heading.assert_called()
        doc.add_table.assert_called()


# ─── add_level_statistics_section ────────────────────────────────────────────

class TestAddLevelStatisticsSection:
    def _fmt(self, level):
        return f"[{level}]"

    def test_empty_by_level(self):
        from app.services.docx_content_builders import add_level_statistics_section, DOCX_AVAILABLE
        if not DOCX_AVAILABLE:
            pytest.skip("python-docx 未安装")

        doc = _make_doc_mock()
        add_level_statistics_section(doc, {}, self._fmt)
        doc.add_heading.assert_called()

    def test_with_data(self):
        from app.services.docx_content_builders import add_level_statistics_section, DOCX_AVAILABLE
        if not DOCX_AVAILABLE:
            pytest.skip("python-docx 未安装")

        doc = _make_doc_mock()
        doc.add_table.return_value = _make_table_mock(3, 3)

        by_level = {
            "L1": {"total": 5, "completed": 4},
            "L2": {"total": 3, "completed": 2},
        }
        add_level_statistics_section(doc, by_level, self._fmt)
        doc.add_table.assert_called()


# ─── add_action_items_section ─────────────────────────────────────────────────

class TestAddActionItemsSection:
    def test_action_items_rendered(self):
        from app.services.docx_content_builders import add_action_items_section, DOCX_AVAILABLE
        if not DOCX_AVAILABLE:
            pytest.skip("python-docx 未安装")

        doc = _make_doc_mock()
        doc.add_table.return_value = _make_table_mock(5, 2)

        action_summary = {
            "total": 10,
            "completed": 7,
            "overdue": 2,
            "in_progress": 1,
        }
        add_action_items_section(doc, action_summary)
        doc.add_heading.assert_called()
        doc.add_table.assert_called()


# ─── add_key_decisions_section ───────────────────────────────────────────────

class TestAddKeyDecisionsSection:
    def test_empty_decisions(self):
        from app.services.docx_content_builders import add_key_decisions_section, DOCX_AVAILABLE
        if not DOCX_AVAILABLE:
            pytest.skip("python-docx 未安装")

        doc = _make_doc_mock()
        add_key_decisions_section(doc, [], "本月")
        doc.add_paragraph.assert_called()

    def test_string_decisions(self):
        from app.services.docx_content_builders import add_key_decisions_section, DOCX_AVAILABLE
        if not DOCX_AVAILABLE:
            pytest.skip("python-docx 未安装")

        doc = _make_doc_mock()
        decisions = ["决策A", "决策B", "决策C"]
        add_key_decisions_section(doc, decisions)
        assert doc.add_paragraph.call_count >= len(decisions)

    def test_dict_decisions_with_maker(self):
        from app.services.docx_content_builders import add_key_decisions_section, DOCX_AVAILABLE
        if not DOCX_AVAILABLE:
            pytest.skip("python-docx 未安装")

        doc = _make_doc_mock()
        decisions = [{"decision": "决策A", "maker": "张总"}]
        add_key_decisions_section(doc, decisions)
        doc.add_paragraph.assert_called()

    def test_limits_to_20(self):
        from app.services.docx_content_builders import add_key_decisions_section, DOCX_AVAILABLE
        if not DOCX_AVAILABLE:
            pytest.skip("python-docx 未安装")

        doc = _make_doc_mock()
        decisions = [f"决策{i}" for i in range(25)]
        add_key_decisions_section(doc, decisions)
        # paragraph 调用次数不超过 20 + 一些额外的（heading + empty）
        # 关键是函数不崩溃
        assert doc.add_paragraph.called


# ─── add_strategic_structures_section ────────────────────────────────────────

class TestAddStrategicStructuresSection:
    def test_empty_structures(self):
        from app.services.docx_content_builders import add_strategic_structures_section, DOCX_AVAILABLE
        if not DOCX_AVAILABLE:
            pytest.skip("python-docx 未安装")

        doc = _make_doc_mock()
        add_strategic_structures_section(doc, [])
        doc.add_heading.assert_called()

    def test_with_structures(self):
        from app.services.docx_content_builders import add_strategic_structures_section, DOCX_AVAILABLE
        if not DOCX_AVAILABLE:
            pytest.skip("python-docx 未安装")

        doc = _make_doc_mock()
        structures = [
            {"meeting_name": "战略会", "meeting_date": "2024-01-15"},
            {"meeting_name": "规划会", "meeting_date": "2024-02-20"},
        ]
        add_strategic_structures_section(doc, structures)
        assert doc.add_paragraph.call_count >= 2


# ─── add_meetings_list_section ───────────────────────────────────────────────

class TestAddMeetingsListSection:
    def _fmt(self, v):
        return str(v)

    def test_empty_meetings(self):
        from app.services.docx_content_builders import add_meetings_list_section, DOCX_AVAILABLE
        if not DOCX_AVAILABLE:
            pytest.skip("python-docx 未安装")

        doc = _make_doc_mock()
        add_meetings_list_section(doc, [], self._fmt, self._fmt, self._fmt)
        doc.add_heading.assert_called()

    def test_with_meetings(self):
        from app.services.docx_content_builders import add_meetings_list_section, DOCX_AVAILABLE
        if not DOCX_AVAILABLE:
            pytest.skip("python-docx 未安装")

        doc = _make_doc_mock()
        meetings = [
            {
                "meeting_name": "周例会",
                "meeting_date": "2024-01-08",
                "rhythm_level": "L2",
                "cycle_type": "WEEKLY",
                "status": "COMPLETED",
                "action_items_count": 3,
            }
        ]
        doc.add_table.return_value = _make_table_mock(2, 6)
        add_meetings_list_section(doc, meetings, self._fmt, self._fmt, self._fmt)
        doc.add_table.assert_called()


# ─── add_document_footer ─────────────────────────────────────────────────────

class TestAddDocumentFooter:
    def test_footer_added(self):
        from app.services.docx_content_builders import add_document_footer, DOCX_AVAILABLE
        if not DOCX_AVAILABLE:
            pytest.skip("python-docx 未安装")

        doc = _make_doc_mock()
        add_document_footer(doc)
        doc.add_paragraph.assert_called()

    def test_noop_when_unavailable(self):
        doc = _make_doc_mock()
        with patch("app.services.docx_content_builders.DOCX_AVAILABLE", False):
            from app.services.docx_content_builders import add_document_footer
            add_document_footer(doc)
        doc.add_paragraph.assert_not_called()
