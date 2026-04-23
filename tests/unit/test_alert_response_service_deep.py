# -*- coding: utf-8 -*-
"""alert_response_service 深度覆盖测试。"""

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.alert import alert_response_service as ars_module
from app.services.alert.alert_response_service import (
    AlertResponseService,
    calculate_avg_response_time,
    calculate_handler_metrics,
    calculate_level_metrics,
    calculate_project_metrics,
    calculate_resolve_times,
    calculate_response_distribution,
    calculate_response_times,
    calculate_type_metrics,
    generate_response_rankings,
)



def _query_chain(all_result=None, first_result=None):
    query = MagicMock()
    query.filter.return_value = query
    query.all.return_value = all_result if all_result is not None else []
    query.first.return_value = first_result
    return query



def test_calculate_response_and_resolve_times_skip_missing_timestamps():
    alerts = [
        SimpleNamespace(
            triggered_at=datetime(2026, 4, 10, 8, 0, 0),
            acknowledged_at=datetime(2026, 4, 10, 10, 0, 0),
            handle_end_at=datetime(2026, 4, 10, 12, 30, 0),
        ),
        SimpleNamespace(
            triggered_at=datetime(2026, 4, 10, 8, 0, 0),
            acknowledged_at=None,
            handle_end_at=None,
        ),
    ]

    response_times = calculate_response_times(alerts)
    resolve_times = calculate_resolve_times(alerts)

    assert len(response_times) == 1
    assert response_times[0]["minutes"] == 120
    assert response_times[0]["hours"] == 2

    assert len(resolve_times) == 1
    assert resolve_times[0]["minutes"] == 150
    assert resolve_times[0]["hours"] == 2.5



def test_distribution_and_avg_response_time_cover_all_buckets_and_empty():
    response_times = [
        {"hours": 0.5, "minutes": 30},
        {"hours": 2, "minutes": 120},
        {"hours": 6, "minutes": 360},
        {"hours": 9, "minutes": 540},
        {"hours": 3, "minutes": None},
    ]

    distribution = calculate_response_distribution(response_times)

    assert distribution == {
        "<1小时": 1,
        "1-4小时": 2,
        "4-8小时": 1,
        ">8小时": 1,
    }
    assert calculate_avg_response_time(response_times) == (30 + 120 + 360 + 540) / 4
    assert calculate_avg_response_time([]) == 0
    assert calculate_avg_response_time([{"minutes": None}]) == 0



def test_level_and_type_metrics_cover_unknowns():
    response_times = [
        {
            "hours": 1.5,
            "alert": SimpleNamespace(alert_level="WARNING", rule=SimpleNamespace(rule_type="COST")),
        },
        {
            "hours": 3.0,
            "alert": SimpleNamespace(alert_level="WARNING", rule=None),
        },
        {
            "hours": 6.0,
            "alert": SimpleNamespace(alert_level=None, rule=SimpleNamespace(rule_type="QUALITY")),
        },
    ]

    level_metrics = calculate_level_metrics(response_times)
    type_metrics = calculate_type_metrics(response_times)

    assert level_metrics["WARNING"]["count"] == 2
    assert level_metrics["WARNING"]["avg_hours"] == 2.25
    assert level_metrics["UNKNOWN"]["max_hours"] == 6.0

    assert type_metrics["COST"]["count"] == 1
    assert type_metrics["QUALITY"]["avg_hours"] == 6.0
    assert type_metrics["UNKNOWN"]["min_hours"] == 3.0



def test_project_and_handler_metrics_cover_existing_and_fallback_names():
    response_times = [
        {"hours": 2.0, "alert": SimpleNamespace(project_id=1, acknowledged_by=11)},
        {"hours": 4.0, "alert": SimpleNamespace(project_id=1, acknowledged_by=11)},
        {"hours": 5.0, "alert": SimpleNamespace(project_id=2, acknowledged_by=22)},
        {"hours": 7.0, "alert": SimpleNamespace(project_id=None, acknowledged_by=None)},
    ]

    db = MagicMock()
    db.query.side_effect = [
        _query_chain(first_result=SimpleNamespace(project_name="项目A")),
        _query_chain(first_result=SimpleNamespace(project_name="项目A")),
        _query_chain(first_result=None),
        _query_chain(first_result=SimpleNamespace(username="张三")),
        _query_chain(first_result=SimpleNamespace(username="张三")),
        _query_chain(first_result=None),
    ]

    project_metrics = calculate_project_metrics(response_times, db)
    handler_metrics = calculate_handler_metrics(response_times, db)

    assert project_metrics["项目A"]["count"] == 2
    assert project_metrics["项目A"]["avg_hours"] == 3.0
    assert project_metrics["项目2"]["project_id"] == 2

    assert handler_metrics["张三"]["count"] == 2
    assert handler_metrics["张三"]["avg_hours"] == 3.0
    assert handler_metrics["用户22"]["user_id"] == 22



def test_generate_response_rankings_orders_fast_and_slow_lists():
    project_metrics = {
        "项目A": {"project_id": 1, "avg_hours": 2.345, "count": 3},
        "项目B": {"project_id": 2, "avg_hours": 8.1, "count": 2},
    }
    handler_metrics = {
        "张三": {"user_id": 11, "avg_hours": 1.111, "count": 4},
        "李四": {"user_id": 22, "avg_hours": 9.876, "count": 1},
    }

    rankings = generate_response_rankings(project_metrics, handler_metrics)

    assert rankings["fastest_projects"][0]["project_name"] == "项目A"
    assert rankings["slowest_projects"][0]["project_name"] == "项目B"
    assert rankings["fastest_handlers"][0]["handler_name"] == "张三"
    assert rankings["slowest_handlers"][0]["handler_name"] == "李四"
    assert rankings["fastest_handlers"][0]["avg_hours"] == 1.11



def test_alert_response_service_calculate_daily_metrics(monkeypatch):
    acknowledged_alerts = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
    resolved_alerts = [SimpleNamespace(id=3)]
    db = MagicMock()
    db.query.side_effect = [
        _query_chain(all_result=acknowledged_alerts),
        _query_chain(all_result=resolved_alerts),
    ]

    monkeypatch.setattr(ars_module, "calculate_response_times", lambda alerts: [{"hours": 2.0}, {"hours": 4.0}])
    monkeypatch.setattr(ars_module, "calculate_resolve_times", lambda alerts: [{"hours": 1.5}])
    monkeypatch.setattr(ars_module, "calculate_response_distribution", lambda rts: {"<1小时": 0, "1-4小时": 2, "4-8小时": 0, ">8小时": 0})
    monkeypatch.setattr(ars_module, "calculate_level_metrics", lambda rts: {"WARNING": {"count": 2}})
    monkeypatch.setattr(ars_module, "calculate_project_metrics", lambda rts, db_obj: {"项目A": {"count": 2}})
    monkeypatch.setattr(ars_module, "calculate_handler_metrics", lambda rts, db_obj: {"张三": {"count": 2}})
    monkeypatch.setattr(ars_module, "generate_response_rankings", lambda p, h: {"fastest_projects": [], "slowest_projects": [], "fastest_handlers": [], "slowest_handlers": []})

    service = AlertResponseService(db)
    result = service.calculate_daily_metrics()

    assert result["date"] == (datetime.now().date() - timedelta(days=1)).isoformat()
    assert result["total_acknowledged"] == 2
    assert result["total_resolved"] == 1
    assert result["avg_response_hours"] == 3.0
    assert result["avg_resolve_hours"] == 1.5
    assert result["level_metrics"] == {"WARNING": {"count": 2}}
    assert result["project_metrics"] == {"项目A": {"count": 2}}
    assert result["handler_metrics"] == {"张三": {"count": 2}}
    assert "T" in result["timestamp"]
