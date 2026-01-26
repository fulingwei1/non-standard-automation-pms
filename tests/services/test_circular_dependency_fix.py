# -*- coding: utf-8 -*-
"""
循环依赖修复验证测试

测试目标：
1. 验证所有模块可以正常导入（无 ImportError）
2. 验证服务可以正常实例化
3. 验证延迟导入不影响功能
"""

import pytest


class TestCircularDependencyFix:
    """循环依赖修复测试套件"""

    def test_labor_cost_service_import(self):
        """测试人工成本服务可以正常导入"""
        try:
            from app.services.labor_cost_service import LaborCostService
            assert LaborCostService is not None
        except ImportError as e:
            pytest.fail(f"导入 LaborCostService 失败: {e}")

    def test_labor_cost_calculation_service_import(self):
        """测试人工成本计算服务可以正常导入"""
        try:
            from app.services.labor_cost_calculation_service import (
                process_user_costs,
                query_approved_timesheets,
                delete_existing_costs,
            )
            assert process_user_costs is not None
            assert query_approved_timesheets is not None
            assert delete_existing_costs is not None
        except ImportError as e:
            pytest.fail(f"导入 labor_cost_calculation_service 失败: {e}")

    def test_labor_cost_utils_import(self):
        """测试人工成本工具模块可以正常导入"""
        try:
            from app.services.labor_cost.utils import (
                query_approved_timesheets,
                delete_existing_costs,
                group_timesheets_by_user,
                find_existing_cost,
                update_existing_cost,
                create_new_cost,
                check_budget_alert,
            )
            assert query_approved_timesheets is not None
            assert delete_existing_costs is not None
            assert group_timesheets_by_user is not None
            assert find_existing_cost is not None
            assert update_existing_cost is not None
            assert create_new_cost is not None
            assert check_budget_alert is not None
        except ImportError as e:
            pytest.fail(f"导入 labor_cost.utils 失败: {e}")

    def test_status_transition_service_import(self):
        """测试状态转换服务可以正常导入"""
        try:
            from app.services.status_transition_service import StatusTransitionService
            assert StatusTransitionService is not None
        except ImportError as e:
            pytest.fail(f"导入 StatusTransitionService 失败: {e}")

    def test_status_handlers_import(self):
        """测试状态处理器可以正常导入"""
        try:
            from app.services.status_handlers.contract_handler import ContractStatusHandler
            from app.services.status_handlers.material_handler import MaterialStatusHandler
            from app.services.status_handlers.acceptance_handler import AcceptanceStatusHandler
            from app.services.status_handlers.ecn_handler import ECNStatusHandler

            assert ContractStatusHandler is not None
            assert MaterialStatusHandler is not None
            assert AcceptanceStatusHandler is not None
            assert ECNStatusHandler is not None
        except ImportError as e:
            pytest.fail(f"导入状态处理器失败: {e}")

    def test_status_transition_service_instantiation(self, db_session):
        """测试状态转换服务可以正常实例化"""
        from app.services.status_transition_service import StatusTransitionService

        try:
            service = StatusTransitionService(db_session)
            assert service is not None
            assert hasattr(service, 'contract_handler')
            assert hasattr(service, 'material_handler')
            assert hasattr(service, 'acceptance_handler')
            assert hasattr(service, 'ecn_handler')
        except Exception as e:
            pytest.fail(f"实例化 StatusTransitionService 失败: {e}")

    def test_status_handlers_are_loaded(self, db_session):
        """测试状态处理器已正确加载"""
        from app.services.status_transition_service import StatusTransitionService

        service = StatusTransitionService(db_session)

        # 验证处理器已加载
        assert service.contract_handler is not None
        assert service.material_handler is not None
        assert service.acceptance_handler is not None
        assert service.ecn_handler is not None

        # 验证处理器类型正确
        from app.services.status_handlers.contract_handler import ContractStatusHandler
        from app.services.status_handlers.material_handler import MaterialStatusHandler
        from app.services.status_handlers.acceptance_handler import AcceptanceStatusHandler
        from app.services.status_handlers.ecn_handler import ECNStatusHandler

        assert isinstance(service.contract_handler, ContractStatusHandler)
        assert isinstance(service.material_handler, MaterialStatusHandler)
        assert isinstance(service.acceptance_handler, AcceptanceStatusHandler)
        assert isinstance(service.ecn_handler, ECNStatusHandler)

    def test_no_circular_import_error_at_runtime(self):
        """测试运行时不会出现循环导入错误"""
        import sys

        # 清除可能的缓存模块
        modules_to_clear = [
            'app.services.status_transition_service',
            'app.services.status_handlers',
            'app.services.status_handlers.contract_handler',
            'app.services.labor_cost_service',
            'app.services.labor_cost_calculation_service',
        ]

        for module in modules_to_clear:
            if module in sys.modules:
                del sys.modules[module]

        # 尝试导入 - 不应该出现 ImportError
        try:
            from app.services.status_transition_service import StatusTransitionService
            from app.services.labor_cost_service import LaborCostService

            assert StatusTransitionService is not None
            assert LaborCostService is not None
        except ImportError as e:
            pytest.fail(f"运行时循环导入错误: {e}")

    def test_labor_cost_service_methods_accessible(self):
        """测试人工成本服务方法可以访问"""
        from app.services.labor_cost_service import LaborCostService

        # 验证静态方法存在
        assert hasattr(LaborCostService, 'get_user_hourly_rate')
        assert hasattr(LaborCostService, 'calculate_project_labor_cost')
        assert hasattr(LaborCostService, 'calculate_all_projects_labor_cost')
        assert hasattr(LaborCostService, 'calculate_monthly_labor_cost')

        # 验证方法可调用
        assert callable(LaborCostService.get_user_hourly_rate)
        assert callable(LaborCostService.calculate_project_labor_cost)

    def test_status_transition_service_methods_accessible(self, db_session):
        """测试状态转换服务方法可以访问"""
        from app.services.status_transition_service import StatusTransitionService

        service = StatusTransitionService(db_session)

        # 验证方法存在
        assert hasattr(service, 'handle_contract_signed')
        assert hasattr(service, 'handle_bom_published')

        # 验证方法可调用
        assert callable(service.handle_contract_signed)
        assert callable(service.handle_bom_published)


class TestDelayedImportPattern:
    """延迟导入模式测试"""

    def test_lazy_import_in_process_user_costs(self):
        """测试 process_user_costs 使用了延迟导入"""
        import inspect
        from app.services.labor_cost_calculation_service import process_user_costs

        # 获取函数源代码
        source = inspect.getsource(process_user_costs)

        # 验证包含延迟导入注释
        assert '延迟导入' in source or 'lazy import' in source.lower()

        # 验证导入在函数内部
        assert 'from app.services.labor_cost_service import LaborCostService' in source

    def test_lazy_import_in_status_transition_service_init(self):
        """测试 StatusTransitionService.__init__ 使用了延迟导入"""
        import inspect
        from app.services.status_transition_service import StatusTransitionService

        # 获取 __init__ 源代码
        source = inspect.getsource(StatusTransitionService.__init__)

        # 验证包含延迟导入注释
        assert '延迟导入' in source or 'lazy import' in source.lower()

        # 验证导入在方法内部
        assert 'from app.services.status_handlers' in source


class TestModuleLevelImports:
    """模块级导入测试 - 验证没有危险的模块级循环导入"""

    def test_no_module_level_import_in_labor_cost_calculation_service(self):
        """验证 labor_cost_calculation_service 没有模块级导入 LaborCostService"""
        import inspect
        from app.services import labor_cost_calculation_service

        source = inspect.getsource(labor_cost_calculation_service)
        lines = source.split('\n')

        # 检查前50行（模块级别）
        module_level_lines = []
        in_function = False
        for line in lines[:50]:
            if line.strip().startswith('def ') or line.strip().startswith('class '):
                in_function = True
            if not in_function:
                module_level_lines.append(line)

        module_level_code = '\n'.join(module_level_lines)

        # 验证模块级别没有导入 LaborCostService
        assert 'from app.services.labor_cost_service import LaborCostService' not in module_level_code, \
            "labor_cost_calculation_service 在模块级别导入了 LaborCostService，违反了延迟导入原则"

    def test_no_module_level_import_in_status_transition_service(self):
        """验证 status_transition_service 没有模块级导入 status_handlers"""
        import inspect
        from app.services import status_transition_service

        source = inspect.getsource(status_transition_service)
        lines = source.split('\n')

        # 检查前50行（模块级别）
        module_level_lines = []
        in_class = False
        for line in lines[:50]:
            if line.strip().startswith('class '):
                in_class = True
                break
            # 跳过注释行
            if not line.strip().startswith('#'):
                module_level_lines.append(line)

        module_level_code = '\n'.join(module_level_lines)

        # 验证模块级别没有导入处理器
        assert 'from app.services.status_handlers import' not in module_level_code, \
            "status_transition_service 在模块级别导入了 status_handlers，违反了延迟导入原则"
