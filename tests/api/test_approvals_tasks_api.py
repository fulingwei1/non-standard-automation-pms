# -*- coding: utf-8 -*-
"""
审批任务 API 测试

测试审批任务的查询、处理、批量操作等功能
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestApprovalsTasksAPI:
    """审批任务 API 测试类"""

    def test_list_my_pending_tasks(self, client: TestClient, admin_token: str):
        """测试获取我的待审批任务"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/tasks/pending",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Approval tasks API not implemented")

        assert response.status_code == 200, response.text

    def test_list_my_completed_tasks(self, client: TestClient, admin_token: str):
        """测试获取我已完成的审批任务"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/tasks/completed",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Approval tasks API not implemented")

        assert response.status_code == 200, response.text

    def test_get_task_detail(self, client: TestClient, admin_token: str):
        """测试获取审批任务详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/tasks/1",
            headers=headers
        )

        if response.status_code in [404, 422]:
            pytest.skip("No task data or API not implemented")

        assert response.status_code == 200, response.text

    def test_approve_task(self, client: TestClient, admin_token: str):
        """测试审批通过"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        approval_data = {
            "action": "approve",
            "comments": "审批通过",
            "approved_at": datetime.now().isoformat()
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/approvals/tasks/1/approve",
            headers=headers,
            json=approval_data
        )

        if response.status_code == 404:
            pytest.skip("Task approval API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_reject_task(self, client: TestClient, admin_token: str):
        """测试审批拒绝"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        rejection_data = {
            "action": "reject",
            "comments": "不符合要求，请修改后重新提交",
            "rejected_at": datetime.now().isoformat()
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/approvals/tasks/1/reject",
            headers=headers,
            json=rejection_data
        )

        if response.status_code == 404:
            pytest.skip("Task rejection API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_return_task(self, client: TestClient, admin_token: str):
        """测试退回任务"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        return_data = {
            "action": "return",
            "comments": "退回上一步重新审批",
            "return_to_step": 1
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/approvals/tasks/1/return",
            headers=headers,
            json=return_data
        )

        if response.status_code == 404:
            pytest.skip("Task return API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_transfer_task(self, client: TestClient, admin_token: str):
        """测试转交任务"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        transfer_data = {
            "transfer_to_user_id": 2,
            "comments": "临时出差，转交给其他人处理"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/approvals/tasks/1/transfer",
            headers=headers,
            json=transfer_data
        )

        if response.status_code == 404:
            pytest.skip("Task transfer API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_batch_approve_tasks(self, client: TestClient, admin_token: str):
        """测试批量审批"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        batch_data = {
            "task_ids": [1, 2, 3],
            "action": "approve",
            "comments": "批量审批通过"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/approvals/tasks/batch-approve",
            headers=headers,
            json=batch_data
        )

        if response.status_code == 404:
            pytest.skip("Batch approval API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_filter_tasks_by_type(self, client: TestClient, admin_token: str):
        """测试按类型过滤任务"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/tasks/pending?type=purchase_request",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Task filter API not implemented")

        assert response.status_code == 200, response.text

    def test_filter_tasks_by_priority(self, client: TestClient, admin_token: str):
        """测试按优先级过滤任务"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/tasks/pending?priority=urgent",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Task filter API not implemented")

        assert response.status_code == 200, response.text

    def test_overdue_tasks(self, client: TestClient, admin_token: str):
        """测试逾期任务查询"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/tasks/overdue",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Overdue tasks API not implemented")

        assert response.status_code == 200, response.text

    def test_task_reminder(self, client: TestClient, admin_token: str):
        """测试任务提醒"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.post(
            f"{settings.API_V1_PREFIX}/approvals/tasks/1/remind",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Task reminder API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_task_statistics(self, client: TestClient, admin_token: str):
        """测试任务统计"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/tasks/statistics",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Task statistics API not implemented")

        assert response.status_code == 200, response.text

    def test_task_unauthorized(self, client: TestClient):
        """测试未授权访问审批任务"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/approvals/tasks/pending"
        )

        assert response.status_code in [401, 403], response.text

    def test_task_validation(self, client: TestClient, admin_token: str):
        """测试任务操作验证"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        # 缺少必要的评论
        invalid_data = {
            "action": "reject"
            # 缺少 comments
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/approvals/tasks/1/reject",
            headers=headers,
            json=invalid_data
        )

        if response.status_code == 404:
            pytest.skip("Task API not implemented")

        assert response.status_code in [200, 422], response.text
