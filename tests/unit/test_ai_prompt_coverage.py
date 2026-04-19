# -*- coding: utf-8 -*-
"""ai_prompt单元测试"""

from app.services.work_log_ai.ai_prompt import AIPromptMixin


class TestAIPromptMixinInit:
    def test_methods_available(self):
        assert AIPromptMixin is not None
        assert hasattr(AIPromptMixin, "_build_ai_prompt")
        assert hasattr(AIPromptMixin, "_parse_ai_response")
