# -*- coding: utf-8 -*-
"""
第四十七批覆盖测试 - work_log_auto_generator.py
"""
import pytest

pytest.importorskip("app.services.work_log_auto_generator")

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, call, patch

from app.services.work_log_auto_generator import WorkLogAutoGenerator


def _make_gen():
    db = MagicMock()
    return WorkLogAutoGenerator(db), db


# ---------- generate_work_log_from_timesheet ----------

def test_generate_returns_none_when_submitted_exists(tmp_path):
    gen, db = _make_gen()
    # 已有SUBMITTED日志
    existing = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = existing
    result = gen.generate_work_log_from_timesheet(user_id=1, work_date=date(2025, 1, 1))
    assert result is None


def test_generate_returns_none_when_no_timesheets():
    gen, db = _make_gen()

    def query_side(model):
        q = MagicMock()
        if model.__name__ == "WorkLog":
            q.filter.return_value.first.return_value = None
        elif model.__name__ == "Timesheet":
            q.filter.return_value.order_by.return_value.all.return_value = []
        return q

    db.query.side_effect = lambda m: query_side(m)
    result = gen.generate_work_log_from_timesheet(user_id=1, work_date=date(2025, 1, 1))
    assert result is None


def test_generate_returns_none_when_no_user():
    gen, db = _make_gen()

    ts = MagicMock()
    ts.project_id = None
    ts.hours = Decimal("8")
    ts.task_id = None
    ts.task_name = "开发"
    ts.work_content = "写代码"
    ts.work_result = ""
    ts.progress_before = None
    ts.progress_after = None

    def query_side(model):
        q = MagicMock()
        if model.__name__ == "WorkLog":
            q.filter.return_value.first.return_value = None
        elif model.__name__ == "Timesheet":
            q.filter.return_value.order_by.return_value.all.return_value = [ts]
        elif model.__name__ == "User":
            q.filter.return_value.first.return_value = None
        return q

    db.query.side_effect = lambda m: query_side(m)
    result = gen.generate_work_log_from_timesheet(user_id=1, work_date=date(2025, 1, 1))
    assert result is None


# ---------- generate_yesterday_work_logs ----------

def test_generate_yesterday_work_logs_calls_batch():
    gen, db = _make_gen()
    with patch.object(gen, "batch_generate_work_logs", return_value={"generated_count": 5}) as mock_batch:
        result = gen.generate_yesterday_work_logs()
    yesterday = date.today() - timedelta(days=1)
    mock_batch.assert_called_once_with(
        start_date=yesterday, end_date=yesterday, user_ids=None, auto_submit=False
    )
    assert result["generated_count"] == 5


# ---------- batch_generate_work_logs ----------

def test_batch_generate_stats_structure():
    gen, db = _make_gen()
    with patch.object(gen, "generate_work_log_from_timesheet", return_value=None):
        # 用空用户列表快速跑
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []
        db.query.return_value.filter.return_value.all.return_value = []
        stats = gen.batch_generate_work_logs(
            start_date=date(2025, 1, 1), end_date=date(2025, 1, 1)
        )
    assert "generated_count" in stats
    assert "error_count" in stats


def test_batch_generate_counts_generated():
    gen, db = _make_gen()
    fake_log = MagicMock()
    user = MagicMock()
    user.id = 1
    user.real_name = "测试人"

    db.query.return_value.filter.return_value.all.return_value = [user]

    with patch.object(gen, "generate_work_log_from_timesheet", return_value=fake_log):
        stats = gen.batch_generate_work_logs(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 2),
            user_ids=[1]
        )
    assert stats["generated_count"] == 2  # 2天各1个
