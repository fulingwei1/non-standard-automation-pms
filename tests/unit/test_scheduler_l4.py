# -*- coding: utf-8 -*-
"""
Unit tests for app/utils/scheduler.py — L4组补充
重点覆盖 _wrap_job_callable、job_listener、shutdown_scheduler 等
"""

import json
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch, call

import pytest


# ---------------------------------------------------------------------------
# job_listener
# ---------------------------------------------------------------------------

class TestJobListenerL4:
    """Tests for job_listener — supplemental L4."""

    def test_success_event_payload_structure(self):
        """Success event JSON payload contains expected keys."""
        from app.utils.scheduler import job_listener

        mock_event = MagicMock()
        mock_event.job_id = "sync_task"
        mock_event.jobstore = "default"
        mock_event.scheduled_run_time = datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
        mock_event.exception = None

        with patch("app.utils.scheduler.logger") as mock_logger:
            job_listener(mock_event)

        call_str = mock_logger.info.call_args[0][0]
        # Parse embedded JSON
        json_part = call_str.replace("[scheduler] ", "")
        payload = json.loads(json_part)
        assert payload["job_id"] == "sync_task"
        assert payload["status"] == "success"
        assert "scheduled_time" in payload

    def test_failure_event_payload_contains_error(self):
        """Failure event JSON includes error string."""
        from app.utils.scheduler import job_listener

        mock_event = MagicMock()
        mock_event.job_id = "broken_task"
        mock_event.jobstore = "default"
        mock_event.scheduled_run_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        mock_event.exception = RuntimeError("connection timeout")

        with patch("app.utils.scheduler.logger") as mock_logger:
            job_listener(mock_event)

        call_str = mock_logger.error.call_args[0][0]
        json_part = call_str.replace("[scheduler] ", "")
        payload = json.loads(json_part)
        assert payload["status"] == "failed"
        assert "connection timeout" in payload["error"]

    def test_scheduled_time_none_handled(self):
        """job_listener handles None scheduled_run_time gracefully."""
        from app.utils.scheduler import job_listener

        mock_event = MagicMock()
        mock_event.job_id = "job1"
        mock_event.jobstore = "default"
        mock_event.scheduled_run_time = None
        mock_event.exception = None

        with patch("app.utils.scheduler.logger") as mock_logger:
            job_listener(mock_event)  # should not raise
        mock_logger.info.assert_called_once()


# ---------------------------------------------------------------------------
# _wrap_job_callable
# ---------------------------------------------------------------------------

class TestWrapJobCallableL4:
    """Tests for _wrap_job_callable — direct invocation."""

    def _make_task(self, task_id="job_x"):
        return {
            "id": task_id,
            "name": "Test Job",
            "owner": "team",
            "category": "sync",
        }

    def test_success_logs_start_and_success(self):
        """Wrapper logs job_run_start and job_run_success on normal execution."""
        from app.utils.scheduler import _wrap_job_callable

        def simple_func():
            return "ok"

        task = self._make_task()

        with patch("app.utils.scheduler.logger") as mock_logger, \
             patch("app.utils.scheduler.record_job_success") as mock_success:
            wrapped = _wrap_job_callable(simple_func, task)
            result = wrapped()

        assert result == "ok"
        # Two info logs: start + success
        assert mock_logger.info.call_count == 2
        start_log = mock_logger.info.call_args_list[0][0][0]
        end_log = mock_logger.info.call_args_list[1][0][0]
        assert "job_run_start" in start_log
        assert "job_run_success" in end_log

    def test_failure_logs_error_and_reraises(self):
        """Wrapper logs job_run_failed and re-raises the exception."""
        from app.utils.scheduler import _wrap_job_callable

        def failing_func():
            raise ValueError("something went wrong")

        task = self._make_task("failing_job")

        with patch("app.utils.scheduler.logger") as mock_logger, \
             patch("app.utils.scheduler.record_job_failure") as mock_fail:
            wrapped = _wrap_job_callable(failing_func, task)
            with pytest.raises(ValueError, match="something went wrong"):
                wrapped()

        mock_logger.error.assert_called_once()
        error_log = mock_logger.error.call_args[0][0]
        assert "job_run_failed" in error_log
        assert "something went wrong" in error_log
        mock_fail.assert_called_once()

    def test_records_success_metrics(self):
        """record_job_success called with correct job_id and positive duration."""
        from app.utils.scheduler import _wrap_job_callable

        def func():
            return None

        task = self._make_task("metrics_job")

        with patch("app.utils.scheduler.logger"), \
             patch("app.utils.scheduler.record_job_success") as mock_success:
            wrapped = _wrap_job_callable(func, task)
            wrapped()

        args = mock_success.call_args[0]
        assert args[0] == "metrics_job"
        assert isinstance(args[1], float)
        assert args[1] >= 0  # duration_ms non-negative

    def test_records_failure_metrics(self):
        """record_job_failure called with correct job_id on exception."""
        from app.utils.scheduler import _wrap_job_callable

        def func():
            raise TypeError("type error")

        task = self._make_task("fail_metrics")

        with patch("app.utils.scheduler.logger"), \
             patch("app.utils.scheduler.record_job_failure") as mock_fail:
            wrapped = _wrap_job_callable(func, task)
            with pytest.raises(TypeError):
                wrapped()

        args = mock_fail.call_args[0]
        assert args[0] == "fail_metrics"

    def test_success_log_contains_duration_ms(self):
        """Success log payload includes a non-negative duration_ms."""
        from app.utils.scheduler import _wrap_job_callable

        def func():
            return 42

        task = self._make_task()

        with patch("app.utils.scheduler.logger") as mock_logger, \
             patch("app.utils.scheduler.record_job_success"):
            wrapped = _wrap_job_callable(func, task)
            wrapped()

        success_log = mock_logger.info.call_args_list[1][0][0]
        json_part = success_log.replace("[scheduler] ", "")
        payload = json.loads(json_part)
        assert "duration_ms" in payload
        assert payload["duration_ms"] >= 0


# ---------------------------------------------------------------------------
# _resolve_callable
# ---------------------------------------------------------------------------

class TestResolveCallableL4:
    """Tests for _resolve_callable."""

    def test_resolves_function_from_module(self):
        """Resolves a real function by module + callable name."""
        from app.utils.scheduler import _resolve_callable

        task = {"module": "app.utils.scheduler", "callable": "job_listener"}
        func = _resolve_callable(task)
        assert callable(func)

    def test_raises_on_invalid_module(self):
        """ModuleNotFoundError raised for unknown module."""
        from app.utils.scheduler import _resolve_callable

        with pytest.raises(ModuleNotFoundError):
            _resolve_callable({"module": "no.such.module", "callable": "fn"})

    def test_raises_on_invalid_callable(self):
        """AttributeError raised when callable not found in module."""
        from app.utils.scheduler import _resolve_callable

        with pytest.raises(AttributeError):
            _resolve_callable({"module": "app.utils.scheduler", "callable": "does_not_exist"})


# ---------------------------------------------------------------------------
# shutdown_scheduler
# ---------------------------------------------------------------------------

class TestShutdownSchedulerL4:
    """Tests for shutdown_scheduler."""

    def test_shuts_down_running_scheduler(self):
        """Calls scheduler.shutdown() when scheduler is running."""
        from app.utils.scheduler import shutdown_scheduler

        with patch("app.utils.scheduler.scheduler") as mock_sched, \
             patch("app.utils.scheduler.logger") as mock_logger:
            mock_sched.running = True
            shutdown_scheduler()

        mock_sched.shutdown.assert_called_once()
        mock_logger.info.assert_called_once()

    def test_does_nothing_when_not_running(self):
        """Does not call shutdown() if scheduler is not running."""
        from app.utils.scheduler import shutdown_scheduler

        with patch("app.utils.scheduler.scheduler") as mock_sched, \
             patch("app.utils.scheduler.logger") as mock_logger:
            mock_sched.running = False
            shutdown_scheduler()

        mock_sched.shutdown.assert_not_called()
        mock_logger.info.assert_not_called()


# ---------------------------------------------------------------------------
# _load_task_config_from_db
# ---------------------------------------------------------------------------

class TestLoadTaskConfigFromDbL4:
    """Tests for _load_task_config_from_db."""

    def test_returns_none_on_exception(self):
        """Returns None when an exception occurs."""
        from app.utils.scheduler import _load_task_config_from_db

        with patch("app.utils.scheduler.get_db_session", side_effect=Exception("DB down")), \
             patch("app.utils.scheduler.logger") as mock_logger:
            result = _load_task_config_from_db("some_task")

        assert result is None
        mock_logger.warning.assert_called_once()
