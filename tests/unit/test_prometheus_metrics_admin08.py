# -*- coding: utf-8 -*-
"""ADMIN-08: Prometheus must be able to scrape /metrics."""

from fastapi.testclient import TestClient

from app.main import app


def test_metrics_endpoint_returns_prometheus_text():
    response = TestClient(app).get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    body = response.text
    assert "# HELP pms_app_health" in body
    assert "pms_app_health" in body
    assert "pms_dependency_up" in body


def test_metrics_endpoint_exports_scheduler_job_counters():
    from app.utils.scheduler_metrics import METRICS, record_job_success

    METRICS.reset()
    record_job_success("admin10_job", 42.0, "2026-07-05T00:00:00+00:00")

    response = TestClient(app).get("/metrics")

    assert response.status_code == 200
    body = response.text
    assert "# HELP pms_scheduler_job_success_total" in body
    assert 'pms_scheduler_job_success_total{job_id="admin10_job"} 1' in body
    assert 'pms_scheduler_job_last_duration_ms{job_id="admin10_job"} 42.0' in body


def test_prometheus_config_does_not_scrape_raw_database_ports():
    config = open("monitoring/prometheus.yml", encoding="utf-8").read()

    assert "mysql:3306" not in config
    assert "redis:6379" not in config
