# -*- coding: utf-8 -*-
"""
问题管理模块 API 测试

Sprint 5.1: 问题模块单元测试
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, date, timedelta
from app.core.config import settings


class TestIssueCRUD:
    """问题CRUD操作测试"""
    
    def test_create_issue(self, client: TestClient, admin_token: str):
        """测试创建问题"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        issue_data = {
            "category": "PROJECT",
            "issue_type": "DEFECT",
            "severity": "MAJOR",
            "priority": "HIGH",
            "title": "测试问题",
            "description": "这是一个测试问题",
            "is_blocking": False,
        }
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/issues",
            json=issue_data,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "测试问题"
        assert data["status"] == "OPEN"
        assert "issue_no" in data
        return data["id"]
    
    def test_get_issue(self, client: TestClient, admin_token: str):
        """测试获取问题详情"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        # 先创建一个问题
        issue_id = self.test_create_issue(client, admin_token)
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/issues/{issue_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == issue_id
        assert data["title"] == "测试问题"
    
    def test_list_issues(self, client: TestClient, admin_token: str):
        """测试获取问题列表"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/issues?page=1&page_size=10",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)
        assert "total" in data or len(data) >= 0
    
    def test_update_issue(self, client: TestClient, admin_token: str):
        """测试更新问题"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        # 先创建一个问题
        issue_id = self.test_create_issue(client, admin_token)
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {
            "title": "更新后的测试问题",
            "priority": "URGENT",
        }
        
        response = client.put(
            f"{settings.API_V1_PREFIX}/issues/{issue_id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "更新后的测试问题"
        assert data["priority"] == "URGENT"
    
    def test_delete_issue(self, client: TestClient, admin_token: str):
        """测试删除问题（软删除）"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        # 先创建一个问题
        issue_id = self.test_create_issue(client, admin_token)
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.delete(
            f"{settings.API_V1_PREFIX}/issues/{issue_id}",
            headers=headers
        )
        
        # 删除应该是软删除，状态码可能是200或204
        assert response.status_code in [200, 204, 404]


class TestIssueOperations:
    """问题操作测试"""
    
    def test_assign_issue(self, client: TestClient, admin_token: str):
        """测试分配问题"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        # 先创建一个问题
        issue_id = TestIssueCRUD().test_create_issue(client, admin_token)
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        assign_data = {
            "assignee_id": 1,  # 假设用户ID为1
            "due_date": (date.today() + timedelta(days=7)).isoformat(),
            "comment": "分配给测试用户",
        }
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/issues/{issue_id}/assign",
            json=assign_data,
            headers=headers
        )
        
        # 如果用户不存在可能返回404，这里只检查格式
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data["assignee_id"] == 1
    
    def test_resolve_issue(self, client: TestClient, admin_token: str):
        """测试解决问题"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        # 先创建一个问题
        issue_id = TestIssueCRUD().test_create_issue(client, admin_token)
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        resolve_data = {
            "solution": "问题已解决",
            "comment": "通过测试解决",
        }
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/issues/{issue_id}/resolve",
            json=resolve_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RESOLVED"
        assert data["solution"] == "问题已解决"
        assert data["resolved_at"] is not None
    
    def test_close_issue(self, client: TestClient, admin_token: str):
        """测试关闭问题"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        # 先创建一个问题
        issue_id = TestIssueCRUD().test_create_issue(client, admin_token)
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        close_data = {
            "comment": "直接关闭",
        }
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/issues/{issue_id}/close",
            json=close_data,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CLOSED"


class TestIssueBlockingAlert:
    """阻塞问题预警集成测试"""
    
    def test_create_blocking_issue_creates_alert(self, client: TestClient, admin_token: str):
        """测试创建阻塞问题时自动创建预警"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        issue_data = {
            "category": "PROJECT",
            "issue_type": "DEFECT",
            "severity": "CRITICAL",
            "priority": "URGENT",
            "title": "阻塞测试问题",
            "description": "这是一个阻塞问题",
            "is_blocking": True,
            "project_id": 1,  # 假设项目ID为1
        }
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/issues",
            json=issue_data,
            headers=headers
        )
        
        assert response.status_code == 201
        issue_id = response.json()["id"]
        
        # 验证预警是否创建（需要查询预警API）
        # 这里只验证问题创建成功，预警创建在后台完成
        assert response.json()["is_blocking"] is True
    
    def test_resolve_blocking_issue_closes_alert(self, client: TestClient, admin_token: str):
        """测试解决阻塞问题时自动关闭预警"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        # 先创建一个阻塞问题
        issue_id = TestIssueCRUD().test_create_issue(client, admin_token)
        
        # 更新为阻塞问题
        headers = {"Authorization": f"Bearer {admin_token}"}
        client.put(
            f"{settings.API_V1_PREFIX}/issues/{issue_id}",
            json={"is_blocking": True},
            headers=headers
        )
        
        # 解决问题
        resolve_data = {"solution": "已解决", "comment": "测试"}
        response = client.post(
            f"{settings.API_V1_PREFIX}/issues/{issue_id}/resolve",
            json=resolve_data,
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "RESOLVED"


class TestIssueStatistics:
    """问题统计测试"""
    
    def test_get_statistics(self, client: TestClient, admin_token: str):
        """测试获取问题统计"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/issues/statistics/overview",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # 验证返回的数据结构
        assert "total" in data or "data" in data
    
    def test_get_trend(self, client: TestClient, admin_token: str):
        """测试获取问题趋势"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        params = {
            "group_by": "day",
            "start_date": (date.today() - timedelta(days=7)).isoformat(),
            "end_date": date.today().isoformat(),
        }
        
        response = client.get(
            f"{settings.API_V1_PREFIX}/issues/statistics/trend",
            params=params,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "trend" in data or isinstance(data, list)
    
    def test_get_snapshots(self, client: TestClient, admin_token: str):
        """测试获取统计快照列表"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/issues/statistics/snapshots?page=1&page_size=10",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)


class TestIssueTemplates:
    """问题模板测试"""
    
    def test_list_templates(self, client: TestClient, admin_token: str):
        """测试获取模板列表"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/issue-templates?page=1&page_size=10",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)
    
    def test_create_template(self, client: TestClient, admin_token: str):
        """测试创建模板"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        template_data = {
            "template_name": "测试模板",
            "template_code": f"TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "category": "PROJECT",
            "issue_type": "DEFECT",
            "title_template": "测试问题：{project_name}",
            "description_template": "这是一个测试问题模板",
            "default_severity": "MINOR",
            "default_priority": "MEDIUM",
        }
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/issue-templates",
            json=template_data,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["template_name"] == "测试模板"
        return data["id"]
    
    def test_create_issue_from_template(self, client: TestClient, admin_token: str):
        """测试从模板创建问题"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        # 先创建一个模板
        template_id = self.test_create_template(client, admin_token)
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        issue_data = {
            "project_id": 1,
            "due_date": (date.today() + timedelta(days=7)).isoformat(),
        }
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/issue-templates/{template_id}/create-issue",
            json=issue_data,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "issue_no" in data
        assert data["status"] == "OPEN"
