# -*- coding: utf-8 -*-
"""
第三十三批覆盖率测试 - AI分析混入 (AIAnalysisMixin)
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import date

try:
    from app.services.work_log_ai.ai_analysis import AIAnalysisMixin
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="ai_analysis 导入失败")


class ConcreteAIAnalysis(AIAnalysisMixin):
    """用于测试的具体实现类"""
    def __init__(self):
        pass


class TestAnalyzeWithAISync:
    def test_sync_raises_when_api_fails(self):
        """API请求失败时抛出异常"""
        analyzer = ConcreteAIAnalysis()

        with patch("app.services.work_log_ai.ai_analysis.httpx") as mock_httpx:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = Exception("HTTP 500")
            mock_client.post.return_value = mock_response
            mock_httpx.Client.return_value = mock_client

            with pytest.raises(Exception):
                analyzer._analyze_with_ai_sync(
                    content="今天完成了机械设计",
                    user_projects=[],
                    work_date=date(2026, 1, 15)
                )

    def test_sync_parses_valid_response(self):
        """API返回合法choices时解析成功"""
        analyzer = ConcreteAIAnalysis()
        analyzer._build_ai_prompt = MagicMock(return_value="prompt text")
        analyzer._parse_ai_response = MagicMock(return_value={"work_items": [], "total_hours": 8.0})

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"work_items": [], "total_hours": 8.0}'}}]
        }

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response

        with patch("app.services.work_log_ai.ai_analysis.httpx.Client", return_value=mock_client):
            result = analyzer._analyze_with_ai_sync(
                content="完成了测试",
                user_projects=[],
                work_date=date(2026, 1, 15)
            )

        assert "work_items" in result

    def test_sync_raises_on_empty_choices(self):
        """API返回空choices时抛出ValueError"""
        analyzer = ConcreteAIAnalysis()
        analyzer._build_ai_prompt = MagicMock(return_value="prompt")

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"choices": []}

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response

        with patch("app.services.work_log_ai.ai_analysis.httpx.Client", return_value=mock_client):
            with pytest.raises(ValueError, match="AI API返回格式异常"):
                analyzer._analyze_with_ai_sync(
                    content="测试",
                    user_projects=[],
                    work_date=date(2026, 1, 15)
                )


class TestAnalyzeWithAIAsync:
    @pytest.mark.asyncio
    async def test_async_raises_on_api_error(self):
        """异步版本API失败时抛出异常"""
        analyzer = ConcreteAIAnalysis()
        analyzer._build_ai_prompt = MagicMock(return_value="prompt")

        mock_response = AsyncMock()
        mock_response.raise_for_status.side_effect = Exception("Timeout")

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.services.work_log_ai.ai_analysis.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(Exception):
                await analyzer._analyze_with_ai(
                    content="测试工作内容",
                    user_projects=[],
                    work_date=date(2026, 1, 15)
                )

    @pytest.mark.asyncio
    async def test_async_parses_valid_response(self):
        """异步版本解析正常响应"""
        analyzer = ConcreteAIAnalysis()
        analyzer._build_ai_prompt = MagicMock(return_value="prompt")
        analyzer._parse_ai_response = MagicMock(return_value={"work_items": [{"hours": 4}], "total_hours": 4.0})

        # raise_for_status 和 json 是同步方法
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock(return_value=None)
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"work_items": [{"hours": 4}], "total_hours": 4.0}'}}]
        }

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.services.work_log_ai.ai_analysis.httpx.AsyncClient", return_value=mock_client):
            result = await analyzer._analyze_with_ai(
                content="完成3D建模",
                user_projects=[{"id": 1, "code": "PJ001", "name": "测试项目"}],
                work_date=date(2026, 1, 15)
            )

        assert "work_items" in result

    @pytest.mark.asyncio
    async def test_async_raises_on_empty_choices(self):
        """异步版本空choices时抛出ValueError"""
        analyzer = ConcreteAIAnalysis()
        analyzer._build_ai_prompt = MagicMock(return_value="prompt")

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock(return_value=None)
        mock_response.json.return_value = {"choices": []}

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.services.work_log_ai.ai_analysis.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(ValueError, match="AI API返回格式异常"):
                await analyzer._analyze_with_ai(
                    content="测试",
                    user_projects=[],
                    work_date=date(2026, 1, 15)
                )
