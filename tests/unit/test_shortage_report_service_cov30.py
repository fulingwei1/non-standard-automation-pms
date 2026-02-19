# -*- coding: utf-8 -*-
"""
Unit tests for shortage_report_service (deprecated module) (第三十批)
"""
import warnings

import pytest


class TestShortageReportServiceDeprecated:
    def test_import_triggers_deprecation_warning(self):
        """验证导入 shortage_report_service 时触发 DeprecationWarning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            import importlib
            import app.services.shortage_report_service as _mod
            importlib.reload(_mod)

            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            assert len(deprecation_warnings) >= 1
            assert "shortage_report_service" in str(deprecation_warnings[0].message).lower() or \
                   "shortage" in str(deprecation_warnings[0].message).lower()

    def test_module_exports_expected_symbols(self):
        """验证废弃模块正确导出所有预期符号"""
        import app.services.shortage_report_service as mod

        expected_exports = [
            "calculate_alert_statistics",
            "calculate_report_statistics",
            "calculate_kit_statistics",
            "calculate_arrival_statistics",
            "calculate_response_time_statistics",
            "calculate_stoppage_statistics",
            "build_daily_report_data",
        ]
        for name in expected_exports:
            assert hasattr(mod, name), f"缺少导出符号: {name}"

    def test_module_all_is_defined(self):
        """验证 __all__ 已定义"""
        import app.services.shortage_report_service as mod
        assert hasattr(mod, "__all__")
        assert isinstance(mod.__all__, list)
        assert len(mod.__all__) > 0

    def test_symbols_are_callable(self):
        """验证导出的符号是可调用的（函数）"""
        import app.services.shortage_report_service as mod

        for name in mod.__all__:
            obj = getattr(mod, name)
            assert callable(obj), f"{name} 应该是可调用的"

    def test_functions_come_from_shortage_reports_service(self):
        """验证函数实际上来自 shortage.shortage_reports_service"""
        import app.services.shortage_report_service as deprecated_mod
        from app.services.shortage import shortage_reports_service as new_mod

        for name in deprecated_mod.__all__:
            deprecated_fn = getattr(deprecated_mod, name)
            new_fn = getattr(new_mod, name)
            assert deprecated_fn is new_fn, f"{name} 应该指向相同的函数"
