# -*- coding: utf-8 -*-
"""AIAnalysisMixin 单元测试"""
from datetime import date
from unittest.mock import MagicMock, patch
import pytest

from app.services.work_log_ai.ai_analysis import AIAnalysisMixin


class ConcreteAI(AIAnalysisMixin):
    pass


class TestAIAnalysisMixin:
    def setup_method(self):
        self.ai = ConcreteAI()

    @patch("app.services.work_log_ai.ai_analysis.ALIBABA_API_KEY", "test-key")
    @patch("app.services.work_log_ai.ai_analysis.ALIBABA_BASE_URL", "http://test.api")
    @patch("app.services.work_log_ai.ai_analysis.ALIBABA_MODEL", "test-model")
    def test_analyze_sync_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()  # no-op
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"work_items": []}'}}]
        }
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response

        with patch("httpx.Client", return_value=mock_client), \
             patch.object(self.ai, "_build_ai_prompt", return_value="test prompt"), \
             patch.object(self.ai, "_parse_ai_response", return_value={"items": []}):
            result = self.ai._analyze_with_ai_sync("content", [], date.today())
            assert result == {"items": []}

    @patch("app.services.work_log_ai.ai_analysis.ALIBABA_API_KEY", "test-key")
    @patch("app.services.work_log_ai.ai_analysis.ALIBABA_BASE_URL", "http://test.api")
    @patch("app.services.work_log_ai.ai_analysis.ALIBABA_MODEL", "test-model")
    def test_analyze_sync_bad_response(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"error": "bad"}
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response

        with patch("httpx.Client", return_value=mock_client), \
             patch.object(self.ai, "_build_ai_prompt", return_value="test"):
            with pytest.raises(ValueError, match="格式异常"):
                self.ai._analyze_with_ai_sync("content", [], date.today())
