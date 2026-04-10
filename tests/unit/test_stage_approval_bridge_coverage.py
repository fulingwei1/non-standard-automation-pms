# -*- coding: utf-8 -*-
"""stage_approval_bridge单元测试"""
import pytest
from unittest.mock import Mock
from app.services.stage_approval_bridge import StageApprovalBridge

class TestStageApprovalBridgeInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = StageApprovalBridge(mock_db)
        assert hasattr(service, 'db')
