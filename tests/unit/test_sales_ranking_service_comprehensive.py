# -*- coding: utf-8 -*-
"""
SalesRankingService 综合单元测试

测试覆盖:
- get_active_config: 获取当前配置
- save_config: 保存新配置
- _validate_metrics: 验证指标配置
- calculate_rankings: 计算排名
- _get_contract_and_collection_data: 获取合同和回款数据
- _get_acceptance_amount_map: 获取验收金额映射
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


class TestSalesRankingServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        from app.services.sales_ranking_service import SalesRankingService

        mock_db = MagicMock()

        with patch("app.services.sales_ranking_service.SalesTeamService"):
            service = SalesRankingService(mock_db)

        assert service.db == mock_db

    def test_has_default_metrics(self):
        """测试有默认指标配置"""
        from app.services.sales_ranking_service import SalesRankingService

        assert len(SalesRankingService.DEFAULT_METRICS) >= 5
        assert SalesRankingService.PRIMARY_WEIGHT_TARGET == 0.8
        assert SalesRankingService.TOTAL_WEIGHT_TARGET == 1.0


class TestGetActiveConfig:
    """测试 get_active_config 方法"""

    def test_returns_existing_config(self):
        """测试返回已存在的配置"""
        from app.services.sales_ranking_service import SalesRankingService

        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.metrics = [{"key": "test"}]

        mock_db.query.return_value.order_by.return_value.first.return_value = mock_config

        with patch("app.services.sales_ranking_service.SalesTeamService"):
            service = SalesRankingService(mock_db)
            result = service.get_active_config()

        assert result == mock_config

    def test_creates_default_config_when_none_exists(self):
        """测试不存在时创建默认配置"""
        from app.services.sales_ranking_service import SalesRankingService

        mock_db = MagicMock()
        mock_db.query.return_value.order_by.return_value.first.return_value = None

        with patch("app.services.sales_ranking_service.SalesTeamService"):
            service = SalesRankingService(mock_db)
            result = service.get_active_config()

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


class TestSaveConfig:
    """测试 save_config 方法"""

    def test_saves_valid_config(self):
        """测试保存有效配置"""
        from app.services.sales_ranking_service import SalesRankingService

        mock_db = MagicMock()

        metrics = [
            {"key": "contract_amount", "label": "合同金额", "weight": 0.4, "data_source": "contract_amount", "is_primary": True},
            {"key": "acceptance_amount", "label": "验收金额", "weight": 0.2, "data_source": "acceptance_amount", "is_primary": True},
            {"key": "collection_amount", "label": "回款金额", "weight": 0.2, "data_source": "collection_amount", "is_primary": True},
            {"key": "opportunity_count", "label": "商机数量", "weight": 0.2, "data_source": "opportunity_count", "is_primary": False},
        ]

        with patch("app.services.sales_ranking_service.SalesTeamService"):
            service = SalesRankingService(mock_db)
            result = service.save_config(metrics, operator_id=1)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


class TestValidateMetrics:
    """测试 _validate_metrics 方法"""

    def test_raises_error_when_empty_metrics(self):
        """测试空指标时抛出异常"""
        from app.services.sales_ranking_service import SalesRankingService

        mock_db = MagicMock()

        with patch("app.services.sales_ranking_service.SalesTeamService"):
            service = SalesRankingService(mock_db)

        with pytest.raises(ValueError) as exc_info:
            service._validate_metrics([])

        assert "至少需要配置一条指标" in str(exc_info.value)

    def test_raises_error_for_duplicate_keys(self):
        """测试重复键时抛出异常"""
        from app.services.sales_ranking_service import SalesRankingService

        mock_db = MagicMock()

        metrics = [
            {"key": "contract_amount", "weight": 0.5, "data_source": "contract_amount"},
            {"key": "contract_amount", "weight": 0.5, "data_source": "contract_amount"},  # Duplicate
        ]

        with patch("app.services.sales_ranking_service.SalesTeamService"):
            service = SalesRankingService(mock_db)

        with pytest.raises(ValueError) as exc_info:
            service._validate_metrics(metrics)

        assert "不能重复" in str(exc_info.value)

    def test_raises_error_for_invalid_data_source(self):
        """测试无效数据源时抛出异常"""
        from app.services.sales_ranking_service import SalesRankingService

        mock_db = MagicMock()

        metrics = [
            {"key": "test", "weight": 1.0, "data_source": "invalid_source"},
        ]

        with patch("app.services.sales_ranking_service.SalesTeamService"):
            service = SalesRankingService(mock_db)

        with pytest.raises(ValueError) as exc_info:
            service._validate_metrics(metrics)

        assert "不支持的数据来源" in str(exc_info.value)

    def test_raises_error_for_zero_weight(self):
        """测试零权重时抛出异常"""
        from app.services.sales_ranking_service import SalesRankingService

        mock_db = MagicMock()

        metrics = [
            {"key": "contract_amount", "weight": 0, "data_source": "contract_amount"},
        ]

        with patch("app.services.sales_ranking_service.SalesTeamService"):
            service = SalesRankingService(mock_db)

        with pytest.raises(ValueError) as exc_info:
            service._validate_metrics(metrics)

        assert "权重必须大于0" in str(exc_info.value)

    def test_raises_error_when_total_weight_not_1(self):
        """测试总权重不为1时抛出异常"""
        from app.services.sales_ranking_service import SalesRankingService

        mock_db = MagicMock()

        metrics = [
            {"key": "contract_amount", "weight": 0.5, "data_source": "contract_amount", "is_primary": True},
        ]

        with patch("app.services.sales_ranking_service.SalesTeamService"):
            service = SalesRankingService(mock_db)

        with pytest.raises(ValueError) as exc_info:
            service._validate_metrics(metrics)

        assert "权重之和必须等于 1.0" in str(exc_info.value)

    def test_raises_error_when_primary_weight_not_08(self):
        """测试主要指标权重不为0.8时抛出异常"""
        from app.services.sales_ranking_service import SalesRankingService

        mock_db = MagicMock()

        # Primary weights sum to 0.6, not 0.8
        metrics = [
            {"key": "contract_amount", "weight": 0.2, "data_source": "contract_amount", "is_primary": True},
            {"key": "acceptance_amount", "weight": 0.2, "data_source": "acceptance_amount", "is_primary": True},
            {"key": "collection_amount", "weight": 0.2, "data_source": "collection_amount", "is_primary": True},
            {"key": "opportunity_count", "weight": 0.4, "data_source": "opportunity_count", "is_primary": False},
        ]

        with patch("app.services.sales_ranking_service.SalesTeamService"):
            service = SalesRankingService(mock_db)

        with pytest.raises(ValueError) as exc_info:
            service._validate_metrics(metrics)

        assert "三项权重之和必须为 0.8" in str(exc_info.value)

    def test_sorts_metrics_by_weight_descending(self):
        """测试按权重降序排列"""
        from app.services.sales_ranking_service import SalesRankingService

        mock_db = MagicMock()

        metrics = [
            {"key": "contract_amount", "weight": 0.4, "data_source": "contract_amount", "is_primary": True},
            {"key": "acceptance_amount", "weight": 0.2, "data_source": "acceptance_amount", "is_primary": True},
            {"key": "collection_amount", "weight": 0.2, "data_source": "collection_amount", "is_primary": True},
            {"key": "opportunity_count", "weight": 0.2, "data_source": "opportunity_count", "is_primary": False},
        ]

        with patch("app.services.sales_ranking_service.SalesTeamService"):
            service = SalesRankingService(mock_db)
            result = service._validate_metrics(metrics)

        weights = [m["weight"] for m in result]
        assert weights == sorted(weights, reverse=True)


class TestCalculateRankings:
    """测试 calculate_rankings 方法"""

    def test_returns_empty_rankings_when_no_users(self):
        """测试无用户时返回空排名"""
        from app.services.sales_ranking_service import SalesRankingService

        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.metrics = SalesRankingService.DEFAULT_METRICS
        mock_db.query.return_value.order_by.return_value.first.return_value = mock_config

        with patch("app.services.sales_ranking_service.SalesTeamService"):
            service = SalesRankingService(mock_db)
            result = service.calculate_rankings(
                users=[],
                start_datetime=datetime(2026, 1, 1),
                end_datetime=datetime(2026, 1, 31),
            )

        assert result["rankings"] == []

    def test_calculates_rankings_for_users(self):
        """测试为用户计算排名"""
        from app.services.sales_ranking_service import SalesRankingService

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.metrics = [
            {"key": "contract_amount", "label": "合同金额", "weight": 0.8, "data_source": "contract_amount"},
            {"key": "opportunity_count", "label": "商机数量", "weight": 0.2, "data_source": "opportunity_count"},
        ]

        mock_user1 = MagicMock()
        mock_user1.id = 1
        mock_user1.real_name = "张三"
        mock_user1.username = "zhangsan"
        mock_user1.department = "销售部"

        mock_user2 = MagicMock()
        mock_user2.id = 2
        mock_user2.real_name = "李四"
        mock_user2.username = "lisi"
        mock_user2.department = "销售部"

        mock_db.query.return_value.order_by.return_value.first.return_value = mock_config

        with patch("app.services.sales_ranking_service.SalesTeamService") as MockTeamService:
            mock_team_service = MagicMock()
            mock_team_service.get_lead_quality_stats_map.return_value = {}
            mock_team_service.get_followup_statistics_map.return_value = {}
            mock_team_service.get_opportunity_stats_map.return_value = {
                1: {"opportunity_count": 10},
                2: {"opportunity_count": 5},
            }
            MockTeamService.return_value = mock_team_service

            service = SalesRankingService(mock_db)

            with patch.object(service, "_get_acceptance_amount_map", return_value={}):
                with patch.object(service, "_get_contract_and_collection_data", return_value={
                    1: {"contract_amount": 100000, "contract_count": 5, "collection_amount": 50000},
                    2: {"contract_amount": 200000, "contract_count": 8, "collection_amount": 100000},
                }):
                    result = service.calculate_rankings(
                        users=[mock_user1, mock_user2],
                        start_datetime=datetime(2026, 1, 1),
                        end_datetime=datetime(2026, 1, 31),
                    )

        assert len(result["rankings"]) == 2
        # Rankings should be sorted
        assert result["rankings"][0]["rank"] == 1
        assert result["rankings"][1]["rank"] == 2

    def test_sorts_by_score_by_default(self):
        """测试默认按评分排序"""
        from app.services.sales_ranking_service import SalesRankingService

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.metrics = [
            {"key": "contract_amount", "label": "合同金额", "weight": 1.0, "data_source": "contract_amount"},
        ]

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.real_name = "测试"
        mock_user.username = "test"
        mock_user.department = "销售部"

        mock_db.query.return_value.order_by.return_value.first.return_value = mock_config

        with patch("app.services.sales_ranking_service.SalesTeamService") as MockTeamService:
            mock_team_service = MagicMock()
            mock_team_service.get_lead_quality_stats_map.return_value = {}
            mock_team_service.get_followup_statistics_map.return_value = {}
            mock_team_service.get_opportunity_stats_map.return_value = {}
            MockTeamService.return_value = mock_team_service

            service = SalesRankingService(mock_db)

            with patch.object(service, "_get_acceptance_amount_map", return_value={}):
                with patch.object(service, "_get_contract_and_collection_data", return_value={
                    1: {"contract_amount": 100000, "contract_count": 5, "collection_amount": 50000},
                }):
                    result = service.calculate_rankings(
                        users=[mock_user],
                        start_datetime=datetime(2026, 1, 1),
                        end_datetime=datetime(2026, 1, 31),
                        ranking_type="score",
                    )

        assert result["ranking_type"] == "score"


class TestGetContractAndCollectionData:
    """测试 _get_contract_and_collection_data 方法"""

    def test_returns_empty_when_no_user_ids(self):
        """测试无用户ID时返回空"""
        from app.services.sales_ranking_service import SalesRankingService

        mock_db = MagicMock()

        with patch("app.services.sales_ranking_service.SalesTeamService"):
            service = SalesRankingService(mock_db)
            result = service._get_contract_and_collection_data(
                user_ids=[],
                start_datetime=datetime(2026, 1, 1),
                end_datetime=datetime(2026, 1, 31),
            )

        assert result == {}

    def test_aggregates_contract_data(self):
        """测试聚合合同数据"""
        from app.services.sales_ranking_service import SalesRankingService

        mock_db = MagicMock()

        mock_contract_row = MagicMock()
        mock_contract_row.owner_id = 1
        mock_contract_row.count = 5
        mock_contract_row.contract_amount = 100000

        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.group_by.return_value.all.return_value = [
            mock_contract_row
        ]

        # Invoice query returns empty
        mock_db.query.return_value.join.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.group_by.return_value.all.return_value = []

        with patch("app.services.sales_ranking_service.SalesTeamService"):
            service = SalesRankingService(mock_db)
            result = service._get_contract_and_collection_data(
                user_ids=[1],
                start_datetime=datetime(2026, 1, 1),
                end_datetime=datetime(2026, 1, 31),
            )

        assert 1 in result
        assert result[1]["contract_amount"] == 100000
        assert result[1]["contract_count"] == 5


class TestGetAcceptanceAmountMap:
    """测试 _get_acceptance_amount_map 方法"""

    def test_returns_empty_when_no_user_ids(self):
        """测试无用户ID时返回空"""
        from app.services.sales_ranking_service import SalesRankingService

        mock_db = MagicMock()

        with patch("app.services.sales_ranking_service.SalesTeamService"):
            service = SalesRankingService(mock_db)
            result = service._get_acceptance_amount_map(
                user_ids=[],
                start_datetime=datetime(2026, 1, 1),
                end_datetime=datetime(2026, 1, 31),
            )

        assert result == {}

    def test_aggregates_acceptance_amounts(self):
        """测试聚合验收金额"""
        from app.services.sales_ranking_service import SalesRankingService

        mock_db = MagicMock()

        mock_row = MagicMock()
        mock_row.owner_id = 1
        mock_row.acceptance_amount = 50000

        mock_db.query.return_value.join.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.group_by.return_value.all.return_value = [
            mock_row
        ]

        with patch("app.services.sales_ranking_service.SalesTeamService"):
            service = SalesRankingService(mock_db)
            result = service._get_acceptance_amount_map(
                user_ids=[1],
                start_datetime=datetime(2026, 1, 1),
                end_datetime=datetime(2026, 1, 31),
            )

        assert result[1] == 50000
