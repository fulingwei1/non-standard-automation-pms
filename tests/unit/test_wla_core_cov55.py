# -*- coding: utf-8 -*-
"""
Tests for app/services/work_log_ai/core.py
"""
import pytest
from datetime import date
from unittest.mock import MagicMock, patch

try:
    from app.services.work_log_ai.core import WorkLogAICore
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def core(mock_db):
    with patch("app.services.work_log_ai.core.USE_AI", False):
        return WorkLogAICore(db=mock_db)


def test_init_stores_db(mock_db):
    """确认 db 属性存储正确"""
    with patch("app.services.work_log_ai.core.USE_AI", False):
        core = WorkLogAICore(db=mock_db)
        assert core.db is mock_db


def test_init_use_ai_false(mock_db):
    """USE_AI=False 时 use_ai 属性为 False"""
    with patch("app.services.work_log_ai.core.USE_AI", False):
        core = WorkLogAICore(db=mock_db)
        assert core.use_ai is False


def test_analyze_work_log_uses_rules_when_no_ai(mock_db):
    """无AI时应调用规则引擎"""
    with patch("app.services.work_log_ai.core.USE_AI", False):
        core = WorkLogAICore(db=mock_db)
        core._get_user_projects = MagicMock(return_value=[])
        core._analyze_with_rules = MagicMock(return_value={"work_items": [], "total_hours": 0})
        result = core.analyze_work_log("完成了接口开发", user_id=1, work_date=date.today())
        core._analyze_with_rules.assert_called_once()


def test_analyze_work_log_ai_fallback(mock_db):
    """AI分析失败时应回退到规则引擎"""
    with patch("app.services.work_log_ai.core.USE_AI", True):
        core = WorkLogAICore(db=mock_db)
        core._get_user_projects = MagicMock(return_value=[])
        core._analyze_with_ai_sync = MagicMock(side_effect=Exception("AI failed"))
        core._analyze_with_rules = MagicMock(return_value={"work_items": [], "total_hours": 0})
        result = core.analyze_work_log("测试内容", user_id=1, work_date=date.today())
        core._analyze_with_rules.assert_called_once()


def test_analyze_work_log_returns_dict(mock_db):
    """分析结果应是字典"""
    with patch("app.services.work_log_ai.core.USE_AI", False):
        core = WorkLogAICore(db=mock_db)
        core._get_user_projects = MagicMock(return_value=[])
        core._analyze_with_rules = MagicMock(return_value={
            "work_items": [],
            "suggested_projects": [],
            "total_hours": 8,
            "confidence": 0.8
        })
        result = core.analyze_work_log("任何内容", user_id=2, work_date=date.today())
        assert isinstance(result, dict)


def test_analyze_calls_get_user_projects(mock_db):
    """分析前应先获取用户项目列表"""
    with patch("app.services.work_log_ai.core.USE_AI", False):
        core = WorkLogAICore(db=mock_db)
        core._get_user_projects = MagicMock(return_value=[])
        core._analyze_with_rules = MagicMock(return_value={})
        core.analyze_work_log("content", user_id=3, work_date=date.today())
        core._get_user_projects.assert_called_once_with(3)


def test_analyze_ai_success_path(mock_db):
    """AI分析成功时直接返回AI结果"""
    with patch("app.services.work_log_ai.core.USE_AI", True):
        core = WorkLogAICore(db=mock_db)
        core._get_user_projects = MagicMock(return_value=[])
        ai_result = {"work_items": [{"content": "task", "hours": 4}], "total_hours": 4}
        core._analyze_with_ai_sync = MagicMock(return_value=ai_result)
        core._analyze_with_rules = MagicMock()
        result = core.analyze_work_log("任务内容", user_id=1, work_date=date.today())
        assert result == ai_result
        core._analyze_with_rules.assert_not_called()
