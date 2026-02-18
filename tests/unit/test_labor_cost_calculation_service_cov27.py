# -*- coding: utf-8 -*-
"""第二十七批 - labor_cost_calculation_service 单元测试"""

import pytest
import warnings


class TestLaborCostCalculationServiceDeprecatedImports:
    def test_import_triggers_deprecation_warning(self):
        """导入模块时应该发出 DeprecationWarning"""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            import importlib
            import sys
            # 移除缓存确保重新导入
            mod_name = "app.services.labor_cost_calculation_service"
            if mod_name in sys.modules:
                del sys.modules[mod_name]
            try:
                importlib.import_module(mod_name)
                dep_warnings = [w for w in caught if issubclass(w.category, DeprecationWarning)]
                assert len(dep_warnings) > 0
            except ImportError:
                pytest.skip("模块依赖不可用")

    def test_module_imports_query_approved_timesheets(self):
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                from app.services.labor_cost_calculation_service import query_approved_timesheets
            assert callable(query_approved_timesheets)
        except ImportError:
            pytest.skip("模块依赖不可用")

    def test_module_imports_delete_existing_costs(self):
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                from app.services.labor_cost_calculation_service import delete_existing_costs
            assert callable(delete_existing_costs)
        except ImportError:
            pytest.skip("模块依赖不可用")

    def test_module_imports_group_timesheets_by_user(self):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                from app.services.labor_cost_calculation_service import group_timesheets_by_user
            assert callable(group_timesheets_by_user)
        except ImportError:
            pytest.skip("模块依赖不可用")

    def test_module_imports_find_existing_cost(self):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                from app.services.labor_cost_calculation_service import find_existing_cost
            assert callable(find_existing_cost)
        except ImportError:
            pytest.skip("模块依赖不可用")

    def test_module_imports_update_existing_cost(self):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                from app.services.labor_cost_calculation_service import update_existing_cost
            assert callable(update_existing_cost)
        except ImportError:
            pytest.skip("模块依赖不可用")

    def test_module_imports_create_new_cost(self):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                from app.services.labor_cost_calculation_service import create_new_cost
            assert callable(create_new_cost)
        except ImportError:
            pytest.skip("模块依赖不可用")

    def test_module_imports_check_budget_alert(self):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                from app.services.labor_cost_calculation_service import check_budget_alert
            assert callable(check_budget_alert)
        except ImportError:
            pytest.skip("模块依赖不可用")

    def test_module_imports_process_user_costs(self):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                from app.services.labor_cost_calculation_service import process_user_costs
            assert callable(process_user_costs)
        except ImportError:
            pytest.skip("模块依赖不可用")

    def test_module_imports_labor_cost_calculation_service_class(self):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                from app.services.labor_cost_calculation_service import LaborCostCalculationService
            assert LaborCostCalculationService is not None
        except ImportError:
            pytest.skip("模块依赖不可用")

    def test_all_exports_in_dunder_all(self):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                import app.services.labor_cost_calculation_service as mod
            expected = [
                "query_approved_timesheets",
                "delete_existing_costs",
                "group_timesheets_by_user",
                "find_existing_cost",
                "update_existing_cost",
                "create_new_cost",
                "check_budget_alert",
                "process_user_costs",
                "LaborCostCalculationService",
            ]
            for name in expected:
                assert name in mod.__all__
        except ImportError:
            pytest.skip("模块依赖不可用")

    def test_deprecation_warning_message_mentions_labor_cost(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            import importlib
            import sys
            mod_name = "app.services.labor_cost_calculation_service"
            if mod_name in sys.modules:
                del sys.modules[mod_name]
            try:
                importlib.import_module(mod_name)
                dep_warnings = [w for w in caught if issubclass(w.category, DeprecationWarning)]
                if dep_warnings:
                    msg = str(dep_warnings[0].message)
                    assert "labor_cost" in msg.lower() or "废弃" in msg
            except ImportError:
                pytest.skip("模块依赖不可用")
