# -*- coding: utf-8 -*-
"""第十批：SolutionCreditService 单元测试"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.solution_credit_service import SolutionCreditService, CreditTransactionType
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="模块导入失败")


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return SolutionCreditService(db)


def _make_user(credits=100):
    u = MagicMock()
    u.id = 1
    u.solution_credits = credits
    return u


def test_service_init(db):
    """服务初始化"""
    svc = SolutionCreditService(db)
    assert svc.db is db


def test_credit_transaction_types():
    """验证积分交易类型常量"""
    assert CreditTransactionType.INIT == "INIT"
    assert CreditTransactionType.GENERATE == "GENERATE"
    assert CreditTransactionType.ADMIN_ADD == "ADMIN_ADD"
    assert CreditTransactionType.REFUND == "REFUND"


def test_get_user_balance_not_found(service, db):
    """用户不存在时返回0"""
    db.query.return_value.filter.return_value.first.return_value = None
    balance = service.get_user_balance(user_id=999)
    assert balance == 0


def test_get_user_balance_existing_user(service, db):
    """正常用户余额查询"""
    user = _make_user(credits=150)
    db.query.return_value.filter.return_value.first.return_value = user
    balance = service.get_user_balance(user_id=1)
    assert balance == 150


def test_get_config_default(service, db):
    """没有数据库配置时返回默认值"""
    db.query.return_value.filter.return_value.first.return_value = None
    val = service.get_config("INITIAL_CREDITS")
    assert val == SolutionCreditService.DEFAULT_CONFIG["INITIAL_CREDITS"]


def test_get_config_from_db(service, db):
    """从数据库获取配置"""
    config = MagicMock()
    config.config_value = "200"
    db.query.return_value.filter.return_value.first.return_value = config
    val = service.get_config("INITIAL_CREDITS")
    assert val == 200


def test_default_config_keys(service):
    """默认配置包含所有必要键"""
    keys = ["INITIAL_CREDITS", "GENERATE_COST", "MIN_CREDITS_TO_GENERATE", "MAX_CREDITS"]
    for k in keys:
        assert k in SolutionCreditService.DEFAULT_CONFIG


def test_get_config_unknown_key(service, db):
    """未知配置键返回0"""
    db.query.return_value.filter.return_value.first.return_value = None
    val = service.get_config("UNKNOWN_KEY")
    assert val == 0
