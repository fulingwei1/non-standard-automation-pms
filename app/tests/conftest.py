# -*- coding: utf-8 -*-
"""
测试配置文件
提供共享的fixtures和测试配置
"""
import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session


@pytest.fixture
def mock_db_session():
    """提供通用的模拟数据库会话"""
    db = Mock(spec=Session)
    db.query = Mock(return_value=Mock())
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    db.rollback = Mock()
    db.close = Mock()
    return db


@pytest.fixture
def mock_current_user():
    """提供模拟当前用户"""
    from app.models.user import User
    user = Mock(spec=User)
    user.id = 1
    user.username = "test_user"
    user.email = "test@example.com"
    user.is_active = True
    return user
