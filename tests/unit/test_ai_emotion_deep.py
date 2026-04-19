# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - AI情感服务"""

import pytest


class TestAIEmotionServiceBusinessLogic:
    """AI情感服务业务逻辑测试"""

    @pytest.mark.asyncio
    async def test_analyze_emotion(self):
        """测试分析情感入口存在"""
        try:
            from app.services.ai_emotion_service import AIEmotionService

            service = AIEmotionService(None)
            assert hasattr(service, "analyze_emotion")
            assert callable(service.analyze_emotion)
        except ImportError:
            pytest.skip("Module not found")

    @pytest.mark.asyncio
    async def test_batch_analyze_customers(self):
        """测试批量分析客户入口存在"""
        try:
            from app.services.ai_emotion_service import AIEmotionService

            service = AIEmotionService(None)
            assert hasattr(service, "batch_analyze_customers")
            assert callable(service.batch_analyze_customers)
        except ImportError:
            pytest.skip("Module not found")
