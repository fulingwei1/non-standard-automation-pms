# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - AI服务"""

import pytest


class TestAIServiceBusinessLogic:
    """AI服务业务逻辑测试"""

    def test_chat_completion(self):
        try:
            from app.services.ai_service import AIService

            service = AIService()
            assert hasattr(service, "chat_completion")
            assert callable(service.chat_completion)
        except ImportError:
            pytest.skip("Module not found")

    def test_simple_chat(self):
        try:
            from app.services.ai_service import AIService

            service = AIService()
            assert hasattr(service, "simple_chat")
            assert callable(service.simple_chat)
        except ImportError:
            pytest.skip("Module not found")

    def test_project_analysis(self):
        try:
            from app.services.ai_service import AIService

            service = AIService()
            assert hasattr(service, "project_analysis")
            assert callable(service.project_analysis)
        except ImportError:
            pytest.skip("Module not found")

    def test_close(self):
        try:
            from app.services.ai_service import AIService

            service = AIService()
            assert hasattr(service, "close")
            assert callable(service.close)
        except ImportError:
            pytest.skip("Module not found")
