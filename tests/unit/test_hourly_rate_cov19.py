# -*- coding: utf-8 -*-
"""
第十九批 - 时薪配置服务单元测试
"""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.hourly_rate_service")


def _make_config(hourly_rate=Decimal("150")):
    cfg = MagicMock()
    cfg.hourly_rate = hourly_rate
    return cfg


def _make_db_with_side_effect(user_return, user_config_return=None, role_return=None,
                               dept_config_return=None, default_config_return=None):
    """构建按查询模型区分返回值的 db mock"""
    from app.models.user import User
    from app.models.hourly_rate import HourlyRateConfig
    from app.models.user import UserRole
    from app.models.organization import Department

    db = MagicMock()

    user_q = MagicMock()
    user_q.filter.return_value.first.return_value = user_return

    config_q = MagicMock()
    config_q.filter.return_value.order_by.return_value.first.return_value = user_config_return

    role_q = MagicMock()
    role_q.filter.return_value.all.return_value = role_return or []

    dept_q = MagicMock()
    dept_q.filter.return_value.first.return_value = None

    def query_side_effect(model):
        if model is User:
            return user_q
        if model is UserRole:
            return role_q
        if model is Department:
            return dept_q
        return config_q  # HourlyRateConfig

    db.query.side_effect = query_side_effect
    return db


def test_get_user_hourly_rate_user_not_found():
    """用户不存在时返回默认时薪"""
    from app.services.hourly_rate_service import HourlyRateService
    db = _make_db_with_side_effect(user_return=None)
    rate = HourlyRateService.get_user_hourly_rate(db, user_id=999)
    assert rate == HourlyRateService.DEFAULT_HOURLY_RATE


def test_get_user_hourly_rate_user_config():
    """用户有个人配置时返回用户配置时薪"""
    from app.services.hourly_rate_service import HourlyRateService
    user = MagicMock()
    user.department = None
    user_config = _make_config(Decimal("200"))
    db = _make_db_with_side_effect(user_return=user, user_config_return=user_config)
    rate = HourlyRateService.get_user_hourly_rate(db, user_id=1)
    assert rate == Decimal("200")


def test_get_user_hourly_rate_fallback_to_default_constant():
    """无任何配置时使用硬编码默认值 100"""
    from app.services.hourly_rate_service import HourlyRateService
    user = MagicMock()
    user.department = None
    db = _make_db_with_side_effect(user_return=user, user_config_return=None)
    rate = HourlyRateService.get_user_hourly_rate(db, user_id=2)
    # 没有角色配置、部门配置、默认配置时，返回 DEFAULT_HOURLY_RATE
    assert rate == HourlyRateService.DEFAULT_HOURLY_RATE


def test_default_hourly_rate_value():
    """默认时薪常量为 100"""
    from app.services.hourly_rate_service import HourlyRateService
    assert HourlyRateService.DEFAULT_HOURLY_RATE == Decimal("100")


def test_get_users_hourly_rates_multiple():
    """批量获取多用户时薪"""
    from app.services.hourly_rate_service import HourlyRateService
    db = MagicMock()
    with patch.object(HourlyRateService, 'get_user_hourly_rate') as mock_get:
        mock_get.side_effect = [Decimal("100"), Decimal("150"), Decimal("200")]
        result = HourlyRateService.get_users_hourly_rates(db, [1, 2, 3])
    assert result == {1: Decimal("100"), 2: Decimal("150"), 3: Decimal("200")}


def test_get_users_hourly_rates_empty():
    """空列表时返回空字典"""
    from app.services.hourly_rate_service import HourlyRateService
    db = MagicMock()
    result = HourlyRateService.get_users_hourly_rates(db, [])
    assert result == {}


def test_get_hourly_rate_history_no_filters():
    """无过滤条件时查询所有记录"""
    from app.services.hourly_rate_service import HourlyRateService

    cfg = MagicMock()
    cfg.id = 1
    cfg.config_type = "USER"
    cfg.user_id = 1
    cfg.role_id = None
    cfg.dept_id = None
    cfg.hourly_rate = Decimal("150")
    cfg.effective_date = date(2024, 1, 1)
    cfg.expiry_date = None
    cfg.is_active = True
    cfg.remark = "测试"
    cfg.created_at = date(2024, 1, 1)
    cfg.updated_at = date(2024, 1, 1)

    db = MagicMock()
    db.query.return_value.order_by.return_value.all.return_value = [cfg]

    result = HourlyRateService.get_hourly_rate_history(db)
    assert len(result) == 1
    assert result[0]['config_type'] == 'USER'
    assert result[0]['hourly_rate'] == Decimal("150")


def test_get_hourly_rate_history_with_user_filter():
    """按用户 ID 过滤查询"""
    from app.services.hourly_rate_service import HourlyRateService

    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    result = HourlyRateService.get_hourly_rate_history(db, user_id=1)
    assert result == []
