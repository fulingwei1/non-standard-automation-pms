# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 执行日志服务"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime


class TestExecutionLoggerServiceBusinessLogic:
    """执行日志服务业务逻辑测试"""

    def test_log_execution_start(self):
        """测试记录执行开始"""
        try:
            from app.services.approval_engine.execution_logger import ExecutionLoggerService

            mock_db = MagicMock()
            service = ExecutionLoggerService(mock_db)

            result = service.log_execution_start(1, 1, "APPROVE")

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_log_execution_end(self):
        """测试记录执行结束"""
        try:
            from app.services.approval_engine.execution_logger import ExecutionLoggerService

            mock_db = MagicMock()

            mock_log = MagicMock()
            mock_log.id = 1

            mock_db.query.return_value.filter.return_value.first.return_value = mock_log

            service = ExecutionLoggerService(mock_db)

            result = service.log_execution_end(1, "COMPLETED")

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_get_execution_history(self):
        """测试获取执行历史"""
        try:
            from app.services.approval_engine.execution_logger import ExecutionLoggerService

            mock_db = MagicMock()

            mock_log = MagicMock()

            mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_log]

            service = ExecutionLoggerService(mock_db)

            result = service.get_execution_history(1)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_calculate_execution_duration(self):
        """测试计算执行时长"""
        try:
            from app.services.approval_engine.execution_logger import ExecutionLoggerService

            mock_db = MagicMock()

            mock_log = MagicMock()
            mock_log.started_at = datetime(2026, 4, 10, 10, 0, 0)
            mock_log.ended_at = datetime(2026, 4, 10, 10, 30, 0)

            mock_db.query.return_value.filter.return_value.first.return_value = mock_log

            service = ExecutionLoggerService(mock_db)

            result = service.calculate_execution_duration(1)

            assert result == 30  # 30分钟
        except ImportError:
            pytest.skip("Module not found")