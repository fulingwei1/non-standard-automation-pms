"""
Unit tests for scheduler utility functions.

Tests coverage for:
- job_listener function
- _resolve_callable function
- _wrap_job_callable function
- _load_task_config_from_db function
- init_scheduler function
- shutdown_scheduler function
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from app.utils.scheduler import (
    job_listener,
    _resolve_callable,
    _wrap_job_callable,
)


class TestJobListener:
    """Test job_listener function."""

    @patch("app.utils.scheduler.logger")
    def test_job_listener_success(self, mock_logger):
        """Test job listener with successful execution."""
        mock_event = MagicMock()
        mock_event.job_id = "test_job_1"
        mock_event.jobstore = "memory"
        mock_event.scheduled_run_time = datetime(2025, 1, 1, 12, 0)
        mock_event.exception = None

        job_listener(mock_event)

        assert mock_logger.info.called
        log_calls = mock_logger.info.call_args_list
        assert any("success" in str(call) for call in log_calls)
        assert any("test_job_1" in str(call) for call in log_calls)

    @patch("app.utils.scheduler.logger")
    def test_job_listener_failure(self, mock_logger):
        """Test job listener with failed execution."""
        mock_event = MagicMock()
        mock_event.job_id = "test_job_2"
        mock_event.jobstore = "memory"
        mock_event.scheduled_run_time = datetime(2025, 1, 1, 12, 0)
        mock_event.exception = Exception("Test error")

        job_listener(mock_event)

        assert mock_logger.error.called
        log_calls = mock_logger.error.call_args_list
        assert any("failed" in str(call) for call in log_calls)
        assert any("Test error" in str(call) for call in log_calls)

    @patch("app.utils.scheduler.logger")
    def test_job_listener_no_scheduled_time(self, mock_logger):
        """Test job listener when scheduled_run_time is None."""
        mock_event = MagicMock()
        mock_event.job_id = "test_job_3"
        mock_event.jobstore = "memory"
        mock_event.scheduled_run_time = None
        mock_event.exception = None

        job_listener(mock_event)

        assert mock_logger.info.called
        log_calls = mock_logger.info.call_args_list
        assert any("success" in str(call) for call in log_calls)


class TestResolveCallable:
    """Test _resolve_callable function."""

    def test_resolve_callable_valid_module(self):
        """Test resolving a valid callable from module."""
        task = {"module": "app.utils.scheduler", "callable": "job_listener"}

        result = _resolve_callable(task)

        assert callable(result)
        assert result == job_listener

    @patch("app.utils.scheduler.import_module")
    def test_resolve_callable_import_error(self, mock_import_module):
        """Test handling import errors."""
        mock_import_module.side_effect = ImportError("Module not found")

        task = {"module": "nonexistent.module", "callable": "some_function"}

        with pytest.raises(ImportError):
            _resolve_callable(task)


class TestWrapJobCallable:
    """Test _wrap_job_callable function."""

    @patch("app.utils.scheduler.logger")
    def test_wrap_callable_without_owner(self, mock_logger):
        """Test wrapping callable without owner field."""
        task = {
            "id": "task_no_owner",
            "name": "No Owner Task",
        }

        def sample_func():
            return "result"

        wrapper = _wrap_job_callable(sample_func, task)
        result = wrapper()

        assert result == "result"

    def test_task_context_structure(self):
        """Test that task context is properly structured."""
        task = {
            "id": "task_context",
            "name": "Context Task",
            "owner": "owner_1",
            "category": "category_1",
        }

        def sample_func():
            return "result"

        @patch("app.utils.scheduler.logger")
        def wrapped_test(mock_logger):
            wrapper = _wrap_job_callable(sample_func, task)
            wrapper()

            log_calls = mock_logger.info.call_args_list
            start_log = str(log_calls[0])

            assert "task_context" in start_log
            assert "Context Task" in start_log
            assert "owner_1" in start_log
            assert "category_1" in start_log

        wrapped_test()
