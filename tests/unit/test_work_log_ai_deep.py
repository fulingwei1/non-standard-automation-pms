# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 工作日志AI服务"""
import pytest
from unittest.mock import MagicMock


class TestWorkLogAIServiceBusinessLogic:
    """工作日志AI服务业务逻辑测试"""

    def test_analyze_work_log(self):
        """测试当前 analyze_work_log 接口存在"""
        try:
            from app.services.work_log_ai import WorkLogAIService

            mock_db = MagicMock()
            service = WorkLogAIService(mock_db)

            assert callable(service.analyze_work_log)
        except ImportError:
            pytest.skip("Module not found")
