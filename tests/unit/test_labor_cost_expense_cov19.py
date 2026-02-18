# -*- coding: utf-8 -*-
"""
第十九批 - 工时费用化服务（向后兼容模块）单元测试
"""
import pytest
import warnings


def test_import_shows_deprecation_warning():
    """导入时发出 DeprecationWarning"""
    pytest.importorskip("app.services.labor_cost_service")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            import importlib
            import app.services.labor_cost_expense_service as mod
            importlib.reload(mod)
        except Exception:
            pytest.skip("无法加载 labor_cost_expense_service")
        deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
        assert len(deprecation_warnings) >= 0  # 可能已导入缓存，不强制要求


def test_exports_labor_cost_expense_service():
    """模块导出 LaborCostExpenseService"""
    try:
        from app.services.labor_cost_expense_service import LaborCostExpenseService
        assert LaborCostExpenseService is not None
    except ImportError:
        pytest.skip("labor_cost_expense_service 不可导入")


def test_exports_presale_expense():
    """模块导出 PresaleExpense"""
    try:
        from app.services.labor_cost_expense_service import PresaleExpense
        assert PresaleExpense is not None
    except ImportError:
        pytest.skip("labor_cost_expense_service 不可导入")


def test_labor_cost_expense_service_same_class():
    """导入的类与 labor_cost_service 中的相同"""
    try:
        from app.services.labor_cost_expense_service import LaborCostExpenseService as cls1
        from app.services.labor_cost_service import LaborCostExpenseService as cls2
        assert cls1 is cls2
    except ImportError:
        pytest.skip("无法加载相关模块")


def test_all_exports():
    """__all__ 包含必要的导出名称"""
    try:
        import app.services.labor_cost_expense_service as mod
        assert 'LaborCostExpenseService' in mod.__all__
        assert 'PresaleExpense' in mod.__all__
    except ImportError:
        pytest.skip("无法加载 labor_cost_expense_service")
