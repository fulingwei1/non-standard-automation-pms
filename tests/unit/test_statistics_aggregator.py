# -*- coding: utf-8 -*-
"""
app/common/statistics/aggregator.py 覆盖率测试（当前 0%）
"""
import pytest
from unittest.mock import MagicMock, AsyncMock


class TestStatisticsAggregator:
    """测试统计聚合器"""

    @pytest.fixture
    def aggregator(self):
        from app.common.statistics.aggregator import StatisticsAggregator
        db = MagicMock()
        return StatisticsAggregator(db=db)

    def test_init(self, aggregator):
        assert aggregator.db is not None
        assert aggregator._services == {}

    def test_register_service(self, aggregator):
        mock_service = MagicMock()
        aggregator.register_service("projects", mock_service)
        assert "projects" in aggregator._services
        assert aggregator._services["projects"] is mock_service

    def test_register_multiple_services(self, aggregator):
        svc1 = MagicMock()
        svc2 = MagicMock()
        aggregator.register_service("a", svc1)
        aggregator.register_service("b", svc2)
        assert len(aggregator._services) == 2

    @pytest.mark.asyncio
    async def test_get_overview_stats_empty(self, aggregator):
        result = await aggregator.get_overview_stats()
        assert isinstance(result, dict)
        assert result == {}

    @pytest.mark.asyncio
    async def test_get_overview_stats_with_service(self, aggregator):
        mock_service = MagicMock()
        mock_service.count_total = AsyncMock(return_value=10)
        mock_service.count_by_status = AsyncMock(return_value={"active": 5, "closed": 5})
        aggregator.register_service("projects", mock_service)

        result = await aggregator.get_overview_stats()
        assert isinstance(result, dict)
        assert "projects" in result
        assert result["projects"]["total"] == 10

    @pytest.mark.asyncio
    async def test_get_overview_stats_filter_services(self, aggregator):
        svc1 = MagicMock()
        svc1.count_total = AsyncMock(return_value=5)
        svc1.count_by_status = AsyncMock(return_value={})
        svc2 = MagicMock()
        svc2.count_total = AsyncMock(return_value=0)
        aggregator.register_service("svc1", svc1)
        aggregator.register_service("svc2", svc2)

        result = await aggregator.get_overview_stats(services=["svc1"])
        assert "svc1" in result
        assert "svc2" not in result

    @pytest.mark.asyncio
    async def test_get_overview_stats_nonexistent_service(self, aggregator):
        """请求不存在的服务时应该被跳过"""
        result = await aggregator.get_overview_stats(services=["nonexistent"])
        assert isinstance(result, dict)
        assert "nonexistent" not in result

    @pytest.mark.asyncio
    async def test_get_trends_with_service(self, aggregator):
        mock_service = MagicMock()
        mock_service.get_trend = AsyncMock(return_value=[{"date": "2026-01-01", "count": 3}])
        aggregator.register_service("projects", mock_service)

        result = await aggregator.get_trends(
            service_name="projects",
            date_field="created_at",
            days=30
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_trends_nonexistent_service_raises(self, aggregator):
        """找不到服务时抛出 ValueError"""
        with pytest.raises(ValueError, match="nonexistent"):
            await aggregator.get_trends(
                service_name="nonexistent",
                date_field="created_at",
            )

    @pytest.mark.asyncio
    async def test_get_comparison_with_service(self, aggregator):
        mock_service = MagicMock()
        mock_service.count_total = AsyncMock(side_effect=[10, 8])  # current=10, previous=8
        aggregator.register_service("projects", mock_service)

        result = await aggregator.get_comparison(
            service_name="projects",
            field="status",
        )
        assert isinstance(result, dict)
        assert result["current"] == 10
        assert result["previous"] == 8
        assert result["change"] == 2

    @pytest.mark.asyncio
    async def test_get_comparison_nonexistent_service_raises(self, aggregator):
        with pytest.raises(ValueError):
            await aggregator.get_comparison(
                service_name="nonexistent",
                field="status",
            )
