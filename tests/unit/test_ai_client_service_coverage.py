# -*- coding: utf-8 -*-
"""ai_client_service单元测试"""

from app.services.ai_client_service import AIClientService


class TestAIClientServiceInit:
    def test_init_no_args(self):
        service = AIClientService()
        assert service is not None
        assert hasattr(service, "generate_solution")
