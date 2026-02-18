# -*- coding: utf-8 -*-
"""第二十一批：AI客户端服务单元测试"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.ai_client_service")


@pytest.fixture
def service_no_keys():
    with patch.dict("os.environ", {"OPENAI_API_KEY": "", "KIMI_API_KEY": "", "ZHIPU_API_KEY": ""}):
        from app.services.ai_client_service import AIClientService
        return AIClientService()


class TestAIClientServiceInit:
    def test_init_without_keys(self, service_no_keys):
        assert service_no_keys.openai_client is None
        assert service_no_keys.zhipu_client is None

    def test_default_model_is_glm5(self, service_no_keys):
        assert service_no_keys.default_model == "glm-5"


class TestGenerateSolution:
    def test_glm_model_calls_glm(self, service_no_keys):
        with patch.object(service_no_keys, "_call_glm5") as mock_glm:
            mock_glm.return_value = {"content": "GLM结果", "model": "glm-5-mock"}
            result = service_no_keys.generate_solution("设计一套AGV系统", model="glm-5")
        mock_glm.assert_called_once()
        assert result["content"] == "GLM结果"

    def test_gpt_model_calls_openai(self, service_no_keys):
        with patch.object(service_no_keys, "_call_openai") as mock_openai:
            mock_openai.return_value = {"content": "GPT结果", "model": "gpt-4-mock"}
            result = service_no_keys.generate_solution("方案设计", model="gpt-4")
        mock_openai.assert_called_once()

    def test_kimi_model_calls_kimi(self, service_no_keys):
        with patch.object(service_no_keys, "_call_kimi") as mock_kimi:
            mock_kimi.return_value = {"content": "Kimi结果", "model": "kimi-mock"}
            result = service_no_keys.generate_solution("需求分析", model="kimi")
        mock_kimi.assert_called_once()

    def test_unknown_model_falls_back_to_glm(self, service_no_keys):
        with patch.object(service_no_keys, "_call_glm5") as mock_glm:
            mock_glm.return_value = {"content": "默认结果"}
            result = service_no_keys.generate_solution("任务", model="unknown-model")
        mock_glm.assert_called_once()


class TestGenerateArchitecture:
    def test_calls_generate_solution(self, service_no_keys):
        with patch.object(service_no_keys, "generate_solution") as mock_gen:
            mock_gen.return_value = {"content": "架构图"}
            result = service_no_keys.generate_architecture("生成架构图", model="gpt-4")
        mock_gen.assert_called_once()
        assert result["content"] == "架构图"


class TestMockResponse:
    def test_mock_response_returns_dict(self, service_no_keys):
        result = service_no_keys._mock_response("普通文本", "glm-5")
        assert "content" in result
        assert "model" in result
        assert "usage" in result
        assert "glm-5-mock" in result["model"]

    def test_mock_response_architecture(self, service_no_keys):
        result = service_no_keys._mock_response("请生成架构图 Mermaid", "gpt-4")
        assert "content" in result
        assert "mermaid" in result["content"].lower() or "graph" in result["content"]

    def test_mock_response_usage_fields(self, service_no_keys):
        result = service_no_keys._mock_response("测试提示词", "kimi")
        usage = result["usage"]
        assert "prompt_tokens" in usage
        assert "completion_tokens" in usage
        assert "total_tokens" in usage


class TestCallGlm5WithoutClient:
    def test_returns_mock_when_no_client(self, service_no_keys):
        result = service_no_keys._call_glm5("任务描述", "glm-5", 0.7, 2000)
        assert "content" in result
        assert "glm-5" in result["model"]
