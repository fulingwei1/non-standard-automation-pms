# -*- coding: utf-8 -*-
"""
Unit tests for app/utils/scheduler.py
Covers: job_listener, _resolve_callable, _wrap_job_callable, shutdown_scheduler
"""

import pytest
import json
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timezone

from app.utils.scheduler import (
    job_listener,
    _resolve_callable,
    _wrap_job_callable,
    shutdown_scheduler,
)


class TestJobListener:
    """Tests for job_listener function."""

    @patch("app.utils.scheduler.logger")
    def test_success_event_logs_info(self, mock_logger):
        """Successful job event logs at INFO level."""
        event = MagicMock()
        event.job_id = "my_job"
        event.jobstore = "default"
        event.scheduled_run_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        event.exception = None

        job_listener(event)

        mock_logger.info.assert_called_once()
        logged_msg = mock_logger.info.call_args[0][0]
        assert "my_job" in logged_msg
        assert "success" in logged_msg

    @patch("app.utils.scheduler.logger")
    def test_failure_event_logs_error(self, mock_logger):
        """Failed job event logs at ERROR level."""
        event = MagicMock()
        event.job_id = "failing_job"
        event.jobstore = "default"
        event.scheduled_run_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        event.exception = RuntimeError("task crashed")

        job_listener(event)

        mock_logger.error.assert_called_once()
        logged_msg = mock_logger.error.call_args[0][0]
        assert "failing_job" in logged_msg
        assert "failed" in logged_msg
        assert "task crashed" in logged_msg

    @patch("app.utils.scheduler.logger")
    def test_success_payload_is_valid_json(self, mock_logger):
        """Logged message contains valid JSON payload."""
        event = MagicMock()
        event.job_id = "json_job"
        event.jobstore = "default"
        event.scheduled_run_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
        event.exception = None

        job_listener(event)

        msg = mock_logger.info.call_args[0][0]
        # Extract JSON part
        json_part = msg[len("[scheduler] "):]
        parsed = json.loads(json_part)
        assert parsed["job_id"] == "json_job"
        assert parsed["status"] == "success"

    @patch("app.utils.scheduler.logger")
    def test_event_with_no_scheduled_time(self, mock_logger):
        """Handles events where scheduled_run_time is None."""
        event = MagicMock()
        event.job_id = "notimed_job"
        event.jobstore = "default"
        event.scheduled_run_time = None
        event.exception = None

        job_listener(event)  # should not raise
        mock_logger.info.assert_called_once()


class TestResolveCallable:
    """Tests for _resolve_callable function."""

    def test_resolves_callable_from_module(self):
        """_resolve_callable imports module and returns attribute."""
        task = {
            "module": "app.utils.scheduler_metrics",
            "callable": "record_job_success",
        }
        func = _resolve_callable(task)
        from app.utils.scheduler_metrics import record_job_success
        assert func is record_job_success

    def test_raises_on_invalid_module(self):
        """Raises ImportError for non-existent module."""
        task = {
            "module": "non_existent_module_xyz",
            "callable": "some_func",
        }
        with pytest.raises((ImportError, ModuleNotFoundError)):
            _resolve_callable(task)

    def test_raises_on_invalid_callable(self):
        """Raises AttributeError for non-existent callable."""
        task = {
            "module": "app.utils.scheduler_metrics",
            "callable": "nonexistent_func_xyz",
        }
        with pytest.raises(AttributeError):
            _resolve_callable(task)


class TestWrapJobCallable:
    """Tests for _wrap_job_callable function."""

    def test_wrapped_function_called(self):
        """Wrapped function executes the original callable."""
        results = []
        def my_task():
            results.append("executed")

        task = {"id": "task_1", "name": "Test Task", "owner": "dev", "category": "test"}
        wrapped = _wrap_job_callable(my_task, task)
        wrapped()

        assert "executed" in results

    def test_success_recorded_in_metrics(self):
        """Successful execution records job success in metrics."""
        def my_task():
            return "ok"

        task = {"id": "metrics_job", "name": "Metrics Job", "owner": None, "category": None}
        wrapped = _wrap_job_callable(my_task, task)

        with patch("app.utils.scheduler.record_job_success") as mock_success:
            wrapped()
            mock_success.assert_called_once()
            args = mock_success.call_args[0]
            assert args[0] == "metrics_job"  # job_id
            assert isinstance(args[1], float)  # duration_ms

    def test_failure_recorded_in_metrics(self):
        """Failed execution records job failure in metrics and re-raises."""
        def failing_task():
            raise ValueError("task failed!")

        task = {"id": "fail_job", "name": "Fail Job", "owner": None, "category": None}
        wrapped = _wrap_job_callable(failing_task, task)

        with patch("app.utils.scheduler.record_job_failure") as mock_failure:
            with pytest.raises(ValueError, match="task failed!"):
                wrapped()
            mock_failure.assert_called_once()
            args = mock_failure.call_args[0]
            assert args[0] == "fail_job"

    @patch("app.utils.scheduler.logger")
    def test_logs_start_and_success_events(self, mock_logger):
        """Wrapped function logs start and success events."""
        def my_task():
            return "done"

        task = {"id": "log_job", "name": "Log Job", "owner": None, "category": None}
        wrapped = _wrap_job_callable(my_task, task)
        wrapped()

        # Should have logged at least 2 times (start + success)
        assert mock_logger.info.call_count >= 2
        all_msgs = " ".join(str(c) for c in mock_logger.info.call_args_list)
        assert "job_run_start" in all_msgs
        assert "job_run_success" in all_msgs

    @patch("app.utils.scheduler.logger")
    def test_logs_failure_event(self, mock_logger):
        """Wrapped function logs failure on exception."""
        def bad_task():
            raise RuntimeError("boom")

        task = {"id": "err_job", "name": "Error Job", "owner": None, "category": None}
        wrapped = _wrap_job_callable(bad_task, task)

        with pytest.raises(RuntimeError):
            wrapped()

        all_msgs = " ".join(str(c) for c in mock_logger.error.call_args_list)
        assert "job_run_failed" in all_msgs


class TestShutdownScheduler:
    """Tests for shutdown_scheduler function."""

    def test_shutdown_when_running(self):
        """Calls scheduler.shutdown() when scheduler is running."""
        with patch("app.utils.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.running = True
            shutdown_scheduler()
            mock_scheduler.shutdown.assert_called_once()

    def test_no_shutdown_when_not_running(self):
        """Does not call scheduler.shutdown() when scheduler is stopped."""
        with patch("app.utils.scheduler.scheduler") as mock_scheduler:
            mock_scheduler.running = False
            shutdown_scheduler()
            mock_scheduler.shutdown.assert_not_called()
