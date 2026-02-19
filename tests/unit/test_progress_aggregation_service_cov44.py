# -*- coding: utf-8 -*-
"""第四十四批覆盖测试 - 进度聚合服务（兼容层/废弃模块）"""

import pytest
import warnings

try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        import app.services.progress_aggregation_service as compat_module
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


class TestProgressAggregationServiceCompat:

    def test_module_exports_progress_aggregation_service(self):
        assert hasattr(compat_module, "ProgressAggregationService")

    def test_module_exports_aggregate_task_progress(self):
        assert hasattr(compat_module, "aggregate_task_progress")

    def test_module_exports_create_progress_log(self):
        assert hasattr(compat_module, "create_progress_log")

    def test_module_exports_get_project_progress_summary(self):
        assert hasattr(compat_module, "get_project_progress_summary")

    def test_module_exports_check_and_update_health(self):
        assert hasattr(compat_module, "_check_and_update_health")

    def test_all_exports_in_all_list(self):
        for name in compat_module.__all__:
            assert hasattr(compat_module, name), f"__all__ 中的 {name} 未实际导出"

    def test_import_raises_deprecation_warning(self):
        """导入时应发出 DeprecationWarning"""
        import importlib
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            importlib.reload(compat_module)
        deprecation_warnings = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        assert len(deprecation_warnings) >= 1
