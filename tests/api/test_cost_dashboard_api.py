# -*- coding: utf-8 -*-
"""
成本仪表盘API测试
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.models.user import User


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """模拟认证用户"""
    user = MagicMock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.real_name = "测试用户"
    return user


@pytest.fixture
def auth_headers(mock_user):
    """模拟认证头"""
    # 简化版：实际测试应该使用真实的JWT token
    return {"Authorization": "Bearer test_token"}


class TestCostOverviewAPI:
    """测试成本总览API"""

    @patch("app.api.v1.endpoints.dashboard.cost_dashboard.deps.get_db")
    @patch("app.api.v1.endpoints.dashboard.cost_dashboard.security.require_permission")
    def test_get_cost_overview_success(self, mock_auth, mock_db, client, mock_user):
        """测试成功获取成本总览"""
        mock_auth.return_value = mock_user
        
        with patch("app.services.cost_dashboard_service.CostDashboardService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_cost_overview.return_value = {
                "total_projects": 10,
                "total_budget": 1000000,
                "total_actual_cost": 800000,
                "total_contract_amount": 1200000,
                "budget_execution_rate": 80.0,
                "cost_overrun_count": 2,
                "cost_normal_count": 5,
                "cost_alert_count": 3,
                "month_budget": 83333.33,
                "month_actual_cost": 70000,
                "month_variance": -13333.33,
                "month_variance_pct": -16.0,
            }
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/v1/dashboard/cost/overview")
            
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["total_projects"] == 10
            assert data["data"]["budget_execution_rate"] == 80.0

    @patch("app.api.v1.endpoints.dashboard.cost_dashboard.security.require_permission")
    def test_get_cost_overview_unauthorized(self, mock_auth, client):
        """测试未授权访问"""
        from fastapi import HTTPException
        mock_auth.side_effect = HTTPException(status_code=403, detail="权限不足")
        
        response = client.get("/api/v1/dashboard/cost/overview")
        
        assert response.status_code == 403


class TestTopProjectsAPI:
    """测试TOP项目API"""

    @patch("app.api.v1.endpoints.dashboard.cost_dashboard.deps.get_db")
    @patch("app.api.v1.endpoints.dashboard.cost_dashboard.security.require_permission")
    def test_get_top_projects_success(self, mock_auth, mock_db, client, mock_user):
        """测试成功获取TOP项目"""
        mock_auth.return_value = mock_user
        
        with patch("app.services.cost_dashboard_service.CostDashboardService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_top_projects.return_value = {
                "top_cost_projects": [
                    {
                        "project_id": 1,
                        "project_code": "P001",
                        "project_name": "项目1",
                        "actual_cost": 100000,
                        "budget_amount": 120000,
                        "cost_variance": -20000,
                        "cost_variance_pct": -16.67,
                        "profit": 50000,
                        "profit_margin": 33.33,
                    }
                ],
                "top_overrun_projects": [],
                "top_profit_margin_projects": [],
                "bottom_profit_margin_projects": [],
            }
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/v1/dashboard/cost/top-projects?limit=10")
            
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert len(data["data"]["top_cost_projects"]) == 1

    @patch("app.api.v1.endpoints.dashboard.cost_dashboard.deps.get_db")
    @patch("app.api.v1.endpoints.dashboard.cost_dashboard.security.require_permission")
    def test_get_top_projects_custom_limit(self, mock_auth, mock_db, client, mock_user):
        """测试自定义返回数量"""
        mock_auth.return_value = mock_user
        
        with patch("app.services.cost_dashboard_service.CostDashboardService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_top_projects.return_value = {
                "top_cost_projects": [],
                "top_overrun_projects": [],
                "top_profit_margin_projects": [],
                "bottom_profit_margin_projects": [],
            }
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/v1/dashboard/cost/top-projects?limit=5")
            
            assert response.status_code == 200
            mock_service.get_top_projects.assert_called_once_with(limit=5)


class TestCostAlertsAPI:
    """测试成本预警API"""

    @patch("app.api.v1.endpoints.dashboard.cost_dashboard.deps.get_db")
    @patch("app.api.v1.endpoints.dashboard.cost_dashboard.security.require_permission")
    def test_get_cost_alerts_success(self, mock_auth, mock_db, client, mock_user):
        """测试成功获取成本预警"""
        mock_auth.return_value = mock_user
        
        with patch("app.services.cost_dashboard_service.CostDashboardService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_cost_alerts.return_value = {
                "total_alerts": 3,
                "high_alerts": 1,
                "medium_alerts": 1,
                "low_alerts": 1,
                "alerts": [
                    {
                        "project_id": 1,
                        "project_code": "P001",
                        "project_name": "超支项目",
                        "alert_type": "overrun",
                        "alert_level": "high",
                        "budget_amount": 100000,
                        "actual_cost": 125000,
                        "variance": 25000,
                        "variance_pct": 25.0,
                        "message": "项目成本严重超支 25.0%",
                    }
                ],
            }
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/v1/dashboard/cost/alerts")
            
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["total_alerts"] == 3
            assert data["data"]["high_alerts"] == 1


class TestProjectDashboardAPI:
    """测试项目仪表盘API"""

    @patch("app.api.v1.endpoints.dashboard.cost_dashboard.deps.get_db")
    @patch("app.api.v1.endpoints.dashboard.cost_dashboard.security.require_permission")
    def test_get_project_dashboard_success(self, mock_auth, mock_db, client, mock_user):
        """测试成功获取项目仪表盘"""
        mock_auth.return_value = mock_user
        
        with patch("app.services.cost_dashboard_service.CostDashboardService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_project_cost_dashboard.return_value = {
                "project_id": 1,
                "project_code": "P001",
                "project_name": "测试项目",
                "budget_amount": 100000,
                "actual_cost": 80000,
                "contract_amount": 120000,
                "variance": -20000,
                "variance_pct": -20.0,
                "cost_breakdown": [],
                "monthly_costs": [],
                "cost_trend": [],
                "received_amount": 50000,
                "invoiced_amount": 60000,
                "gross_profit": 40000,
                "profit_margin": 33.33,
            }
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/v1/dashboard/cost/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["project_id"] == 1

    @patch("app.api.v1.endpoints.dashboard.cost_dashboard.deps.get_db")
    @patch("app.api.v1.endpoints.dashboard.cost_dashboard.security.require_permission")
    def test_get_project_dashboard_not_found(self, mock_auth, mock_db, client, mock_user):
        """测试项目不存在"""
        mock_auth.return_value = mock_user
        
        with patch("app.services.cost_dashboard_service.CostDashboardService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_project_cost_dashboard.side_effect = ValueError("项目 999 不存在")
            mock_service_class.return_value = mock_service
            
            response = client.get("/api/v1/dashboard/cost/999")
            
            assert response.status_code == 404


class TestExportAPI:
    """测试导出API"""

    @patch("app.api.v1.endpoints.dashboard.cost_dashboard.deps.get_db")
    @patch("app.api.v1.endpoints.dashboard.cost_dashboard.security.require_permission")
    def test_export_cost_overview(self, mock_auth, mock_db, client, mock_user):
        """测试导出成本总览"""
        mock_auth.return_value = mock_user
        
        with patch("app.services.cost_dashboard_service.CostDashboardService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.get_cost_overview.return_value = {
                "total_projects": 10,
                "total_budget": 1000000,
                "total_actual_cost": 800000,
            }
            mock_service_class.return_value = mock_service
            
            response = client.post(
                "/api/v1/dashboard/cost/export",
                json={
                    "export_type": "csv",
                    "data_type": "cost_overview",
                }
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/csv; charset=utf-8"

    @patch("app.api.v1.endpoints.dashboard.cost_dashboard.deps.get_db")
    @patch("app.api.v1.endpoints.dashboard.cost_dashboard.security.require_permission")
    def test_export_invalid_type(self, mock_auth, mock_db, client, mock_user):
        """测试无效的导出类型"""
        mock_auth.return_value = mock_user
        
        response = client.post(
            "/api/v1/dashboard/cost/export",
            json={
                "export_type": "csv",
                "data_type": "invalid_type",
            }
        )
        
        assert response.status_code == 400


class TestCacheAPI:
    """测试缓存API"""

    @patch("app.api.v1.endpoints.dashboard.cost_dashboard.security.require_permission")
    def test_clear_cache_success(self, mock_auth, client, mock_user):
        """测试清除缓存"""
        mock_auth.return_value = mock_user
        
        with patch("app.services.dashboard_cache_service.get_cache_service") as mock_cache:
            mock_cache_instance = MagicMock()
            mock_cache_instance.clear_pattern.return_value = 5
            mock_cache.return_value = mock_cache_instance
            
            response = client.delete("/api/v1/dashboard/cost/cache")
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["deleted_count"] == 5

    @patch("app.api.v1.endpoints.dashboard.cost_dashboard.security.require_permission")
    def test_clear_cache_custom_pattern(self, mock_auth, client, mock_user):
        """测试自定义缓存模式"""
        mock_auth.return_value = mock_user
        
        with patch("app.services.dashboard_cache_service.get_cache_service") as mock_cache:
            mock_cache_instance = MagicMock()
            mock_cache_instance.clear_pattern.return_value = 3
            mock_cache.return_value = mock_cache_instance
            
            response = client.delete("/api/v1/dashboard/cost/cache?pattern=dashboard:cost:overview")
            
            assert response.status_code == 200
            mock_cache_instance.clear_pattern.assert_called_once_with("dashboard:cost:overview")


class TestForceRefresh:
    """测试强制刷新"""

    @patch("app.api.v1.endpoints.dashboard.cost_dashboard.deps.get_db")
    @patch("app.api.v1.endpoints.dashboard.cost_dashboard.security.require_permission")
    def test_force_refresh_overview(self, mock_auth, mock_db, client, mock_user):
        """测试强制刷新成本总览"""
        mock_auth.return_value = mock_user
        
        with patch("app.services.dashboard_cache_service.get_cache_service") as mock_cache:
            mock_cache_instance = MagicMock()
            mock_cache_instance.get_or_set.return_value = {"total_projects": 10}
            mock_cache.return_value = mock_cache_instance
            
            response = client.get("/api/v1/dashboard/cost/overview?force_refresh=true")
            
            assert response.status_code == 200
            # 验证force_refresh参数被传递
            call_args = mock_cache_instance.get_or_set.call_args
            assert call_args[1]["force_refresh"] is True
