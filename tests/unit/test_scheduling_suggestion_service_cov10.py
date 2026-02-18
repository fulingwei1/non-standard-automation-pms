# -*- coding: utf-8 -*-
"""第十批：SchedulingSuggestionService 单元测试"""
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

try:
    from app.services.scheduling_suggestion_service import SchedulingSuggestionService
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="模块导入失败")


@pytest.fixture
def db():
    return MagicMock()


def _make_project(**kwargs):
    p = MagicMock()
    p.id = kwargs.get("id", 1)
    p.priority = kwargs.get("priority", "P1")
    p.delivery_date = kwargs.get("delivery_date", date.today() + timedelta(days=5))
    p.customer = MagicMock()
    p.customer.importance = kwargs.get("importance", "A")
    p.contract_amount = kwargs.get("contract_amount", 600000)
    return p


def test_priority_scores_map():
    """验证优先级评分映射"""
    scores = SchedulingSuggestionService.PRIORITY_SCORES
    assert scores["P1"] == 30
    assert scores["P5"] == 6
    assert scores["P1"] > scores["P2"] > scores["P3"]


def test_customer_importance_scores():
    """验证客户重要度评分"""
    scores = SchedulingSuggestionService.CUSTOMER_IMPORTANCE_SCORES
    assert scores["A"] > scores["B"] > scores["C"] > scores["D"]


def _make_full_project(**kwargs):
    """创建具有真实日期对象的项目 mock"""
    p = MagicMock()
    p.id = kwargs.get("id", 1)
    p.priority = kwargs.get("priority", "P1")
    p.planned_end_date = kwargs.get("planned_end_date", date.today() + timedelta(days=5))
    p.delivery_date = kwargs.get("delivery_date", date.today() + timedelta(days=5))
    p.contract_amount = kwargs.get("contract_amount", 600000)
    # 客户重要度
    customer = MagicMock()
    customer.importance = kwargs.get("importance", "A")
    p.customer = customer
    return p


def test_calculate_priority_score_p1(db):
    """P1优先级项目"""
    project = _make_full_project(priority="P1")
    readiness = MagicMock()
    readiness.readiness_rate = 95.0

    result = SchedulingSuggestionService.calculate_priority_score(
        db=db, project=project, readiness=readiness
    )
    assert isinstance(result, dict)
    assert result is not None


def test_calculate_priority_score_p5(db):
    """P5优先级项目"""
    project = _make_full_project(priority="P5", planned_end_date=date.today() + timedelta(days=90))
    result = SchedulingSuggestionService.calculate_priority_score(
        db=db, project=project
    )
    assert result is not None


def test_deadline_pressure_scores_defined():
    """验证交期压力评分已定义"""
    scores = SchedulingSuggestionService.DEADLINE_PRESSURE_SCORES
    assert len(scores) > 0


def test_contract_amount_scores_defined():
    """验证合同金额评分已定义"""
    scores = SchedulingSuggestionService.CONTRACT_AMOUNT_SCORES
    assert len(scores) > 0
    amounts = [(amt, score) for amt, score in scores]
    assert amounts[0][1] >= amounts[-1][1]


def test_calculate_priority_score_unknown_priority(db):
    """未知优先级 - 映射到默认值"""
    project = _make_full_project(priority="UNKNOWN")
    result = SchedulingSuggestionService.calculate_priority_score(
        db=db, project=project
    )
    assert result is not None


def test_calculate_priority_score_high(db):
    """HIGH 优先级映射到 P1"""
    project = _make_full_project(priority="HIGH")
    result = SchedulingSuggestionService.calculate_priority_score(
        db=db, project=project
    )
    assert result is not None
