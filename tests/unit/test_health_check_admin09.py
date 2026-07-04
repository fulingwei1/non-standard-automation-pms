# -*- coding: utf-8 -*-
"""ADMIN-09: health checks must reflect dependency state."""


def test_root_health_reports_degraded_when_database_probe_fails(monkeypatch):
    from app import main

    monkeypatch.setattr(
        main,
        "_probe_database",
        lambda: {"status": "down", "error": "db unavailable"},
        raising=False,
    )
    monkeypatch.setattr(
        main,
        "_probe_scheduler",
        lambda: {"status": "up", "running": True, "job_count": 3},
        raising=False,
    )
    monkeypatch.setattr(
        main,
        "_probe_redis",
        lambda: {"status": "disabled", "configured": False},
        raising=False,
    )

    result = main.health_check()

    assert result["status"] == "degraded"
    assert result["dependencies"]["database"]["status"] == "down"
    assert result["dependencies"]["scheduler"]["job_count"] == 3
    assert result["dependencies"]["redis"]["status"] == "disabled"


def test_api_health_reports_healthy_when_required_dependencies_are_up(monkeypatch):
    from app import main

    monkeypatch.setattr(main, "_probe_database", lambda: {"status": "up"}, raising=False)
    monkeypatch.setattr(
        main,
        "_probe_scheduler",
        lambda: {"status": "disabled", "running": False, "job_count": 0},
        raising=False,
    )
    monkeypatch.setattr(
        main,
        "_probe_redis",
        lambda: {"status": "disabled", "configured": False},
        raising=False,
    )

    result = main.api_health_check()

    assert result["status"] == "healthy"
    assert "timestamp" in result
    assert result["dependencies"]["database"]["status"] == "up"
