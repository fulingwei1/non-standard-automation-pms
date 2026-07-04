# -*- coding: utf-8 -*-
"""HR-09: holiday DB records must be consumed by work-log rules."""

from datetime import date

from sqlalchemy.orm import Session

from app.models.holiday import Holiday
from app.services.work_log_ai.rule_engine import RuleEngineMixin


class RuleEngineWithDb(RuleEngineMixin):
    def __init__(self, db: Session):
        self.db = db


def test_rule_engine_uses_db_holiday_before_static_calendar(db_session: Session):
    db_session.query(Holiday).filter(Holiday.holiday_date == date(2031, 7, 4)).delete()
    db_session.add(
        Holiday(
            holiday_date=date(2031, 7, 4),
            year=2031,
            holiday_type="HOLIDAY",
            name="公司年度休假",
            is_active=True,
        )
    )
    db_session.commit()

    engine = RuleEngineWithDb(db_session)
    result = engine._analyze_with_rules(
        "年度休假期间远程支持客户，4小时",
        [{"id": 1, "code": "PJ", "name": "客户支持", "keywords": ["客户"]}],
        date(2031, 7, 4),
    )

    assert result["work_items"][0]["work_type"] == "HOLIDAY"
