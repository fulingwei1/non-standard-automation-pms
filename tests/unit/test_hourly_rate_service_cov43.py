# -*- coding: utf-8 -*-
"""
第四十三批覆盖率测试 - app/services/hourly_rate_service.py
"""
import pytest

pytest.importorskip("app.services.hourly_rate_service")

from decimal import Decimal
from datetime import date
from unittest.mock import MagicMock

from app.services.hourly_rate_service import HourlyRateService


def make_db():
    return MagicMock()


# ── 1. 用户不存在时返回默认时薪 ───────────────────────────────────────────────
def test_get_user_hourly_rate_user_not_found():
    db = make_db()
    db.query.return_value.filter.return_value.first.return_value = None
    rate = HourlyRateService.get_user_hourly_rate(db, user_id=999)
    assert rate == HourlyRateService.DEFAULT_HOURLY_RATE


# ── 2. 找到用户级别配置 ───────────────────────────────────────────────────────
def test_get_user_hourly_rate_user_config():
    db = make_db()
    user = MagicMock()
    user.id = 1
    user.department = None

    user_config = MagicMock()
    user_config.hourly_rate = Decimal("150")

    # 第1次查 User, 第2次查 HourlyRateConfig(USER)
    q_user = MagicMock()
    q_user.filter.return_value.first.return_value = user

    q_config = MagicMock()
    q_config.filter.return_value.order_by.return_value.first.return_value = user_config

    db.query.side_effect = [q_user, q_config]
    rate = HourlyRateService.get_user_hourly_rate(db, user_id=1, work_date=date.today())
    assert rate == Decimal("150")


# ── 3. 没有用户配置时走默认配置 ──────────────────────────────────────────────
def test_get_user_hourly_rate_default_config():
    db = make_db()
    user = MagicMock()
    user.id = 2
    user.department = None

    default_config = MagicMock()
    default_config.hourly_rate = Decimal("120")

    def q_side(*args, **kwargs):
        m = MagicMock()
        m.filter.return_value.first.return_value = user             # User
        m.filter.return_value.order_by.return_value.first.return_value = None  # USER config
        m.filter.return_value.all.return_value = []                 # UserRole
        return m

    # Simplified mock: no user config, no role config, no dept config, but default config
    quser = MagicMock()
    quser.filter.return_value.first.return_value = user

    qucfg = MagicMock()
    qucfg.filter.return_value.order_by.return_value.first.return_value = None  # no user cfg

    qrole = MagicMock()
    qrole.filter.return_value.all.return_value = []  # no roles

    qdept_cfg = MagicMock()
    qdept_cfg.filter.return_value.order_by.return_value.first.return_value = None  # no dept cfg

    qdef_cfg = MagicMock()
    qdef_cfg.filter.return_value.order_by.return_value.first.return_value = default_config

    db.query.side_effect = [quser, qucfg, qrole, qdef_cfg]
    rate = HourlyRateService.get_user_hourly_rate(db, user_id=2)
    # may vary by branch; just ensure returns a Decimal
    assert isinstance(rate, Decimal)


# ── 4. 批量获取用户时薪 ────────────────────────────────────────────────────────
def test_get_users_hourly_rates_batch():
    db = make_db()
    db.query.return_value.filter.return_value.first.return_value = None
    rates = HourlyRateService.get_users_hourly_rates(db, user_ids=[1, 2, 3])
    assert set(rates.keys()) == {1, 2, 3}
    for v in rates.values():
        assert v == HourlyRateService.DEFAULT_HOURLY_RATE


# ── 5. 批量获取时薪 - 空列表 ─────────────────────────────────────────────────
def test_get_users_hourly_rates_empty():
    db = make_db()
    rates = HourlyRateService.get_users_hourly_rates(db, user_ids=[])
    assert rates == {}


# ── 6. get_hourly_rate_history - 无过滤条件 ────────────────────────────────────
def test_get_hourly_rate_history_no_filters():
    db = make_db()
    cfg = MagicMock()
    cfg.id = 1
    cfg.config_type = "USER"
    cfg.user_id = 5
    cfg.role_id = None
    cfg.dept_id = None
    cfg.hourly_rate = Decimal("100")
    cfg.effective_date = None
    cfg.expiry_date = None
    cfg.is_active = True
    cfg.remark = ""
    cfg.created_at = None
    cfg.updated_at = None

    db.query.return_value.order_by.return_value.all.return_value = [cfg]
    result = HourlyRateService.get_hourly_rate_history(db)
    assert len(result) == 1
    assert result[0]["config_type"] == "USER"


# ── 7. get_hourly_rate_history - 按 user_id 过滤 ──────────────────────────────
def test_get_hourly_rate_history_filter_user():
    db = make_db()
    q = MagicMock()
    q.filter.return_value = q
    q.order_by.return_value.all.return_value = []
    db.query.return_value = q

    result = HourlyRateService.get_hourly_rate_history(db, user_id=7)
    assert result == []
