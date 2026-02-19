# -*- coding: utf-8 -*-
"""
第四十七批覆盖测试 - work_log_ai/core.py
"""
import pytest

pytest.importorskip("app.services.work_log_ai.core")

from datetime import date
from unittest.mock import MagicMock, patch

from app.services.work_log_ai.core import WorkLogAICore


def _make_core(use_ai=False):
    db = MagicMock()
    core = WorkLogAICore(db)
    core.use_ai = use_ai
    return core, db


def test_init_sets_db():
    db = MagicMock()
    core = WorkLogAICore(db)
    assert core.db is db


def test_analyze_uses_rules_when_no_ai():
    core, db = _make_core(use_ai=False)
    core._get_user_projects = MagicMock(return_value=[])
    core._analyze_with_rules = MagicMock(return_value={"total_hours": 8, "work_items": []})
    result = core.analyze_work_log("做了一些开发工作", user_id=1, work_date=date(2025, 1, 1))
    core._analyze_with_rules.assert_called_once()
    assert result["total_hours"] == 8


def test_analyze_falls_back_to_rules_on_ai_error():
    core, db = _make_core(use_ai=True)
    core._get_user_projects = MagicMock(return_value=[])
    core._analyze_with_ai_sync = MagicMock(side_effect=RuntimeError("AI error"))
    core._analyze_with_rules = MagicMock(return_value={"total_hours": 4, "work_items": []})
    result = core.analyze_work_log("开发工作", user_id=1, work_date=date(2025, 1, 2))
    core._analyze_with_rules.assert_called_once()
    assert result["total_hours"] == 4


def test_analyze_uses_ai_when_available():
    core, db = _make_core(use_ai=True)
    core._get_user_projects = MagicMock(return_value=[{"id": 1}])
    core._analyze_with_ai_sync = MagicMock(return_value={"total_hours": 6, "work_items": []})
    result = core.analyze_work_log("AI分析内容", user_id=1, work_date=date(2025, 1, 3))
    core._analyze_with_ai_sync.assert_called_once()
    assert result["total_hours"] == 6


def test_analyze_passes_user_projects():
    core, db = _make_core(use_ai=False)
    projects = [{"id": 1, "name": "项目A"}]
    core._get_user_projects = MagicMock(return_value=projects)
    core._analyze_with_rules = MagicMock(return_value={"work_items": [], "total_hours": 0})
    core.analyze_work_log("日志内容", user_id=2, work_date=date(2025, 1, 5))
    call_args = core._analyze_with_rules.call_args
    assert call_args[0][1] == projects


def test_use_ai_flag_reflects_env():
    with patch.dict("os.environ", {"ALIBABA_API_KEY": "test-key"}):
        import importlib
        import app.services.work_log_ai.core as m
        importlib.reload(m)
        assert m.USE_AI is True
    # 还原
    import importlib
    import app.services.work_log_ai.core as m2
    importlib.reload(m2)
