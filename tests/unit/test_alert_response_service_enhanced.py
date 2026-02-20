# -*- coding: utf-8 -*-
"""
AlertResponseService 增强测试 - 提升覆盖率到60%+
目标：补充响应时间计算、分布统计、排行榜生成等核心功能测试
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from app.services import alert_response_service
from app.services.alert_response_service import AlertResponseService
from app.models.alert import AlertRecord
from app.models.project import Project
from app.models.user import User


@pytest.fixture
def mock_db():
    """Mock 数据库会话"""
    return MagicMock()


@pytest.fixture
def service(mock_db):
    """创建服务实例"""
    return AlertResponseService(db=mock_db)


@pytest.fixture
def mock_alert():
    """创建 Mock 告警记录"""
    def _create_alert(**kwargs):
        alert = MagicMock(spec=AlertRecord)
        alert.id = kwargs.get('id', 1)
        alert.alert_level = kwargs.get('alert_level', 'WARNING')
        alert.triggered_at = kwargs.get('triggered_at')
        alert.acknowledged_at = kwargs.get('acknowledged_at')
        alert.handle_end_at = kwargs.get('handle_end_at')
        alert.project_id = kwargs.get('project_id')
        alert.acknowledged_by = kwargs.get('acknowledged_by')
        
        # Mock rule
        rule = MagicMock()
        rule.rule_type = kwargs.get('rule_type', 'project_delay')
        alert.rule = rule
        
        return alert
    return _create_alert


class TestCalculateResponseTimes:
    """测试计算响应时间"""

    def test_calculate_response_times_empty_list(self):
        """测试空列表"""
        result = alert_response_service.calculate_response_times([])
        
        assert result == []

    def test_calculate_response_times_single_alert(self, mock_alert):
        """测试单个告警"""
        base_time = datetime(2024, 1, 1, 8, 0, 0)
        alert = mock_alert(
            triggered_at=base_time,
            acknowledged_at=base_time + timedelta(minutes=30)
        )
        
        result = alert_response_service.calculate_response_times([alert])
        
        assert len(result) == 1
        assert result[0]['minutes'] == 30
        assert result[0]['hours'] == 0.5
        assert result[0]['alert'] == alert

    def test_calculate_response_times_multiple_alerts(self, mock_alert):
        """测试多个告警"""
        base_time = datetime(2024, 1, 1, 8, 0, 0)
        alerts = [
            mock_alert(triggered_at=base_time, acknowledged_at=base_time + timedelta(minutes=15)),
            mock_alert(triggered_at=base_time, acknowledged_at=base_time + timedelta(minutes=60)),
            mock_alert(triggered_at=base_time, acknowledged_at=base_time + timedelta(hours=2)),
        ]
        
        result = alert_response_service.calculate_response_times(alerts)
        
        assert len(result) == 3
        assert result[0]['minutes'] == 15
        assert result[1]['minutes'] == 60
        assert result[2]['hours'] == 2

    def test_calculate_response_times_missing_triggered_at(self, mock_alert):
        """测试缺少triggered_at"""
        alert = mock_alert(
            triggered_at=None,
            acknowledged_at=datetime.now()
        )
        
        result = alert_response_service.calculate_response_times([alert])
        
        assert result == []

    def test_calculate_response_times_missing_acknowledged_at(self, mock_alert):
        """测试缺少acknowledged_at"""
        alert = mock_alert(
            triggered_at=datetime.now(),
            acknowledged_at=None
        )
        
        result = alert_response_service.calculate_response_times([alert])
        
        assert result == []


class TestCalculateResolveTimes:
    """测试计算解决时间"""

    def test_calculate_resolve_times_empty_list(self):
        """测试空列表"""
        result = alert_response_service.calculate_resolve_times([])
        
        assert result == []

    def test_calculate_resolve_times_single_alert(self, mock_alert):
        """测试单个告警"""
        base_time = datetime(2024, 1, 1, 8, 0, 0)
        alert = mock_alert(
            acknowledged_at=base_time,
            handle_end_at=base_time + timedelta(hours=2)
        )
        
        result = alert_response_service.calculate_resolve_times([alert])
        
        assert len(result) == 1
        assert result[0]['minutes'] == 120
        assert result[0]['hours'] == 2

    def test_calculate_resolve_times_missing_times(self, mock_alert):
        """测试缺少时间字段"""
        alert1 = mock_alert(acknowledged_at=None, handle_end_at=datetime.now())
        alert2 = mock_alert(acknowledged_at=datetime.now(), handle_end_at=None)
        
        result = alert_response_service.calculate_resolve_times([alert1, alert2])
        
        assert result == []


class TestCalculateResponseDistribution:
    """测试计算响应时效分布"""

    def test_calculate_distribution_empty_list(self):
        """测试空列表"""
        result = alert_response_service.calculate_response_distribution([])
        
        assert result['<1小时'] == 0
        assert result['1-4小时'] == 0
        assert result['4-8小时'] == 0
        assert result['>8小时'] == 0

    def test_calculate_distribution_under_1_hour(self):
        """测试<1小时"""
        response_times = [
            {'alert': MagicMock(), 'minutes': 30, 'hours': 0.5},
            {'alert': MagicMock(), 'minutes': 45, 'hours': 0.75},
        ]
        
        result = alert_response_service.calculate_response_distribution(response_times)
        
        assert result['<1小时'] == 2
        assert result['1-4小时'] == 0

    def test_calculate_distribution_1_to_4_hours(self):
        """测试1-4小时"""
        response_times = [
            {'alert': MagicMock(), 'minutes': 90, 'hours': 1.5},
            {'alert': MagicMock(), 'minutes': 180, 'hours': 3},
        ]
        
        result = alert_response_service.calculate_response_distribution(response_times)
        
        assert result['<1小时'] == 0
        assert result['1-4小时'] == 2
        assert result['4-8小时'] == 0

    def test_calculate_distribution_4_to_8_hours(self):
        """测试4-8小时"""
        response_times = [
            {'alert': MagicMock(), 'minutes': 300, 'hours': 5},
            {'alert': MagicMock(), 'minutes': 420, 'hours': 7},
        ]
        
        result = alert_response_service.calculate_response_distribution(response_times)
        
        assert result['4-8小时'] == 2

    def test_calculate_distribution_over_8_hours(self):
        """测试>8小时"""
        response_times = [
            {'alert': MagicMock(), 'minutes': 600, 'hours': 10},
            {'alert': MagicMock(), 'minutes': 1200, 'hours': 20},
        ]
        
        result = alert_response_service.calculate_response_distribution(response_times)
        
        assert result['>8小时'] == 2

    def test_calculate_distribution_mixed(self):
        """测试混合分布"""
        response_times = [
            {'alert': MagicMock(), 'minutes': 30, 'hours': 0.5},    # <1h
            {'alert': MagicMock(), 'minutes': 120, 'hours': 2},     # 1-4h
            {'alert': MagicMock(), 'minutes': 300, 'hours': 5},     # 4-8h
            {'alert': MagicMock(), 'minutes': 600, 'hours': 10},    # >8h
            {'alert': MagicMock(), 'minutes': 90, 'hours': 1.5},    # 1-4h
        ]
        
        result = alert_response_service.calculate_response_distribution(response_times)
        
        assert result['<1小时'] == 1
        assert result['1-4小时'] == 2
        assert result['4-8小时'] == 1
        assert result['>8小时'] == 1


class TestCalculateLevelMetrics:
    """测试按级别统计响应时效"""

    def test_calculate_level_metrics_empty_list(self):
        """测试空列表"""
        result = alert_response_service.calculate_level_metrics([])
        
        assert result == {}

    def test_calculate_level_metrics_single_level(self, mock_alert):
        """测试单一级别"""
        alerts = [mock_alert(alert_level='CRITICAL') for _ in range(3)]
        response_times = [
            {'alert': alerts[0], 'hours': 1.0},
            {'alert': alerts[1], 'hours': 2.0},
            {'alert': alerts[2], 'hours': 3.0},
        ]
        
        result = alert_response_service.calculate_level_metrics(response_times)
        
        assert 'CRITICAL' in result
        assert result['CRITICAL']['count'] == 3
        assert result['CRITICAL']['avg_hours'] == 2.0
        assert result['CRITICAL']['min_hours'] == 1.0
        assert result['CRITICAL']['max_hours'] == 3.0

    def test_calculate_level_metrics_multiple_levels(self, mock_alert):
        """测试多个级别"""
        alert1 = mock_alert(alert_level='CRITICAL')
        alert2 = mock_alert(alert_level='HIGH')
        alert3 = mock_alert(alert_level='CRITICAL')
        
        response_times = [
            {'alert': alert1, 'hours': 1.0},
            {'alert': alert2, 'hours': 2.0},
            {'alert': alert3, 'hours': 3.0},
        ]
        
        result = alert_response_service.calculate_level_metrics(response_times)
        
        assert 'CRITICAL' in result
        assert 'HIGH' in result
        assert result['CRITICAL']['count'] == 2
        assert result['HIGH']['count'] == 1


class TestCalculateTypeMetrics:
    """测试按类型统计响应时效"""

    def test_calculate_type_metrics_basic(self, mock_alert):
        """测试基本类型统计"""
        alert1 = mock_alert(rule_type='project_delay')
        alert2 = mock_alert(rule_type='cost_overrun')
        
        response_times = [
            {'alert': alert1, 'hours': 1.5},
            {'alert': alert2, 'hours': 2.5},
        ]
        
        result = alert_response_service.calculate_type_metrics(response_times)
        
        assert 'project_delay' in result
        assert 'cost_overrun' in result
        assert result['project_delay']['count'] == 1
        assert result['cost_overrun']['count'] == 1

    def test_calculate_type_metrics_no_rule(self, mock_alert):
        """测试无规则的告警"""
        alert = mock_alert()
        alert.rule = None
        
        response_times = [{'alert': alert, 'hours': 1.0}]
        
        result = alert_response_service.calculate_type_metrics(response_times)
        
        assert 'UNKNOWN' in result


class TestCalculateProjectMetrics:
    """测试按项目统计响应时效"""

    def test_calculate_project_metrics_basic(self, mock_db, mock_alert):
        """测试基本项目统计"""
        alert1 = mock_alert(project_id=1)
        alert2 = mock_alert(project_id=2)
        
        # Mock projects
        project1 = MagicMock(spec=Project)
        project1.project_name = "项目A"
        project2 = MagicMock(spec=Project)
        project2.project_name = "项目B"
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [project1, project2]
        
        response_times = [
            {'alert': alert1, 'hours': 1.0},
            {'alert': alert2, 'hours': 2.0},
        ]
        
        result = alert_response_service.calculate_project_metrics(response_times, mock_db)
        
        assert "项目A" in result
        assert "项目B" in result
        assert result["项目A"]["count"] == 1
        assert result["项目B"]["count"] == 1

    def test_calculate_project_metrics_no_project(self, mock_db, mock_alert):
        """测试无项目ID的告警"""
        alert = mock_alert(project_id=None)
        
        response_times = [{'alert': alert, 'hours': 1.0}]
        
        result = alert_response_service.calculate_project_metrics(response_times, mock_db)
        
        assert result == {}


class TestCalculateHandlerMetrics:
    """测试按责任人统计响应时效"""

    def test_calculate_handler_metrics_basic(self, mock_db, mock_alert):
        """测试基本责任人统计"""
        alert1 = mock_alert(acknowledged_by=1)
        alert2 = mock_alert(acknowledged_by=2)
        
        # Mock users
        user1 = MagicMock(spec=User)
        user1.username = "用户A"
        user2 = MagicMock(spec=User)
        user2.username = "用户B"
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [user1, user2]
        
        response_times = [
            {'alert': alert1, 'hours': 1.5},
            {'alert': alert2, 'hours': 2.5},
        ]
        
        result = alert_response_service.calculate_handler_metrics(response_times, mock_db)
        
        assert "用户A" in result
        assert "用户B" in result
        assert result["用户A"]["avg_hours"] == 1.5

    def test_calculate_handler_metrics_no_handler(self, mock_db, mock_alert):
        """测试无责任人的告警"""
        alert = mock_alert(acknowledged_by=None)
        
        response_times = [{'alert': alert, 'hours': 1.0}]
        
        result = alert_response_service.calculate_handler_metrics(response_times, mock_db)
        
        assert result == {}


class TestGenerateResponseRankings:
    """测试生成响应时效排行榜"""

    def test_generate_rankings_basic(self):
        """测试基本排行榜"""
        project_metrics = {
            "项目A": {"project_id": 1, "avg_hours": 1.0, "count": 10},
            "项目B": {"project_id": 2, "avg_hours": 2.0, "count": 8},
            "项目C": {"project_id": 3, "avg_hours": 3.0, "count": 5},
        }
        
        handler_metrics = {
            "用户A": {"user_id": 1, "avg_hours": 1.5, "count": 15},
            "用户B": {"user_id": 2, "avg_hours": 2.5, "count": 12},
        }
        
        result = alert_response_service.generate_response_rankings(
            project_metrics,
            handler_metrics
        )
        
        assert "fastest_projects" in result
        assert "slowest_projects" in result
        assert "fastest_handlers" in result
        assert "slowest_handlers" in result
        
        # 最快的项目应该是项目A
        assert result["fastest_projects"][0]["project_name"] == "项目A"
        # 最慢的项目应该是项目C
        assert result["slowest_projects"][0]["project_name"] == "项目C"

    def test_generate_rankings_limit_to_5(self):
        """测试限制前5名"""
        project_metrics = {f"项目{i}": {"project_id": i, "avg_hours": float(i), "count": 10} 
                          for i in range(1, 11)}
        
        handler_metrics = {f"用户{i}": {"user_id": i, "avg_hours": float(i), "count": 10} 
                          for i in range(1, 11)}
        
        result = alert_response_service.generate_response_rankings(
            project_metrics,
            handler_metrics
        )
        
        assert len(result["fastest_projects"]) == 5
        assert len(result["slowest_projects"]) == 5
        assert len(result["fastest_handlers"]) == 5
        assert len(result["slowest_handlers"]) == 5

    def test_generate_rankings_empty_metrics(self):
        """测试空指标"""
        result = alert_response_service.generate_response_rankings({}, {})
        
        assert result["fastest_projects"] == []
        assert result["slowest_projects"] == []
        assert result["fastest_handlers"] == []
        assert result["slowest_handlers"] == []


class TestAlertResponseServiceCalculateDailyMetrics:
    """测试计算每日预警响应指标"""

    @patch('app.services.alert_response_service.calculate_response_times')
    @patch('app.services.alert_response_service.calculate_resolve_times')
    @patch('app.services.alert_response_service.calculate_response_distribution')
    @patch('app.services.alert_response_service.calculate_level_metrics')
    @patch('app.services.alert_response_service.calculate_project_metrics')
    @patch('app.services.alert_response_service.calculate_handler_metrics')
    @patch('app.services.alert_response_service.generate_response_rankings')
    def test_calculate_daily_metrics_basic(self, mock_rankings, mock_handler, mock_project,
                                          mock_level, mock_distribution, mock_resolve,
                                          mock_response, service, mock_db):
        """测试基本每日指标计算"""
        # Setup mock queries
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        # Setup mock returns
        mock_response.return_value = []
        mock_resolve.return_value = []
        mock_distribution.return_value = {'<1小时': 0}
        mock_level.return_value = {}
        mock_project.return_value = {}
        mock_handler.return_value = {}
        mock_rankings.return_value = {
            'fastest_projects': [],
            'slowest_projects': [],
            'fastest_handlers': [],
            'slowest_handlers': []
        }
        
        result = service.calculate_daily_metrics()
        
        assert 'date' in result
        assert 'total_acknowledged' in result
        assert 'total_resolved' in result
        assert 'avg_response_hours' in result
        assert 'avg_resolve_hours' in result
        assert 'response_distribution' in result
        assert 'level_metrics' in result
        assert 'project_metrics' in result
        assert 'handler_metrics' in result
        assert 'rankings' in result

    @patch('app.services.alert_response_service.calculate_response_times')
    @patch('app.services.alert_response_service.calculate_resolve_times')
    @patch('app.services.alert_response_service.calculate_response_distribution')
    @patch('app.services.alert_response_service.calculate_level_metrics')
    @patch('app.services.alert_response_service.calculate_project_metrics')
    @patch('app.services.alert_response_service.calculate_handler_metrics')
    @patch('app.services.alert_response_service.generate_response_rankings')
    def test_calculate_daily_metrics_with_data(self, mock_rankings, mock_handler, mock_project,
                                               mock_level, mock_distribution, mock_resolve,
                                               mock_response, service, mock_db, mock_alert):
        """测试有数据的每日指标"""
        # Setup alerts
        alerts = [mock_alert() for _ in range(5)]
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = alerts
        
        # Setup mock returns with data
        mock_response.return_value = [
            {'hours': 1.0}, {'hours': 2.0}, {'hours': 3.0}
        ]
        mock_resolve.return_value = [
            {'hours': 3.0}, {'hours': 4.0}
        ]
        mock_distribution.return_value = {'<1小时': 1, '1-4小时': 2}
        mock_level.return_value = {'HIGH': {'count': 3}}
        mock_project.return_value = {'项目A': {'count': 5}}
        mock_handler.return_value = {'用户A': {'count': 3}}
        mock_rankings.return_value = {
            'fastest_projects': [{'project_name': '项目A', 'avg_hours': 1.5}],
            'slowest_projects': [],
            'fastest_handlers': [],
            'slowest_handlers': []
        }
        
        result = service.calculate_daily_metrics()
        
        assert result['total_acknowledged'] == 5
        assert result['total_resolved'] == 5
        assert result['avg_response_hours'] == 2.0  # (1+2+3)/3
        assert result['avg_resolve_hours'] == 3.5   # (3+4)/2

    @patch('app.services.alert_response_service.calculate_response_times')
    @patch('app.services.alert_response_service.calculate_resolve_times')
    @patch('app.services.alert_response_service.calculate_response_distribution')
    @patch('app.services.alert_response_service.calculate_level_metrics')
    @patch('app.services.alert_response_service.calculate_project_metrics')
    @patch('app.services.alert_response_service.calculate_handler_metrics')
    @patch('app.services.alert_response_service.generate_response_rankings')
    def test_calculate_daily_metrics_no_data(self, mock_rankings, mock_handler, mock_project,
                                            mock_level, mock_distribution, mock_resolve,
                                            mock_response, service, mock_db):
        """测试无数据的每日指标"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        mock_response.return_value = []
        mock_resolve.return_value = []
        mock_distribution.return_value = {'<1小时': 0}
        mock_level.return_value = {}
        mock_project.return_value = {}
        mock_handler.return_value = {}
        mock_rankings.return_value = {
            'fastest_projects': [],
            'slowest_projects': [],
            'fastest_handlers': [],
            'slowest_handlers': []
        }
        
        result = service.calculate_daily_metrics()
        
        assert result['total_acknowledged'] == 0
        assert result['total_resolved'] == 0
        assert result['avg_response_hours'] == 0
        assert result['avg_resolve_hours'] == 0
