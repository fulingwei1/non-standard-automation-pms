# -*- coding: utf-8 -*-
"""
AlertResponseService 综合单元测试

测试覆盖:
- calculate_response_times: 计算响应时间
- calculate_resolve_times: 计算解决时间
- calculate_response_distribution: 计算响应时效分布
- calculate_level_metrics: 按级别统计响应时效
- calculate_type_metrics: 按类型统计响应时效
- calculate_project_metrics: 按项目统计响应时效
- calculate_handler_metrics: 按责任人统计响应时效
- generate_response_rankings: 生成响应时效排行榜
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest


class TestCalculateResponseTimes:
    """测试 calculate_response_times 函数"""

    def test_returns_empty_list_when_no_alerts(self):
        """测试无预警时返回空列表"""
        from app.services.alert_response_service import calculate_response_times

        result = calculate_response_times([])

        assert result == []

    def test_calculates_response_time_correctly(self):
        """测试正确计算响应时间"""
        from app.services.alert_response_service import calculate_response_times

        mock_alert = MagicMock()
        mock_alert.triggered_at = datetime.now() - timedelta(hours=2)
        mock_alert.acknowledged_at = datetime.now()

        result = calculate_response_times([mock_alert])

        assert len(result) == 1
        assert abs(result[0]["minutes"] - 120) < 1  # 约120分钟
        assert abs(result[0]["hours"] - 2) < 0.1  # 约2小时

    def test_skips_alerts_without_timestamps(self):
        """测试跳过无时间戳的预警"""
        from app.services.alert_response_service import calculate_response_times

        mock_alert1 = MagicMock()
        mock_alert1.triggered_at = None
        mock_alert1.acknowledged_at = datetime.now()

        mock_alert2 = MagicMock()
        mock_alert2.triggered_at = datetime.now()
        mock_alert2.acknowledged_at = None

        result = calculate_response_times([mock_alert1, mock_alert2])

        assert result == []

    def test_handles_multiple_alerts(self):
        """测试处理多个预警"""
        from app.services.alert_response_service import calculate_response_times

        now = datetime.now()

        mock_alert1 = MagicMock()
        mock_alert1.triggered_at = now - timedelta(hours=1)
        mock_alert1.acknowledged_at = now

        mock_alert2 = MagicMock()
        mock_alert2.triggered_at = now - timedelta(hours=3)
        mock_alert2.acknowledged_at = now

        result = calculate_response_times([mock_alert1, mock_alert2])

        assert len(result) == 2


class TestCalculateResolveTimes:
    """测试 calculate_resolve_times 函数"""

    def test_returns_empty_list_when_no_alerts(self):
        """测试无预警时返回空列表"""
        from app.services.alert_response_service import calculate_resolve_times

        result = calculate_resolve_times([])

        assert result == []

    def test_calculates_resolve_time_correctly(self):
        """测试正确计算解决时间"""
        from app.services.alert_response_service import calculate_resolve_times

        mock_alert = MagicMock()
        mock_alert.acknowledged_at = datetime.now() - timedelta(hours=4)
        mock_alert.handle_end_at = datetime.now()

        result = calculate_resolve_times([mock_alert])

        assert len(result) == 1
        assert abs(result[0]["hours"] - 4) < 0.1

    def test_skips_alerts_without_timestamps(self):
        """测试跳过无时间戳的预警"""
        from app.services.alert_response_service import calculate_resolve_times

        mock_alert = MagicMock()
        mock_alert.acknowledged_at = None
        mock_alert.handle_end_at = datetime.now()

        result = calculate_resolve_times([mock_alert])

        assert result == []


class TestCalculateResponseDistribution:
    """测试 calculate_response_distribution 函数"""

    def test_returns_zero_distribution_when_no_data(self):
        """测试无数据时返回零分布"""
        from app.services.alert_response_service import calculate_response_distribution

        result = calculate_response_distribution([])

        assert result["<1小时"] == 0
        assert result["1-4小时"] == 0
        assert result["4-8小时"] == 0
        assert result[">8小时"] == 0

    def test_categorizes_less_than_1_hour(self):
        """测试分类小于1小时"""
        from app.services.alert_response_service import calculate_response_distribution

        result = calculate_response_distribution([{"hours": 0.5}])

        assert result["<1小时"] == 1

    def test_categorizes_1_to_4_hours(self):
        """测试分类1-4小时"""
        from app.services.alert_response_service import calculate_response_distribution

        result = calculate_response_distribution([{"hours": 2.5}])

        assert result["1-4小时"] == 1

    def test_categorizes_4_to_8_hours(self):
        """测试分类4-8小时"""
        from app.services.alert_response_service import calculate_response_distribution

        result = calculate_response_distribution([{"hours": 6}])

        assert result["4-8小时"] == 1

    def test_categorizes_more_than_8_hours(self):
        """测试分类大于8小时"""
        from app.services.alert_response_service import calculate_response_distribution

        result = calculate_response_distribution([{"hours": 10}])

        assert result[">8小时"] == 1

    def test_handles_multiple_entries(self):
        """测试处理多个条目"""
        from app.services.alert_response_service import calculate_response_distribution

        data = [
            {"hours": 0.5},
            {"hours": 2},
            {"hours": 5},
            {"hours": 12},
        ]

        result = calculate_response_distribution(data)

        assert result["<1小时"] == 1
        assert result["1-4小时"] == 1
        assert result["4-8小时"] == 1
        assert result[">8小时"] == 1


class TestCalculateLevelMetrics:
    """测试 calculate_level_metrics 函数"""

    def test_returns_empty_when_no_data(self):
        """测试无数据时返回空"""
        from app.services.alert_response_service import calculate_level_metrics

        result = calculate_level_metrics([])

        assert result == {}

    def test_groups_by_level(self):
        """测试按级别分组"""
        from app.services.alert_response_service import calculate_level_metrics

        mock_alert1 = MagicMock()
        mock_alert1.alert_level = "WARNING"

        mock_alert2 = MagicMock()
        mock_alert2.alert_level = "CRITICAL"

        data = [
            {"alert": mock_alert1, "hours": 2},
            {"alert": mock_alert2, "hours": 4},
        ]

        result = calculate_level_metrics(data)

        assert "WARNING" in result
        assert "CRITICAL" in result
        assert result["WARNING"]["count"] == 1
        assert result["CRITICAL"]["count"] == 1

    def test_calculates_statistics(self):
        """测试计算统计指标"""
        from app.services.alert_response_service import calculate_level_metrics

        mock_alert1 = MagicMock()
        mock_alert1.alert_level = "WARNING"

        mock_alert2 = MagicMock()
        mock_alert2.alert_level = "WARNING"

        data = [
            {"alert": mock_alert1, "hours": 2},
            {"alert": mock_alert2, "hours": 4},
        ]

        result = calculate_level_metrics(data)

        assert result["WARNING"]["count"] == 2
        assert result["WARNING"]["avg_hours"] == 3
        assert result["WARNING"]["min_hours"] == 2
        assert result["WARNING"]["max_hours"] == 4

    def test_handles_unknown_level(self):
        """测试处理未知级别"""
        from app.services.alert_response_service import calculate_level_metrics

        mock_alert = MagicMock()
        mock_alert.alert_level = None

        data = [{"alert": mock_alert, "hours": 1}]

        result = calculate_level_metrics(data)

        assert "UNKNOWN" in result


class TestCalculateTypeMetrics:
    """测试 calculate_type_metrics 函数"""

    def test_returns_empty_when_no_data(self):
        """测试无数据时返回空"""
        from app.services.alert_response_service import calculate_type_metrics

        result = calculate_type_metrics([])

        assert result == {}

    def test_groups_by_rule_type(self):
        """测试按规则类型分组"""
        from app.services.alert_response_service import calculate_type_metrics

        mock_rule = MagicMock()
        mock_rule.rule_type = "PROGRESS_DELAY"

        mock_alert = MagicMock()
        mock_alert.rule = mock_rule

        data = [{"alert": mock_alert, "hours": 2}]

        result = calculate_type_metrics(data)

        assert "PROGRESS_DELAY" in result

    def test_handles_missing_rule(self):
        """测试处理缺失规则"""
        from app.services.alert_response_service import calculate_type_metrics

        mock_alert = MagicMock()
        mock_alert.rule = None

        data = [{"alert": mock_alert, "hours": 1}]

        result = calculate_type_metrics(data)

        assert "UNKNOWN" in result


class TestCalculateProjectMetrics:
    """测试 calculate_project_metrics 函数"""

    def test_returns_empty_when_no_project_data(self):
        """测试无项目数据时返回空"""
        from app.services.alert_response_service import calculate_project_metrics

        mock_db = MagicMock()
        mock_alert = MagicMock()
        mock_alert.project_id = None

        data = [{"alert": mock_alert, "hours": 1}]

        result = calculate_project_metrics(data, mock_db)

        assert result == {}

    def test_groups_by_project(self):
        """测试按项目分组"""
        from app.services.alert_response_service import calculate_project_metrics

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.project_name = "测试项目"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        mock_alert = MagicMock()
        mock_alert.project_id = 1

        data = [{"alert": mock_alert, "hours": 2}]

        result = calculate_project_metrics(data, mock_db)

        assert "测试项目" in result
        assert result["测试项目"]["project_id"] == 1

    def test_calculates_project_statistics(self):
        """测试计算项目统计"""
        from app.services.alert_response_service import calculate_project_metrics

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.project_name = "测试项目"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        mock_alert1 = MagicMock()
        mock_alert1.project_id = 1

        mock_alert2 = MagicMock()
        mock_alert2.project_id = 1

        data = [
            {"alert": mock_alert1, "hours": 2},
            {"alert": mock_alert2, "hours": 4},
        ]

        result = calculate_project_metrics(data, mock_db)

        assert result["测试项目"]["count"] == 2
        assert result["测试项目"]["avg_hours"] == 3


class TestCalculateHandlerMetrics:
    """测试 calculate_handler_metrics 函数"""

    def test_returns_empty_when_no_handler_data(self):
        """测试无责任人数据时返回空"""
        from app.services.alert_response_service import calculate_handler_metrics

        mock_db = MagicMock()
        mock_alert = MagicMock()
        mock_alert.acknowledged_by = None

        data = [{"alert": mock_alert, "hours": 1}]

        result = calculate_handler_metrics(data, mock_db)

        assert result == {}

    def test_groups_by_handler(self):
        """测试按责任人分组"""
        from app.services.alert_response_service import calculate_handler_metrics

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.username = "张三"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        mock_alert = MagicMock()
        mock_alert.acknowledged_by = 1

        data = [{"alert": mock_alert, "hours": 2}]

        result = calculate_handler_metrics(data, mock_db)

        assert "张三" in result
        assert result["张三"]["user_id"] == 1


class TestGenerateResponseRankings:
    """测试 generate_response_rankings 函数"""

    def test_returns_empty_rankings_when_no_data(self):
        """测试无数据时返回空排行"""
        from app.services.alert_response_service import generate_response_rankings

        result = generate_response_rankings({}, {})

        assert result["fastest_projects"] == []
        assert result["slowest_projects"] == []
        assert result["fastest_handlers"] == []
        assert result["slowest_handlers"] == []

    def test_returns_top_5_fastest_and_slowest(self):
        """测试返回前5最快和最慢"""
        from app.services.alert_response_service import generate_response_rankings

        project_metrics = {}
        for i in range(10):
            project_metrics[f"项目{i}"] = {
                "project_id": i,
                "avg_hours": i * 0.5,
                "count": 10,
            }

        handler_metrics = {}
        for i in range(10):
            handler_metrics[f"用户{i}"] = {
                "user_id": i,
                "avg_hours": i * 0.5,
                "count": 10,
            }

        result = generate_response_rankings(project_metrics, handler_metrics)

        assert len(result["fastest_projects"]) == 5
        assert len(result["slowest_projects"]) == 5
        assert len(result["fastest_handlers"]) == 5
        assert len(result["slowest_handlers"]) == 5

    def test_fastest_has_lowest_avg_hours(self):
        """测试最快有最低平均时间"""
        from app.services.alert_response_service import generate_response_rankings

        project_metrics = {
            "项目A": {"project_id": 1, "avg_hours": 1, "count": 5},
            "项目B": {"project_id": 2, "avg_hours": 5, "count": 5},
        }

        result = generate_response_rankings(project_metrics, {})

        assert result["fastest_projects"][0]["project_name"] == "项目A"
        assert result["slowest_projects"][0]["project_name"] == "项目B"

    def test_rounds_avg_hours(self):
        """测试四舍五入平均时间"""
        from app.services.alert_response_service import generate_response_rankings

        project_metrics = {
            "项目A": {"project_id": 1, "avg_hours": 1.234567, "count": 5},
        }

        result = generate_response_rankings(project_metrics, {})

        assert result["fastest_projects"][0]["avg_hours"] == 1.23
