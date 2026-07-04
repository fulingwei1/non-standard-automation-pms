from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from fastapi import HTTPException

from app.api.v1.endpoints import relationship_maturity


class _Query:
    def __init__(self, rows=None, first_value=None):
        self._rows = rows or []
        self._first_value = first_value

    def filter(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def all(self):
        return self._rows

    def first(self):
        return self._first_value

    def get(self, _id):
        return self._first_value


class _Db:
    def __init__(self, customer=None, opportunity=None, scores=None, customers_by_id=None):
        self.customer = customer
        self.opportunity = opportunity
        self.scores = scores or []
        self.customers_by_id = customers_by_id or {}

    def query(self, model):
        name = getattr(model, "__name__", "")
        if name == "CustomerRelationshipScore":
            return _Query(rows=self.scores)
        if name == "Customer":
            return _Query(first_value=self.customer)
        if name == "Opportunity":
            return _Query(first_value=self.opportunity)
        return _Query()


def test_customer_assessment_uses_scoring_service_and_real_customer(monkeypatch):
    calls = []

    class DummyScoringService:
        def __init__(self, db):
            self.db = db

        def calculate_customer_score(self, customer_id, opportunity_id=None, save_to_db=True):
            calls.append(
                {
                    "customer_id": customer_id,
                    "opportunity_id": opportunity_id,
                    "save_to_db": save_to_db,
                }
            )
            return {
                "customer_id": customer_id,
                "opportunity_id": opportunity_id,
                "assessment_date": "2026-07-04",
                "dimension_scores": {},
                "overall_assessment": {
                    "total_score": 32,
                    "max_score": 100,
                    "maturity_level": "L2",
                    "maturity_level_name": "发展级",
                    "estimated_win_rate": 27,
                },
                "radar_data": [],
                "improvement_recommendations": [],
            }

    monkeypatch.setattr(
        relationship_maturity,
        "RelationshipScoringService",
        DummyScoringService,
        raising=False,
    )
    db = _Db(
        customer=SimpleNamespace(id=9, customer_name="真实客户A"),
        opportunity=SimpleNamespace(id=3, opp_name="真实商机B"),
    )

    result = relationship_maturity.get_customer_relationship_assessment(
        customer_id=9,
        opportunity_id=3,
        db=db,
        current_user=Mock(),
    )

    assert calls == [{"customer_id": 9, "opportunity_id": 3, "save_to_db": False}]
    assert result["customer_name"] == "真实客户A"
    assert result["opportunity_name"] == "真实商机B"
    assert result["overall_assessment"]["total_score"] == 32
    assert "宁德时代" not in str(result)


def test_customer_assessment_raises_404_for_missing_customer():
    db = _Db(customer=None)

    try:
        relationship_maturity.get_customer_relationship_assessment(
            customer_id=999,
            db=db,
            current_user=Mock(),
        )
    except HTTPException as exc:
        assert exc.status_code == 404
        assert exc.detail == "客户不存在"
    else:
        raise AssertionError("missing customer must raise 404")


def test_improvement_plan_uses_computed_gap_without_name_error():
    result = relationship_maturity.create_relationship_improvement_plan(
        customer_id=7,
        current_score=40,
        target_score=60,
        timeline_days=30,
        db=Mock(),
        current_user=Mock(),
    )

    assert result["gap"] == 20
    assert result["milestones"][0]["target_score"] == 46
    assert "李四" not in str(result)


def test_portfolio_analysis_uses_score_records_not_static_demo_customers(monkeypatch):
    score_a = SimpleNamespace(
        customer_id=1,
        total_score=78,
        maturity_level="L4",
        estimated_win_rate=72,
        score_date="2026-07-04",
    )
    score_b = SimpleNamespace(
        customer_id=2,
        total_score=42,
        maturity_level="L2",
        estimated_win_rate=35,
        score_date="2026-07-04",
    )
    customers = {
        1: SimpleNamespace(id=1, customer_name="真实客户A", annual_revenue=5000000),
        2: SimpleNamespace(id=2, customer_name="真实客户B", annual_revenue=3000000),
    }

    class PortfolioDb(_Db):
        def query(self, model):
            name = getattr(model, "__name__", "")
            if name == "CustomerRelationshipScore":
                return _Query(rows=[score_a, score_b])
            if name == "Customer":
                query = _Query(first_value=None)

                def filter(*_args, **_kwargs):
                    # Endpoint filters by Customer.id; tests only need deterministic current lookup.
                    query._first_value = customers[len([c for c in customers.values() if c is not None]) - len(customers) + 1]
                    return query

                query.filter = filter
                return query
            return _Query()

    db = PortfolioDb(scores=[score_a, score_b])

    lookup = {1: customers[1], 2: customers[2]}
    monkeypatch.setattr(
        relationship_maturity,
        "_get_customer",
        lambda db, customer_id: lookup.get(customer_id),
        raising=False,
    )

    result = relationship_maturity.get_relationship_portfolio_analysis(
        db=db,
        current_user=Mock(),
    )

    assert result["total_customers"] == 2
    assert [item["customer_name"] for item in result["key_accounts"]] == ["真实客户A", "真实客户B"]
    assert "宁德时代" not in str(result)
    assert "比亚迪" not in str(result)


def test_sales_ai_relationship_page_does_not_embed_demo_accounts():
    source = Path("frontend/src/pages/SalesAI/RelationshipMaturity.jsx").read_text()

    assert "relationshipMaturityApi" in source
    assert "宁德时代" not in source
    assert "比亚迪" not in source
    assert "useState({" not in source
