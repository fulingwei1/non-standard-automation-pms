# -*- coding: utf-8 -*-
"""
第十九批 - 失败模式分析模块单元测试
"""
import pytest
from collections import defaultdict
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

pytest.importorskip("app.services.resource_waste_analysis.failure_patterns")


def make_instance():
    from app.services.resource_waste_analysis.failure_patterns import FailurePatternsMixin

    class ConcreteFailurePatterns(FailurePatternsMixin):
        """测试用的具体类，混入 FailurePatternsMixin"""
        def __init__(self, db):
            self.db = db
            self._notifications = []

        def _send_notification(self, n):
            self._notifications.append(n)

    db = MagicMock()
    return ConcreteFailurePatterns(db)


def test_analyze_failure_patterns_no_projects():
    """无失败项目时返回空结果"""
    inst = make_instance()
    inst.db.query.return_value.filter.return_value.all.return_value = []
    result = inst.analyze_failure_patterns()
    assert result['loss_reason_distribution'] == {}
    assert result['high_waste_characteristics'] == []
    assert result['early_warning_indicators'] == []
    assert '数据不足' in result['recommendations'][0]


def test_analyze_failure_patterns_with_date_filters():
    """传入日期范围时查询正常执行"""
    inst = make_instance()
    mock_query = MagicMock()
    inst.db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = []
    result = inst.analyze_failure_patterns(
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31)
    )
    assert isinstance(result, dict)
    assert 'recommendations' in result


def test_analyze_failure_patterns_with_failed_projects():
    """有失败项目时正确统计丢标原因分布"""
    inst = make_instance()

    p1 = MagicMock()
    p1.id = 1
    p1.loss_reason = 'PRICE_TOO_HIGH'
    p1.evaluation_score = 50

    p2 = MagicMock()
    p2.id = 2
    p2.loss_reason = 'PRICE_TOO_HIGH'
    p2.evaluation_score = 70

    inst.db.query.return_value.filter.return_value.all.return_value = [p1, p2]
    # work_hours 查询
    inst.db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
        (1, 30.0), (2, 10.0)
    ]

    result = inst.analyze_failure_patterns()
    assert 'loss_reason_distribution' in result
    assert 'early_warning_indicators' in result
    assert isinstance(result['early_warning_indicators'], list)
    assert len(result['early_warning_indicators']) > 0


def test_analyze_failure_patterns_recommendations_price():
    """价格原因丢标最多时给出对应建议"""
    inst = make_instance()

    projects = []
    for i in range(5):
        p = MagicMock()
        p.id = i + 1
        p.loss_reason = 'PRICE_TOO_HIGH'
        p.evaluation_score = 80
        projects.append(p)

    inst.db.query.return_value.filter.return_value.all.return_value = projects
    inst.db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

    result = inst.analyze_failure_patterns()
    recs = result['recommendations']
    assert any('价格' in r or '成本' in r for r in recs)


def test_analyze_failure_patterns_recommendations_tech():
    """技术不匹配丢标时给出对应建议"""
    inst = make_instance()

    projects = []
    for i in range(3):
        p = MagicMock()
        p.id = i + 1
        p.loss_reason = 'TECH_NOT_MATCH'
        p.evaluation_score = 75
        projects.append(p)

    inst.db.query.return_value.filter.return_value.all.return_value = projects
    inst.db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

    result = inst.analyze_failure_patterns()
    recs = result['recommendations']
    assert any('技术' in r for r in recs)


def test_analyze_failure_patterns_high_waste_characteristic():
    """低评估分高工时时标记高浪费特征"""
    inst = make_instance()

    projects = []
    for i in range(10):
        p = MagicMock()
        p.id = i + 1
        p.loss_reason = 'OTHER'
        p.evaluation_score = 50  # 低分
        projects.append(p)

    inst.db.query.return_value.filter.return_value.all.return_value = projects
    # 每个项目超过 40 工时
    inst.db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
        (i + 1, 60.0) for i in range(10)
    ]

    result = inst.analyze_failure_patterns()
    # 超过 30% 的低分高工时项目应触发特征
    assert isinstance(result['high_waste_characteristics'], list)


def test_analyze_failure_patterns_returns_dict_structure():
    """返回结果包含所有必需字段"""
    inst = make_instance()
    inst.db.query.return_value.filter.return_value.all.return_value = []
    result = inst.analyze_failure_patterns()
    for key in ['loss_reason_distribution', 'high_waste_characteristics',
                'early_warning_indicators', 'recommendations']:
        assert key in result
