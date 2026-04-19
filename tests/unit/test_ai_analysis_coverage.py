# -*- coding: utf-8 -*-
"""ai_analysis单元测试"""

from app.services.work_log_ai.ai_analysis import AIAnalysisMixin


class TestAIAnalysisMixinInit:
    def test_methods_available(self):
        assert AIAnalysisMixin is not None
        assert hasattr(AIAnalysisMixin, "_analyze_with_ai_sync")
        assert hasattr(AIAnalysisMixin, "_analyze_with_ai")
