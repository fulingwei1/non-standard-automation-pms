# -*- coding: utf-8 -*-
"""
第三十九批覆盖率测试 - sales_ranking_service.py
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.sales_ranking_service", reason="import failed, skip")


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    with patch("app.services.sales_ranking_service.SalesTeamService"):
        from app.services.sales_ranking_service import SalesRankingService
        svc = SalesRankingService(mock_db)
        svc.team_service = MagicMock()
        return svc


class TestSalesRankingValidateMetrics:

    def test_empty_metrics_raises(self, service):
        with pytest.raises(ValueError, match="至少需要配置"):
            service._validate_metrics([])

    def test_duplicate_key_raises(self, service):
        metrics = [
            {"key": "contract_amount", "data_source": "contract_amount", "weight": 0.5, "is_primary": True},
            {"key": "contract_amount", "data_source": "contract_amount", "weight": 0.5, "is_primary": True},
        ]
        with pytest.raises(ValueError, match="key"):
            service._validate_metrics(metrics)

    def test_invalid_data_source_raises(self, service):
        metrics = [
            {"key": "my_metric", "data_source": "not_supported", "weight": 1.0, "is_primary": False},
        ]
        with pytest.raises(ValueError, match="不支持的数据来源"):
            service._validate_metrics(metrics)

    def test_zero_weight_raises(self, service):
        metrics = [
            {"key": "contract_amount", "data_source": "contract_amount", "weight": 0, "is_primary": True},
        ]
        with pytest.raises(ValueError):
            service._validate_metrics(metrics)

    def test_total_weight_not_one_raises(self, service):
        metrics = [
            {"key": "contract_amount", "data_source": "contract_amount", "weight": 0.5, "is_primary": True},
        ]
        with pytest.raises(ValueError, match="权重之和"):
            service._validate_metrics(metrics)


class TestSalesRankingGetActiveConfig:

    def test_returns_existing_config(self, service, mock_db):
        mock_config = MagicMock(metrics=[{"key": "contract_amount", "weight": 1.0}])
        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.first.return_value = mock_config

        config = service.get_active_config()
        assert config is mock_config

    def test_creates_default_config_when_none(self, service, mock_db):
        mock_q = MagicMock()
        mock_db.query.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.first.return_value = None

        with patch("app.services.sales_ranking_service.save_obj") as mock_save, \
             patch("app.services.sales_ranking_service.SalesRankingConfig") as MockConfig:
            mock_instance = MagicMock(metrics=service.DEFAULT_METRICS)
            MockConfig.return_value = mock_instance
            config = service.get_active_config()
            assert config is not None


class TestSalesRankingCalculateRankings:

    def test_empty_users_returns_empty_rankings(self, service):
        mock_config = MagicMock(metrics=service.DEFAULT_METRICS)
        with patch.object(service, "get_active_config", return_value=mock_config):
            result = service.calculate_rankings(
                [], datetime(2024, 1, 1), datetime(2024, 12, 31)
            )
        assert result["rankings"] == []

    def test_rankings_have_rank_field(self, service, mock_db):
        user = MagicMock(id=1, real_name="张三", username="zhangsan", department="销售部")
        mock_config = MagicMock(metrics=service.DEFAULT_METRICS)

        service.team_service.get_lead_quality_stats_map.return_value = {}
        service.team_service.get_followup_statistics_map.return_value = {}
        service.team_service.get_opportunity_stats_map.return_value = {}

        with patch.object(service, "get_active_config", return_value=mock_config), \
             patch.object(service, "_get_acceptance_amount_map", return_value={1: 0}), \
             patch.object(service, "_get_contract_and_collection_data", return_value={}):
            result = service.calculate_rankings(
                [user], datetime(2024, 1, 1), datetime(2024, 12, 31)
            )
        assert len(result["rankings"]) == 1
        assert result["rankings"][0]["rank"] == 1
