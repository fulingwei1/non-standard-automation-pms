# -*- coding: utf-8 -*-
"""
第四十七批覆盖测试 - win_rate_prediction_service/history.py
"""
import pytest

pytest.importorskip("app.services.win_rate_prediction_service.history")

from unittest.mock import MagicMock

from app.services.win_rate_prediction_service.history import (
    get_customer_cooperation_history,
    get_salesperson_historical_win_rate,
    get_similar_leads_statistics,
)


def _make_service_with_query_result(result):
    svc = MagicMock()
    svc.db.query.return_value.filter.return_value.first.return_value = result
    return svc


# ---------- get_salesperson_historical_win_rate ----------

def test_salesperson_win_rate_no_data():
    svc = MagicMock()
    stats = MagicMock()
    stats.total = 0
    stats.won = 0
    svc.db.query.return_value.filter.return_value.first.return_value = stats
    rate, count = get_salesperson_historical_win_rate(svc, salesperson_id=1)
    assert rate == 0.20  # 默认行业平均
    assert count == 0


def test_salesperson_win_rate_with_data():
    svc = MagicMock()
    stats = MagicMock()
    stats.total = 10
    stats.won = 7
    svc.db.query.return_value.filter.return_value.first.return_value = stats
    rate, count = get_salesperson_historical_win_rate(svc, salesperson_id=1)
    assert rate == pytest.approx(0.7)
    assert count == 10


# ---------- get_customer_cooperation_history ----------

def test_customer_history_no_ids():
    svc = MagicMock()
    total, won = get_customer_cooperation_history(svc)
    assert total == 0
    assert won == 0


def test_customer_history_by_id():
    svc = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.count.side_effect = [5, 3]  # total, won
    svc.db.query.return_value = q
    total, won = get_customer_cooperation_history(svc, customer_id=42)
    assert total == 5
    assert won == 3


def test_customer_history_by_name_not_found():
    svc = MagicMock()
    svc.db.query.return_value.filter.return_value.first.return_value = None
    total, won = get_customer_cooperation_history(svc, customer_name="不存在客户")
    assert total == 0
    assert won == 0


# ---------- get_similar_leads_statistics ----------

def test_similar_leads_empty():
    svc = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = []
    svc.db.query.return_value = q
    dim = MagicMock()
    dim.total_score = 60
    count, rate = get_similar_leads_statistics(svc, dim)
    assert count == 0
    assert rate == 0


def test_similar_leads_with_data():
    from app.models.enums import LeadOutcomeEnum
    svc = MagicMock()

    won_p = MagicMock()
    won_p.outcome = LeadOutcomeEnum.WON.value
    lost_p = MagicMock()
    lost_p.outcome = LeadOutcomeEnum.LOST.value

    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = [won_p, lost_p]
    svc.db.query.return_value = q

    dim = MagicMock()
    dim.total_score = 70

    count, rate = get_similar_leads_statistics(svc, dim)
    assert count == 2
    assert rate == pytest.approx(0.5)
