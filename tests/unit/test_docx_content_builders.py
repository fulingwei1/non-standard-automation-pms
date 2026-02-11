# -*- coding: utf-8 -*-
"""Word文档内容构建工具函数测试"""
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime

import pytest


class TestDocxContentBuildersNotAvailable:
    """测试 DOCX 不可用时的行为"""

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', False)
    def test_setup_document_formatting_no_docx(self):
        from app.services.docx_content_builders import setup_document_formatting
        doc = MagicMock()
        result = setup_document_formatting(doc)
        assert result is None

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', False)
    def test_add_document_header_no_docx(self):
        from app.services.docx_content_builders import add_document_header
        doc = MagicMock()
        result = add_document_header(doc, "title", "period")
        assert result is None

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', False)
    def test_add_summary_section_no_docx(self):
        from app.services.docx_content_builders import add_summary_section
        doc = MagicMock()
        result = add_summary_section(doc, {})
        assert result is None

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', False)
    def test_add_comparison_section_no_docx(self):
        from app.services.docx_content_builders import add_comparison_section
        doc = MagicMock()
        result = add_comparison_section(doc, {})
        assert result is None

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', False)
    def test_add_level_statistics_section_no_docx(self):
        from app.services.docx_content_builders import add_level_statistics_section
        doc = MagicMock()
        result = add_level_statistics_section(doc, {}, lambda x: x)
        assert result is None

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', False)
    def test_add_action_items_section_no_docx(self):
        from app.services.docx_content_builders import add_action_items_section
        doc = MagicMock()
        result = add_action_items_section(doc, {})
        assert result is None

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', False)
    def test_add_key_decisions_section_no_docx(self):
        from app.services.docx_content_builders import add_key_decisions_section
        doc = MagicMock()
        result = add_key_decisions_section(doc, [])
        assert result is None

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', False)
    def test_add_strategic_structures_section_no_docx(self):
        from app.services.docx_content_builders import add_strategic_structures_section
        doc = MagicMock()
        result = add_strategic_structures_section(doc, [])
        assert result is None

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', False)
    def test_add_meetings_list_section_no_docx(self):
        from app.services.docx_content_builders import add_meetings_list_section
        doc = MagicMock()
        result = add_meetings_list_section(doc, [], lambda x: x, lambda x: x, lambda x: x)
        assert result is None

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', False)
    def test_add_document_footer_no_docx(self):
        from app.services.docx_content_builders import add_document_footer
        doc = MagicMock()
        result = add_document_footer(doc)
        assert result is None


class TestDocxContentBuildersAvailable:
    """测试 DOCX 可用时的行为"""

    @pytest.fixture
    def mock_doc(self):
        doc = MagicMock()
        # Setup sections
        section = MagicMock()
        doc.sections = [section]
        # Setup heading/paragraph returns
        doc.add_heading.return_value = MagicMock(alignment=None)
        para = MagicMock()
        run = MagicMock()
        run.font = MagicMock()
        para.add_run.return_value = run
        para.runs = [run]
        doc.add_paragraph.return_value = para
        # Setup table
        table = MagicMock()
        rows = []
        for i in range(10):
            row = MagicMock()
            cells = []
            for j in range(7):
                cell = MagicMock()
                cell_para = MagicMock()
                cell_run = MagicMock()
                cell_run.font = MagicMock()
                cell_para.runs = [cell_run]
                cell.paragraphs = [cell_para]
                cells.append(cell)
            row.cells = cells
            rows.append(row)
        table.rows = rows
        doc.add_table.return_value = table
        return doc

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', True)
    def test_setup_document_formatting(self, mock_doc):
        from app.services.docx_content_builders import setup_document_formatting
        setup_document_formatting(mock_doc)
        # Should set margins on sections

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', True)
    def test_add_document_header(self, mock_doc):
        from app.services.docx_content_builders import add_document_header
        add_document_header(mock_doc, "Test Report", "2026-01", "MONTHLY")
        mock_doc.add_heading.assert_called()

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', True)
    def test_add_document_header_no_rhythm(self, mock_doc):
        from app.services.docx_content_builders import add_document_header
        add_document_header(mock_doc, "Test Report", "2026-01")
        mock_doc.add_heading.assert_called()

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', True)
    def test_add_summary_section(self, mock_doc):
        from app.services.docx_content_builders import add_summary_section
        summary = {
            'total_meetings': 10,
            'completed_meetings': 8,
            'completion_rate': '80%',
            'total_action_items': 20,
            'completed_action_items': 15,
            'overdue_action_items': 2,
            'action_completion_rate': '75%'
        }
        add_summary_section(mock_doc, summary)
        mock_doc.add_table.assert_called()

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', True)
    def test_add_comparison_section_empty(self, mock_doc):
        from app.services.docx_content_builders import add_comparison_section
        add_comparison_section(mock_doc, {})

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', True)
    def test_add_comparison_section_with_data(self, mock_doc):
        from app.services.docx_content_builders import add_comparison_section
        data = {
            'previous_period': '2025-12',
            'current_period': '2026-01',
            'meetings_comparison': {'current': 10, 'previous': 8, 'change': 2, 'change_rate': '25%'},
            'completed_meetings_comparison': {'current': 8, 'previous': 6, 'change': 2, 'change_rate': '33%'},
            'action_items_comparison': {'current': 20, 'previous': 15, 'change': 5, 'change_rate': '33%'},
            'completed_action_items_comparison': {'current': 15, 'previous': 10, 'change': 5, 'change_rate': '50%'},
            'completion_rate_comparison': {'current': '75%', 'previous': '67%', 'change': '8%', 'change_value': 8}
        }
        add_comparison_section(mock_doc, data)

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', True)
    def test_add_level_statistics_section_empty(self, mock_doc):
        from app.services.docx_content_builders import add_level_statistics_section
        add_level_statistics_section(mock_doc, {}, lambda x: x)

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', True)
    def test_add_key_decisions_with_decisions(self, mock_doc):
        from app.services.docx_content_builders import add_key_decisions_section
        decisions = [
            "Decision 1",
            {"decision": "Decision 2", "maker": "Alice"}
        ]
        add_key_decisions_section(mock_doc, decisions)

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', True)
    def test_add_key_decisions_empty(self, mock_doc):
        from app.services.docx_content_builders import add_key_decisions_section
        add_key_decisions_section(mock_doc, [])

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', True)
    def test_add_strategic_structures(self, mock_doc):
        from app.services.docx_content_builders import add_strategic_structures_section
        structures = [{'meeting_name': 'M1', 'meeting_date': '2026-01-01'}]
        add_strategic_structures_section(mock_doc, structures)

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', True)
    def test_add_meetings_list_empty(self, mock_doc):
        from app.services.docx_content_builders import add_meetings_list_section
        add_meetings_list_section(mock_doc, [], lambda x: x, lambda x: x, lambda x: x)

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', True)
    def test_add_meetings_list_with_data(self, mock_doc):
        from app.services.docx_content_builders import add_meetings_list_section
        meetings = [{
            'meeting_name': 'Test Meeting',
            'meeting_date': '2026-01-01T00:00:00',
            'rhythm_level': 'MONTHLY',
            'cycle_type': 'REGULAR',
            'status': 'COMPLETED',
            'action_items_count': 5
        }]
        add_meetings_list_section(mock_doc, meetings, lambda x: x, lambda x: x, lambda x: x)

    @patch('app.services.docx_content_builders.DOCX_AVAILABLE', True)
    def test_add_document_footer(self, mock_doc):
        from app.services.docx_content_builders import add_document_footer
        add_document_footer(mock_doc)
        mock_doc.add_paragraph.assert_called()
