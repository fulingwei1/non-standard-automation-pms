# -*- coding: utf-8 -*-
"""GLM API包装服务单元测试 - 第三十六批"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

pytest.importorskip("app.services.glm_service")

try:
    from app.services.glm_service import get_glm_service, call_glm_api, _generate_mock_response
    import app.services.glm_service as glm_module
except ImportError:
    pytestmark = pytest.mark.skip(reason="导入失败")
    get_glm_service = None


class TestGetGlmService:
    def test_returns_service_instance(self):
        # 重置全局单例
        glm_module._glm_service = None
        svc = get_glm_service()
        assert svc is not None

    def test_returns_same_singleton(self):
        glm_module._glm_service = None
        svc1 = get_glm_service()
        svc2 = get_glm_service()
        assert svc1 is svc2


class TestGenerateMockResponse:
    def test_returns_string(self):
        result = _generate_mock_response("test prompt")
        assert isinstance(result, str)

    def test_contains_json_structure(self):
        result = _generate_mock_response("test")
        assert "{" in result and "}" in result

    def test_contains_level_key(self):
        result = _generate_mock_response("test")
        assert "level" in result.lower() or "MEDIUM" in result


@pytest.mark.asyncio
class TestCallGlmApi:
    async def test_unavailable_service_returns_mock(self):
        glm_module._glm_service = None
        mock_svc = MagicMock()
        mock_svc.is_available.return_value = False
        with patch.object(glm_module, "get_glm_service", return_value=mock_svc):
            result = await call_glm_api("hello world")
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_available_service_calls_chat(self):
        glm_module._glm_service = None
        mock_svc = MagicMock()
        mock_svc.is_available.return_value = True
        mock_svc.chat.return_value = "AI回复内容"
        with patch.object(glm_module, "get_glm_service", return_value=mock_svc):
            result = await call_glm_api("prompt text")
        assert result == "AI回复内容"

    async def test_with_system_prompt_adds_to_messages(self):
        mock_svc = MagicMock()
        mock_svc.is_available.return_value = True
        mock_svc.chat.return_value = "OK"
        with patch.object(glm_module, "get_glm_service", return_value=mock_svc):
            result = await call_glm_api("user msg", system_prompt="system instructions")
        mock_svc.chat.assert_called_once()
        messages = mock_svc.chat.call_args[1]["messages"]
        roles = [m["role"] for m in messages]
        assert "system" in roles
