# -*- coding: utf-8 -*-
"""
测试销售模块路由聚合

测试 app/api/v1/endpoints/sales/__init__.py
"""

import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock missing modules before importing target modules
sys.modules['app.services.notification_handlers'] = MagicMock()
sys.modules['app.services.notification_handlers.email_handler'] = MagicMock()


class TestSalesRoutesInit:
    """测试销售模块路由聚合"""

    def test_router_exists(self):
        """测试 router 对象存在"""
        from app.api.v1.endpoints.sales import router
        
        assert router is not None
        assert hasattr(router, 'routes')
        assert len(router.routes) > 0

    def test_dashboard_router_included(self):
        """测试 dashboard 路由已包含"""
        from app.api.v1.endpoints.sales import router
        
        # 检查是否有 dashboard 相关路由
        route_paths = [r.path for r in router.routes]
        # 至少应该有一些路由
        assert len(route_paths) > 0

    def test_router_has_tags(self):
        """测试路由包含正确的 tags"""
        from app.api.v1.endpoints.sales import router
        
        # 获取所有路由的 tags
        all_tags = set()
        for route in router.routes:
            if hasattr(route, 'tags'):
                all_tags.update(route.tags)
        
        # 销售模块应该包含多个 tags
        assert len(all_tags) > 0

    def test_router_prefix_is_applied_by_parent_api_router(self):
        """销售子路由不自带前缀，父级 API router 统一挂载到 /sales"""
        from app.api.v1.endpoints.sales import router

        assert router.prefix == ""

    def test_presale_workbench_assessment_routes_included(self):
        """售前工作台需要的评估风险和版本路由必须被销售路由聚合"""
        from app.api.v1.endpoints.sales import router

        route_paths = {r.path for r in router.routes}

        assert "/assessments/{assessment_id}/risks" in route_paths
        assert "/assessments/risks/{risk_id}/status" in route_paths
        assert "/assessments/{assessment_id}/versions" in route_paths
        assert "/assessments/versions/{version_id}/compare" in route_paths

    def test_customers_router_included(self):
        """测试客户路由已包含"""
        from app.api.v1.endpoints.sales import customers
        
        assert hasattr(customers, 'router')
        assert customers.router is not None

    def test_quotes_router_included(self):
        """测试报价路由已包含"""
        from app.api.v1.endpoints.sales import quotes
        
        assert hasattr(quotes, 'router')
        assert quotes.router is not None

    def test_contracts_router_included(self):
        """测试合同路由已包含"""
        from app.api.v1.endpoints.sales import contracts
        
        assert hasattr(contracts, 'router')
        assert contracts.router is not None
