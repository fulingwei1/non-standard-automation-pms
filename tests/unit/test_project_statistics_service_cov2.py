# -*- coding: utf-8 -*-
"""
project_statistics_service.py 单元测试（第二批）
"""
import pytest
from datetime import date
from unittest.mock import MagicMock, patch


# ─── 1. calculate_status_statistics ──────────────────────────────────────────
def test_calculate_status_statistics():
    from app.services.project_statistics_service import calculate_status_statistics

    p1 = MagicMock()
    p1.status = "ACTIVE"
    p2 = MagicMock()
    p2.status = "ACTIVE"
    p3 = MagicMock()
    p3.status = "COMPLETED"

    mock_query = MagicMock()
    mock_query.all.return_value = [p1, p2, p3]

    result = calculate_status_statistics(mock_query)
    assert result == {"ACTIVE": 2, "COMPLETED": 1}


def test_calculate_status_statistics_empty():
    from app.services.project_statistics_service import calculate_status_statistics

    mock_query = MagicMock()
    mock_query.all.return_value = []

    result = calculate_status_statistics(mock_query)
    assert result == {}


# ─── 2. calculate_stage_statistics ───────────────────────────────────────────
def test_calculate_stage_statistics():
    from app.services.project_statistics_service import calculate_stage_statistics

    p1 = MagicMock()
    p1.stage = "S2"
    p2 = MagicMock()
    p2.stage = "S3"
    p3 = MagicMock()
    p3.stage = "S2"

    mock_query = MagicMock()
    mock_query.all.return_value = [p1, p2, p3]

    result = calculate_stage_statistics(mock_query)
    assert result == {"S2": 2, "S3": 1}


# ─── 3. calculate_health_statistics ─────────────────────────────────────────
def test_calculate_health_statistics():
    from app.services.project_statistics_service import calculate_health_statistics

    p1 = MagicMock()
    p1.health = "GREEN"
    p2 = MagicMock()
    p2.health = "RED"

    mock_query = MagicMock()
    mock_query.all.return_value = [p1, p2]

    result = calculate_health_statistics(mock_query)
    assert "GREEN" in result
    assert "RED" in result


# ─── 4. calculate_pm_statistics ──────────────────────────────────────────────
def test_calculate_pm_statistics():
    from app.services.project_statistics_service import calculate_pm_statistics

    p1 = MagicMock()
    p1.pm_id = 1
    p1.pm_name = "Alice"
    p2 = MagicMock()
    p2.pm_id = 1
    p2.pm_name = "Alice"
    p3 = MagicMock()
    p3.pm_id = 2
    p3.pm_name = "Bob"

    mock_query = MagicMock()
    mock_query.all.return_value = [p1, p2, p3]

    result = calculate_pm_statistics(mock_query)
    assert len(result) == 2
    # 按pm_id分组
    pm_counts = {r["pm_id"]: r["count"] for r in result}
    assert pm_counts[1] == 2
    assert pm_counts[2] == 1


def test_calculate_pm_statistics_no_pm():
    from app.services.project_statistics_service import calculate_pm_statistics

    p = MagicMock()
    p.pm_id = None  # 没有PM

    mock_query = MagicMock()
    mock_query.all.return_value = [p]

    result = calculate_pm_statistics(mock_query)
    assert result == []


# ─── 5. calculate_customer_statistics ────────────────────────────────────────
def test_calculate_customer_statistics():
    from app.services.project_statistics_service import calculate_customer_statistics

    p1 = MagicMock()
    p1.customer_id = 10
    p1.customer_name = "Acme"
    p1.contract_amount = 100000

    p2 = MagicMock()
    p2.customer_id = 10
    p2.customer_name = "Acme"
    p2.contract_amount = 50000

    mock_query = MagicMock()
    mock_query.all.return_value = [p1, p2]

    result = calculate_customer_statistics(mock_query)
    assert len(result) == 1
    assert result[0]["customer_name"] == "Acme"
    assert result[0]["total_amount"] == 150000.0
    assert result[0]["count"] == 2


# ─── 6. ProjectStatisticsServiceBase - CostStatisticsService ────────────────
def test_cost_statistics_service_project_not_found():
    from app.services.project_statistics_service import CostStatisticsService

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    svc = CostStatisticsService(mock_db)
    with pytest.raises(ValueError, match="项目不存在"):
        svc.get_project(999)


def test_cost_statistics_service_get_model():
    from app.services.project_statistics_service import CostStatisticsService

    mock_db = MagicMock()
    svc = CostStatisticsService(mock_db)
    model = svc.get_model()
    assert model is not None
    assert svc.get_project_id_field() == "project_id"


# ─── 7. build_project_statistics ─────────────────────────────────────────────
def test_build_project_statistics_basic():
    from app.services.project_statistics_service import build_project_statistics

    p1 = MagicMock()
    p1.status = "ACTIVE"
    p1.stage = "S1"
    p1.health = "GREEN"
    p1.pm_id = 1
    p1.pm_name = "PM1"
    p1.progress_pct = 50

    mock_query = MagicMock()
    mock_query.all.return_value = [p1]

    result = build_project_statistics(MagicMock(), mock_query)
    assert result["total"] == 1
    assert "by_status" in result
    assert "by_stage" in result
    assert "by_health" in result
