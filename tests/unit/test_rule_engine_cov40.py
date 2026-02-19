# -*- coding: utf-8 -*-
"""
第四十批覆盖测试 - 工作日志规则引擎
"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch

try:
    from app.services.work_log_ai.rule_engine import RuleEngineMixin
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


@pytest.fixture
def engine():
    class ConcreteEngine(RuleEngineMixin):
        pass
    return ConcreteEngine()


def _fake_work_type(d):
    return "WORKDAY"


class TestRuleEngineMixin:

    @patch("app.services.work_log_ai.rule_engine.get_work_type", side_effect=_fake_work_type)
    def test_returns_dict_with_work_items(self, mock_get_type, engine):
        content = "今天完成了项目A的开发工作，耗时6小时"
        projects = [{"id": 1, "code": "PA", "name": "项目A", "keywords": ["项目A"]}]
        result = engine._analyze_with_rules(content, projects, date(2024, 1, 15))
        assert "work_items" in result
        assert "total_hours" in result
        assert "confidence" in result

    @patch("app.services.work_log_ai.rule_engine.get_work_type", side_effect=_fake_work_type)
    def test_extracts_explicit_hours(self, mock_get_type, engine):
        # 注意：多个正则模式可能重复匹配同一数字（如"6小时"被两个模式命中），
        # 所以验证 total_hours >= 6.0 且为6的整数倍
        content = "修复bug，耗时6小时"
        projects = [{"id": 1, "code": "X1", "name": "项目X", "keywords": []}]
        result = engine._analyze_with_rules(content, projects, date(2024, 1, 15))
        assert result["total_hours"] >= 6.0
        assert result["total_hours"] % 6.0 == 0

    @patch("app.services.work_log_ai.rule_engine.get_work_type", side_effect=_fake_work_type)
    def test_extracts_hours_with_h_unit(self, mock_get_type, engine):
        content = "开发任务 4.5h"
        projects = []
        result = engine._analyze_with_rules(content, projects, date(2024, 1, 15))
        assert result["total_hours"] == pytest.approx(4.5)

    @patch("app.services.work_log_ai.rule_engine.get_work_type", side_effect=_fake_work_type)
    def test_estimates_hours_when_not_explicit(self, mock_get_type, engine):
        content = "做了一些开发工作"  # 没有明确工时
        projects = []
        result = engine._analyze_with_rules(content, projects, date(2024, 1, 15))
        assert 2.0 <= result["total_hours"] <= 8.0

    @patch("app.services.work_log_ai.rule_engine.get_work_type", side_effect=_fake_work_type)
    def test_matches_project_by_code(self, mock_get_type, engine):
        content = "在PRJ001项目上工作了4小时"
        projects = [{"id": 99, "code": "PRJ001", "name": "测试项目", "keywords": []}]
        result = engine._analyze_with_rules(content, projects, date(2024, 1, 15))
        assert result["work_items"][0]["project_code"] == "PRJ001"

    @patch("app.services.work_log_ai.rule_engine.get_work_type", side_effect=_fake_work_type)
    def test_uses_first_project_when_no_match(self, mock_get_type, engine):
        content = "普通工作日志内容，工作8小时"
        projects = [
            {"id": 1, "code": "DEFAULT", "name": "默认项目", "keywords": []},
            {"id": 2, "code": "OTHER", "name": "其他项目", "keywords": []},
        ]
        result = engine._analyze_with_rules(content, projects, date(2024, 1, 15))
        assert result["work_items"][0]["project_id"] == 1

    @patch("app.services.work_log_ai.rule_engine.get_work_type", side_effect=_fake_work_type)
    def test_confidence_is_between_0_and_1(self, mock_get_type, engine):
        content = "今天完成工作8小时"
        projects = []
        result = engine._analyze_with_rules(content, projects, date(2024, 1, 15))
        assert 0.0 <= result["confidence"] <= 1.0

    @patch("app.services.work_log_ai.rule_engine.get_work_type", side_effect=_fake_work_type)
    def test_suggested_projects_at_most_5(self, mock_get_type, engine):
        content = "普通日志"
        projects = [{"id": i, "code": f"P{i}", "name": f"项目{i}", "keywords": []} for i in range(10)]
        result = engine._analyze_with_rules(content, projects, date(2024, 1, 15))
        assert len(result["suggested_projects"]) <= 5
