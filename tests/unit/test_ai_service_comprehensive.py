# -*- coding: utf-8 -*-
"""
AIService 综合单元测试

测试覆盖:
- __init__: 初始化服务
- chat_completion: 聊天完成
- simple_chat: 简单聊天
- project_analysis: 项目分析
- close: 关闭客户端
- get_ai_service: 获取服务实例
- analyze_project_with_ai: 便捷分析函数
- chat_with_ai: 便捷聊天函数
"""

from unittest.mock import MagicMock, patch, AsyncMock
import json

import pytest


class TestAIServiceInit:
    """测试 AIService 初始化"""

    def test_initializes_with_settings(self):
        """测试使用配置初始化"""
        mock_settings = MagicMock()
        mock_settings.KIMI_API_KEY = "test-key"
        mock_settings.KIMI_API_BASE = "https://api.kimi.ai"
        mock_settings.KIMI_MODEL = "kimi-chat"
        mock_settings.KIMI_MAX_TOKENS = 4096
        mock_settings.KIMI_TEMPERATURE = 0.7
        mock_settings.KIMI_TIMEOUT = 30
        mock_settings.KIMI_ENABLED = True

        with patch('app.services.ai_service.settings', mock_settings):
            with patch('app.services.ai_service.httpx.AsyncClient') as mock_client:
                from app.services.ai_service import AIService

                # 需要重新创建实例
                service = AIService()

                assert service.api_key == "test-key"
                assert service.model == "kimi-chat"
                assert service.enabled is True

    def test_disabled_when_no_api_key(self):
        """测试没有 API Key 时禁用"""
        mock_settings = MagicMock()
        mock_settings.KIMI_API_KEY = None
        mock_settings.KIMI_ENABLED = True

        with patch('app.services.ai_service.settings', mock_settings):
            from app.services.ai_service import AIService

            service = AIService()

            assert service.enabled is False
            assert service.client is None

    def test_disabled_when_kimi_disabled(self):
        """测试 KIMI_ENABLED=False 时禁用"""
        mock_settings = MagicMock()
        mock_settings.KIMI_API_KEY = "test-key"
        mock_settings.KIMI_ENABLED = False

        with patch('app.services.ai_service.settings', mock_settings):
            from app.services.ai_service import AIService

            service = AIService()

            assert service.enabled is False


class TestChatCompletion:
    """测试 chat_completion 方法"""

    @pytest.mark.asyncio
    async def test_raises_when_disabled(self):
        """测试服务禁用时抛出异常"""
        from app.services.ai_service import AIService
        from fastapi import HTTPException

        mock_settings = MagicMock()
        mock_settings.KIMI_API_KEY = None
        mock_settings.KIMI_ENABLED = False

        with patch('app.services.ai_service.settings', mock_settings):
            service = AIService()

            with pytest.raises(HTTPException) as exc_info:
                await service.chat_completion([{"role": "user", "content": "test"}])

            assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_raises_when_client_not_initialized(self):
        """测试客户端未初始化时抛出异常"""
        from app.services.ai_service import AIService
        from fastapi import HTTPException

        mock_settings = MagicMock()
        mock_settings.KIMI_API_KEY = "key"
        mock_settings.KIMI_ENABLED = True

        with patch('app.services.ai_service.settings', mock_settings):
            service = AIService()
            service.enabled = True
            service.client = None

            with pytest.raises(HTTPException) as exc_info:
                await service.chat_completion([{"role": "user", "content": "test"}])

            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_successful_chat_completion(self):
        """测试成功的聊天完成"""
        from app.services.ai_service import AIService

        mock_settings = MagicMock()
        mock_settings.KIMI_API_KEY = "key"
        mock_settings.KIMI_API_BASE = "https://api.kimi.ai"
        mock_settings.KIMI_MODEL = "kimi-chat"
        mock_settings.KIMI_MAX_TOKENS = 4096
        mock_settings.KIMI_TEMPERATURE = 0.7
        mock_settings.KIMI_TIMEOUT = 30
        mock_settings.KIMI_ENABLED = True

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello!"}}]
        }

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch('app.services.ai_service.settings', mock_settings):
            with patch('app.services.ai_service.httpx.AsyncClient', return_value=mock_client):
                service = AIService()
                service.client = mock_client
                service.enabled = True

                result = await service.chat_completion(
                    [{"role": "user", "content": "Hi"}]
                )

                assert result["choices"][0]["message"]["content"] == "Hello!"

    @pytest.mark.asyncio
    async def test_handles_api_error(self):
        """测试处理 API 错误"""
        from app.services.ai_service import AIService
        from fastapi import HTTPException

        mock_settings = MagicMock()
        mock_settings.KIMI_API_KEY = "key"
        mock_settings.KIMI_API_BASE = "https://api.kimi.ai"
        mock_settings.KIMI_MODEL = "kimi-chat"
        mock_settings.KIMI_MAX_TOKENS = 4096
        mock_settings.KIMI_TEMPERATURE = 0.7
        mock_settings.KIMI_TIMEOUT = 30
        mock_settings.KIMI_ENABLED = True

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.content = b'{"error": {"message": "Bad request"}}'
        mock_response.json.return_value = {"error": {"message": "Bad request"}}

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch('app.services.ai_service.settings', mock_settings):
            with patch('app.services.ai_service.httpx.AsyncClient', return_value=mock_client):
                service = AIService()
                service.client = mock_client
                service.enabled = True

                with pytest.raises(HTTPException) as exc_info:
                    await service.chat_completion([{"role": "user", "content": "Hi"}])

                assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_handles_timeout(self):
        """测试处理超时"""
        from app.services.ai_service import AIService
        from fastapi import HTTPException
        import httpx

        mock_settings = MagicMock()
        mock_settings.KIMI_API_KEY = "key"
        mock_settings.KIMI_API_BASE = "https://api.kimi.ai"
        mock_settings.KIMI_MODEL = "kimi-chat"
        mock_settings.KIMI_MAX_TOKENS = 4096
        mock_settings.KIMI_TEMPERATURE = 0.7
        mock_settings.KIMI_TIMEOUT = 30
        mock_settings.KIMI_ENABLED = True

        mock_client = MagicMock()
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

        with patch('app.services.ai_service.settings', mock_settings):
            with patch('app.services.ai_service.httpx.AsyncClient', return_value=mock_client):
                service = AIService()
                service.client = mock_client
                service.enabled = True

                with pytest.raises(HTTPException) as exc_info:
                    await service.chat_completion([{"role": "user", "content": "Hi"}])

                assert exc_info.value.status_code == 504


class TestSimpleChat:
    """测试 simple_chat 方法"""

    @pytest.mark.asyncio
    async def test_returns_content(self):
        """测试返回内容"""
        from app.services.ai_service import AIService

        mock_settings = MagicMock()
        mock_settings.KIMI_API_KEY = "key"
        mock_settings.KIMI_ENABLED = True
        mock_settings.KIMI_API_BASE = "https://api.kimi.ai"
        mock_settings.KIMI_MODEL = "kimi-chat"
        mock_settings.KIMI_MAX_TOKENS = 4096
        mock_settings.KIMI_TEMPERATURE = 0.7
        mock_settings.KIMI_TIMEOUT = 30

        with patch('app.services.ai_service.settings', mock_settings):
            service = AIService()
            service.enabled = True

            with patch.object(service, 'chat_completion', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = {
                    "choices": [{"message": {"content": "测试响应"}}]
                }

                result = await service.simple_chat("测试问题")

                assert result == "测试响应"

    @pytest.mark.asyncio
    async def test_includes_context(self):
        """测试包含上下文"""
        from app.services.ai_service import AIService

        mock_settings = MagicMock()
        mock_settings.KIMI_API_KEY = "key"
        mock_settings.KIMI_ENABLED = True
        mock_settings.KIMI_API_BASE = "https://api.kimi.ai"
        mock_settings.KIMI_MODEL = "kimi-chat"
        mock_settings.KIMI_MAX_TOKENS = 4096
        mock_settings.KIMI_TEMPERATURE = 0.7
        mock_settings.KIMI_TIMEOUT = 30

        with patch('app.services.ai_service.settings', mock_settings):
            service = AIService()
            service.enabled = True

            with patch.object(service, 'chat_completion', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = {
                    "choices": [{"message": {"content": "响应"}}]
                }

                await service.simple_chat("问题", context="你是专家")

                call_args = mock_chat.call_args[0][0]
                assert len(call_args) == 2
                assert call_args[0]["role"] == "system"
                assert call_args[0]["content"] == "你是专家"

    @pytest.mark.asyncio
    async def test_handles_parse_error(self):
        """测试处理解析错误"""
        from app.services.ai_service import AIService
        from fastapi import HTTPException

        mock_settings = MagicMock()
        mock_settings.KIMI_API_KEY = "key"
        mock_settings.KIMI_ENABLED = True
        mock_settings.KIMI_API_BASE = "https://api.kimi.ai"
        mock_settings.KIMI_MODEL = "kimi-chat"
        mock_settings.KIMI_MAX_TOKENS = 4096
        mock_settings.KIMI_TEMPERATURE = 0.7
        mock_settings.KIMI_TIMEOUT = 30

        with patch('app.services.ai_service.settings', mock_settings):
            service = AIService()
            service.enabled = True

            with patch.object(service, 'chat_completion', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = {"choices": []}  # 空的 choices

                with pytest.raises(HTTPException) as exc_info:
                    await service.simple_chat("问题")

                assert exc_info.value.status_code == 500


class TestProjectAnalysis:
    """测试 project_analysis 方法"""

    @pytest.mark.asyncio
    async def test_returns_parsed_json(self):
        """测试返回解析的 JSON"""
        from app.services.ai_service import AIService

        mock_settings = MagicMock()
        mock_settings.KIMI_API_KEY = "key"
        mock_settings.KIMI_ENABLED = True
        mock_settings.KIMI_API_BASE = "https://api.kimi.ai"
        mock_settings.KIMI_MODEL = "kimi-chat"
        mock_settings.KIMI_MAX_TOKENS = 4096
        mock_settings.KIMI_TEMPERATURE = 0.7
        mock_settings.KIMI_TIMEOUT = 30

        analysis_result = {
            "risk_level": "中",
            "main_risks": ["风险1"],
            "overall_summary": "总结"
        }

        with patch('app.services.ai_service.settings', mock_settings):
            service = AIService()
            service.enabled = True

            with patch.object(service, 'simple_chat', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = json.dumps(analysis_result)

                result = await service.project_analysis({"name": "测试项目"})

                assert result["risk_level"] == "中"
                assert result["main_risks"] == ["风险1"]

    @pytest.mark.asyncio
    async def test_returns_raw_text_on_json_error(self):
        """测试 JSON 解析失败时返回原始文本"""
        from app.services.ai_service import AIService

        mock_settings = MagicMock()
        mock_settings.KIMI_API_KEY = "key"
        mock_settings.KIMI_ENABLED = True
        mock_settings.KIMI_API_BASE = "https://api.kimi.ai"
        mock_settings.KIMI_MODEL = "kimi-chat"
        mock_settings.KIMI_MAX_TOKENS = 4096
        mock_settings.KIMI_TEMPERATURE = 0.7
        mock_settings.KIMI_TIMEOUT = 30

        with patch('app.services.ai_service.settings', mock_settings):
            service = AIService()
            service.enabled = True

            with patch.object(service, 'simple_chat', new_callable=AsyncMock) as mock_chat:
                mock_chat.return_value = "这不是有效的JSON"

                result = await service.project_analysis({"name": "测试项目"})

                assert "raw_analysis" in result
                assert result["raw_analysis"] == "这不是有效的JSON"


class TestClose:
    """测试 close 方法"""

    @pytest.mark.asyncio
    async def test_closes_client(self):
        """测试关闭客户端"""
        from app.services.ai_service import AIService

        mock_settings = MagicMock()
        mock_settings.KIMI_API_KEY = "key"
        mock_settings.KIMI_ENABLED = True
        mock_settings.KIMI_API_BASE = "https://api.kimi.ai"
        mock_settings.KIMI_MODEL = "kimi-chat"
        mock_settings.KIMI_MAX_TOKENS = 4096
        mock_settings.KIMI_TEMPERATURE = 0.7
        mock_settings.KIMI_TIMEOUT = 30

        mock_client = MagicMock()
        mock_client.aclose = AsyncMock()

        with patch('app.services.ai_service.settings', mock_settings):
            service = AIService()
            service.client = mock_client

            await service.close()

            mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_no_client(self):
        """测试没有客户端时不报错"""
        from app.services.ai_service import AIService

        mock_settings = MagicMock()
        mock_settings.KIMI_API_KEY = None
        mock_settings.KIMI_ENABLED = False

        with patch('app.services.ai_service.settings', mock_settings):
            service = AIService()

            # 应该不抛出异常
            await service.close()


class TestHelperFunctions:
    """测试辅助函数"""

    @pytest.mark.asyncio
    async def test_get_ai_service_returns_instance(self):
        """测试获取 AI 服务实例"""
        from app.services.ai_service import get_ai_service

        result = await get_ai_service()

        assert result is not None

    @pytest.mark.asyncio
    async def test_analyze_project_with_ai(self):
        """测试项目分析便捷函数"""
        from app.services.ai_service import analyze_project_with_ai

        with patch('app.services.ai_service.get_ai_service', new_callable=AsyncMock) as mock_get:
            mock_service = MagicMock()
            mock_service.project_analysis = AsyncMock(return_value={"result": "ok"})
            mock_get.return_value = mock_service

            result = await analyze_project_with_ai({"name": "test"})

            assert result == {"result": "ok"}

    @pytest.mark.asyncio
    async def test_chat_with_ai(self):
        """测试聊天便捷函数"""
        from app.services.ai_service import chat_with_ai

        with patch('app.services.ai_service.get_ai_service', new_callable=AsyncMock) as mock_get:
            mock_service = MagicMock()
            mock_service.simple_chat = AsyncMock(return_value="响应")
            mock_get.return_value = mock_service

            result = await chat_with_ai("问题", "上下文")

            assert result == "响应"
