# -*- coding: utf-8 -*-
"""
approval_workflow/core.py 单元测试

测试审批工作流服务核心类
"""

import pytest
from unittest.mock import MagicMock
from app.services.approval_workflow.core import ApprovalWorkflowCore


@pytest.mark.unit
class TestApprovalWorkflowCore:
    """测试 ApprovalWorkflowCore 类"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        mock_db = MagicMock()

        core = ApprovalWorkflowCore(db=mock_db)

        assert core.db == mock_db

    def test_db_attribute_exists(self):
        """测试 db 属性存在"""
        mock_db = MagicMock()

        core = ApprovalWorkflowCore(db=mock_db)

        assert hasattr(core, "db")
        assert core.db is not None
