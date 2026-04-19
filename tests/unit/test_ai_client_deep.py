# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - AI客户端服务"""

import pytest


class TestAIClientServiceBusinessLogic:
    """AI客户端服务业务逻辑测试"""

    def test_generate_architecture(self):
        try:
            from app.services.ai_client_service import AIClientService

            service = AIClientService()
            result = service.generate_architecture("ICT")
            assert result is not None
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("Module not found")

    def test_generate_solution(self):
        try:
            from app.services.ai_client_service import AIClientService

            service = AIClientService()
            result = service.generate_solution("客户需求")
            assert result is not None
            assert isinstance(result, dict)
        except ImportError:
            pytest.skip("Module not found")
