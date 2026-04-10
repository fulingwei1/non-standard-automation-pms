# -*- coding: utf-8 -*-
"""acceptance单元测试"""
from unittest.mock import Mock

from app.services.bonus.acceptance import AcceptanceBonusTrigger


class TestAcceptanceBonusTriggerInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = AcceptanceBonusTrigger(mock_db)
        assert hasattr(service, "db")
