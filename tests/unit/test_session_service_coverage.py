# -*- coding: utf-8 -*-
"""session_service单元测试"""
import pytest
from app.services.session_service import SessionService

class TestSessionServiceInit:
    def test_init_without_db(self):
        """测试无参数初始化"""
        service = SessionService()
        assert service is not None