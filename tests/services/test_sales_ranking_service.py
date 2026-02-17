# -*- coding: utf-8 -*-
"""
SalesRankingService 单元测试 - N5组
覆盖：配置管理、指标验证、排名算法、边界情况
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.services.sales_ranking_service import SalesRankingService


def _make_user(uid=1, name="张三", username="zhangsan", department="销售部"):
    u = MagicMock()
    u.id = uid
    u.real_name = name
    u.username = username
    u.department = department
    return u


def _make_db_query(db, first_result=None, all_results=None):
    q = MagicMock()
    q.filter.return_value = q
    q.order_by.return_value = q
    q.join.return_value = q
    q.group_by.return_value = q
    q.first.return_value = first_result
    q.all.return_value = all_results or []
    db.query.return_value = q
    return q


class TestValidateMetrics(unittest.TestCase):
    """_validate_metrics 指标验证逻辑"""

    def setUp(self):
        self.db = MagicMock()
        with patch('app.services.sales_ranking_service.SalesTeamService'):
            self.svc = SalesRankingService(self.db)

    def _valid_metrics(self):
        """返回一组合法指标（权重和=1.0，primary=0.8）"""
        return [
            {"key": "contract_amount", "label": "合同金额", "weight": 0.4,
             "data_source": "contract_amount", "is_primary": True},
            {"key": "acceptance_amount", "label": "验收金额", "weight": 0.2,
             "data_source": "acceptance_amount", "is_primary": True},
            {"key": "collection_amount", "label": "回款金额", "weight": 0.2,
             "data_source": "collection_amount", "is_primary": True},
            {"key": "opportunity_count", "label": "商机数量", "weight": 0.2,
             "data_source": "opportunity_count", "is_primary": False},
        ]

    def test_valid_metrics_pass(self):
        """合法指标配置应通过验证"""
        result = self.svc._validate_metrics(self._valid_metrics())
        self.assertEqual(len(result), 4)

    def test_empty_metrics_raises(self):
        """空指标列表应抛出 ValueError"""
        with self.assertRaises(ValueError) as ctx:
            self.svc._validate_metrics([])
        self.assertIn("至少", str(ctx.exception))

    def test_duplicate_key_raises(self):
        """重复的 key 应抛出 ValueError"""
        metrics = self._valid_metrics()
        metrics.append({"key": "contract_amount", "label": "重复",
                        "weight": 0.01, "data_source": "contract_amount"})
        with self.assertRaises(ValueError):
            self.svc._validate_metrics(metrics)

    def test_invalid_data_source_raises(self):
        """不支持的 data_source 应抛出 ValueError"""
        metrics = self._valid_metrics()
        metrics[3]["data_source"] = "invalid_source_xyz"
        with self.assertRaises(ValueError) as ctx:
            self.svc._validate_metrics(metrics)
        self.assertIn("invalid_source_xyz", str(ctx.exception))

    def test_weight_zero_raises(self):
        """权重<=0 应抛出 ValueError"""
        metrics = self._valid_metrics()
        metrics[0]["weight"] = 0.0
        with self.assertRaises(ValueError) as ctx:
            self.svc._validate_metrics(metrics)
        self.assertIn("权重", str(ctx.exception))

    def test_total_weight_not_one_raises(self):
        """总权重不等于1.0应抛出 ValueError"""
        metrics = self._valid_metrics()
        metrics[0]["weight"] = 0.3  # total = 0.3+0.2+0.2+0.2 = 0.9
        with self.assertRaises(ValueError) as ctx:
            self.svc._validate_metrics(metrics)
        self.assertIn("1.0", str(ctx.exception))

    def test_primary_weight_not_08_raises(self):
        """主要指标权重之和不等于0.8应抛出 ValueError"""
        # primary=0.3+0.2+0.2=0.7, total=1.0
        metrics = [
            {"key": "contract_amount", "label": "合同金额", "weight": 0.3,
             "data_source": "contract_amount", "is_primary": True},
            {"key": "acceptance_amount", "label": "验收金额", "weight": 0.2,
             "data_source": "acceptance_amount", "is_primary": True},
            {"key": "collection_amount", "label": "回款金额", "weight": 0.2,
             "data_source": "collection_amount", "is_primary": True},
            {"key": "opportunity_count", "label": "商机数量", "weight": 0.3,
             "data_source": "opportunity_count", "is_primary": False},
        ]
        with self.assertRaises(ValueError) as ctx:
            self.svc._validate_metrics(metrics)
        self.assertIn("0.8", str(ctx.exception))

    def test_metrics_sorted_by_weight_desc(self):
        """验证后指标应按权重降序排列"""
        result = self.svc._validate_metrics(self._valid_metrics())
        weights = [m["weight"] for m in result]
        self.assertEqual(weights, sorted(weights, reverse=True))

    def test_missing_key_raises(self):
        """缺少 key 的指标应抛出 ValueError"""
        metrics = self._valid_metrics()
        metrics[0]["key"] = None
        with self.assertRaises(ValueError):
            self.svc._validate_metrics(metrics)


class TestGetActiveConfig(unittest.TestCase):
    """get_active_config 配置获取逻辑"""

    def setUp(self):
        self.db = MagicMock()
        with patch('app.services.sales_ranking_service.SalesTeamService'):
            self.svc = SalesRankingService(self.db)

    def test_returns_existing_config(self):
        """已有配置时应直接返回"""
        existing = MagicMock(metrics=SalesRankingService.DEFAULT_METRICS)
        _make_db_query(self.db, first_result=existing)

        result = self.svc.get_active_config()
        self.assertEqual(result, existing)

    def test_creates_default_when_no_config(self):
        """无配置时应创建默认配置并返回"""
        q = MagicMock()
        q.order_by.return_value = q
        q.first.return_value = None
        self.db.query.return_value = q

        with patch('app.services.sales_ranking_service.save_obj') as mock_save:
            result = self.svc.get_active_config()
            mock_save.assert_called_once()
            self.assertIsNotNone(result)
            self.assertEqual(result.metrics, self.svc.DEFAULT_METRICS)


class TestSaveConfig(unittest.TestCase):
    """save_config 保存配置"""

    def setUp(self):
        self.db = MagicMock()
        with patch('app.services.sales_ranking_service.SalesTeamService'):
            self.svc = SalesRankingService(self.db)

    def _valid_metrics(self):
        return [
            {"key": "contract_amount", "label": "合同金额", "weight": 0.4,
             "data_source": "contract_amount", "is_primary": True},
            {"key": "acceptance_amount", "label": "验收金额", "weight": 0.2,
             "data_source": "acceptance_amount", "is_primary": True},
            {"key": "collection_amount", "label": "回款金额", "weight": 0.2,
             "data_source": "collection_amount", "is_primary": True},
            {"key": "opportunity_count", "label": "商机", "weight": 0.2,
             "data_source": "opportunity_count", "is_primary": False},
        ]

    def test_save_config_success(self):
        """合法配置应能保存"""
        with patch('app.services.sales_ranking_service.save_obj') as mock_save:
            result = self.svc.save_config(self._valid_metrics(), operator_id=1)
            mock_save.assert_called_once()
            self.assertIsNotNone(result)

    def test_save_config_invalid_raises(self):
        """非法配置应在保存前抛出异常"""
        with self.assertRaises(ValueError):
            self.svc.save_config([])


class TestCalculateRankings(unittest.TestCase):
    """calculate_rankings 排名算法"""

    def setUp(self):
        self.db = MagicMock()
        with patch('app.services.sales_ranking_service.SalesTeamService') as MockTeam:
            self.mock_team = MockTeam.return_value
            self.svc = SalesRankingService(self.db)

    def test_empty_users_returns_empty_rankings(self):
        """无用户时返回空排名"""
        q = MagicMock()
        q.order_by.return_value = q
        q.first.return_value = MagicMock(metrics=SalesRankingService.DEFAULT_METRICS)
        self.db.query.return_value = q

        result = self.svc.calculate_rankings(
            users=[],
            start_datetime=datetime(2025, 1, 1),
            end_datetime=datetime(2025, 12, 31),
        )
        self.assertEqual(result["rankings"], [])
        self.assertEqual(result["ranking_type"], "score")

    def test_single_user_rank_is_1(self):
        """单用户时排名应为第1"""
        user = _make_user(uid=1)
        config = MagicMock(metrics=SalesRankingService.DEFAULT_METRICS)

        q = MagicMock()
        q.order_by.return_value = q
        q.first.return_value = config
        q.group_by.return_value = q
        q.filter.return_value = q
        q.join.return_value = q
        q.all.return_value = []
        self.db.query.return_value = q

        self.mock_team.get_lead_quality_stats_map.return_value = {}
        self.mock_team.get_followup_statistics_map.return_value = {}
        self.mock_team.get_opportunity_stats_map.return_value = {}

        result = self.svc.calculate_rankings(
            users=[user],
            start_datetime=datetime(2025, 1, 1),
            end_datetime=datetime(2025, 12, 31),
        )
        self.assertEqual(len(result["rankings"]), 1)
        self.assertEqual(result["rankings"][0]["rank"], 1)

    def test_multiple_users_ranked_by_score(self):
        """多用户时按分数排序"""
        users = [_make_user(uid=i, name=f"user{i}") for i in range(1, 4)]
        config = MagicMock(metrics=SalesRankingService.DEFAULT_METRICS)

        q = MagicMock()
        q.order_by.return_value = q
        q.first.return_value = config
        q.group_by.return_value = q
        q.filter.return_value = q
        q.join.return_value = q
        q.all.return_value = []
        self.db.query.return_value = q

        self.mock_team.get_lead_quality_stats_map.return_value = {}
        self.mock_team.get_followup_statistics_map.return_value = {}
        self.mock_team.get_opportunity_stats_map.return_value = {
            1: {"opportunity_count": 10, "pipeline_amount": 500000.0, "avg_est_margin": 0.2},
            2: {"opportunity_count": 5, "pipeline_amount": 200000.0, "avg_est_margin": 0.15},
            3: {"opportunity_count": 1, "pipeline_amount": 10000.0, "avg_est_margin": 0.1},
        }

        result = self.svc.calculate_rankings(
            users=users,
            start_datetime=datetime(2025, 1, 1),
            end_datetime=datetime(2025, 12, 31),
            ranking_type="score",
        )
        ranks = [e["rank"] for e in result["rankings"]]
        self.assertEqual(sorted(ranks), [1, 2, 3])

    def test_unknown_ranking_type_defaults_to_score(self):
        """未知排名类型默认按 score 排序"""
        user = _make_user()
        config = MagicMock(metrics=SalesRankingService.DEFAULT_METRICS)

        q = MagicMock()
        q.order_by.return_value = q
        q.first.return_value = config
        q.group_by.return_value = q
        q.filter.return_value = q
        q.join.return_value = q
        q.all.return_value = []
        self.db.query.return_value = q

        self.mock_team.get_lead_quality_stats_map.return_value = {}
        self.mock_team.get_followup_statistics_map.return_value = {}
        self.mock_team.get_opportunity_stats_map.return_value = {}

        result = self.svc.calculate_rankings(
            users=[user],
            start_datetime=datetime(2025, 1, 1),
            end_datetime=datetime(2025, 12, 31),
            ranking_type="nonexistent_type",
        )
        self.assertEqual(result["ranking_type"], "score")


class TestGetAcceptanceAmountMap(unittest.TestCase):
    """_get_acceptance_amount_map 验收金额统计"""

    def setUp(self):
        self.db = MagicMock()
        with patch('app.services.sales_ranking_service.SalesTeamService'):
            self.svc = SalesRankingService(self.db)

    def test_empty_user_ids_returns_empty(self):
        """无用户ID时返回空dict"""
        result = self.svc._get_acceptance_amount_map(
            [], datetime(2025, 1, 1), datetime(2025, 12, 31)
        )
        self.assertEqual(result, {})

    def test_with_user_ids_queries_db(self):
        """有用户ID时应查询数据库"""
        q = MagicMock()
        q.join.return_value = q
        q.filter.return_value = q
        q.group_by.return_value = q
        row = MagicMock(owner_id=1, acceptance_amount=50000.0)
        q.all.return_value = [row]
        self.db.query.return_value = q

        result = self.svc._get_acceptance_amount_map(
            [1], datetime(2025, 1, 1), datetime(2025, 12, 31)
        )
        self.assertIn(1, result)
        self.assertEqual(result[1], 50000.0)


if __name__ == "__main__":
    unittest.main()
