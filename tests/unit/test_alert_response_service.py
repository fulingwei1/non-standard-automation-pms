# -*- coding: utf-8 -*-
"""
Tests for alert_response_service service
Covers: app/services/alert_response_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 93 lines
Batch: 3
"""

from datetime import datetime


class MockAlertRecord:
    """模拟 AlertRecord 类"""

    def __init__(
        self,
        alert_no: str,
        alert_level: str,
        triggered_at: datetime,
        acknowledged_at: datetime = None,
        handle_end_at: datetime = None,
        acknowledhed_by: int = None,
        project_id: int = None,
    ):
        self.alert_no = alert_no
        self.alert_level = alert_level
        self.triggered_at = triggered_at
        self.acknowledged_at = acknowledged_at
        self.handle_end_at = handle_end_at
        self.acknowledged_by = acknowledhed_by
        self.project_id = project_id


class MockAlertRule:
    """模拟 AlertRule 类"""

    def __init__(self, rule_type: str):
        self.rule_type = rule_type


class TestCalculateResponseTimes:
    """测试 calculate_response_times 函数"""

    def test_calculate_response_times(self):
        """测试计算响应时间"""
        from app.services.alert_response_service import calculate_response_times

        alerts = [
            MockAlertRecord(
                alert_no="ALT001",
                alert_level="WARNING",
                triggered_at=datetime(2024, 2, 1, 10, 0),
                acknowledged_at=datetime(2024, 2, 1, 11, 30),  # 1.5小时
            ),
            MockAlertRecord(
                alert_no="ALT002",
                alert_level="ERROR",
                triggered_at=datetime(2024, 2, 1, 12, 0),
                acknowledged_at=datetime(2024, 2, 1, 12, 30),  # 0.5小时
            ),
        ]

        response_times = calculate_response_times(alerts)

        assert len(response_times) == 2
        assert response_times[0]["minutes"] == 90.0
        assert response_times[0]["hours"] == 1.5
        assert response_times[1]["minutes"] == 30.0
        assert response_times[1]["hours"] == 0.5

    def test_calculate_response_times_missing_timestamps(self):
        """测试处理缺少时间戳的预警"""
        from app.services.alert_response_service import calculate_response_times

        alerts = [
            MockAlertRecord(
                alert_no="ALT001",
                alert_level="WARNING",
                triggered_at=None,
                acknowledged_at=datetime(2024, 2, 1, 11, 30),
            ),
            MockAlertRecord(
                alert_no="ALT002",
                alert_level="ERROR",
                triggered_at=datetime(2024, 2, 1, 12, 0),
                acknowledged_at=None,
            ),
        ]

        response_times = calculate_response_times(alerts)

        assert len(response_times) == 0


class TestCalculateResolveTimes:
    """测试 calculate_resolve_times 函数"""

    def test_calculate_resolve_times(self):
        """测试计算解决时间"""
        from app.services.alert_response_service import calculate_resolve_times

        alerts = [
            MockAlertRecord(
                alert_no="ALT001",
                alert_level="WARNING",
                triggered_at=datetime(2024, 2, 1, 10, 0),
                acknowledged_at=datetime(2024, 2, 1, 11, 0),
                handle_end_at=datetime(2024, 2, 1, 14, 0),  # 3小时
            ),
        ]

        resolve_times = calculate_resolve_times(alerts)

        assert len(resolve_times) == 1
        assert resolve_times[0]["hours"] == 3.0
        assert resolve_times[0]["minutes"] == 180.0


class TestCalculateResponseDistribution:
    """测试 calculate_response_distribution 函数"""

    def test_calculate_response_distribution(self):
        """测试计算响应时效分布"""
        from app.services.alert_response_service import calculate_response_distribution

        response_times = [
            {
                "alert": MockAlertRecord("ALT001", "WARNING", None),
                "minutes": 30,
                "hours": 0.5,
            },  # <1小时
            {
                "alert": MockAlertRecord("ALT002", "ERROR", None),
                "minutes": 120,
                "hours": 2.0,
            },  # 1-4小时
            {
                "alert": MockAlertRecord("ALT003", "WARNING", None),
                "minutes": 360,
                "hours": 6.0,
            },  # 4-8小时
            {
                "alert": MockAlertRecord("ALT004", "ERROR", None),
                "minutes": 600,
                "hours": 10.0,
            },  # >8小时
        ]

        distribution = calculate_response_distribution(response_times)

        assert distribution["<1小时"] == 1
        assert distribution["1-4小时"] == 1
        assert distribution["4-8小时"] == 1
        assert distribution[">8小时"] == 1


class TestCalculateLevelMetrics:
    """测试 calculate_level_metrics 函数"""

    def test_calculate_level_metrics(self):
        """测试按级别统计响应时效"""
        from app.services.alert_response_service import calculate_level_metrics

        response_times = [
            {"alert": MockAlertRecord("ALT001", "WARNING", None), "hours": 1.0},
            {"alert": MockAlertRecord("ALT002", "WARNING", None), "hours": 2.0},
            {"alert": MockAlertRecord("ALT003", "ERROR", None), "hours": 0.5},
            {"alert": MockAlertRecord("ALT004", "ERROR", None), "hours": 1.5},
        ]

        metrics = calculate_level_metrics(response_times)

        assert "WARNING" in metrics
        assert "ERROR" in metrics

        assert metrics["WARNING"]["count"] == 2
        assert metrics["WARNING"]["avg_hours"] == 1.5
        assert metrics["WARNING"]["min_hours"] == 1.0
        assert metrics["WARNING"]["max_hours"] == 2.0

        assert metrics["ERROR"]["count"] == 2
        assert metrics["ERROR"]["avg_hours"] == 1.0


class TestCalculateTypeMetrics:
    """测试 calculate_type_metrics 函数"""

    def test_calculate_type_metrics(self):
        """测试按类型统计响应时效"""
        from app.services.alert_response_service import calculate_type_metrics

        alerts = [
            MockAlertRecord(
                alert_no="ALT001",
                alert_level="WARNING",
                triggered_at=datetime(2024, 2, 1, 10, 0),
                acknowledged_at=datetime(2024, 2, 1, 11, 0),
            ),
        ]

        alerts[0].rule = MockAlertRule("PROGRESS")

        alerts.append(
            MockAlertRecord(
                alert_no="ALT002",
                alert_level="ERROR",
                triggered_at=datetime(2024, 2, 1, 12, 0),
                acknowledged_at=datetime(2024, 2, 1, 13, 0),
            )
        )
        alerts[1].rule = MockAlertRule("COST")

        response_times = [
            {"alert": alerts[0], "hours": 1.0},
            {"alert": alerts[1], "hours": 1.5},
        ]

        metrics = calculate_type_metrics(response_times)

        assert "PROGRESS" in metrics
        assert "COST" in metrics


class TestGenerateResponseRankings:
    """测试 generate_response_rankings 函数"""

    def test_generate_response_rankings(self):
        """测试生成响应时效排行榜"""
        from app.services.alert_response_service import generate_response_rankings

        project_metrics = {
            "Project A": {
                "project_id": 1,
                "count": 10,
                "avg_hours": 0.5,
            },
            "Project B": {
                "project_id": 2,
                "count": 8,
                "avg_hours": 2.5,
            },
            "Project C": {
                "project_id": 3,
                "count": 15,
                "avg_hours": 1.0,
            },
        }

        handler_metrics = {
            "User A": {
                "user_id": 1,
                "count": 5,
                "avg_hours": 0.3,
            },
            "User B": {
                "user_id": 2,
                "count": 7,
                "avg_hours": 1.5,
            },
        }

        rankings = generate_response_rankings(project_metrics, handler_metrics)

        assert "fastest_projects" in rankings
        assert "slowest_projects" in rankings
        assert "fastest_handlers" in rankings
        assert "slowest_handlers" in rankings

        assert rankings["fastest_projects"][0]["project_name"] == "Project A"
        assert rankings["slowest_projects"][0]["project_name"] == "Project B"
        assert rankings["fastest_handlers"][0]["handler_name"] == "User A"
        assert rankings["slowest_handlers"][0]["handler_name"] == "User B"
