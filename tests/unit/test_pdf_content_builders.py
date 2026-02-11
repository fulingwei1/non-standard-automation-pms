# -*- coding: utf-8 -*-
"""PDF内容构建工具函数测试"""
from unittest.mock import MagicMock, patch

import pytest


class TestPdfNotAvailable:
    @patch('app.services.pdf_content_builders.REPORTLAB_AVAILABLE', False)
    def test_build_basic_info_section(self):
        from app.services.pdf_content_builders import build_basic_info_section
        result = build_basic_info_section(MagicMock(), MagicMock(), MagicMock(), "R001", 1, {})
        assert result == []

    @patch('app.services.pdf_content_builders.REPORTLAB_AVAILABLE', False)
    def test_build_statistics_section(self):
        from app.services.pdf_content_builders import build_statistics_section
        result = build_statistics_section(MagicMock(), MagicMock(), {})
        assert result == []

    @patch('app.services.pdf_content_builders.REPORTLAB_AVAILABLE', False)
    def test_build_conclusion_section(self):
        from app.services.pdf_content_builders import build_conclusion_section
        result = build_conclusion_section(MagicMock(), {})
        assert result == []

    @patch('app.services.pdf_content_builders.REPORTLAB_AVAILABLE', False)
    def test_build_issues_section(self):
        from app.services.pdf_content_builders import build_issues_section
        result = build_issues_section(MagicMock(), MagicMock(), {})
        assert result == []

    @patch('app.services.pdf_content_builders.REPORTLAB_AVAILABLE', False)
    def test_build_signatures_section(self):
        from app.services.pdf_content_builders import build_signatures_section
        result = build_signatures_section(MagicMock(), MagicMock(), {})
        assert result == []

    @patch('app.services.pdf_content_builders.REPORTLAB_AVAILABLE', False)
    def test_build_footer_section(self):
        from app.services.pdf_content_builders import build_footer_section
        result = build_footer_section(MagicMock(), {})
        assert result == []


class TestPdfAvailable:
    @patch('app.services.pdf_content_builders.REPORTLAB_AVAILABLE', True)
    def test_build_basic_info_section(self):
        from app.services.pdf_content_builders import build_basic_info_section
        order = MagicMock(acceptance_type='FAT', order_no='AC-001', actual_end_date=None, location='Lab')
        project = MagicMock(project_name='Test Project')
        machine = MagicMock(machine_name='Machine 1')
        styles = {'title': MagicMock(), 'normal': MagicMock()}
        with patch('app.services.pdf_content_builders.get_info_table_style'):
            result = build_basic_info_section(order, project, machine, "R001", 1, styles)
            assert len(result) > 0

    @patch('app.services.pdf_content_builders.REPORTLAB_AVAILABLE', True)
    def test_build_conclusion_section(self):
        from app.services.pdf_content_builders import build_conclusion_section
        order = MagicMock(overall_result='PASSED', conclusion='Good', conditions=None)
        styles = {'heading': MagicMock(), 'normal': MagicMock()}
        result = build_conclusion_section(order, styles)
        assert len(result) > 0

    @patch('app.services.pdf_content_builders.REPORTLAB_AVAILABLE', True)
    def test_build_statistics_section(self):
        from app.services.pdf_content_builders import build_statistics_section
        order = MagicMock(id=1)
        db = MagicMock()
        item = MagicMock(category_code='C1', category_name='Cat1', result_status='PASSED', sort_order=1)
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [item]
        styles = {'heading': MagicMock(), 'normal': MagicMock()}
        with patch('app.services.pdf_content_builders.get_stats_table_style'):
            result = build_statistics_section(order, db, styles)
            assert len(result) > 0

    @patch('app.services.pdf_content_builders.REPORTLAB_AVAILABLE', True)
    def test_build_issues_no_issues(self):
        from app.services.pdf_content_builders import build_issues_section
        order = MagicMock(id=1)
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        styles = {'heading': MagicMock(), 'normal': MagicMock()}
        result = build_issues_section(order, db, styles)
        assert result == []

    @patch('app.services.pdf_content_builders.REPORTLAB_AVAILABLE', True)
    def test_build_issues_with_issues(self):
        from app.services.pdf_content_builders import build_issues_section
        order = MagicMock(id=1)
        db = MagicMock()
        issue = MagicMock(
            issue_no='I001', title='Bug', severity='CRITICAL',
            status='OPEN', is_blocking=True
        )
        db.query.return_value.filter.return_value.all.return_value = [issue]
        styles = {'heading': MagicMock(), 'normal': MagicMock()}
        with patch('app.services.pdf_content_builders.get_issue_table_style'):
            result = build_issues_section(order, db, styles)
            assert len(result) > 0

    @patch('app.services.pdf_content_builders.REPORTLAB_AVAILABLE', True)
    def test_build_signatures(self):
        from app.services.pdf_content_builders import build_signatures_section
        order = MagicMock(id=1)
        db = MagicMock()
        sig = MagicMock(signer_type='QA', signer_name='Alice', signer_role='QA', signer_company='Co', signed_at=None)
        db.query.return_value.filter.return_value.all.return_value = [sig]
        styles = {'heading': MagicMock(), 'normal': MagicMock()}
        with patch('app.services.pdf_content_builders.get_signature_table_style'):
            result = build_signatures_section(order, db, styles)
            assert len(result) > 0

    @patch('app.services.pdf_content_builders.REPORTLAB_AVAILABLE', True)
    def test_build_footer(self):
        from app.services.pdf_content_builders import build_footer_section
        user = MagicMock(real_name='Admin', username='admin')
        styles = {'footer': MagicMock()}
        result = build_footer_section(user, styles)
        assert len(result) > 0
