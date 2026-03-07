# -*- coding: utf-8 -*-
"""KPI采集器注册器单元测试"""
import pytest

from app.services.strategy.kpi_collector.registry import (
    _collectors,
    get_collector,
    register_collector,
)


class TestKpiRegistry:
    def setup_method(self):
        self._backup = dict(_collectors)

    def teardown_method(self):
        _collectors.clear()
        _collectors.update(self._backup)

    def test_register_and_get(self):
        @register_collector("test_module")
        def my_collector():
            return "data"

        assert get_collector("test_module") is my_collector
        assert my_collector() == "data"

    def test_get_nonexistent(self):
        assert get_collector("nonexistent") is None
