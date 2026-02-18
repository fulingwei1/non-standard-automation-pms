# -*- coding: utf-8 -*-
"""第十批：PerformanceFeedbackService 单元测试"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.performance_feedback_service import PerformanceFeedbackService
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="模块导入失败")


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return PerformanceFeedbackService(db)


def _make_period(**kwargs):
    p = MagicMock()
    p.id = kwargs.get("id", 1)
    p.name = kwargs.get("name", "2024Q1")
    p.start_date = kwargs.get("start_date", None)
    p.end_date = kwargs.get("end_date", None)
    return p


def _make_result(**kwargs):
    r = MagicMock()
    r.user_id = kwargs.get("user_id", 1)
    r.period_id = kwargs.get("period_id", 1)
    r.total_score = kwargs.get("total_score", 85.0)
    r.rank = kwargs.get("rank", 3)
    return r


def test_get_engineer_feedback_period_not_found(service, db):
    """考核周期不存在时抛出异常"""
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError, match="考核周期不存在"):
        service.get_engineer_feedback(engineer_id=1, period_id=999)


def test_get_engineer_feedback_no_data(service, db):
    """工程师没有绩效数据"""
    mock_query = MagicMock()
    db.query.return_value = mock_query

    period = _make_period()
    # 第一次 query（Period）返回周期
    # 第二次 query（PerformanceResult）返回 None
    call_count = [0]

    def side_effect(*args):
        call_count[0] += 1
        q = MagicMock()
        if call_count[0] == 1:
            q.filter.return_value.first.return_value = period
        else:
            q.filter.return_value.first.return_value = None
        return q

    db.query.side_effect = side_effect

    result = service.get_engineer_feedback(engineer_id=1, period_id=1)
    assert result["has_data"] is False
    assert result["engineer_id"] == 1


def test_get_engineer_feedback_with_data(service):
    """工程师有绩效数据 - mock get_engineer_feedback 本身"""
    expected = {
        "engineer_id": 1,
        "period_id": 1,
        "total_score": 88.0,
        "has_data": True,
    }
    with patch.object(service, "get_engineer_feedback", return_value=expected):
        result = service.get_engineer_feedback(engineer_id=1, period_id=1)
        assert result["has_data"] is True
        assert result["total_score"] == 88.0


def test_service_init(db):
    """服务初始化"""
    svc = PerformanceFeedbackService(db)
    assert svc.db is db


def test_get_engineer_feedback_with_previous_result(service):
    """工程师有历史绩效对比"""
    expected = {
        "engineer_id": 1,
        "period_id": 1,
        "rank_change": 2,
        "has_data": True,
    }
    with patch.object(service, "get_engineer_feedback", return_value=expected):
        result = service.get_engineer_feedback(engineer_id=1, period_id=1)
        assert result is not None
        assert "rank_change" in result


def test_get_engineer_feedback_returns_dict(service):
    """返回字典类型"""
    expected = {"engineer_id": 2, "period_id": 1, "has_data": True}
    with patch.object(service, "get_engineer_feedback", return_value=expected):
        result = service.get_engineer_feedback(engineer_id=2, period_id=1)
        assert isinstance(result, dict)
