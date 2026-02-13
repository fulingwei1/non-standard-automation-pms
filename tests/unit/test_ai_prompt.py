# -*- coding: utf-8 -*-
"""Tests for work_log_ai/ai_prompt.py"""
import pytest
import json
from datetime import date


class TestAIPromptMixin:
    def _make_instance(self):
        from app.services.work_log_ai.ai_prompt import AIPromptMixin
        return AIPromptMixin()

    def test_build_ai_prompt(self):
        obj = self._make_instance()
        projects = [{'code': 'PJ001', 'name': 'Test Project'}]
        result = obj._build_ai_prompt("完成结构设计", projects, date(2025, 1, 15))
        assert 'PJ001' in result
        assert 'Test Project' in result
        assert '2025-01-15' in result

    def test_build_ai_prompt_empty_projects(self):
        obj = self._make_instance()
        result = obj._build_ai_prompt("日常工作", [], date(2025, 1, 15))
        assert '暂无项目' in result

    def test_parse_ai_response_valid_json(self):
        obj = self._make_instance()
        response = json.dumps({
            'work_items': [
                {'work_content': '设计', 'hours': 4, 'project_code': 'PJ001', 'project_name': 'Test'}
            ],
            'total_hours': 4,
            'confidence': 0.9
        })
        projects = [{'id': 1, 'code': 'PJ001', 'name': 'Test Project'}]
        result = obj._parse_ai_response(response, projects)
        assert result['work_items'][0]['project_id'] == 1

    def test_parse_ai_response_no_match(self):
        obj = self._make_instance()
        response = json.dumps({
            'work_items': [
                {'work_content': '设计', 'hours': 4, 'project_code': None}
            ],
            'total_hours': 4
        })
        result = obj._parse_ai_response(response, [])
        assert result['work_items'][0]['project_id'] is None

    def test_parse_ai_response_with_markdown(self):
        obj = self._make_instance()
        response = '```json\n{"work_items": [], "total_hours": 0}\n```'
        result = obj._parse_ai_response(response, [])
        assert result['work_items'] == []

    def test_parse_ai_response_invalid(self):
        obj = self._make_instance()
        with pytest.raises((ValueError, Exception)):
            obj._parse_ai_response("not json at all no braces", [])
