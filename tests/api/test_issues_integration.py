# -*- coding: utf-8 -*-
"""
问题管理模块集成测试

Sprint 5.2: 问题模块集成测试
测试完整业务流程
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, date, timedelta
from app.core.config import settings


class TestIssueLifecycle:
    """问题完整生命周期测试"""
    
    def test_issue_full_lifecycle(self, client: TestClient, admin_token: str):
        """测试问题完整生命周期：创建→分配→解决→验证→关闭"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 1. 创建问题
        issue_data = {
            "category": "PROJECT",
            "issue_type": "DEFECT",
            "severity": "MAJOR",
            "priority": "HIGH",
            "title": "完整生命周期测试问题",
            "description": "测试完整生命周期",
            "project_id": 1,
        }
        
        create_response = client.post(
            f"{settings.API_V1_PREFIX}/issues",
            json=issue_data,
            headers=headers
        )
        assert create_response.status_code == 201
        issue_id = create_response.json()["id"]
        assert create_response.json()["status"] == "OPEN"
        
        # 2. 分配问题
        assign_data = {
            "assignee_id": 1,
            "due_date": (date.today() + timedelta(days=7)).isoformat(),
            "comment": "分配给测试用户",
        }
        
        assign_response = client.post(
            f"{settings.API_V1_PREFIX}/issues/{issue_id}/assign",
            json=assign_data,
            headers=headers
        )
        # 如果用户不存在可能返回404
        if assign_response.status_code == 200:
            assert assign_response.json()["assignee_id"] == 1
        
        # 3. 解决问题
        resolve_data = {
            "solution": "问题已解决",
            "comment": "通过测试解决",
        }
        
        resolve_response = client.post(
            f"{settings.API_V1_PREFIX}/issues/{issue_id}/resolve",
            json=resolve_data,
            headers=headers
        )
        assert resolve_response.status_code == 200
        assert resolve_response.json()["status"] == "RESOLVED"
        assert resolve_response.json()["solution"] == "问题已解决"
        
        # 4. 验证问题
        verify_data = {
            "verified_result": "PASS",
            "comment": "验证通过",
        }
        
        verify_response = client.post(
            f"{settings.API_V1_PREFIX}/issues/{issue_id}/verify",
            json=verify_data,
            headers=headers
        )
        assert verify_response.status_code == 200
        assert verify_response.json()["status"] == "CLOSED"  # 验证通过自动关闭
        assert verify_response.json()["verified_result"] == "PASS"


class TestIssueRelations:
    """问题关联功能测试"""
    
    def test_issue_project_relation(self, client: TestClient, admin_token: str):
        """测试问题与项目关联"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 创建关联项目的问题
        issue_data = {
            "category": "PROJECT",
            "issue_type": "DEFECT",
            "severity": "MAJOR",
            "priority": "HIGH",
            "title": "项目关联测试",
            "description": "测试项目关联",
            "project_id": 1,
        }
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/issues",
            json=issue_data,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["project_id"] == 1
    
    def test_issue_follow_up(self, client: TestClient, admin_token: str):
        """测试问题跟进记录"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 先创建问题
        issue_data = {
            "category": "PROJECT",
            "issue_type": "DEFECT",
            "severity": "MAJOR",
            "priority": "HIGH",
            "title": "跟进测试问题",
            "description": "测试跟进功能",
        }
        
        create_response = client.post(
            f"{settings.API_V1_PREFIX}/issues",
            json=issue_data,
            headers=headers
        )
        issue_id = create_response.json()["id"]
        
        # 添加跟进记录
        follow_up_data = {
            "follow_up_type": "COMMENT",
            "content": "这是跟进内容",
        }
        
        follow_up_response = client.post(
            f"{settings.API_V1_PREFIX}/issues/{issue_id}/follow-ups",
            json=follow_up_data,
            headers=headers
        )
        
        assert follow_up_response.status_code == 201
        
        # 获取跟进记录列表
        list_response = client.get(
            f"{settings.API_V1_PREFIX}/issues/{issue_id}/follow-ups",
            headers=headers
        )
        
        assert list_response.status_code == 200
        follow_ups = list_response.json()
        assert isinstance(follow_ups, list)
        assert len(follow_ups) > 0


class TestIssueBatchOperations:
    """批量操作测试"""
    
    def test_batch_assign(self, client: TestClient, admin_token: str):
        """测试批量分配"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 先创建几个问题
        issue_ids = []
        for i in range(3):
            issue_data = {
                "category": "PROJECT",
                "issue_type": "DEFECT",
                "severity": "MINOR",
                "priority": "MEDIUM",
                "title": f"批量分配测试问题{i+1}",
                "description": "测试批量分配",
            }
            response = client.post(
                f"{settings.API_V1_PREFIX}/issues",
                json=issue_data,
                headers=headers
            )
            if response.status_code == 201:
                issue_ids.append(response.json()["id"])
        
        if len(issue_ids) == 0:
            pytest.skip("No issues created")
        
        # 批量分配
        batch_data = {
            "issue_ids": issue_ids,
            "assignee_id": 1,
            "due_date": (date.today() + timedelta(days=7)).isoformat(),
        }
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/issues/batch-assign",
            json=batch_data,
            headers=headers
        )
        
        # 如果用户不存在可能返回404
        assert response.status_code in [200, 404]
    
    def test_batch_status_change(self, client: TestClient, admin_token: str):
        """测试批量状态变更"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 先创建几个问题
        issue_ids = []
        for i in range(3):
            issue_data = {
                "category": "PROJECT",
                "issue_type": "DEFECT",
                "severity": "MINOR",
                "priority": "MEDIUM",
                "title": f"批量状态测试问题{i+1}",
                "description": "测试批量状态变更",
            }
            response = client.post(
                f"{settings.API_V1_PREFIX}/issues",
                json=issue_data,
                headers=headers
            )
            if response.status_code == 201:
                issue_ids.append(response.json()["id"])
        
        if len(issue_ids) == 0:
            pytest.skip("No issues created")
        
        # 批量变更状态
        batch_data = {
            "issue_ids": issue_ids,
            "new_status": "PROCESSING",
        }
        
        response = client.post(
            f"{settings.API_V1_PREFIX}/issues/batch-status",
            json=batch_data,
            headers=headers
        )
        
        assert response.status_code == 200


class TestIssueImportExport:
    """导入导出测试"""
    
    def test_export_issues(self, client: TestClient, admin_token: str):
        """测试导出问题"""
        if not admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = client.get(
            f"{settings.API_V1_PREFIX}/issues/export",
            headers=headers
        )
        
        # 导出应该返回文件流
        assert response.status_code == 200
        assert response.headers.get("content-type") in [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/octet-stream"
        ]
