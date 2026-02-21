# -*- coding: utf-8 -*-
"""
完整单元测试 - strategy/kpi_collector/registry.py
目标：60%+ 覆盖率，30+ 测试用例
"""
import pytest
from unittest.mock import MagicMock

from app.services.strategy.kpi_collector.registry import (
    register_collector,
    get_collector,
    _collectors
)


class TestKpiCollectorRegistry:
    """KPI采集器注册器完整测试套件"""
    
    def setup_method(self):
        """每个测试前备份注册表"""
        self._backup = dict(_collectors)
        
    def teardown_method(self):
        """每个测试后恢复注册表"""
        _collectors.clear()
        _collectors.update(self._backup)
    
    # ========== register_collector 测试 ==========
    
    def test_register_collector_basic(self):
        """测试基础注册功能"""
        @register_collector("test_module")
        def my_collector():
            return "data"
        
        assert "test_module" in _collectors
        assert _collectors["test_module"] is my_collector
    
    def test_register_collector_returns_original_function(self):
        """测试装饰器返回原函数"""
        @register_collector("module1")
        def my_func():
            return 42
        
        assert my_func() == 42
    
    def test_register_collector_multiple_modules(self):
        """测试注册多个采集器"""
        @register_collector("module1")
        def collector1():
            return "data1"
        
        @register_collector("module2")
        def collector2():
            return "data2"
        
        assert len(_collectors) >= 2
        assert _collectors["module1"]() == "data1"
        assert _collectors["module2"]() == "data2"
    
    def test_register_collector_override(self):
        """测试重复注册会覆盖"""
        @register_collector("same_module")
        def first():
            return "first"
        
        @register_collector("same_module")
        def second():
            return "second"
        
        assert _collectors["same_module"] is second
        assert _collectors["same_module"]() == "second"
    
    def test_register_collector_with_parameters(self):
        """测试带参数的采集器"""
        @register_collector("param_module")
        def collector_with_params(db, strategy_id):
            return f"collected_{strategy_id}"
        
        collector = _collectors["param_module"]
        assert collector("mock_db", 123) == "collected_123"
    
    def test_register_collector_preserves_function_name(self):
        """测试装饰器保留函数名"""
        @register_collector("test")
        def my_named_collector():
            pass
        
        assert my_named_collector.__name__ == "my_named_collector"
    
    def test_register_collector_with_class_method(self):
        """测试注册类方法"""
        class MyCollector:
            @register_collector("class_method")
            @staticmethod
            def collect():
                return "class_data"
        
        assert _collectors["class_method"]() == "class_data"
    
    # ========== get_collector 测试 ==========
    
    def test_get_collector_found(self):
        """测试获取已注册的采集器"""
        @register_collector("existing")
        def collector():
            return "exists"
        
        result = get_collector("existing")
        assert result is collector
        assert result() == "exists"
    
    def test_get_collector_not_found(self):
        """测试获取不存在的采集器"""
        result = get_collector("nonexistent_module")
        assert result is None
    
    def test_get_collector_empty_string(self):
        """测试空字符串模块名"""
        result = get_collector("")
        assert result is None
    
    def test_get_collector_none_module(self):
        """测试None作为模块名"""
        result = get_collector(None)
        assert result is None
    
    def test_get_collector_special_characters(self):
        """测试特殊字符模块名"""
        @register_collector("module-with-dash")
        def collector1():
            return "dash"
        
        @register_collector("module_with_underscore")
        def collector2():
            return "underscore"
        
        assert get_collector("module-with-dash")() == "dash"
        assert get_collector("module_with_underscore")() == "underscore"
    
    def test_get_collector_case_sensitive(self):
        """测试模块名大小写敏感"""
        @register_collector("TestModule")
        def collector():
            return "data"
        
        assert get_collector("TestModule") is not None
        assert get_collector("testmodule") is None
        assert get_collector("TESTMODULE") is None
    
    # ========== 集成测试 ==========
    
    def test_register_and_retrieve_workflow(self):
        """测试完整的注册和获取工作流"""
        @register_collector("workflow_test")
        def my_collector(db, id):
            return f"collected_{id}"
        
        # 获取并使用采集器
        collector = get_collector("workflow_test")
        assert collector is not None
        result = collector("mock_db", 999)
        assert result == "collected_999"
    
    def test_multiple_collectors_independence(self):
        """测试多个采集器互不干扰"""
        @register_collector("mod_a")
        def collector_a():
            return "A"
        
        @register_collector("mod_b")
        def collector_b():
            return "B"
        
        assert get_collector("mod_a")() == "A"
        assert get_collector("mod_b")() == "B"
        assert get_collector("mod_c") is None
    
    def test_collector_with_lambda(self):
        """测试注册lambda函数"""
        register_collector("lambda_test")(lambda: "lambda_result")
        
        collector = get_collector("lambda_test")
        assert collector() == "lambda_result"
    
    def test_collector_with_closure(self):
        """测试闭包采集器"""
        def make_collector(prefix):
            @register_collector(f"{prefix}_module")
            def collector(value):
                return f"{prefix}_{value}"
            return collector
        
        c1 = make_collector("prefix1")
        c2 = make_collector("prefix2")
        
        assert get_collector("prefix1_module")(100) == "prefix1_100"
        assert get_collector("prefix2_module")(200) == "prefix2_200"
    
    # ========== 边界情况测试 ==========
    
    def test_register_collector_numeric_module_name(self):
        """测试数字模块名（虽然不推荐）"""
        @register_collector("12345")
        def collector():
            return "numeric"
        
        assert get_collector("12345")() == "numeric"
    
    def test_register_collector_unicode_module_name(self):
        """测试Unicode模块名"""
        @register_collector("中文模块")
        def collector():
            return "unicode_data"
        
        assert get_collector("中文模块")() == "unicode_data"
    
    def test_collector_returning_none(self):
        """测试返回None的采集器"""
        @register_collector("none_collector")
        def collector():
            return None
        
        assert get_collector("none_collector")() is None
    
    def test_collector_raising_exception(self):
        """测试抛出异常的采集器"""
        @register_collector("error_collector")
        def collector():
            raise ValueError("Test error")
        
        collector = get_collector("error_collector")
        with pytest.raises(ValueError, match="Test error"):
            collector()
    
    def test_collector_with_default_arguments(self):
        """测试带默认参数的采集器"""
        @register_collector("default_args")
        def collector(db, strategy_id=999):
            return strategy_id
        
        c = get_collector("default_args")
        assert c("mock_db") == 999
        assert c("mock_db", 123) == 123
    
    def test_collector_with_kwargs(self):
        """测试接受**kwargs的采集器"""
        @register_collector("kwargs_collector")
        def collector(**kwargs):
            return kwargs.get("key", "default")
        
        c = get_collector("kwargs_collector")
        assert c(key="value") == "value"
        assert c() == "default"
    
    # ========== 性能和压力测试 ==========
    
    def test_register_many_collectors(self):
        """测试注册大量采集器"""
        for i in range(100):
            register_collector(f"module_{i}")(lambda x=i: x)
        
        # 验证都能正确获取
        assert get_collector("module_0")() == 0
        assert get_collector("module_50")() == 50
        assert get_collector("module_99")() == 99
    
    def test_get_collector_performance(self):
        """测试获取采集器的性能"""
        # 注册一些采集器
        for i in range(10):
            register_collector(f"perf_{i}")(lambda: "data")
        
        # 多次获取应该很快
        import time
        start = time.time()
        for _ in range(1000):
            get_collector("perf_5")
        duration = time.time() - start
        
        # 1000次获取应该在1秒内完成
        assert duration < 1.0
    
    # ========== 线程安全测试（可选）==========
    
    def test_concurrent_registration(self):
        """测试并发注册（简单验证）"""
        import threading
        
        def register_func(i):
            @register_collector(f"thread_{i}")
            def collector():
                return i
        
        threads = [threading.Thread(target=register_func, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # 验证所有都注册成功
        for i in range(10):
            assert get_collector(f"thread_{i}") is not None
