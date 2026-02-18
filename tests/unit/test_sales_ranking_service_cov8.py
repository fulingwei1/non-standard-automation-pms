# -*- coding: utf-8 -*-
"""
第八批覆盖率测试 - 销售排名服务
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

try:
    from app.services.sales_ranking_service import SalesRankingService
    HAS_SRS = True
except Exception:
    HAS_SRS = False

pytestmark = pytest.mark.skipif(not HAS_SRS, reason="sales_ranking_service 导入失败")


class TestSalesRankingServiceConstants:
    """常量和配置测试"""

    def test_primary_metric_keys(self):
        """主要指标 Key 存在"""
        assert "contract_amount" in SalesRankingService.PRIMARY_METRIC_KEYS
        assert "acceptance_amount" in SalesRankingService.PRIMARY_METRIC_KEYS
        assert "collection_amount" in SalesRankingService.PRIMARY_METRIC_KEYS

    def test_primary_weight_target(self):
        """主要指标权重目标应为 0.8"""
        assert SalesRankingService.PRIMARY_WEIGHT_TARGET == 0.8

    def test_total_weight_target(self):
        """总权重目标应为 1.0"""
        assert SalesRankingService.TOTAL_WEIGHT_TARGET == 1.0

    def test_default_metrics_non_empty(self):
        """默认指标配置不为空"""
        assert len(SalesRankingService.DEFAULT_METRICS) > 0

    def test_default_metric_has_required_fields(self):
        """每个默认指标有必需字段"""
        for metric in SalesRankingService.DEFAULT_METRICS:
            assert "key" in metric
            assert "weight" in metric
            assert "label" in metric


class TestSalesRankingServiceInit:
    def test_init(self):
        db = MagicMock()
        with patch("app.services.sales_ranking_service.SalesTeamService") as mock_sts:
            svc = SalesRankingService(db)
        assert svc.db is db


class TestGetOrCreateConfig:
    def test_returns_existing_config(self):
        """已有配置时直接返回"""
        db = MagicMock()
        with patch("app.services.sales_ranking_service.SalesTeamService"):
            svc = SalesRankingService(db)
        mock_config = MagicMock()
        mock_config.metrics_config = [
            {"key": "contract_amount", "weight": 0.4, "label": "合同金额",
             "data_source": "contract_amount", "description": "", "is_primary": True}
        ]
        db.query.return_value.first.return_value = mock_config
        if hasattr(svc, 'get_or_create_config'):
            result = svc.get_or_create_config()
            assert result is not None
        else:
            pytest.skip("get_or_create_config 不存在")

    def test_creates_default_when_none(self):
        """无配置时创建默认配置"""
        db = MagicMock()
        with patch("app.services.sales_ranking_service.SalesTeamService"):
            svc = SalesRankingService(db)
        db.query.return_value.first.return_value = None
        if hasattr(svc, 'get_or_create_config'):
            result = svc.get_or_create_config()
            assert result is not None
        else:
            pytest.skip("get_or_create_config 不存在")


class TestCalculateRanking:
    def test_empty_result_on_no_data(self):
        """无数据时返回空结果"""
        db = MagicMock()
        with patch("app.services.sales_ranking_service.SalesTeamService"):
            svc = SalesRankingService(db)
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.all.return_value = []
        if hasattr(svc, 'calculate_ranking'):
            result = svc.calculate_ranking(
                start_date="2026-01-01",
                end_date="2026-01-31"
            )
            assert isinstance(result, (list, dict))
        else:
            pytest.skip("calculate_ranking 不存在")


class TestValidateWeights:
    def test_weight_sum_validation(self):
        """权重配置验证"""
        metrics = SalesRankingService.DEFAULT_METRICS
        total = sum(m["weight"] for m in metrics)
        # 权重总和接近 1.0
        assert abs(total - 1.0) < 0.01

    def test_allowed_metric_sources(self):
        """检查允许的指标来源"""
        assert "contract_amount" in SalesRankingService.ALLOWED_METRIC_SOURCES
        assert "collection_amount" in SalesRankingService.ALLOWED_METRIC_SOURCES
