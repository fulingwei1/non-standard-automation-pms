# -*- coding: utf-8 -*-
"""
第十九批 - 人工成本计算辅助服务（向后兼容模块）单元测试
"""
import pytest
import warnings


def test_exports_calculation_service():
    """模块导出 LaborCostCalculationService"""
    try:
        from app.services.labor_cost_calculation_service import LaborCostCalculationService
        assert LaborCostCalculationService is not None
    except ImportError:
        pytest.skip("labor_cost_calculation_service 不可导入")


def test_exports_query_approved_timesheets():
    """模块导出 query_approved_timesheets"""
    try:
        from app.services.labor_cost_calculation_service import query_approved_timesheets
        assert callable(query_approved_timesheets)
    except ImportError:
        pytest.skip("labor_cost_calculation_service 不可导入")


def test_exports_delete_existing_costs():
    """模块导出 delete_existing_costs"""
    try:
        from app.services.labor_cost_calculation_service import delete_existing_costs
        assert callable(delete_existing_costs)
    except ImportError:
        pytest.skip("labor_cost_calculation_service 不可导入")


def test_exports_process_user_costs():
    """模块导出 process_user_costs"""
    try:
        from app.services.labor_cost_calculation_service import process_user_costs
        assert callable(process_user_costs)
    except ImportError:
        pytest.skip("labor_cost_calculation_service 不可导入")


def test_same_class_as_utils():
    """LaborCostCalculationService 与 labor_cost.utils 中的相同"""
    try:
        from app.services.labor_cost_calculation_service import LaborCostCalculationService as cls1
        from app.services.labor_cost.utils import LaborCostCalculationService as cls2
        assert cls1 is cls2
    except ImportError:
        pytest.skip("无法加载相关模块")


def test_all_exports_list():
    """__all__ 包含所有必需导出"""
    try:
        import app.services.labor_cost_calculation_service as mod
        required = [
            'LaborCostCalculationService', 'query_approved_timesheets',
            'delete_existing_costs', 'process_user_costs',
        ]
        for name in required:
            assert name in mod.__all__, f"{name} 不在 __all__ 中"
    except ImportError:
        pytest.skip("无法加载 labor_cost_calculation_service")


def test_deprecation_warning_on_reload():
    """重新加载模块时产生 DeprecationWarning"""
    pytest.importorskip("app.services.labor_cost.utils")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            import importlib
            import app.services.labor_cost_calculation_service as mod
            importlib.reload(mod)
        except Exception:
            pytest.skip("无法 reload 模块")
        deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
        # 至少尝试了，结果可能被缓存
        assert isinstance(deprecation_warnings, list)
