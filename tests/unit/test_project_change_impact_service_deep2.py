# -*- coding: utf-8 -*-
"""Deep coverage for app.services.project_change_impact_service."""

from collections import deque
from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services import project_change_impact_service as svc


class QueryStub:
    def __init__(self, *, first=None, all=None, count=None, scalar=None):
        self._first = first
        self._all = [] if all is None else all
        self._count = count if count is not None else len(self._all)
        self._scalar = scalar

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self._first

    def all(self):
        return self._all

    def count(self):
        return self._count

    def scalar(self):
        return self._scalar


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
        self.refreshed = []
        self.flushes = 0

    def query(self, model):
        key = model if model in self.query_plan else str(model)
        queue = self.query_plan.get(key)
        if not queue:
            return QueryStub()
        return queue.popleft()

    def add(self, obj):
        self.added.append(obj)
        if getattr(obj, "id", None) is None:
            obj.id = len(self.added)

    def commit(self):
        self.commits += 1

    def refresh(self, obj):
        self.refreshed.append(obj)

    def flush(self):
        self.flushes += 1
        for index, obj in enumerate(self.added, start=1):
            if getattr(obj, "id", None) is None:
                obj.id = 100 + index


def q(*, first=None, all=None, count=None, scalar=None):
    return QueryStub(first=first, all=all, count=count, scalar=scalar)


def test_assess_impact_creates_record_with_inferred_risk_and_auto_milestones():
    ecn = SimpleNamespace(id=1, ecn_no="ECN-001", priority="URGENT")
    project = SimpleNamespace(id=10, project_code="PRJ-10", stage="EXECUTION", progress_pct=60)
    milestones = [
        SimpleNamespace(id=101, milestone_name="设计评审", planned_date=date(2026, 4, 20)),
        SimpleNamespace(id=102, milestone_name="现场验收", planned_date=None),
    ]
    db = FakeDB(
        {
            svc.Ecn: q(first=ecn),
            svc.Project: q(first=project),
            svc.ProjectMilestone: q(all=milestones),
        }
    )

    record = svc.assess_impact(
        db,
        ecn_id=1,
        project_id=10,
        current_user_id=99,
        machine_id=5,
        schedule_impact_days=3,
        rework_cost=Decimal("100"),
        scrap_cost=Decimal("50"),
        additional_cost=Decimal("25"),
        risk_description="高优先级变更",
        remark="需要同步跟进",
    )

    assert record.ecn_no == "ECN-001"
    assert record.project_id == 10
    assert record.total_cost_impact == Decimal("175")
    assert record.risk_level == "CRITICAL"
    assert record.status == "ASSESSED"
    assert record.impact_report["schedule"]["delay_days"] == 3
    assert record.impact_report["cost"]["total"] == 175.0
    assert record.impact_report["risk"]["description"] == "高优先级变更"
    assert len(record.affected_milestones) == 2
    assert "预计延期 3 天" in record.impact_summary
    assert db.commits == 1
    assert db.refreshed == [record]


@pytest.mark.parametrize(
    ("ecn_result", "project_result", "message"),
    [
        (None, object(), "ECN 1 不存在"),
        (SimpleNamespace(id=1, ecn_no="ECN-001", priority="LOW"), None, "项目 10 不存在"),
    ],
)
def test_assess_impact_validates_required_records(ecn_result, project_result, message):
    db = FakeDB({svc.Ecn: q(first=ecn_result), svc.Project: q(first=project_result)})

    with pytest.raises(ValueError, match=message):
        svc.assess_impact(db, ecn_id=1, project_id=10, current_user_id=99)


def test_execute_linkage_updates_project_costs_risks_and_milestones(monkeypatch):
    record = SimpleNamespace(
        id=1,
        status="ASSESSED",
        project_id=10,
        machine_id=5,
        ecn_no="ECN-001",
        schedule_impact_days=4,
        total_cost_impact=Decimal("180"),
        affected_milestones=[{"milestone_id": 101}],
        risk_level="HIGH",
        actual_delay_days=None,
        actual_cost_impact=None,
        milestones_updated=False,
        milestone_update_detail=None,
        costs_recorded=False,
        cost_record_ids=None,
        risk_created=False,
        risk_record_id=None,
        executed_by=None,
        executed_at=None,
        remark=None,
    )
    project = SimpleNamespace(id=10, planned_end_date=date(2026, 5, 1))
    db = FakeDB({svc.ProjectChangeImpact: q(first=record), svc.Project: q(first=project)})

    monkeypatch.setattr(
        svc,
        "_update_project_milestones",
        lambda db, project_id, machine_id, delay_days, affected_milestones: [
            {"milestone_id": 101, "new_date": "2026-05-05"}
        ],
    )
    monkeypatch.setattr(svc, "_record_project_costs", lambda db, record, user_id: [201, 202])
    monkeypatch.setattr(svc, "_create_project_risk", lambda db, record, user_id: 301)

    result = svc.execute_linkage(
        db,
        impact_id=1,
        current_user_id=88,
        actual_delay_days=6,
        actual_cost_impact=Decimal("220"),
        remark="已执行联动",
    )

    assert result is record
    assert record.actual_delay_days == 6
    assert record.actual_cost_impact == Decimal("220")
    assert record.milestones_updated is True
    assert record.costs_recorded is True
    assert record.risk_created is True
    assert record.cost_record_ids == [201, 202]
    assert record.risk_record_id == 301
    assert record.executed_by == 88
    assert record.status == "COMPLETED"
    assert project.planned_end_date == date(2026, 5, 7)
    assert db.commits == 1
    assert db.refreshed == [record]


@pytest.mark.parametrize(
    ("record", "message"),
    [
        (None, "影响记录 1 不存在"),
        (SimpleNamespace(id=1, status="COMPLETED"), "影响记录状态为 COMPLETED，无法执行联动"),
    ],
)
def test_execute_linkage_rejects_missing_or_invalid_records(record, message):
    db = FakeDB({svc.ProjectChangeImpact: q(first=record)})

    with pytest.raises(ValueError, match=message):
        svc.execute_linkage(db, impact_id=1, current_user_id=88)


def test_project_change_summary_and_delay_history_use_actual_values_when_present():
    project = SimpleNamespace(id=10, project_name="装配线项目")
    impact1 = SimpleNamespace(
        id=1,
        ecn_id=101,
        ecn_no="ECN-101",
        status="ASSESSED",
        actual_delay_days=None,
        schedule_impact_days=3,
        actual_cost_impact=None,
        total_cost_impact=Decimal("120"),
        risk_level="LOW",
        assessed_at=datetime(2026, 4, 1, 10, 0, 0),
        executed_at=None,
        created_at=datetime(2026, 4, 1, 10, 0, 0),
    )
    impact2 = SimpleNamespace(
        id=2,
        ecn_id=102,
        ecn_no="ECN-102",
        status="COMPLETED",
        actual_delay_days=5,
        schedule_impact_days=2,
        actual_cost_impact=Decimal("300"),
        total_cost_impact=Decimal("250"),
        risk_level="CRITICAL",
        assessed_at=datetime(2026, 4, 2, 10, 0, 0),
        executed_at=datetime(2026, 4, 3, 12, 0, 0),
        created_at=datetime(2026, 4, 2, 10, 0, 0),
    )

    summary_db = FakeDB({svc.Project: q(first=project), svc.ProjectChangeImpact: q(all=[impact1, impact2])})
    summary = svc.get_project_change_summary(summary_db, project_id=10)

    assert summary["project_name"] == "装配线项目"
    assert summary["total_ecn_count"] == 2
    assert summary["assessed_count"] == 1
    assert summary["completed_count"] == 1
    assert summary["total_delay_days"] == 8
    assert summary["total_cost_impact"] == Decimal("420")
    assert summary["high_risk_count"] == 1
    assert summary["impacts"] == [impact1, impact2]

    history_db = FakeDB({svc.ProjectChangeImpact: q(all=[impact1, impact2])})
    history = svc.get_project_delay_history(history_db, project_id=10)

    assert history == [
        {
            "impact_id": 1,
            "ecn_id": 101,
            "ecn_no": "ECN-101",
            "delay_days": 3,
            "cumulative_delay_days": 3,
            "risk_level": "LOW",
            "status": "ASSESSED",
            "assessed_at": "2026-04-01T10:00:00",
            "executed_at": None,
        },
        {
            "impact_id": 2,
            "ecn_id": 102,
            "ecn_no": "ECN-102",
            "delay_days": 5,
            "cumulative_delay_days": 8,
            "risk_level": "CRITICAL",
            "status": "COMPLETED",
            "assessed_at": "2026-04-02T10:00:00",
            "executed_at": "2026-04-03T12:00:00",
        },
    ]


def test_project_change_summary_requires_existing_project():
    db = FakeDB({svc.Project: q(first=None)})

    with pytest.raises(ValueError, match="项目 10 不存在"):
        svc.get_project_change_summary(db, project_id=10)


def test_get_ecn_project_impacts_and_impact_detail_return_query_results():
    impacts = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
    detail = SimpleNamespace(id=7, ecn_no="ECN-007")

    impacts_db = FakeDB({svc.ProjectChangeImpact: q(all=impacts)})
    detail_db = FakeDB({svc.ProjectChangeImpact: q(first=detail)})

    assert svc.get_ecn_project_impacts(impacts_db, ecn_id=5) == impacts
    assert svc.get_impact_detail(detail_db, impact_id=7) is detail


def test_helper_functions_cover_thresholds_summaries_and_recommendations():
    assert svc._infer_risk_level(31, Decimal("0"), None) == "CRITICAL"
    assert svc._infer_risk_level(10, Decimal("0"), None) == "MEDIUM"
    assert svc._infer_risk_level(0, Decimal("60000"), None) == "HIGH"
    assert svc._infer_risk_level(0, Decimal("0"), None) == "LOW"

    ecn = SimpleNamespace(ecn_no="ECN-009")
    project = SimpleNamespace(project_code="PRJ-9")
    summary = svc._generate_impact_summary(
        ecn,
        project,
        delay_days=0,
        total_cost=Decimal("88"),
        risk_level="MEDIUM",
        affected_milestones=[{"milestone_id": 1}],
    )
    assert summary == "ECN ECN-009 对项目 PRJ-9 的影响评估：；无进度影响；成本影响 ¥88.00；风险等级：中；影响 1 个里程碑"
    assert (
        svc._generate_impact_summary(
            ecn,
            project,
            delay_days=0,
            total_cost=Decimal("0"),
            risk_level="UNKNOWN",
            affected_milestones=None,
        )
        == "ECN ECN-009 对项目 PRJ-9 的影响评估：；无进度影响；无成本影响；风险等级：UNKNOWN"
    )

    assert "立即组织评审会议" in svc._generate_recommendation(1, Decimal("1"), "CRITICAL")
    assert "重点关注" in svc._generate_recommendation(1, Decimal("1"), "HIGH")
    assert "周报跟踪" in svc._generate_recommendation(1, Decimal("1"), "MEDIUM")
    assert "影响可控" in svc._generate_recommendation(0, Decimal("0"), "LOW")


def test_milestone_helpers_cover_auto_assess_and_update_paths():
    auto_db = FakeDB(
        {
            svc.ProjectMilestone: q(
                all=[
                    SimpleNamespace(id=1, milestone_name="设计", planned_date=date(2026, 4, 10)),
                    SimpleNamespace(id=2, milestone_name="交付", planned_date=None),
                ]
            )
        }
    )
    auto_result = svc._auto_assess_milestone_impact(auto_db, project_id=10, machine_id=5, delay_days=2)
    assert auto_result == [
        {
            "milestone_id": 1,
            "name": "设计",
            "original_date": "2026-04-10",
            "new_date": "2026-04-12",
            "delay_days": 2,
        },
        {
            "milestone_id": 2,
            "name": "交付",
            "original_date": None,
            "new_date": None,
            "delay_days": 2,
        },
    ]

    specific_ms = SimpleNamespace(id=1, milestone_name="设计", planned_date=date(2026, 4, 10))
    specific_db = FakeDB({svc.ProjectMilestone: q(first=specific_ms)})
    specific_result = svc._update_project_milestones(
        specific_db,
        project_id=10,
        machine_id=None,
        delay_days=3,
        affected_milestones=[{"milestone_id": 1}],
    )
    assert specific_result == [{"milestone_id": 1, "name": "设计", "old_date": "2026-04-10", "new_date": "2026-04-13"}]

    all_ms = SimpleNamespace(id=2, milestone_name="交付", planned_date=date(2026, 4, 15))
    all_db = FakeDB({svc.ProjectMilestone: q(all=[all_ms])})
    all_result = svc._update_project_milestones(all_db, project_id=10, machine_id=8, delay_days=1, affected_milestones=None)
    assert all_result == [{"milestone_id": 2, "name": "交付", "old_date": "2026-04-15", "new_date": "2026-04-16"}]


def test_cost_and_risk_helpers_create_expected_records(monkeypatch):
    record = SimpleNamespace(
        project_id=7,
        machine_id=3,
        ecn_id=8,
        ecn_no="ECN-888",
        rework_cost=Decimal("20"),
        scrap_cost=Decimal("30"),
        additional_cost=Decimal("40"),
        schedule_impact_days=6,
        total_cost_impact=Decimal("90"),
        risk_level="CRITICAL",
        risk_description="关键设备改型",
    )
    db = FakeDB()

    cost_ids = svc._record_project_costs(db, record, user_id=55)

    assert cost_ids == [1, 2, 3]
    assert [obj.cost_type for obj in db.added[:3]] == ["ECN_REWORK", "ECN_SCRAP", "ECN_ADDITIONAL"]
    assert db.added[0].description == "返工成本 - ECN ECN-888"
    assert db.flushes == 3

    monkeypatch.setattr(svc.func, "count", lambda *args, **kwargs: "COUNT_EXPR")
    risk_db = FakeDB({"COUNT_EXPR": q(scalar=2)})
    risk_id = svc._create_project_risk(risk_db, record, user_id=55)

    assert risk_id == 1
    risk = risk_db.added[0]
    assert risk.risk_no == "RISK-0007-003"
    assert risk.risk_name == "ECN变更风险 - ECN-888"
    assert risk.probability == "HIGH"
    assert risk.status == "IDENTIFIED"
    assert "成本影响 ¥90.00" in risk.description
