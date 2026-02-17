# -*- coding: utf-8 -*-
"""
app/services/ai_client_service.py 覆盖率测试（当前 19%）
专注于不依赖外部 API 的方法（_mock_response, generate_solution 分支等）
"""
import pytest
from unittest.mock import MagicMock, patch


class TestAIClientServiceInit:
    """测试初始化"""

    def test_init_no_api_keys(self):
        with patch.dict("os.environ", {}, clear=False):
            from app.services.ai_client_service import AIClientService
            svc = AIClientService()
            assert svc.default_model == "glm-5"

    def test_init_sets_default_model(self):
        from app.services.ai_client_service import AIClientService
        svc = AIClientService()
        assert svc.default_model == "glm-5"


class TestMockResponse:
    """测试 _mock_response（不依赖 API）"""

    @pytest.fixture
    def svc(self):
        from app.services.ai_client_service import AIClientService
        return AIClientService()

    def test_mock_response_returns_dict(self, svc):
        result = svc._mock_response("test prompt", "glm-5")
        assert isinstance(result, dict)
        assert "content" in result
        assert "model" in result
        assert "usage" in result

    def test_mock_response_architecture_prompt(self, svc):
        result = svc._mock_response("生成架构图 Mermaid 流程图", "gpt-4")
        assert isinstance(result, dict)
        assert result["model"] == "gpt-4-mock"

    def test_mock_response_solution_prompt(self, svc):
        result = svc._mock_response("设计一套自动化方案", "glm-5")
        assert isinstance(result, dict)
        content = result["content"]
        assert content is not None

    def test_mock_response_usage_structure(self, svc):
        result = svc._mock_response("short", "glm-5-mock")
        usage = result["usage"]
        assert "prompt_tokens" in usage
        assert "completion_tokens" in usage
        assert "total_tokens" in usage
        assert all(isinstance(v, int) for v in usage.values())

    def test_mock_solution_returns_string_or_dict(self, svc):
        result = svc._mock_solution()
        assert result is not None
        assert len(str(result)) > 0

    def test_mock_architecture_diagram(self, svc):
        result = svc._mock_architecture_diagram()
        assert result is not None
        assert isinstance(result, str)


class TestGenerateSolution:
    """测试 generate_solution 路由逻辑（mock 实际 API 调用）"""

    @pytest.fixture
    def svc(self):
        from app.services.ai_client_service import AIClientService
        return AIClientService()

    def test_glm_model_routes_to_glm(self, svc):
        mock_result = {"content": "glm result", "model": "glm-5"}
        with patch.object(svc, "_call_glm5", return_value=mock_result) as mock_glm:
            result = svc.generate_solution("test", model="glm-5")
            mock_glm.assert_called_once()
            assert result == mock_result

    def test_gpt_model_routes_to_openai(self, svc):
        mock_result = {"content": "gpt result", "model": "gpt-4"}
        with patch.object(svc, "_call_openai", return_value=mock_result) as mock_oai:
            result = svc.generate_solution("test", model="gpt-4")
            mock_oai.assert_called_once()

    def test_kimi_model_routes_to_kimi(self, svc):
        mock_result = {"content": "kimi result", "model": "kimi"}
        with patch.object(svc, "_call_kimi", return_value=mock_result) as mock_kimi:
            result = svc.generate_solution("test", model="kimi-v2")
            mock_kimi.assert_called_once()

    def test_unknown_model_defaults_to_glm(self, svc):
        mock_result = {"content": "default result", "model": "glm-5"}
        with patch.object(svc, "_call_glm5", return_value=mock_result) as mock_glm:
            result = svc.generate_solution("test", model="unknown-model")
            mock_glm.assert_called_once()

    def test_generate_architecture_calls_solution(self, svc):
        mock_result = {"content": "arch", "model": "gpt-4"}
        with patch.object(svc, "generate_solution", return_value=mock_result) as mock_gen:
            result = svc.generate_architecture("create architecture", model="gpt-4")
            mock_gen.assert_called_once()
            assert result == mock_result
