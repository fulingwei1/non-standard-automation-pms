# -*- coding: utf-8 -*-
"""design_review_sync_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.design_review_sync_service import DesignReviewSyncService

class TestDesignReviewSyncServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = DesignReviewSyncService(mock_db)
        assert hasattr(service, 'db')
