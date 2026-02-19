# -*- coding: utf-8 -*-
"""
第三十三批覆盖率测试 - AI提示词混入 (AIPromptMixin)
"""
import pytest
from unittest.mock import MagicMock
from datetime import date

try:
    from app.services.work_log_ai.ai_prompt import AIPromptMixin
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="ai_prompt 导入失败")


class ConcreteAIPrompt(AIPromptMixin):
    """用于测试的具体实现类"""
    pass


class TestBuildAiPrompt:
    def setup_method(self):
        self.mixin = ConcreteAIPrompt()
        self.work_date = date(2026, 1, 15)
        self.projects = [
            {"id": 1, "code": "PJ001", "name": "机器人项目"},
            {"id": 2, "code": "PJ002", "name": "自动化线体"},
        ]

    def test_prompt_contains_content(self):
        """生成的提示词包含工作日志内容"""
        content = "今天完成了机械结构设计，进行了3D建模"
        prompt = self.mixin._build_ai_prompt(content, self.projects, self.work_date)
        assert content in prompt

    def test_prompt_contains_date(self):
        """生成的提示词包含工作日期"""
        prompt = self.mixin._build_ai_prompt("任意内容", self.projects, self.work_date)
        assert "2026-01-15" in prompt

    def test_prompt_contains_project_codes(self):
        """生成的提示词包含项目编码"""
        prompt = self.mixin._build_ai_prompt("内容", self.projects, self.work_date)
        assert "PJ001" in prompt
        assert "PJ002" in prompt

    def test_prompt_with_no_projects(self):
        """无项目时提示词包含默认文案"""
        prompt = self.mixin._build_ai_prompt("内容", [], self.work_date)
        assert "暂无项目" in prompt

    def test_prompt_truncates_to_10_projects(self):
        """超过10个项目时只取前10个"""
        many_projects = [
            {"id": i, "code": f"PJ{i:03d}", "name": f"项目{i}"}
            for i in range(15)
        ]
        prompt = self.mixin._build_ai_prompt("内容", many_projects, self.work_date)
        # PJ014 (第15个) 不应该出现
        assert "PJ014" not in prompt

    def test_prompt_contains_json_format_instruction(self):
        """提示词包含JSON格式说明"""
        prompt = self.mixin._build_ai_prompt("内容", [], self.work_date)
        assert "work_items" in prompt
        assert "total_hours" in prompt


class TestParseAiResponse:
    def setup_method(self):
        self.mixin = ConcreteAIPrompt()
        self.projects = [
            {"id": 1, "code": "PJ001", "name": "机器人项目"},
            {"id": 2, "code": "PJ002", "name": "自动化线体"},
        ]

    def test_parse_valid_json(self):
        """解析合法JSON格式的AI响应"""
        ai_response = '{"work_items": [{"work_content": "设计", "hours": 4, "project_code": "PJ001"}], "total_hours": 4}'
        result = self.mixin._parse_ai_response(ai_response, self.projects)
        assert "work_items" in result
        assert len(result["work_items"]) == 1

    def test_parse_extracts_json_from_markdown(self):
        """从Markdown代码块中提取JSON"""
        ai_response = '一些文字\n{"work_items": [], "total_hours": 0}\n更多文字'
        result = self.mixin._parse_ai_response(ai_response, self.projects)
        assert "work_items" in result

    def test_parse_invalid_json_raises(self):
        """无法解析时抛出 ValueError"""
        with pytest.raises(ValueError, match="有效的JSON"):
            self.mixin._parse_ai_response("这不是JSON格式的内容！！！", self.projects)

    def test_project_code_matched_adds_project_id(self):
        """匹配到项目编码时补充project_id"""
        ai_response = '{"work_items": [{"project_code": "PJ001", "hours": 4}], "total_hours": 4}'
        result = self.mixin._parse_ai_response(ai_response, self.projects)
        item = result["work_items"][0]
        assert item.get("project_id") == 1
        assert item.get("project_name") == "机器人项目"

    def test_unknown_project_code_no_name_sets_none_id(self):
        """未匹配到项目编码且无project_name时，project_id设为None"""
        ai_response = '{"work_items": [{"project_code": "UNKNOWN", "hours": 2}], "total_hours": 2}'
        result = self.mixin._parse_ai_response(ai_response, self.projects)
        item = result["work_items"][0]
        # 无法按名称匹配，只清除project_id
        assert item.get("project_id") is None

    def test_null_project_code_sets_none_id(self):
        """project_code为null时project_id设为None"""
        ai_response = '{"work_items": [{"project_code": null, "hours": 3}], "total_hours": 3}'
        result = self.mixin._parse_ai_response(ai_response, self.projects)
        item = result["work_items"][0]
        assert item.get("project_id") is None
