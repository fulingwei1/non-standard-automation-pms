# -*- coding: utf-8 -*-
"""APPR-22: progress scheduler jobs must feed unified scheduler metrics."""

from unittest.mock import MagicMock, patch

import pytest


def _mock_job(job_id: str, name: str):
    def noop():
        return None

    job = MagicMock()
    job.id = job_id
    job.name = name
    job.next_run_time = None
    job.trigger = "cron"
    job.func = noop
    return job


def test_progress_scheduler_registered_job_records_success_metrics():
    from app import scheduler_progress

    mock_scheduler = MagicMock()
    mock_scheduler.get_jobs.return_value = []

    def fake_progress_job():
        return {"success": True}

    with (
        patch.object(scheduler_progress, "scheduler", mock_scheduler),
        patch.object(
            scheduler_progress,
            "run_progress_auto_processing_job",
            fake_progress_job,
        ),
        patch.object(scheduler_progress, "record_job_success", create=True) as mock_success,
    ):
        scheduler_progress.start_scheduler()
        registered_job = mock_scheduler.add_job.call_args.kwargs["func"]
        result = registered_job()

    assert result == {"success": True}
    mock_success.assert_called_once()
    job_id, duration_ms, timestamp = mock_success.call_args[0]
    assert job_id == "progress_auto_processing_daily"
    assert isinstance(duration_ms, float)
    assert duration_ms >= 0
    assert timestamp


def test_scheduler_status_includes_progress_scheduler_jobs():
    from app.api.v1.endpoints.scheduler.status import get_scheduler_status

    main_scheduler = MagicMock()
    main_scheduler.running = True
    main_scheduler.get_jobs.return_value = [_mock_job("main_job", "Main Job")]

    progress_scheduler = MagicMock()
    progress_scheduler.running = True
    progress_scheduler.get_jobs.return_value = [
        _mock_job("progress_auto_processing_daily", "进度预测与依赖巡检自动处理")
    ]

    with (
        patch("app.utils.scheduler.scheduler", main_scheduler),
        patch("app.scheduler_progress.scheduler", progress_scheduler),
    ):
        response = get_scheduler_status(current_user=object())

    job_ids = {job["id"] for job in response.data["jobs"]}
    assert response.data["running"] is True
    assert response.data["job_count"] == 2
    assert job_ids == {"main_job", "progress_auto_processing_daily"}


def test_scheduler_jobs_includes_progress_scheduler_jobs():
    from app.api.v1.endpoints.scheduler.status import get_scheduler_jobs

    main_scheduler = MagicMock()
    main_scheduler.get_jobs.return_value = [_mock_job("main_job", "Main Job")]

    progress_scheduler = MagicMock()
    progress_scheduler.get_jobs.return_value = [
        _mock_job("progress_auto_processing_daily", "进度预测与依赖巡检自动处理")
    ]

    with (
        patch("app.utils.scheduler.scheduler", main_scheduler),
        patch("app.scheduler_progress.scheduler", progress_scheduler),
    ):
        response = get_scheduler_jobs(current_user=object())

    job_ids = {job["id"] for job in response.data["jobs"]}
    assert response.data["total"] == 2
    assert job_ids == {"main_job", "progress_auto_processing_daily"}


def test_progress_scheduler_registered_job_records_failure_metrics():
    from app import scheduler_progress

    mock_scheduler = MagicMock()
    mock_scheduler.get_jobs.return_value = []

    def failing_progress_job():
        raise RuntimeError("progress failed")

    with (
        patch.object(scheduler_progress, "scheduler", mock_scheduler),
        patch.object(
            scheduler_progress,
            "run_progress_auto_processing_job",
            failing_progress_job,
        ),
        patch.object(scheduler_progress, "record_job_failure", create=True) as mock_failure,
    ):
        scheduler_progress.start_scheduler()
        registered_job = mock_scheduler.add_job.call_args.kwargs["func"]
        with pytest.raises(RuntimeError, match="progress failed"):
            registered_job()

    mock_failure.assert_called_once()
    job_id, duration_ms, timestamp = mock_failure.call_args[0]
    assert job_id == "progress_auto_processing_daily"
    assert isinstance(duration_ms, float)
    assert duration_ms >= 0
    assert timestamp
