# -*- coding: utf-8 -*-
"""Deep coverage for app.services.ecn.ecn_scheduler."""

from collections import deque
from contextlib import contextmanager
from datetime import datetime, timedelta
from types import SimpleNamespace
import runpy
import warnings

import app.dependencies
import app.services.ecn.notification
from app.services.ecn import ecn_scheduler as svc


class QueryStub:
    def __init__(self, *, first=None, all=None):
        self._first = first
        self._all = [] if all is None else all

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self._all

    def first(self):
        return self._first


class FakeDB:
    def __init__(self, query_plan=None):
        self.query_plan = {}
        for key, value in (query_plan or {}).items():
            if isinstance(value, deque):
                self.query_plan[key] = value
            elif isinstance(value, list):
                self.query_plan[key] = deque(value)
            else:
                self.query_plan[key] = deque([value])
        self.added = []
        self.commits = 0

    def query(self, model):
        key = model if model in self.query_plan else str(model)
        queue = self.query_plan.get(key)
        if not queue:
            return QueryStub()
        return queue.popleft()

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.commits += 1


def q(*, first=None, all=None):
    return QueryStub(first=first, all=all)


@contextmanager
def _db_context(db):
    yield db


def test_overdue_checkers_build_expected_alerts_and_mark_records():
    now = datetime.now()
    ecn = SimpleNamespace(id=1, ecn_no="ECN-001", ecn_title="测试ECN", applicant_id=55)

    eval_alert = SimpleNamespace(id=11, ecn_id=1, eval_dept="研发部", created_at=now - timedelta(days=5))
    eval_skipped = SimpleNamespace(id=12, ecn_id=2, eval_dept="质量部", created_at=now - timedelta(days=4))
    eval_db = FakeDB({svc.EcnEvaluation: q(all=[eval_alert, eval_skipped]), svc.Ecn: [q(first=ecn), q(first=None)]})
    eval_result = svc.check_evaluation_overdue(eval_db)
    assert len(eval_result) == 1
    assert eval_result[0]["type"] == "EVALUATION_OVERDUE"
    assert eval_result[0]["eval_dept"] == "研发部"
    assert "超时" in eval_result[0]["message"]

    approval = SimpleNamespace(
        id=21,
        ecn_id=1,
        approval_level=2,
        approval_role="部门经理",
        due_date=now - timedelta(days=2),
        is_overdue=False,
    )
    approval_skipped = SimpleNamespace(
        id=22,
        ecn_id=2,
        approval_level=1,
        approval_role="总监",
        due_date=now - timedelta(days=1),
        is_overdue=False,
    )
    approval_db = FakeDB({svc.EcnApproval: q(all=[approval, approval_skipped]), svc.Ecn: [q(first=ecn), q(first=None)]})
    approval_result = svc.check_approval_overdue(approval_db)
    assert len(approval_result) == 1
    assert approval_result[0]["type"] == "APPROVAL_OVERDUE"
    assert approval.is_overdue is True
    assert approval_db.added == [approval]
    assert approval_db.commits == 1

    task = SimpleNamespace(id=31, ecn_id=1, task_name="结构调整", planned_end=(now - timedelta(days=3)).date())
    task_skipped = SimpleNamespace(id=32, ecn_id=2, task_name="文档更新", planned_end=(now - timedelta(days=1)).date())
    task_db = FakeDB({svc.EcnTask: q(all=[task, task_skipped]), svc.Ecn: [q(first=ecn), q(first=None)]})
    task_result = svc.check_task_overdue(task_db)
    assert len(task_result) == 1
    assert task_result[0]["type"] == "TASK_OVERDUE"
    assert task_result[0]["task_name"] == "结构调整"


def test_check_all_overdue_aggregates_results_from_context(monkeypatch):
    db = FakeDB()
    monkeypatch.setattr(svc, "get_db_session", lambda: _db_context(db))
    monkeypatch.setattr(svc, "check_evaluation_overdue", lambda db: [{"type": "E1"}])
    monkeypatch.setattr(svc, "check_approval_overdue", lambda db: [{"type": "A1"}])
    monkeypatch.setattr(svc, "check_task_overdue", lambda db: [{"type": "T1"}])

    assert svc.check_all_overdue() == [{"type": "E1"}, {"type": "A1"}, {"type": "T1"}]


def test_send_overdue_notifications_handles_each_alert_type_and_errors(monkeypatch):
    ecn = SimpleNamespace(id=1, applicant_id=55)
    evaluation_owner = SimpleNamespace(id=11, evaluator_id=101)
    evaluation_fallback = SimpleNamespace(id=12, evaluator_id=None)
    approval = SimpleNamespace(id=21, approver_id=202)
    task = SimpleNamespace(id=31, assignee_id=303)
    task_error = SimpleNamespace(id=32, assignee_id=404)
    db = FakeDB(
        {
            svc.EcnEvaluation: [q(first=evaluation_owner), q(first=evaluation_fallback)],
            svc.Ecn: [q(first=ecn)],
            svc.EcnApproval: q(first=approval),
            svc.EcnTask: [q(first=task), q(first=task_error)],
        }
    )

    monkeypatch.setattr(app.dependencies, "get_db_session", lambda: _db_context(db))
    notifications = []

    def fake_notify(_db, alert, user_ids):
        notifications.append((alert["type"], tuple(user_ids)))
        if alert["ecn_no"] == "ECN-ERR":
            raise RuntimeError("notify failed")

    monkeypatch.setattr(app.services.ecn.notification, "notify_overdue_alert", fake_notify)

    svc.send_overdue_notifications(
        [
            {"type": "EVALUATION_OVERDUE", "ecn_id": 1, "ecn_no": "ECN-001", "eval_id": 11},
            {"type": "EVALUATION_OVERDUE", "ecn_id": 1, "ecn_no": "ECN-002", "eval_id": 12},
            {"type": "APPROVAL_OVERDUE", "ecn_id": 1, "ecn_no": "ECN-003", "approval_id": 21},
            {"type": "TASK_OVERDUE", "ecn_id": 1, "ecn_no": "ECN-004", "task_id": 31},
            {"type": "TASK_OVERDUE", "ecn_id": 1, "ecn_no": "ECN-ERR", "task_id": 32},
        ]
    )

    assert notifications == [
        ("EVALUATION_OVERDUE", (101,)),
        ("EVALUATION_OVERDUE", (55,)),
        ("APPROVAL_OVERDUE", (202,)),
        ("TASK_OVERDUE", (303,)),
        ("TASK_OVERDUE", (404,)),
    ]


def test_send_overdue_notifications_returns_early_for_empty_alerts(monkeypatch):
    called = []
    monkeypatch.setattr(app.dependencies, "get_db_session", lambda: called.append(True) or _db_context(FakeDB()))

    svc.send_overdue_notifications([])

    assert called == []


def test_run_scheduler_handles_alerts_no_alerts_and_exceptions(monkeypatch):
    send_calls = []
    monkeypatch.setattr(svc, "send_overdue_notifications", lambda alerts: send_calls.append(list(alerts)))

    monkeypatch.setattr(svc, "check_all_overdue", lambda: [{"type": "TEST"}])
    svc.run_ecn_scheduler()
    assert send_calls == [[{"type": "TEST"}]]

    monkeypatch.setattr(svc, "check_all_overdue", lambda: [])
    svc.run_ecn_scheduler()
    assert send_calls == [[{"type": "TEST"}]]

    monkeypatch.setattr(svc, "check_all_overdue", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    svc.run_ecn_scheduler()


def test_module_main_branch_runs_scheduler_with_empty_context(monkeypatch):
    monkeypatch.setattr(app.dependencies, "get_db_session", lambda: _db_context(FakeDB()))

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"'app\.services\.ecn\.ecn_scheduler' found in sys\.modules.*",
            category=RuntimeWarning,
        )
        runpy.run_module("app.services.ecn.ecn_scheduler", run_name="__main__")
