# -*- coding: utf-8 -*-
"""status_update_service单元测试"""
from app.services.status_update_service import StatusUpdateResult


class TestStatusUpdateResultInit:
    def test_init_with_db(self):
        result = StatusUpdateResult(success=True, entity=None, old_status="A", new_status="B")
        assert result.success is True
