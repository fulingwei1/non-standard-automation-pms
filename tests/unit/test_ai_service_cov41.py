# -*- coding: utf-8 -*-
"""Unit tests for app/services/ai_service.py - batch 41"""
import pytest

pytest.importorskip("app.services.ai_service")

from unittest.mock import AsyncMock, MagicMock, patch
import json


@pytest.fixture
def mock_settings():
    with patch("app.services.ai_service.settings") as s:
        s.KIMI_API_KEY = "test-key"
        s.KIMI_API_BASE = "https://api.example.com"
        s.KIMI_MODEL = "moonshot-v1-8k"
        s.KIMI_MAX_TOKENS = 4096
        s.KIMI_TEMPERATURE = 0.3
        s.KIMI_TIMEOUT = 30
        s.KIMI_ENABLED = True
        yield s


def test_ai_service_disabled_when_no_key():
    with patch("app.services.ai_service.settings") as s:
        s.KIMI_API_KEY = None
        s.KIMI_API_BASE = "https://api.example.com"
        s.KIMI_MODEL = "moonshot-v1-8k"
        s.KIMI_MAX_TOKENS = 4096
        s.KIMI_TEMPERATURE = 0.3
        s.KIMI_TIMEOUT = 30
        s.KIMI_ENABLED = True
        with patch("app.services.ai_service.httpx.AsyncClient"):
            from app.services.ai_service import AIService
            svc = AIService()
            assert svc.enabled is False
            assert svc.client is None


def test_ai_service_enabled_with_key(mock_settings):
    with patch("app.services.ai_service.httpx.AsyncClient") as MockClient:
        MockClient.return_value = MagicMock()
        from app.services.ai_service import AIService
        svc = AIService()
        assert svc.enabled is True
        assert svc.client is not None


@pytest.mark.asyncio
async def test_chat_completion_raises_when_disabled():
    with patch("app.services.ai_service.settings") as s:
        s.KIMI_API_KEY = None
        s.KIMI_API_BASE = "https://api.example.com"
        s.KIMI_MODEL = "moonshot-v1-8k"
        s.KIMI_MAX_TOKENS = 4096
        s.KIMI_TEMPERATURE = 0.3
        s.KIMI_TIMEOUT = 30
        s.KIMI_ENABLED = False
        with patch("app.services.ai_service.httpx.AsyncClient"):
            from app.services.ai_service import AIService
            from fastapi import HTTPException
            svc = AIService()
            with pytest.raises(HTTPException) as exc_info:
                await svc.chat_completion([{"role": "user", "content": "hello"}])
            assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_chat_completion_success(mock_settings):
    with patch("app.services.ai_service.httpx.AsyncClient") as MockClient:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "hi"}}]}
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        MockClient.return_value = mock_client
        from app.services.ai_service import AIService
        svc = AIService()
        result = await svc.chat_completion([{"role": "user", "content": "hello"}])
        assert "choices" in result


@pytest.mark.asyncio
async def test_simple_chat_extracts_content(mock_settings):
    with patch("app.services.ai_service.httpx.AsyncClient") as MockClient:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "AI response"}}]}
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        MockClient.return_value = mock_client
        from app.services.ai_service import AIService
        svc = AIService()
        result = await svc.simple_chat("test prompt")
        assert result == "AI response"


@pytest.mark.asyncio
async def test_project_analysis_returns_dict(mock_settings):
    with patch("app.services.ai_service.httpx.AsyncClient") as MockClient:
        expected = {"risk_level": "低", "overall_summary": "良好"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(expected, ensure_ascii=False)}}]
        }
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        MockClient.return_value = mock_client
        from app.services.ai_service import AIService
        svc = AIService()
        result = await svc.project_analysis({"project_name": "TestProject"})
        assert result["risk_level"] == "低"


@pytest.mark.asyncio
async def test_project_analysis_handles_invalid_json(mock_settings):
    with patch("app.services.ai_service.httpx.AsyncClient") as MockClient:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "not valid json"}}]
        }
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        MockClient.return_value = mock_client
        from app.services.ai_service import AIService
        svc = AIService()
        result = await svc.project_analysis({"project_name": "test"})
        assert "raw_analysis" in result


@pytest.mark.asyncio
async def test_get_ai_service_returns_instance(mock_settings):
    with patch("app.services.ai_service.httpx.AsyncClient"):
        from app.services.ai_service import get_ai_service, AIService
        svc = await get_ai_service()
        assert isinstance(svc, AIService)
