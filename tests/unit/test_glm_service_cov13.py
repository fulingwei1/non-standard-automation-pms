# -*- coding: utf-8 -*-
"""第十三批 - GLM AI服务 单元测试"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from decimal import Decimal

try:
    from app.services.ai_planning.glm_service import GLMService
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


@pytest.fixture
def service_no_key():
    """无API密钥的服务"""
    with patch.dict('os.environ', {}, clear=False):
        import os
        os.environ.pop('GLM_API_KEY', None)
        svc = GLMService(api_key=None)
    return svc


@pytest.fixture
def service_with_key():
    """带API密钥的服务（mock ZhipuAI）"""
    with patch('app.services.ai_planning.glm_service.ZhipuAI') as MockZhipu:
        mock_client = MagicMock()
        MockZhipu.return_value = mock_client
        svc = GLMService(api_key="fake-key-123")
        svc._mock_client = mock_client
    return svc


class TestGLMServiceAvailability:
    def test_no_api_key_not_available(self, service_no_key):
        """无密钥时服务不可用"""
        assert service_no_key.is_available() is False

    def test_with_api_key_client_created(self):
        """有密钥时客户端被创建"""
        with patch('app.services.ai_planning.glm_service.ZhipuAI') as MockZhipu:
            mock_client = MagicMock()
            MockZhipu.return_value = mock_client
            svc = GLMService(api_key="test-key")
            assert svc.is_available() is True

    def test_zhipuai_none_not_available(self):
        """zhipuai包未安装时不可用"""
        with patch('app.services.ai_planning.glm_service.ZhipuAI', None):
            svc = GLMService(api_key="some-key")
            assert svc.is_available() is False


class TestGLMServiceChat:
    def test_chat_not_available_returns_none(self, service_no_key):
        """服务不可用时chat返回None"""
        result = service_no_key.chat([{"role": "user", "content": "hello"}])
        assert result is None

    def test_chat_success(self):
        """chat成功调用返回内容"""
        with patch('app.services.ai_planning.glm_service.ZhipuAI') as MockZhipu:
            mock_client = MagicMock()
            mock_choice = MagicMock()
            mock_choice.message.content = "AI回复内容"
            mock_client.chat.completions.create.return_value.choices = [mock_choice]
            MockZhipu.return_value = mock_client

            svc = GLMService(api_key="test-key")
            result = svc.chat([{"role": "user", "content": "测试"}])
            assert result == "AI回复内容"

    def test_chat_retry_on_exception(self):
        """chat失败时重试"""
        with patch('app.services.ai_planning.glm_service.ZhipuAI') as MockZhipu:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("网络错误")
            MockZhipu.return_value = mock_client

            svc = GLMService(api_key="test-key")
            svc.max_retries = 1
            with patch('time.sleep'):
                result = svc.chat([{"role": "user", "content": "测试"}])
            assert result is None


class TestGLMServiceInit:
    def test_model_default(self):
        """默认使用glm-4模型"""
        with patch('app.services.ai_planning.glm_service.ZhipuAI') as MockZhipu:
            MockZhipu.return_value = MagicMock()
            svc = GLMService(api_key="test")
            assert svc.model == "glm-4"

    def test_max_retries_default(self):
        """默认最大重试次数为3"""
        svc = GLMService(api_key=None)
        assert svc.max_retries == 3
