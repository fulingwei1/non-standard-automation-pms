# -*- coding: utf-8 -*-
"""
Tests for ai_service
Covers: app/services/ai_service.py
"""

import json
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from fastapi import HTTPException

import httpx


class TestAIServiceInit:
    """Test suite for AIService initialization."""

    def test_init_enabled_with_api_key(self):
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.KIMI_API_KEY = "test-api-key"
            mock_settings.KIMI_API_BASE = "https://api.test.com"
            mock_settings.KIMI_MODEL = "test-model"
            mock_settings.KIMI_MAX_TOKENS = 1000
            mock_settings.KIMI_TEMPERATURE = 0.7
            mock_settings.KIMI_TIMEOUT = 30
            mock_settings.KIMI_ENABLED = True

            from app.services.ai_service import AIService
            service = AIService()

            assert service.enabled is True
            assert service.api_key == "test-api-key"
            assert service.base_url == "https://api.test.com"
            assert service.model == "test-model"
            assert service.client is not None

    def test_init_disabled_when_kimi_disabled(self):
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.KIMI_API_KEY = "test-api-key"
            mock_settings.KIMI_API_BASE = "https://api.test.com"
            mock_settings.KIMI_MODEL = "test-model"
            mock_settings.KIMI_MAX_TOKENS = 1000
            mock_settings.KIMI_TEMPERATURE = 0.7
            mock_settings.KIMI_TIMEOUT = 30
            mock_settings.KIMI_ENABLED = False

            from app.services.ai_service import AIService
            service = AIService()

            assert service.enabled is False
            assert service.client is None

    def test_init_disabled_when_no_api_key(self):
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.KIMI_API_KEY = None
            mock_settings.KIMI_API_BASE = "https://api.test.com"
            mock_settings.KIMI_MODEL = "test-model"
            mock_settings.KIMI_MAX_TOKENS = 1000
            mock_settings.KIMI_TEMPERATURE = 0.7
            mock_settings.KIMI_TIMEOUT = 30
            mock_settings.KIMI_ENABLED = True

            from app.services.ai_service import AIService
            service = AIService()

            assert service.enabled is False
            assert service.client is None


class TestChatCompletion:
    """Test suite for chat_completion method."""

    @pytest.fixture
    def enabled_service(self):
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.KIMI_API_KEY = "test-api-key"
            mock_settings.KIMI_API_BASE = "https://api.test.com"
            mock_settings.KIMI_MODEL = "test-model"
            mock_settings.KIMI_MAX_TOKENS = 1000
            mock_settings.KIMI_TEMPERATURE = 0.7
            mock_settings.KIMI_TIMEOUT = 30
            mock_settings.KIMI_ENABLED = True

            from app.services.ai_service import AIService
            service = AIService()
            yield service

    @pytest.fixture
    def disabled_service(self):
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.KIMI_API_KEY = None
            mock_settings.KIMI_API_BASE = "https://api.test.com"
            mock_settings.KIMI_MODEL = "test-model"
            mock_settings.KIMI_MAX_TOKENS = 1000
            mock_settings.KIMI_TEMPERATURE = 0.7
            mock_settings.KIMI_TIMEOUT = 30
            mock_settings.KIMI_ENABLED = False

            from app.services.ai_service import AIService
            service = AIService()
            yield service

    @pytest.mark.asyncio
    async def test_chat_completion_disabled_service(self, disabled_service):
        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(HTTPException) as exc_info:
            await disabled_service.chat_completion(messages)

        assert exc_info.value.status_code == 503
        assert "未启用" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_chat_completion_no_client(self, enabled_service):
        enabled_service.client = None

        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(HTTPException) as exc_info:
            await enabled_service.chat_completion(messages)

        assert exc_info.value.status_code == 500
        assert "未初始化" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_chat_completion_success(self, enabled_service):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello!"}}]
        }

        enabled_service.client = AsyncMock()
        enabled_service.client.post = AsyncMock(return_value=mock_response)

        messages = [{"role": "user", "content": "Hi"}]
        result = await enabled_service.chat_completion(messages)

        assert result == {"choices": [{"message": {"content": "Hello!"}}]}
        enabled_service.client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_completion_with_custom_params(self, enabled_service):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}

        enabled_service.client = AsyncMock()
        enabled_service.client.post = AsyncMock(return_value=mock_response)

        messages = [{"role": "user", "content": "Test"}]
        await enabled_service.chat_completion(
            messages,
            model="custom-model",
            max_tokens=500,
            temperature=0.5,
            stream=True
        )

        call_args = enabled_service.client.post.call_args
        payload = call_args[1]["json"]
        assert payload["model"] == "custom-model"
        assert payload["max_tokens"] == 500
        assert payload["temperature"] == 0.5
        assert payload["stream"] is True

    @pytest.mark.asyncio
    async def test_chat_completion_api_error(self, enabled_service):
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.content = b'{"error": {"message": "Invalid request"}}'
        mock_response.json.return_value = {"error": {"message": "Invalid request"}}

        enabled_service.client = AsyncMock()
        enabled_service.client.post = AsyncMock(return_value=mock_response)

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(HTTPException) as exc_info:
            await enabled_service.chat_completion(messages)

        # The HTTPException raised for API errors is caught by the general
        # exception handler and re-raised with 500 status
        assert exc_info.value.status_code == 500
        assert "Invalid request" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_chat_completion_api_error_empty_content(self, enabled_service):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.content = b''

        enabled_service.client = AsyncMock()
        enabled_service.client.post = AsyncMock(return_value=mock_response)

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(HTTPException) as exc_info:
            await enabled_service.chat_completion(messages)

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_chat_completion_timeout(self, enabled_service):
        enabled_service.client = AsyncMock()
        enabled_service.client.post = AsyncMock(
            side_effect=httpx.TimeoutException("Timeout")
        )

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(HTTPException) as exc_info:
            await enabled_service.chat_completion(messages)

        assert exc_info.value.status_code == 504
        assert "超时" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_chat_completion_request_error(self, enabled_service):
        enabled_service.client = AsyncMock()
        enabled_service.client.post = AsyncMock(
            side_effect=httpx.RequestError("Connection failed")
        )

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(HTTPException) as exc_info:
            await enabled_service.chat_completion(messages)

        assert exc_info.value.status_code == 502
        assert "请求失败" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_chat_completion_unknown_error(self, enabled_service):
        enabled_service.client = AsyncMock()
        enabled_service.client.post = AsyncMock(
            side_effect=Exception("Unknown error")
        )

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(HTTPException) as exc_info:
            await enabled_service.chat_completion(messages)

        assert exc_info.value.status_code == 500
        assert "内部错误" in exc_info.value.detail


class TestSimpleChat:
    """Test suite for simple_chat method."""

    @pytest.fixture
    def enabled_service(self):
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.KIMI_API_KEY = "test-api-key"
            mock_settings.KIMI_API_BASE = "https://api.test.com"
            mock_settings.KIMI_MODEL = "test-model"
            mock_settings.KIMI_MAX_TOKENS = 1000
            mock_settings.KIMI_TEMPERATURE = 0.7
            mock_settings.KIMI_TIMEOUT = 30
            mock_settings.KIMI_ENABLED = True

            from app.services.ai_service import AIService
            service = AIService()
            yield service

    @pytest.mark.asyncio
    async def test_simple_chat_without_context(self, enabled_service):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "AI response"}}]
        }

        enabled_service.client = AsyncMock()
        enabled_service.client.post = AsyncMock(return_value=mock_response)

        result = await enabled_service.simple_chat("Hello")

        assert result == "AI response"

        # Verify message format
        call_args = enabled_service.client.post.call_args
        payload = call_args[1]["json"]
        messages = payload["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_simple_chat_with_context(self, enabled_service):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Context-aware response"}}]
        }

        enabled_service.client = AsyncMock()
        enabled_service.client.post = AsyncMock(return_value=mock_response)

        result = await enabled_service.simple_chat(
            "Hello",
            context="You are a helpful assistant"
        )

        assert result == "Context-aware response"

        # Verify message format includes system message
        call_args = enabled_service.client.post.call_args
        payload = call_args[1]["json"]
        messages = payload["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helpful assistant"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_simple_chat_invalid_response_format(self, enabled_service):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "format"}

        enabled_service.client = AsyncMock()
        enabled_service.client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(HTTPException) as exc_info:
            await enabled_service.simple_chat("Hello")

        assert exc_info.value.status_code == 500
        assert "格式错误" in exc_info.value.detail


class TestProjectAnalysis:
    """Test suite for project_analysis method."""

    @pytest.fixture
    def enabled_service(self):
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.KIMI_API_KEY = "test-api-key"
            mock_settings.KIMI_API_BASE = "https://api.test.com"
            mock_settings.KIMI_MODEL = "test-model"
            mock_settings.KIMI_MAX_TOKENS = 1000
            mock_settings.KIMI_TEMPERATURE = 0.7
            mock_settings.KIMI_TIMEOUT = 30
            mock_settings.KIMI_ENABLED = True

            from app.services.ai_service import AIService
            service = AIService()
            yield service

    @pytest.mark.asyncio
    async def test_project_analysis_json_response(self, enabled_service):
        analysis_result = {
            "risk_level": "中",
            "main_risks": ["进度风险"],
            "technical_challenges": ["技术难点1"],
            "resource_suggestions": ["建议1"],
            "schedule_risks": ["风险1"],
            "cost_recommendations": ["建议1"],
            "overall_summary": "项目分析总结"
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(analysis_result)}}]
        }

        enabled_service.client = AsyncMock()
        enabled_service.client.post = AsyncMock(return_value=mock_response)

        project_data = {
            "name": "测试项目",
            "status": "进行中",
            "budget": 100000
        }

        result = await enabled_service.project_analysis(project_data)

        assert result["risk_level"] == "中"
        assert "进度风险" in result["main_risks"]
        assert result["overall_summary"] == "项目分析总结"

    @pytest.mark.asyncio
    async def test_project_analysis_non_json_response(self, enabled_service):
        # AI returns plain text instead of JSON
        plain_text_response = "这是一个纯文本分析结果，不是JSON格式"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": plain_text_response}}]
        }

        enabled_service.client = AsyncMock()
        enabled_service.client.post = AsyncMock(return_value=mock_response)

        project_data = {"name": "测试项目"}

        result = await enabled_service.project_analysis(project_data)

        # Should fallback to raw_analysis
        assert "raw_analysis" in result
        assert result["raw_analysis"] == plain_text_response


class TestClose:
    """Test suite for close method."""

    @pytest.mark.asyncio
    async def test_close_with_client(self):
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.KIMI_API_KEY = "test-api-key"
            mock_settings.KIMI_API_BASE = "https://api.test.com"
            mock_settings.KIMI_MODEL = "test-model"
            mock_settings.KIMI_MAX_TOKENS = 1000
            mock_settings.KIMI_TEMPERATURE = 0.7
            mock_settings.KIMI_TIMEOUT = 30
            mock_settings.KIMI_ENABLED = True

            from app.services.ai_service import AIService
            service = AIService()

            mock_client = AsyncMock()
            service.client = mock_client

            await service.close()

            mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_without_client(self):
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.KIMI_API_KEY = None
            mock_settings.KIMI_API_BASE = "https://api.test.com"
            mock_settings.KIMI_MODEL = "test-model"
            mock_settings.KIMI_MAX_TOKENS = 1000
            mock_settings.KIMI_TEMPERATURE = 0.7
            mock_settings.KIMI_TIMEOUT = 30
            mock_settings.KIMI_ENABLED = False

            from app.services.ai_service import AIService
            service = AIService()

            # Should not raise error when client is None
            await service.close()


class TestHelperFunctions:
    """Test suite for module-level helper functions."""

    @pytest.mark.asyncio
    async def test_get_ai_service(self):
        with patch('app.services.ai_service.ai_service') as mock_global_service:
            from app.services.ai_service import get_ai_service

            result = await get_ai_service()

            assert result == mock_global_service

    @pytest.mark.asyncio
    async def test_analyze_project_with_ai(self):
        with patch('app.services.ai_service.get_ai_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.project_analysis = AsyncMock(
                return_value={"risk_level": "低"}
            )
            mock_get_service.return_value = mock_service

            from app.services.ai_service import analyze_project_with_ai

            project_data = {"name": "Test"}
            result = await analyze_project_with_ai(project_data)

            assert result == {"risk_level": "低"}
            mock_service.project_analysis.assert_called_once_with(project_data)

    @pytest.mark.asyncio
    async def test_chat_with_ai(self):
        with patch('app.services.ai_service.get_ai_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.simple_chat = AsyncMock(return_value="AI response")
            mock_get_service.return_value = mock_service

            from app.services.ai_service import chat_with_ai

            result = await chat_with_ai("Hello", context="Be helpful")

            assert result == "AI response"
            mock_service.simple_chat.assert_called_once_with("Hello", "Be helpful")

    @pytest.mark.asyncio
    async def test_chat_with_ai_no_context(self):
        with patch('app.services.ai_service.get_ai_service') as mock_get_service:
            mock_service = AsyncMock()
            mock_service.simple_chat = AsyncMock(return_value="AI response")
            mock_get_service.return_value = mock_service

            from app.services.ai_service import chat_with_ai

            result = await chat_with_ai("Hello")

            assert result == "AI response"
            mock_service.simple_chat.assert_called_once_with("Hello", None)
