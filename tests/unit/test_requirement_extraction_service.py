from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

from sqlalchemy.exc import OperationalError

from app.services.requirement_extraction_service import RequirementExtractionService


def test_estimate_production_hours_accepts_decimal_contract_amount():
    service = RequirementExtractionService(db=None)
    project = SimpleNamespace(contract_amount=Decimal("680000.00"), industry="汽车")

    estimated = service._estimate_production_hours(project)

    assert estimated == 88.4


def test_recommend_engineers_falls_back_when_engineer_capacity_table_missing():
    user = SimpleNamespace(id=101, real_name="张工", username="zhang", department="工程部")

    first_query = MagicMock()
    first_query.outerjoin.return_value.filter.return_value.all.side_effect = OperationalError(
        "select * from engineer_capacity", {}, Exception("no such table: engineer_capacity")
    )

    second_query = MagicMock()
    second_query.filter.return_value.all.return_value = [user]

    db = MagicMock()
    db.query.side_effect = [first_query, second_query]

    service = RequirementExtractionService(db=db)
    requirement = {
        "required_skills": ["电气装配", "PCB测试", "探针调试"],
        "min_multi_project_capacity": 0,
        "min_standardization_score": 0,
        "min_ai_skill_level": "NONE",
    }

    recommendations = service.recommend_engineers(requirement, limit=3)

    assert len(recommendations) == 1
    assert recommendations[0]["engineer_id"] == 101
    assert recommendations[0]["engineer_name"] == "张工"
    assert recommendations[0]["overall_match_score"] >= 60
