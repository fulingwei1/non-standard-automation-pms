# -*- coding: utf-8 -*-
"""ai_service单元测试"""

from app.services.ai_service import AIService


class TestAIServiceInit:
    def test_init_no_args(self):
        service = AIService()
        assert service is not None
        assert hasattr(service, "chat_completion")
