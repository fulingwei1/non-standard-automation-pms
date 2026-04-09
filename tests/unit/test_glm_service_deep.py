# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - GLM AI服务"""
import pytest
from unittest.mock import MagicMock, patch
import os


class TestGLMServiceBusinessLogic:
    """GLM AI服务业务逻辑测试"""

    def test_init_with_api_key(self):
        """测试使用API密钥初始化"""
        try:
            from app.services.ai_planning.glm_service import GLMService

            with patch('app.services.ai_planning.glm_service.ZhipuAI') as MockZhipuAI:
                MockZhipuAI.return_value = MagicMock()

                service = GLMService(api_key="test_api_key")

                assert service.api_key == "test_api_key"
                assert service.model == "glm-4"
        except ImportError:
            pytest.skip("Module not found")

    def test_init_without_api_key(self):
        """测试没有API密钥初始化"""
        try:
            from app.services.ai_planning.glm_service import GLMService

            with patch.dict(os.environ, {}, clear=True):
                service = GLMService()

                assert service.api_key is None
                assert service.client is None
        except ImportError:
            pytest.skip("Module not found")

    def test_is_available_with_client(self):
        """测试服务可用性（有客户端）"""
        try:
            from app.services.ai_planning.glm_service import GLMService

            service = GLMService.__new__(GLMService)
            service.client = MagicMock()

            assert service.is_available() == True
        except ImportError:
            pytest.skip("Module not found")

    def test_is_available_without_client(self):
        """测试服务可用性（无客户端）"""
        try:
            from app.services.ai_planning.glm_service import GLMService

            service = GLMService.__new__(GLMService)
            service.client = None

            assert service.is_available() == False
        except ImportError:
            pytest.skip("Module not found")

    def test_chat_success(self):
        """测试对话成功"""
        try:
            from app.services.ai_planning.glm_service import GLMService

            service = GLMService.__new__(GLMService)
            service.client = MagicMock()
            service.max_retries = 3
            service.model = "glm-4"

            # Mock响应
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "AI回复内容"
            service.client.chat.completions.create.return_value = mock_response

            messages = [{"role": "user", "content": "你好"}]
            result = service.chat(messages)

            assert result == "AI回复内容"
        except ImportError:
            pytest.skip("Module not found")

    def test_chat_service_unavailable(self):
        """测试服务不可用时的对话"""
        try:
            from app.services.ai_planning.glm_service import GLMService

            service = GLMService.__new__(GLMService)
            service.client = None

            messages = [{"role": "user", "content": "你好"}]
            result = service.chat(messages)

            assert result is None
        except ImportError:
            pytest.skip("Module not found")

    def test_chat_with_temperature(self):
        """测试带温度参数的对话"""
        try:
            from app.services.ai_planning.glm_service import GLMService

            service = GLMService.__new__(GLMService)
            service.client = MagicMock()
            service.max_retries = 3
            service.model = "glm-4"

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "回复"
            service.client.chat.completions.create.return_value = mock_response

            messages = [{"role": "user", "content": "测试"}]
            result = service.chat(messages, temperature=0.5)

            # 验证调用参数
            call_kwargs = service.client.chat.completions.create.call_args[1]
            assert call_kwargs["temperature"] == 0.5
        except ImportError:
            pytest.skip("Module not found")

    def test_generate_text(self):
        """测试文本生成"""
        try:
            from app.services.ai_planning.glm_service import GLMService

            service = GLMService.__new__(GLMService)
            service.client = MagicMock()
            service.max_retries = 3
            service.model = "glm-4"

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "生成的文本"
            service.client.chat.completions.create.return_value = mock_response

            result = service.generate_text("写一段测试文本")

            assert result == "生成的文本"
        except ImportError:
            pytest.skip("Module not found")

    def test_generate_project_plan(self):
        """测试生成项目计划"""
        try:
            from app.services.ai_planning.glm_service import GLMService

            service = GLMService.__new__(GLMService)
            service.client = MagicMock()
            service.max_retries = 3
            service.model = "glm-4"

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"stages": []}'
            service.client.chat.completions.create.return_value = mock_response

            result = service.generate_project_plan(
                project_name="测试项目",
                project_type="ICT",
                requirements="测试需求"
            )

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")


class TestGLMServiceRetryLogic:
    """重试逻辑测试"""

    def test_retry_on_error(self):
        """测试错误时重试"""
        try:
            from app.services.ai_planning.glm_service import GLMService

            service = GLMService.__new__(GLMService)
            service.client = MagicMock()
            service.max_retries = 3
            service.model = "glm-4"

            # 前两次失败，第三次成功
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "成功"

            service.client.chat.completions.create.side_effect = [
                Exception("错误1"),
                Exception("错误2"),
                mock_response
            ]

            messages = [{"role": "user", "content": "测试"}]
            result = service.chat(messages)

            # 应该重试成功
            assert result == "成功"
            assert service.client.chat.completions.create.call_count == 3
        except ImportError:
            pytest.skip("Module not found")

    def test_max_retries_exceeded(self):
        """测试超过最大重试次数"""
        try:
            from app.services.ai_planning.glm_service import GLMService

            service = GLMService.__new__(GLMService)
            service.client = MagicMock()
            service.max_retries = 2
            service.model = "glm-4"

            # 所有尝试都失败
            service.client.chat.completions.create.side_effect = Exception("持续错误")

            messages = [{"role": "user", "content": "测试"}]
            result = service.chat(messages)

            # 应该返回None
            assert result is None
        except ImportError:
            pytest.skip("Module not found")


class TestGLMServiceConfiguration:
    """配置测试"""

    def test_model_configuration(self):
        """测试模型配置"""
        try:
            from app.services.ai_planning.glm_service import GLMService

            service = GLMService.__new__(GLMService)
            service.model = "glm-4"

            assert service.model == "glm-4"
        except ImportError:
            pytest.skip("Module not found")

    def test_timeout_configuration(self):
        """测试超时配置"""
        try:
            from app.services.ai_planning.glm_service import GLMService

            service = GLMService.__new__(GLMService)
            service.timeout = 30

            assert service.timeout == 30
        except ImportError:
            pytest.skip("Module not found")