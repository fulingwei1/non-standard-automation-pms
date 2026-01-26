# -*- coding: utf-8 -*-
"""
Scheduler 模块单元测试
测试定时任务调度器的初始化和关闭功能
"""

import json
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.background import BackgroundScheduler


class TestJobListener:
    """Test job_listener function"""

    @patch('app.utils.scheduler.logger')
    def test_job_listener_success(self, mock_logger):
        """Test job_listener logs success event"""
        from app.utils.scheduler import job_listener
        
        # Create mock event
        mock_event = MagicMock()
        mock_event.job_id = "test_job"
        mock_event.jobstore = "default"
        mock_event.scheduled_run_time = datetime.now(timezone.utc)
        mock_event.exception = None
        
        job_listener(mock_event)
        
        # Verify logger.info was called
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "test_job" in call_args
        assert "success" in call_args

    @patch('app.utils.scheduler.logger')
    def test_job_listener_failure(self, mock_logger):
        """Test job_listener logs failure event"""
        from app.utils.scheduler import job_listener
        
        # Create mock event with exception
        mock_event = MagicMock()
        mock_event.job_id = "test_job"
        mock_event.jobstore = "default"
        mock_event.scheduled_run_time = datetime.now(timezone.utc)
        mock_event.exception = ValueError("Test error")
        
        job_listener(mock_event)
        
        # Verify logger.error was called
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        assert "test_job" in call_args
        assert "failed" in call_args
        assert "Test error" in call_args


class TestResolveCallable:
    """Test _resolve_callable function"""

    def test_resolve_callable_success(self):
        """Test resolving callable from module"""
        from app.utils.scheduler import _resolve_callable
        
        task = {
            "module": "app.utils.scheduler",
            "callable": "job_listener"
        }
        
        func = _resolve_callable(task)
        assert callable(func)
        assert func.__name__ == "job_listener"

    def test_resolve_callable_module_not_found(self):
        """Test resolving callable with invalid module"""
        from app.utils.scheduler import _resolve_callable
        
        task = {
            "module": "nonexistent.module",
            "callable": "some_function"
        }
        
        with pytest.raises(ModuleNotFoundError):
            _resolve_callable(task)

    def test_resolve_callable_function_not_found(self):
        """Test resolving callable with invalid function"""
        from app.utils.scheduler import _resolve_callable
        
        task = {
            "module": "app.utils.scheduler",
            "callable": "nonexistent_function"
        }
        
        with pytest.raises(AttributeError):
            _resolve_callable(task)


class TestWrapJobCallable:
    """Test _wrap_job_callable function"""

    @patch('app.utils.scheduler.logger')
    @patch('app.utils.scheduler.record_job_success')
    def test_wrap_job_callable_success(self, mock_record_success, mock_logger):
        """Test wrapped job callable logs success"""
        from app.utils.scheduler import _wrap_job_callable
        
        def test_func():
            return "success"
        
        task = {
            "id": "test_job",
            "name": "Test Job",
            "owner": "test",
            "category": "test"
        }
        
        wrapped = _wrap_job_callable(test_func, task)
        result = wrapped()
        
        assert result == "success"
        mock_logger.info.assert_called()
        mock_record_success.assert_called_once()

    @patch('app.utils.scheduler.logger')
    @patch('app.utils.scheduler.record_job_failure')
    def test_wrap_job_callable_failure(self, mock_record_failure, mock_logger):
        """Test wrapped job callable logs failure"""
        from app.utils.scheduler import _wrap_job_callable
        
        def test_func():
            raise ValueError("Test error")
        
        task = {
            "id": "test_job",
            "name": "Test Job",
            "owner": "test",
            "category": "test"
        }
        
        wrapped = _wrap_job_callable(test_func, task)
        
        with pytest.raises(ValueError):
            wrapped()
        
        mock_logger.error.assert_called()
        mock_record_failure.assert_called_once()

    @patch('app.utils.scheduler.logger')
    @patch('app.utils.scheduler.record_job_success')
    def test_wrap_job_callable_duration_tracking(self, mock_record_success, mock_logger):
        """Test wrapped job callable tracks duration"""
        from app.utils.scheduler import _wrap_job_callable
        
        def slow_func():
            time.sleep(0.1)
            return "done"
        
        task = {
            "id": "test_job",
            "name": "Test Job",
            "owner": "test",
            "category": "test"
        }
        
        wrapped = _wrap_job_callable(slow_func, task)
        wrapped()
        
        # Verify duration was recorded
        call_args = mock_record_success.call_args
        assert call_args[0][0] == "test_job"
        assert call_args[0][1] > 0  # duration_ms > 0


class TestLoadTaskConfigFromDb:
    """Test _load_task_config_from_db function"""

    @patch('app.models.base.get_db_session')
    def test_load_task_config_from_db_success(self, mock_get_db_session):
        """Test loading task config from database"""
        from app.utils.scheduler import _load_task_config_from_db
        
        # Mock database session
        mock_db = MagicMock()
        mock_config = MagicMock()
        mock_config.task_id = "test_task"
        mock_config.is_enabled = True
        mock_config.cron_config = {"hour": 10, "minute": 0}
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_config
        mock_db.query.return_value = mock_query
        
        mock_get_db_session.return_value.__enter__.return_value = mock_db
        mock_get_db_session.return_value.__exit__.return_value = None
        
        result = _load_task_config_from_db("test_task")
        
        assert result is not None
        assert result["enabled"] is True
        assert "cron" in result

    @patch('app.models.base.get_db_session')
    def test_load_task_config_from_db_not_found(self, mock_get_db_session):
        """Test loading task config when not found"""
        from app.utils.scheduler import _load_task_config_from_db
        
        # Mock database session
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        mock_get_db_session.return_value.__enter__.return_value = mock_db
        mock_get_db_session.return_value.__exit__.return_value = None
        
        result = _load_task_config_from_db("test_task")
        
        assert result is None

    @patch('app.utils.scheduler.logger')
    @patch('app.models.base.get_db_session')
    def test_load_task_config_from_db_exception(self, mock_get_db_session, mock_logger):
        """Test loading task config handles exceptions"""
        from app.utils.scheduler import _load_task_config_from_db
        
        mock_get_db_session.side_effect = Exception("Database error")
        
        result = _load_task_config_from_db("test_task")
        
        assert result is None
        mock_logger.warning.assert_called_once()


class TestInitScheduler:
    """Test init_scheduler function"""

    @patch('app.utils.scheduler.scheduler')
    @patch('app.utils.scheduler._load_task_config_from_db')
    @patch('app.utils.scheduler._resolve_callable')
    @patch('app.utils.scheduler._wrap_job_callable')
    @patch('app.utils.scheduler.logger')
    def test_init_scheduler_with_tasks(self, mock_logger, mock_wrap, mock_resolve, mock_load_db, mock_scheduler):
        """Test initializing scheduler with tasks"""
        from app.utils.scheduler import init_scheduler, SCHEDULER_TASKS
        
        # Mock scheduler methods
        mock_scheduler.add_listener = Mock()
        mock_scheduler.add_job = Mock()
        mock_scheduler.start = Mock()
        mock_scheduler.running = False
        
        # Mock task resolution
        def mock_resolve_func(task):
            return lambda: None
        
        mock_resolve.side_effect = mock_resolve_func
        mock_wrap.side_effect = lambda func, task: func
        mock_load_db.return_value = None  # Use default config
        
        # Mock SCHEDULER_TASKS to have at least one enabled task
        with patch('app.utils.scheduler.SCHEDULER_TASKS', [
            {
                "id": "test_task",
                "name": "Test Task",
                "module": "app.utils.scheduler",
                "callable": "job_listener",
                "enabled": True,
                "cron": {"hour": 10}
            }
        ]):
            result = init_scheduler()
        
        assert result == mock_scheduler
        mock_scheduler.add_listener.assert_called_once()
        mock_scheduler.add_job.assert_called()
        mock_scheduler.start.assert_called_once()

    @patch('app.utils.scheduler.scheduler')
    @patch('app.utils.scheduler._load_task_config_from_db')
    @patch('app.utils.scheduler.logger')
    def test_init_scheduler_skips_disabled_tasks(self, mock_logger, mock_load_db, mock_scheduler):
        """Test scheduler skips disabled tasks"""
        from app.utils.scheduler import init_scheduler
        
        mock_scheduler.add_listener = Mock()
        mock_scheduler.add_job = Mock()
        mock_scheduler.start = Mock()
        mock_scheduler.running = False
        mock_load_db.return_value = {"enabled": False}
        
        with patch('app.utils.scheduler.SCHEDULER_TASKS', [
            {
                "id": "disabled_task",
                "name": "Disabled Task",
                "module": "app.utils.scheduler",
                "callable": "job_listener",
                "enabled": True,
                "cron": {"hour": 10}
            }
        ]):
            with patch('app.utils.scheduler._resolve_callable'):
                with patch('app.utils.scheduler._wrap_job_callable'):
                    init_scheduler()
        
        # Should not add disabled task
        mock_scheduler.add_job.assert_not_called()


class TestShutdownScheduler:
    """Test shutdown_scheduler function"""

    @patch('app.utils.scheduler.scheduler')
    @patch('app.utils.scheduler.logger')
    def test_shutdown_scheduler_when_running(self, mock_logger, mock_scheduler):
        """Test shutting down scheduler when running"""
        from app.utils.scheduler import shutdown_scheduler
        
        mock_scheduler.running = True
        mock_scheduler.shutdown = Mock()
        
        shutdown_scheduler()
        
        mock_scheduler.shutdown.assert_called_once()
        mock_logger.info.assert_called_once()

    @patch('app.utils.scheduler.scheduler')
    @patch('app.utils.scheduler.logger')
    def test_shutdown_scheduler_when_not_running(self, mock_logger, mock_scheduler):
        """Test shutting down scheduler when not running"""
        from app.utils.scheduler import shutdown_scheduler
        
        mock_scheduler.running = False
        mock_scheduler.shutdown = Mock()
        
        shutdown_scheduler()
        
        mock_scheduler.shutdown.assert_not_called()
        mock_logger.info.assert_not_called()
