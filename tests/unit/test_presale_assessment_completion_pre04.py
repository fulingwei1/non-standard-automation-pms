# -*- coding: utf-8 -*-
"""PRE-04: auto-created presale assessments must be marked as placeholders."""

from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.enums import AssessmentSourceTypeEnum
from app.models.sales import TechnicalAssessment
from app.services.presale_assessment_completion import complete_presale_source_assessment


def test_auto_created_assessment_is_marked_auto_generated():
    engine = create_engine("sqlite:///:memory:")
    TechnicalAssessment.__table__.create(bind=engine)
    db = sessionmaker(bind=engine)()

    assessment = complete_presale_source_assessment(
        db=db,
        source_type=AssessmentSourceTypeEnum.OPPORTUNITY.value,
        source_id=42,
        current_user=SimpleNamespace(id=7),
    )

    assert assessment.status == "COMPLETED"
    assert assessment.decision == "推荐立项"
    assert assessment.auto_generated is True
