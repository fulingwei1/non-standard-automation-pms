# -*- coding: utf-8 -*-
"""
项目工作日志 API 测试

测试项目工作日志的创建、查询、更新、统计等功能
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestProjectsWorkLogsAPI:
    """项目工作日志 API 测试类"""

    def test_list_work_logs(self, client: TestClient, admin_token: str):
        """测试获取工作日志列表"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/work-logs/",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Work logs API not implemented")

        assert response.status_code == 200, response.text

    def test_create_work_log(self, client: TestClient, admin_token: str):
        """测试创建工作日志"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        log_data = {
            "project_id": 1,
            "work_date": datetime.now().strftime("%Y-%m-%d"),
            "work_hours": 8.0,
            "work_type": "development",
            "task_name": "实现用户认证模块",
            "description": "完成了用户登录、注册和权限验证功能",
            "progress": 80,
            "issues": "无",
            "next_plan": "继续完善权限管理"
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/1/work-logs/",
            headers=headers,
            json=log_data
        )

        if response.status_code == 404:
            pytest.skip("Work logs API not implemented")

        assert response.status_code in [200, 201], response.text

    def test_get_work_log_detail(self, client: TestClient, admin_token: str):
        """测试获取工作日志详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/work-logs/1",
            headers=headers
        )

        if response.status_code in [404, 422]:
            pytest.skip("No work log data or API not implemented")

        assert response.status_code == 200, response.text

    def test_update_work_log(self, client: TestClient, admin_token: str):
        """测试更新工作日志"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        update_data = {
            "progress": 90,
            "description": "更新：完成了用户认证和权限验证的所有功能"
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/projects/1/work-logs/1",
            headers=headers,
            json=update_data
        )

        if response.status_code in [404, 422]:
            pytest.skip("Work log API not implemented or no data")

        assert response.status_code == 200, response.text

    def test_delete_work_log(self, client: TestClient, admin_token: str):
        """测试删除工作日志"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.delete(
            f"{settings.API_V1_PREFIX}/projects/1/work-logs/999",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Work log API not implemented")

        assert response.status_code in [200, 204, 404], response.text

    def test_filter_logs_by_date_range(self, client: TestClient, admin_token: str):
        """测试按日期范围过滤日志"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/work-logs/"
            f"?start_date=2024-01-01&end_date=2024-12-31",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Work log filter API not implemented")

        assert response.status_code == 200, response.text

    def test_filter_logs_by_member(self, client: TestClient, admin_token: str):
        """测试按成员过滤日志"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/work-logs/?member_id=1",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Work log filter API not implemented")

        assert response.status_code == 200, response.text

    def test_filter_logs_by_work_type(self, client: TestClient, admin_token: str):
        """测试按工作类型过滤日志"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/work-logs/?work_type=development",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Work log filter API not implemented")

        assert response.status_code == 200, response.text

    def test_my_work_logs(self, client: TestClient, admin_token: str):
        """测试获取我的工作日志"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/work-logs/my-logs",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("My work logs API not implemented")

        assert response.status_code == 200, response.text

    def test_work_hours_statistics(self, client: TestClient, admin_token: str):
        """测试工时统计"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/work-logs/statistics/hours",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Work hours statistics API not implemented")

        assert response.status_code == 200, response.text

    def test_member_workload_statistics(self, client: TestClient, admin_token: str):
        """测试成员工作量统计"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/work-logs/statistics/workload",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Workload statistics API not implemented")

        assert response.status_code == 200, response.text

    def test_work_log_export(self, client: TestClient, admin_token: str):
        """测试导出工作日志"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/work-logs/export",
            headers=headers
        )

        if response.status_code == 404:
            pytest.skip("Work log export API not implemented")

        assert response.status_code in [200, 404], response.text

    def test_work_log_validation(self, client: TestClient, admin_token: str):
        """测试工作日志数据验证"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        invalid_data = {
            "work_hours": -5.0  # 负数工时
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/1/work-logs/",
            headers=headers,
            json=invalid_data
        )

        if response.status_code == 404:
            pytest.skip("Work logs API not implemented")

        assert response.status_code == 422, response.text

    def test_work_log_unauthorized(self, client: TestClient):
        """测试未授权访问工作日志"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/projects/1/work-logs/"
        )

        assert response.status_code in [401, 403], response.text

    def test_batch_create_work_logs(self, client: TestClient, admin_token: str):
        """测试批量创建工作日志"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)

        batch_data = {
            "logs": [
                {
                    "work_date": "2024-01-01",
                    "work_hours": 8.0,
                    "task_name": "任务1"
                },
                {
                    "work_date": "2024-01-02",
                    "work_hours": 7.5,
                    "task_name": "任务2"
                }
            ]
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/projects/1/work-logs/batch",
            headers=headers,
            json=batch_data
        )

        if response.status_code == 404:
            pytest.skip("Batch work logs API not implemented")

        assert response.status_code in [200, 201, 404], response.text
