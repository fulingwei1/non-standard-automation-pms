# -*- coding: utf-8 -*-
"""
alert_efficiency_service 单元测试

测试预警处理效率分析服务的各个方法
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.services.alert_efficiency_service import (
    calculate_basic_metrics,
    calculate_handler_metrics,
    calculate_project_metrics,
    calculate_type_metrics,
    generate_rankings,
)


def create_mock_alert(
    status='PENDING',
    triggered_at=None,
    acknowledged_at=None,
    alert_level='MEDIUM',
    is_escalated=False,
    project_id=None,
    handler_id=None,
    rule_id=1,
    target_type='project',
    target_id=1,
    rule=None
):
    """创建模拟的预警记录"""
    mock_alert = MagicMock()
    mock_alert.status = status
    mock_alert.triggered_at = triggered_at or datetime.now()
    mock_alert.acknowledged_at = acknowledged_at
    mock_alert.alert_level = alert_level
    mock_alert.is_escalated = is_escalated
    mock_alert.project_id = project_id
    mock_alert.handler_id = handler_id
    mock_alert.acknowledged_by = None
    mock_alert.rule_id = rule_id
    mock_alert.target_type = target_type
    mock_alert.target_id = target_id
    mock_alert.rule = rule
    return mock_alert


def create_mock_engine():
    """创建模拟的规则引擎"""
    mock_engine = MagicMock()
    mock_engine.RESPONSE_TIMEOUT = {
        'LOW': 24,
        'MEDIUM': 8,
        'HIGH': 4,
        'URGENT': 1
    }
    return mock_engine


@pytest.mark.unit
class TestCalculateBasicMetrics:
    """测试 calculate_basic_metrics 函数"""

    def test_empty_alerts(self):
        """测试空预警列表"""
        engine = create_mock_engine()
        result = calculate_basic_metrics([], engine)

        assert result['processing_rate'] == 0
        assert result['timely_processing_rate'] == 0
        assert result['escalation_rate'] == 0
        assert result['duplicate_rate'] == 0

    def test_all_processed(self):
        """测试全部已处理"""
        engine = create_mock_engine()
        now = datetime.now()

        alerts = [
            create_mock_alert(
                status='RESOLVED',
                triggered_at=now - timedelta(hours=2),
                acknowledged_at=now - timedelta(hours=1)
            ),
            create_mock_alert(
                status='CLOSED',
                triggered_at=now - timedelta(hours=3),
                acknowledged_at=now - timedelta(hours=2)
            )
        ]

        result = calculate_basic_metrics(alerts, engine)

        assert result['processing_rate'] == 1.0
        assert result['timely_processing_rate'] == 1.0

    def test_partial_processing(self):
        """测试部分处理"""
        engine = create_mock_engine()
        now = datetime.now()

        alerts = [
            create_mock_alert(status='RESOLVED', triggered_at=now, acknowledged_at=now),
            create_mock_alert(status='PENDING', triggered_at=now),
            create_mock_alert(status='PENDING', triggered_at=now),
            create_mock_alert(status='PENDING', triggered_at=now),
        ]

        result = calculate_basic_metrics(alerts, engine)

        assert result['processing_rate'] == 0.25  # 1/4

    def test_escalation_rate(self):
        """测试升级率"""
        engine = create_mock_engine()
        now = datetime.now()

        alerts = [
            create_mock_alert(is_escalated=True),
            create_mock_alert(is_escalated=True),
            create_mock_alert(is_escalated=False),
            create_mock_alert(is_escalated=False),
        ]

        result = calculate_basic_metrics(alerts, engine)

        assert result['escalation_rate'] == 0.5

    def test_duplicate_rate(self):
        """测试重复预警率"""
        engine = create_mock_engine()
        now = datetime.now()

        alerts = [
            create_mock_alert(rule_id=1, target_type='project', target_id=1, triggered_at=now),
            create_mock_alert(rule_id=1, target_type='project', target_id=1, triggered_at=now + timedelta(hours=1)),  # Duplicate
            create_mock_alert(rule_id=2, target_type='project', target_id=1, triggered_at=now),
        ]

        result = calculate_basic_metrics(alerts, engine)

        assert result['duplicate_rate'] > 0

    def test_timely_processing(self):
        """测试及时处理率"""
        engine = create_mock_engine()
        now = datetime.now()

        # One timely (within 8 hours for MEDIUM), one not
        alerts = [
            create_mock_alert(
                status='RESOLVED',
                triggered_at=now - timedelta(hours=2),
                acknowledged_at=now - timedelta(hours=1),
                alert_level='MEDIUM'
            ),
            create_mock_alert(
                status='RESOLVED',
                triggered_at=now - timedelta(hours=20),
                acknowledged_at=now,
                alert_level='MEDIUM'
            )
        ]

        result = calculate_basic_metrics(alerts, engine)

        assert result['timely_processing_rate'] == 0.5


@pytest.mark.unit
class TestCalculateProjectMetrics:
    """测试 calculate_project_metrics 函数"""

    def test_empty_alerts(self):
        """测试空预警列表"""
        mock_db = MagicMock()
        engine = create_mock_engine()

        result = calculate_project_metrics([], mock_db, engine)

        assert result == {}

    def test_single_project(self):
        """测试单个项目"""
        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.project_name = "Test Project"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        engine = create_mock_engine()
        now = datetime.now()

        alerts = [
            create_mock_alert(
                status='RESOLVED',
                project_id=1,
                triggered_at=now - timedelta(hours=2),
                acknowledged_at=now - timedelta(hours=1)
            ),
            create_mock_alert(
                status='PENDING',
                project_id=1,
                triggered_at=now
            )
        ]

        result = calculate_project_metrics(alerts, mock_db, engine)

        assert 'Test Project' in result
        assert result['Test Project']['total'] == 2
        assert result['Test Project']['processing_rate'] == 0.5

    def test_no_project_id(self):
        """测试没有项目ID的预警"""
        mock_db = MagicMock()
        engine = create_mock_engine()

        alerts = [
            create_mock_alert(project_id=None)
        ]

        result = calculate_project_metrics(alerts, mock_db, engine)

        assert result == {}


@pytest.mark.unit
class TestCalculateHandlerMetrics:
    """测试 calculate_handler_metrics 函数"""

    def test_empty_alerts(self):
        """测试空预警列表"""
        mock_db = MagicMock()
        engine = create_mock_engine()

        result = calculate_handler_metrics([], mock_db, engine)

        assert result == {}

    def test_single_handler(self):
        """测试单个处理人"""
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.username = "test_user"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        engine = create_mock_engine()
        now = datetime.now()

        alerts = [
            create_mock_alert(
                status='RESOLVED',
                handler_id=1,
                triggered_at=now - timedelta(hours=2),
                acknowledged_at=now - timedelta(hours=1)
            ),
            create_mock_alert(
                status='RESOLVED',
                handler_id=1,
                triggered_at=now - timedelta(hours=2),
                acknowledged_at=now - timedelta(hours=1)
            )
        ]

        result = calculate_handler_metrics(alerts, mock_db, engine)

        assert 'test_user' in result
        assert result['test_user']['total'] == 2
        assert result['test_user']['processing_rate'] == 1.0

    def test_no_handler(self):
        """测试没有处理人的预警"""
        mock_db = MagicMock()
        engine = create_mock_engine()

        alerts = [
            create_mock_alert(handler_id=None)
        ]

        result = calculate_handler_metrics(alerts, mock_db, engine)

        assert result == {}


@pytest.mark.unit
class TestCalculateTypeMetrics:
    """测试 calculate_type_metrics 函数"""

    def test_empty_alerts(self):
        """测试空预警列表"""
        engine = create_mock_engine()

        result = calculate_type_metrics([], engine)

        assert result == {}

    def test_single_type(self):
        """测试单个类型"""
        engine = create_mock_engine()
        now = datetime.now()

        mock_rule = MagicMock()
        mock_rule.rule_type = 'SCHEDULE_DELAY'

        alerts = [
            create_mock_alert(
                status='RESOLVED',
                rule=mock_rule,
                triggered_at=now - timedelta(hours=2),
                acknowledged_at=now - timedelta(hours=1)
            ),
            create_mock_alert(
                status='PENDING',
                rule=mock_rule,
                triggered_at=now
            )
        ]

        result = calculate_type_metrics(alerts, engine)

        assert 'SCHEDULE_DELAY' in result
        assert result['SCHEDULE_DELAY']['total'] == 2
        assert result['SCHEDULE_DELAY']['processing_rate'] == 0.5

    def test_multiple_types(self):
        """测试多个类型"""
        engine = create_mock_engine()
        now = datetime.now()

        mock_rule1 = MagicMock()
        mock_rule1.rule_type = 'SCHEDULE_DELAY'

        mock_rule2 = MagicMock()
        mock_rule2.rule_type = 'COST_OVERRUN'

        alerts = [
            create_mock_alert(status='RESOLVED', rule=mock_rule1, triggered_at=now, acknowledged_at=now),
            create_mock_alert(status='PENDING', rule=mock_rule2, triggered_at=now)
        ]

        result = calculate_type_metrics(alerts, engine)

        assert 'SCHEDULE_DELAY' in result
        assert 'COST_OVERRUN' in result

    def test_unknown_type(self):
        """测试未知类型（无规则）"""
        engine = create_mock_engine()

        alerts = [
            create_mock_alert(rule=None)
        ]

        result = calculate_type_metrics(alerts, engine)

        assert 'UNKNOWN' in result


@pytest.mark.unit
class TestGenerateRankings:
    """测试 generate_rankings 函数"""

    def test_empty_metrics(self):
        """测试空指标"""
        result = generate_rankings({}, {})

        assert result['best_projects'] == []
        assert result['worst_projects'] == []
        assert result['best_handlers'] == []
        assert result['worst_handlers'] == []

    def test_rankings_with_data(self):
        """测试有数据的排行"""
        project_metrics = {
            'Project A': {
                'project_id': 1,
                'total': 10,
                'efficiency_score': 90,
                'processing_rate': 0.9,
                'timely_processing_rate': 0.85
            },
            'Project B': {
                'project_id': 2,
                'total': 8,
                'efficiency_score': 70,
                'processing_rate': 0.7,
                'timely_processing_rate': 0.65
            },
            'Project C': {
                'project_id': 3,
                'total': 3,  # Less than 5, should be excluded
                'efficiency_score': 95,
                'processing_rate': 0.95,
                'timely_processing_rate': 0.9
            }
        }

        handler_metrics = {
            'User A': {
                'user_id': 1,
                'total': 10,
                'efficiency_score': 85,
                'processing_rate': 0.85,
                'timely_processing_rate': 0.8
            },
            'User B': {
                'user_id': 2,
                'total': 6,
                'efficiency_score': 60,
                'processing_rate': 0.6,
                'timely_processing_rate': 0.55
            }
        }

        result = generate_rankings(project_metrics, handler_metrics)

        # Project C excluded due to < 5 alerts
        assert len(result['best_projects']) == 2
        assert result['best_projects'][0]['project_name'] == 'Project A'

        assert len(result['best_handlers']) == 2
        assert result['best_handlers'][0]['handler_name'] == 'User A'

    def test_rankings_limit(self):
        """测试排行榜数量限制（最多5个）"""
        project_metrics = {
            f'Project {i}': {
                'project_id': i,
                'total': 10,
                'efficiency_score': 50 + i,
                'processing_rate': 0.5 + i * 0.01,
                'timely_processing_rate': 0.5 + i * 0.01
            }
            for i in range(10)
        }

        result = generate_rankings(project_metrics, {})

        assert len(result['best_projects']) == 5
        assert len(result['worst_projects']) == 5


@pytest.mark.unit
class TestAlertEfficiencyIntegration:
    """集成测试"""

    def test_all_functions_importable(self):
        """测试所有函数可导入"""
        from app.services.alert_efficiency_service import (
            calculate_basic_metrics,
            calculate_handler_metrics,
            calculate_project_metrics,
            calculate_type_metrics,
            generate_rankings,
        )

        assert calculate_basic_metrics is not None
        assert calculate_project_metrics is not None
        assert calculate_handler_metrics is not None
        assert calculate_type_metrics is not None
        assert generate_rankings is not None

    def test_full_workflow(self):
        """测试完整工作流"""
        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.project_name = "Test Project"
        mock_user = MagicMock()
        mock_user.username = "test_user"

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_project,  # For project query
            mock_user,     # For handler query
        ]

        engine = create_mock_engine()
        now = datetime.now()

        mock_rule = MagicMock()
        mock_rule.rule_type = 'SCHEDULE_DELAY'

        alerts = [
            create_mock_alert(
                status='RESOLVED',
                project_id=1,
                handler_id=1,
                rule=mock_rule,
                triggered_at=now - timedelta(hours=2),
                acknowledged_at=now - timedelta(hours=1)
            )
        ]

        # Calculate all metrics
        basic = calculate_basic_metrics(alerts, engine)
        type_metrics = calculate_type_metrics(alerts, engine)

        assert basic['processing_rate'] == 1.0
        assert 'SCHEDULE_DELAY' in type_metrics
