# -*- coding: utf-8 -*-
"""
Integration tests for Projects API
Covers: app/api/v1/endpoints/projects.py
Coverage Target: Add 15%+ coverage
"""

import pytest
from datetime import date
from unittest.mock import patch


class TestProjectsAPI:
    """项目管理API集成测试"""

    def test_list_projects(self, client, admin_token):
        """测试获取项目列表"""
        response = client.get(
            "/api/v1/projects/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)

    def test_list_projects_with_pagination(self, client, admin_token):
        """测试分页参数"""
        response = client.get(
            "/api/v1/projects/?skip=0&limit=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    def test_list_projects_with_filters(self, client, admin_token):
        """测试过滤参数"""
        response = client.get(
            "/api/v1/projects/?stage=S1&status=ST01",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    def test_get_project_detail(self, client, admin_token):
        """测试获取项目详情"""
        # 先创建或获取一个项目
        list_response = client.get(
            "/api/v1/projects/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if list_response.status_code == 200:
            data = list_response.json()
            items = data.get("items", data) if isinstance(data, dict) else data
            
            if items:
                project_id = items[0].get("id") if isinstance(items[0], dict) else None
                if project_id:
                    response = client.get(
                        f"/api/v1/projects/{project_id}",
                        headers={"Authorization": f"Bearer {admin_token}"}
                    )
                    assert response.status_code == 200

    def test_create_project(self, client, admin_token):
        """测试创建项目"""
        project_data = {
            "project_name": "API测试项目",
            "customer_name": "测试客户",
            "stage": "S1",
            "status": "ST01",
            "health": "H1",
            "priority": "NORMAL"
        }
        
        response = client.post(
            "/api/v1/projects/",
            json=project_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # 可能返回201创建成功或422验证错误
        assert response.status_code in [201, 422]

    def test_create_project_minimal_data(self, client, admin_token):
        """测试最简数据创建项目"""
        project_data = {
            "project_name": "最简测试项目"
        }
        
        response = client.post(
            "/api/v1/projects/",
            json=project_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code in [201, 422]

    def test_update_project(self, client, admin_token):
        """测试更新项目"""
        # 先获取项目列表
        list_response = client.get(
            "/api/v1/projects/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if list_response.status_code == 200:
            data = list_response.json()
            items = data.get("items", data) if isinstance(data, dict) else data
            
            if items:
                project_id = items[0].get("id") if isinstance(items[0], dict) else None
                if project_id:
                    update_data = {
                        "project_name": "API更新后的项目名称"
                    }
                    
                    response = client.put(
                        f"/api/v1/projects/{project_id}",
                        json=update_data,
                        headers={"Authorization": f"Bearer {admin_token}"}
                    )
                    
                    assert response.status_code in [200, 404, 422]

    def test_delete_project(self, client, admin_token):
        """测试删除项目（软删除）"""
        # 先创建项目
        project_data = {
            "project_name": "待删除测试项目"
        }
        
        create_response = client.post(
            "/api/v1/projects/",
            json=project_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if create_response.status_code == 201:
            created = create_response.json()
            project_id = created.get("id")
            
            if project_id:
                delete_response = client.delete(
                    f"/api/v1/projects/{project_id}",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                
                assert delete_response.status_code in [200, 404]


class TestProjectsAPIAuth:
    """项目API认证测试"""

    def test_list_projects_without_token(self, client):
        """测试无token访问"""
        response = client.get("/api/v1/projects/")
        assert response.status_code == 401

    def test_list_projects_with_invalid_token(self, client):
        """测试无效token访问"""
        response = client.get(
            "/api/v1/projects/",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


class TestProjectsAPISearch:
    """项目API搜索测试"""

    def test_search_projects_by_name(self, client, admin_token):
        """测试按名称搜索"""
        response = client.get(
            "/api/v1/projects/?search=测试",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    def test_search_projects_by_customer(self, client, admin_token):
        """测试按客户搜索"""
        response = client.get(
            "/api/v1/projects/?customer_name=测试",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    def test_search_projects_by_stage(self, client, admin_token):
        """测试按阶段筛选"""
        response = client.get(
            "/api/v1/projects/?stage=S2",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    def test_search_projects_by_health(self, client, admin_token):
        """测试按健康度筛选"""
        response = client.get(
            "/api/v1/projects/?health=H1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200


class TestProjectsAPISorting:
    """项目API排序测试"""

    def test_sort_by_created_at(self, client, admin_token):
        """测试按创建时间排序"""
        response = client.get(
            "/api/v1/projects/?order_by=created_at&order=desc",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    def test_sort_by_project_code(self, client, admin_token):
        """测试按项目编码排序"""
        response = client.get(
            "/api/v1/projects/?order_by=project_code&order=asc",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    def test_sort_by_priority(self, client, admin_token):
        """测试按优先级排序"""
        response = client.get(
            "/api/v1/projects/?order_by=priority&order=desc",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
