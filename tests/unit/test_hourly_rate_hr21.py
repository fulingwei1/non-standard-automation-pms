# -*- coding: utf-8 -*-
"""HR-21: hourly-rate fallback visibility and versioned changes."""

import logging
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.api.v1.endpoints.hourly_rate import query as hourly_rate_query
from app.api.v1.endpoints.hourly_rate.crud import (
    delete_hourly_rate_config,
    update_hourly_rate_config,
)
from app.models.hourly_rate import HourlyRateConfig
from app.models.user import User
from app.schemas.hourly_rate import HourlyRateConfigUpdate
from app.services.hourly_rate_service import HourlyRateService


def _make_user(db: Session, suffix: str) -> User:
    user = User(
        username=f"hr21_{suffix}_{uuid4().hex[:8]}",
        password_hash="test",
        is_active=True,
        real_name=f"HR21 {suffix}",
    )
    db.add(user)
    db.flush()
    return user


def _clear_hourly_rate_configs(db: Session) -> None:
    db.query(HourlyRateConfig).delete()
    db.commit()


def test_all_level_miss_logs_warning_and_api_marks_fallback(
    db_session: Session, caplog
):
    _clear_hourly_rate_configs(db_session)
    user = _make_user(db_session, "fallback")
    db_session.commit()

    with caplog.at_level(logging.WARNING, logger="app.services.hourly_rate_service"):
        rate = HourlyRateService.get_user_hourly_rate(
            db_session, user.id, date(2026, 1, 15)
        )

    assert rate == Decimal("100")
    assert any("全级未命中" in record.message for record in caplog.records)

    response = hourly_rate_query.get_user_hourly_rate(
        db=db_session,
        user_id=user.id,
        work_date="2026-01-15",
        current_user=user,
    )

    assert response.data["source"] == "系统兜底"
    assert response.data.get("is_fallback") is True
    assert response.data.get("config_id") is None


def test_update_creates_new_version_and_preserves_old_rate_for_old_work_date(
    db_session: Session,
):
    _clear_hourly_rate_configs(db_session)
    user = _make_user(db_session, "version")
    original = HourlyRateConfig(
        config_type="USER",
        user_id=user.id,
        hourly_rate=Decimal("100.00"),
        effective_date=date(2026, 1, 1),
        is_active=True,
    )
    db_session.add(original)
    db_session.commit()
    original_id = original.id

    response = update_hourly_rate_config(
        db=db_session,
        config_id=original_id,
        config_in=HourlyRateConfigUpdate(
            hourly_rate=Decimal("150.00"),
            effective_date=date(2026, 2, 1),
            remark="2026-02 rate adjustment",
        ),
        current_user=user,
    )

    old_version = db_session.get(HourlyRateConfig, original_id)
    new_version = db_session.get(HourlyRateConfig, response.id)

    assert response.id != original_id
    assert old_version.hourly_rate == Decimal("100.00")
    assert old_version.expiry_date == date(2026, 1, 31)
    assert old_version.is_active is True
    assert new_version.hourly_rate == Decimal("150.00")
    assert new_version.user_id == user.id
    assert new_version.is_active is True

    assert (
        HourlyRateService.get_user_hourly_rate(db_session, user.id, date(2026, 1, 15))
        == Decimal("100.00")
    )
    assert (
        HourlyRateService.get_user_hourly_rate(db_session, user.id, date(2026, 2, 15))
        == Decimal("150.00")
    )


def test_delete_soft_expires_config_and_keeps_historical_lookup(db_session: Session):
    _clear_hourly_rate_configs(db_session)
    user = _make_user(db_session, "delete")
    config = HourlyRateConfig(
        config_type="USER",
        user_id=user.id,
        hourly_rate=Decimal("120.00"),
        effective_date=date(2026, 1, 1),
        is_active=True,
    )
    db_session.add(config)
    db_session.commit()
    config_id = config.id

    delete_hourly_rate_config(db=db_session, config_id=config_id, current_user=user)

    stopped = db_session.get(HourlyRateConfig, config_id)
    assert stopped is not None
    assert stopped.is_active is False
    assert stopped.expiry_date is not None
    assert stopped.remark and "已停用" in stopped.remark

    historical_date = max(stopped.effective_date, stopped.expiry_date - timedelta(days=1))
    assert (
        HourlyRateService.get_user_hourly_rate(db_session, user.id, historical_date)
        == Decimal("120.00")
    )
    assert (
        HourlyRateService.get_user_hourly_rate(db_session, user.id, date.today())
        == HourlyRateService.DEFAULT_HOURLY_RATE
    )
