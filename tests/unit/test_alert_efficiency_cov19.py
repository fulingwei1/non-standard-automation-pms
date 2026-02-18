# -*- coding: utf-8 -*-
"""
第十九批 - 预警处理效率分析服务单元测试
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

pytest.importorskip("app.services.alert_efficiency_service")


def _make_alert(status='OPEN', is_escalated=False, rule_id=1,
                target_type='PROJECT', target_id=10,
                triggered_at=None, acknowledged_at=None,
                alert_level='WARNING'):
    a = MagicMock()
    a.status = status
    a.is_escalated = is_escalated
    a.rule_id = rule_id
    a.target_type = target_type
    a.target_id = target_id
    a.alert_level = alert_level
    a.triggered_at = triggered_at or datetime(2024, 3, 15, 9, 0)
    a.acknowledged_at = acknowledged_at
    return a


def _make_engine(response_timeout=None):
    engine = MagicMock()
    engine.RESPONSE_TIMEOUT = response_timeout or {'WARNING': 8, 'CRITICAL': 2}
    return engine


def test_calculate_basic_metrics_empty():
    """无预警时所有指标为 0"""
    from app.services.alert_efficiency_service import calculate_basic_metrics
    engine = _make_engine()
    result = calculate_basic_metrics([], engine)
    assert result['processing_rate'] == 0
    assert result['timely_processing_rate'] == 0
    assert result['escalation_rate'] == 0
    assert result['duplicate_rate'] == 0


def test_calculate_basic_metrics_all_resolved():
    """全部已处理时处理率为 1"""
    from app.services.alert_efficiency_service import calculate_basic_metrics
    engine = _make_engine()
    alerts = [
        _make_alert(status='RESOLVED'),
        _make_alert(status='CLOSED'),
    ]
    result = calculate_basic_metrics(alerts, engine)
    assert result['processing_rate'] == 1.0


def test_calculate_basic_metrics_half_processed():
    """一半处理时处理率为 0.5"""
    from app.services.alert_efficiency_service import calculate_basic_metrics
    engine = _make_engine()
    alerts = [
        _make_alert(status='RESOLVED'),
        _make_alert(status='OPEN'),
    ]
    result = calculate_basic_metrics(alerts, engine)
    assert result['processing_rate'] == 0.5


def test_calculate_basic_metrics_timely_processing():
    """及时处理率：在响应时限内处理"""
    from app.services.alert_efficiency_service import calculate_basic_metrics
    engine = _make_engine({'WARNING': 8})
    t = datetime(2024, 3, 15, 9, 0)
    # 5小时内处理，在8小时限制内
    a = _make_alert(status='RESOLVED', alert_level='WARNING',
                    triggered_at=t, acknowledged_at=t + timedelta(hours=5))
    result = calculate_basic_metrics([a], engine)
    assert result['timely_processing_rate'] == 1.0


def test_calculate_basic_metrics_escalation_rate():
    """升级率正确计算"""
    from app.services.alert_efficiency_service import calculate_basic_metrics
    engine = _make_engine()
    alerts = [
        _make_alert(is_escalated=True),
        _make_alert(is_escalated=True),
        _make_alert(is_escalated=False),
        _make_alert(is_escalated=False),
    ]
    result = calculate_basic_metrics(alerts, engine)
    assert result['escalation_rate'] == 0.5


def test_calculate_basic_metrics_duplicate_rate():
    """同规则同目标24小时内重复触发计为重复"""
    from app.services.alert_efficiency_service import calculate_basic_metrics
    engine = _make_engine()
    t = datetime(2024, 3, 15, 9, 0)
    alerts = [
        _make_alert(rule_id=1, target_id=1, triggered_at=t),
        _make_alert(rule_id=1, target_id=1, triggered_at=t + timedelta(hours=2)),  # 重复
        _make_alert(rule_id=2, target_id=1, triggered_at=t),  # 不同规则
    ]
    result = calculate_basic_metrics(alerts, engine)
    assert result['duplicate_rate'] > 0


def test_calculate_basic_metrics_returns_all_keys():
    """返回结果包含所有必需字段"""
    from app.services.alert_efficiency_service import calculate_basic_metrics
    engine = _make_engine()
    result = calculate_basic_metrics([], engine)
    for key in ['processing_rate', 'timely_processing_rate', 'escalation_rate', 'duplicate_rate']:
        assert key in result
