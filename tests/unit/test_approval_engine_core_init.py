# -*- coding: utf-8 -*-
"""
审批引擎核心类单元测试

测试 ApprovalEngineCore 初始化
"""

import pytest
from unittest.mock import MagicMock

from app.services.approval_engine.engine.core import ApprovalEngineCore


@pytest.mark.unit
class TestApprovalEngineCoreInit:
    """测试 ApprovalEngineCore 类"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        mock_db = MagicMock()
        core = ApprovalEngineCore(db=mock_db)
        assert core.db == mock_db

    def test_db_attribute_exists(self):
        """测试 db 属性存在"""
        mock_db = MagicMock()
        core = ApprovalEngineCore(db=mock_db)
        assert hasattr(core, "db")
        assert core.db is not None

    def test_core_class_exists(self):
        """测试核心类存在"""
        assert ApprovalEngineCore is not None
