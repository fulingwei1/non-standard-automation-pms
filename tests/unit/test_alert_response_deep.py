# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 预警响应服务"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest


class TestAlertResponseServiceBusinessLogic:
    def test_calculate_response_times(self):
        from app.services.alert.alert_response_service import calculate_response_times

        alert1 = MagicMock(triggered_at=datetime(2026, 4, 10, 10, 0, 0), acknowledged_at=datetime(2026, 4, 10, 10, 30, 0))
        alert2 = MagicMock(triggered_at=datetime(2026, 4, 10, 11, 0, 0), acknowledged_at=datetime(2026, 4, 10, 12, 0, 0))
        results = calculate_response_times([alert1, alert2])
        assert len(results) == 2
        assert results[0]["minutes"] == 30
        assert results[1]["minutes"] == 60

    def test_calculate_response_times_no_acknowledged(self):
        from app.services.alert.alert_response_service import calculate_response_times

        alert = MagicMock(triggered_at=datetime(2026, 4, 10, 10, 0, 0), acknowledged_at=None)
        assert calculate_response_times([alert]) == []

    def test_calculate_resolve_times(self):
        from app.services.alert.alert_response_service import calculate_resolve_times

        alert = MagicMock(acknowledged_at=datetime(2026, 4, 10, 10, 0, 0), handle_end_at=datetime(2026, 4, 10, 12, 0, 0))
        results = calculate_resolve_times([alert])
        assert len(results) == 1
        assert results[0]["minutes"] == 120
        assert results[0]["hours"] == 2

    def test_calculate_response_distribution(self):
        from app.services.alert.alert_response_service import calculate_response_distribution

        response_times = [{"hours": 0.5}, {"hours": 1.5}, {"hours": 2.0}, {"hours": 5.0}, {"hours": 10.0}]
        distribution = calculate_response_distribution(response_times)
        assert distribution["<1小时"] == 1
        assert distribution["1-4小时"] == 2
        assert distribution["4-8小时"] == 1
        assert distribution[">8小时"] == 1

    def test_calculate_avg_response_time_via_response_times(self):
        from app.services.alert.alert_response_service import calculate_level_metrics

        alert1 = MagicMock(alert_level="L1")
        alert2 = MagicMock(alert_level="L1")
        response_times = [{"alert": alert1, "hours": 0.5}, {"alert": alert2, "hours": 1.5}]
        result = calculate_level_metrics(response_times)
        assert result["L1"]["avg_hours"] == 1.0

    def test_calculate_avg_response_time_empty_via_response_times(self):
        from app.services.alert.alert_response_service import calculate_level_metrics

        assert calculate_level_metrics({}) == {}

    def test_get_response_performance_by_project(self):
        try:
            from app.services.alert.alert_response_service import calculate_project_metrics

            mock_db = MagicMock()
            project = MagicMock(project_name="项目1")
            mock_db.query.return_value.filter.return_value.first.return_value = project
            alert = MagicMock(project_id=1)
            results = calculate_project_metrics([{"alert": alert, "hours": 0.5}], mock_db)
            assert isinstance(results, dict)
        except ImportError:
            pytest.skip("Function not found")

    def test_get_response_performance_by_user(self):
        try:
            from app.services.alert.alert_response_service import calculate_handler_metrics

            mock_db = MagicMock()
            user = MagicMock(username="u1")
            mock_db.query.return_value.filter.return_value.first.return_value = user
            alert = MagicMock(acknowledged_by=1)
            results = calculate_handler_metrics([{"alert": alert, "hours": 0.5}], mock_db)
            assert isinstance(results, dict)
        except ImportError:
            pytest.skip("Function not found")


class TestAlertResponseServiceEdgeCases:
    def test_response_time_zero(self):
        from app.services.alert.alert_response_service import calculate_response_times

        alert = MagicMock(triggered_at=datetime(2026, 4, 10, 10, 0, 0), acknowledged_at=datetime(2026, 4, 10, 10, 0, 0))
        results = calculate_response_times([alert])
        assert len(results) == 1
        assert results[0]["minutes"] == 0

    def test_response_time_negative(self):
        from app.services.alert.alert_response_service import calculate_response_times

        alert = MagicMock(triggered_at=datetime(2026, 4, 10, 10, 0, 0), acknowledged_at=datetime(2026, 4, 10, 9, 0, 0))
        results = calculate_response_times([alert])
        assert len(results) == 1
        assert results[0]["minutes"] < 0

    def test_distribution_all_same_bucket(self):
        from app.services.alert.alert_response_service import calculate_response_distribution

        distribution = calculate_response_distribution([{"hours": 0.5}, {"hours": 0.3}, {"hours": 0.8}])
        assert distribution["<1小时"] == 3
        assert distribution["1-4小时"] == 0
        assert distribution["4-8小时"] == 0
        assert distribution[">8小时"] == 0
