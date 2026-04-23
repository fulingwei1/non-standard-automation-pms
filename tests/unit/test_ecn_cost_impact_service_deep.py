# -*- coding: utf-8 -*-
"""ecn_cost_impact_service 深度测试"""

from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from app.services.ecn.ecn_cost_impact_service import (
    check_cost_alerts,
    cost_impact_analysis,
    create_cost_record,
    get_cost_tracking,
    get_project_ecn_cost_summary,
)


class FakeQuery:
    def __init__(self, first_value=None, all_value=None, scalar_value=None):
        self._first_value = first_value
        self._all_value = all_value or []
        self._scalar_value = scalar_value

    def filter(self, *args, **kwargs):
        return self

    def group_by(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def first(self):
        return self._first_value

    def all(self):
        return self._all_value

    def scalar(self):
        return self._scalar_value


class TestEcnCostImpactServiceDeep:
    def test_cost_impact_analysis_raises_when_ecn_missing(self):
        db = Mock()
        db.query.return_value = FakeQuery(first_value=None)

        with pytest.raises(ValueError):
            cost_impact_analysis(db, 1)

    def test_cost_impact_analysis_aggregates_direct_and_indirect_costs(self):
        ecn = SimpleNamespace(id=1, ecn_no="ECN-1", project_id=8)
        type_rows = [
            SimpleNamespace(cost_type="SCRAP", estimated_total=100, actual_total=80, record_count=1),
            SimpleNamespace(cost_type="REWORK", estimated_total=50, actual_total=60, record_count=1),
            SimpleNamespace(cost_type="CLAIM", estimated_total=30, actual_total=20, record_count=1),
        ]
        materials = [
            SimpleNamespace(material_id=1, material_code="M1", material_name="Motor", cost_impact=120, obsolete_cost=20)
        ]
        db = Mock()
        db.query.side_effect = [
            FakeQuery(first_value=ecn),
            FakeQuery(all_value=type_rows),
            FakeQuery(all_value=materials),
            FakeQuery(scalar_value=150),
        ]

        result = cost_impact_analysis(db, 1)

        assert result["direct_cost_total"] == Decimal("140")
        assert result["indirect_cost_total"] == Decimal("20")
        assert result["total_cost_impact"] == Decimal("160")
        assert result["top_material_impacts"][0]["new_purchase_cost"] == Decimal("100")
        assert result["assessed_cost_impact"] == Decimal("150")

    def test_get_cost_tracking_builds_trend_and_forecast(self):
        ecn = SimpleNamespace(id=1, ecn_no="ECN-1")
        records = [
            SimpleNamespace(cost_type="SCRAP", estimated_amount=100, actual_amount=110, approval_status="APPROVED", cost_date=date(2026,1,10), created_at=datetime(2026,1,10)),
            SimpleNamespace(cost_type="SCRAP", estimated_amount=50, actual_amount=40, approval_status="PENDING", cost_date=date(2026,2,10), created_at=datetime(2026,2,10)),
            SimpleNamespace(cost_type="ADMIN", estimated_amount=20, actual_amount=30, approval_status="PENDING", cost_date=None, created_at=datetime(2026,3,10)),
        ]
        db = Mock()
        db.query.side_effect = [FakeQuery(first_value=ecn), FakeQuery(all_value=records)]

        result = get_cost_tracking(db, 1)

        assert result["total_estimated"] == Decimal("170")
        assert result["total_actual"] == Decimal("180")
        assert result["variance"] == Decimal("10")
        assert result["variance_ratio"] == 5.88
        assert result["forecast_final_cost"] == Decimal("250")
        assert result["approved_records"] == 1
        assert result["pending_records"] == 2
        assert len(result["cost_trend"]) == 3

    def test_create_cost_record_validates_and_inherits_project(self):
        ecn = SimpleNamespace(id=1, ecn_no="ECN-1", project_id=5)
        db = Mock()
        db.query.return_value = FakeQuery(first_value=ecn)

        with patch(
            "app.services.ecn.ecn_cost_impact_service.EcnCostRecord",
            side_effect=lambda **kwargs: SimpleNamespace(**kwargs, id=66),
        ):
            record = create_cost_record(db, 9, ecn_id=1, cost_type="SCRAP", actual_amount=Decimal("88"))

        assert record.project_id == 5
        assert record.approval_status == "PENDING"
        assert record.recorded_by == 9
        assert db.add.called and db.commit.called and db.refresh.called

    def test_create_cost_record_rejects_invalid_cost_type(self):
        ecn = SimpleNamespace(id=1, ecn_no="ECN-1", project_id=5)
        db = Mock()
        db.query.return_value = FakeQuery(first_value=ecn)

        with pytest.raises(ValueError):
            create_cost_record(db, 1, ecn_id=1, cost_type="BAD")

    def test_get_project_ecn_cost_summary_aggregates_project_costs(self):
        project = SimpleNamespace(id=7, project_name="P7", budget_amount=1000)
        ecns = [
            SimpleNamespace(id=1, ecn_no="E1", ecn_title="A", status="OPEN"),
            SimpleNamespace(id=2, ecn_no="E2", ecn_title="B", status="DONE"),
        ]
        summary1 = SimpleNamespace(est=100, act=150, cnt=2)
        summary2 = SimpleNamespace(est=50, act=100, cnt=1)
        type_rows1 = [SimpleNamespace(cost_type="SCRAP", est=100, act=150, cnt=2)]
        type_rows2 = [SimpleNamespace(cost_type="ADMIN", est=50, act=100, cnt=1)]
        db = Mock()
        db.query.side_effect = [
            FakeQuery(first_value=project),
            FakeQuery(all_value=ecns),
            FakeQuery(first_value=summary1),
            FakeQuery(all_value=type_rows1),
            FakeQuery(first_value=summary2),
            FakeQuery(all_value=type_rows2),
        ]

        result = get_project_ecn_cost_summary(db, 7)

        assert result["total_ecn_count"] == 2
        assert result["total_estimated_cost"] == Decimal("150")
        assert result["total_actual_cost"] == Decimal("250")
        assert result["ecn_cost_ratio"] == 25.0
        assert len(result["cost_by_type"]) == 2

    def test_check_cost_alerts_covers_budget_large_amount_and_trend(self):
        ecn = SimpleNamespace(id=1, ecn_no="ECN-1")
        records = [
            SimpleNamespace(id=1, cost_type="SCRAP", estimated_amount=100, actual_amount=120, approval_status="PENDING", created_at=datetime(2026,1,1)),
            SimpleNamespace(id=2, cost_type="SCRAP", estimated_amount=100, actual_amount=200, approval_status="PENDING", created_at=datetime(2026,1,2)),
            SimpleNamespace(id=3, cost_type="ADMIN", estimated_amount=100, actual_amount=400, approval_status="PENDING", created_at=datetime(2026,1,3)),
        ]
        db = Mock()
        db.query.side_effect = [FakeQuery(first_value=ecn), FakeQuery(all_value=records)]

        result = check_cost_alerts(db, 1, budget_threshold=Decimal("500"), large_amount_threshold=Decimal("300"), trend_check=True)

        alert_types = {a["alert_type"] for a in result["alerts"]}
        assert "OVER_BUDGET" in alert_types
        assert "LARGE_AMOUNT" in alert_types
        assert "TREND_ABNORMAL" in alert_types
        assert result["alert_count"] == 3
