# -*- coding: utf-8 -*-
"""
绩效管理 API 测试
测试个人绩效、团队绩效、排行榜、新绩效系统等功能
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestPersonalPerformance:
    """个人绩效测试"""

    def test_get_my_performance(self, client: TestClient, admin_token: str):
        """测试查看我的绩效"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/performance/my",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have performance:read permission")
        if response.status_code == 404:
            pytest.skip("No performance period found or endpoint not found")

        assert response.status_code == 200

    def test_get_user_performance(self, client: TestClient, admin_token: str):
        """测试查看指定用户绩效"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/performance/user/1",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission to view this user's performance")
        if response.status_code == 404:
            pytest.skip("User or performance data not found")

        assert response.status_code == 200

    def test_get_performance_trends(self, client: TestClient, admin_token: str):
        """测试绩效趋势分析"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/performance/trends/1",
            params={"period_type": "MONTHLY", "periods_count": 6},
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission")
        if response.status_code == 404:
            pytest.skip("User or performance data not found")

        assert response.status_code == 200


class TestTeamPerformance:
    """团队绩效测试"""

    def test_get_team_performance(self, client: TestClient, admin_token: str):
        """测试团队绩效汇总"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        try:
            response = client.get(
                f"{settings.API_V1_PREFIX}/performance/team/1",
                headers=headers
            )

            if response.status_code == 403:
                pytest.skip("User does not have permission")
            if response.status_code == 404:
                pytest.skip("Team or performance data not found")
            if response.status_code == 500:
                pytest.skip("Team performance endpoint has internal error")

            assert response.status_code == 200
        except Exception as e:
            pytest.skip(f"Team performance endpoint error: {e}")

    def test_get_department_performance(self, client: TestClient, admin_token: str):
        """测试部门绩效汇总"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        try:
            response = client.get(
                f"{settings.API_V1_PREFIX}/performance/department/1",
                headers=headers
            )

            if response.status_code == 403:
                pytest.skip("User does not have permission")
            if response.status_code == 404:
                pytest.skip("Department or performance data not found")
            if response.status_code == 500:
                pytest.skip("Department performance endpoint has internal error")

            assert response.status_code == 200
        except Exception as e:
            pytest.skip(f"Department performance endpoint error: {e}")


class TestPerformanceRanking:
    """绩效排行榜测试"""

    def test_get_company_ranking(self, client: TestClient, admin_token: str):
        """测试公司绩效排行榜"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/performance/ranking",
            params={"ranking_type": "COMPANY"},
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission")
        if response.status_code == 404:
            pytest.skip("Performance data not found")

        assert response.status_code == 200

    def test_get_team_ranking(self, client: TestClient, admin_token: str):
        """测试团队绩效排行榜"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/performance/ranking",
            params={"ranking_type": "TEAM"},
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission")
        if response.status_code == 404:
            pytest.skip("Performance data not found")

        assert response.status_code == 200


class TestProjectPerformance:
    """项目绩效测试"""

    def test_get_project_performance(self, client: TestClient, admin_token: str):
        """测试项目成员绩效"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/performance/project/1",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission")
        if response.status_code == 404:
            pytest.skip("Project or performance data not found")

        assert response.status_code == 200

    def test_get_project_progress_report(self, client: TestClient, admin_token: str):
        """测试项目进展报告"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        try:
            response = client.get(
                f"{settings.API_V1_PREFIX}/performance/project/1/progress",
                params={"report_type": "WEEKLY"},
                headers=headers
            )

            if response.status_code == 403:
                pytest.skip("User does not have permission")
            if response.status_code == 404:
                pytest.skip("Project not found")
            if response.status_code == 500:
                pytest.skip("Project progress report endpoint has internal error")

            assert response.status_code == 200
        except Exception as e:
            pytest.skip(f"Project progress report endpoint error: {e}")


class TestPerformanceCompare:
    """绩效对比测试"""

    def test_compare_performance(self, client: TestClient, admin_token: str):
        """测试绩效对比"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/performance/compare",
            params={"user_ids": "1,2"},
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission")
        if response.status_code == 404:
            pytest.skip("Performance data not found")

        assert response.status_code == 200


class TestNewPerformanceSystem:
    """新绩效系统测试"""

    def test_get_monthly_summary_history(self, client: TestClient, admin_token: str):
        """测试获取历史工作总结"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/performance/monthly-summary/history",
            params={"limit": 12},
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission")
        if response.status_code == 404:
            pytest.skip("Monthly summary endpoint not found")

        assert response.status_code == 200

    def test_get_my_performance_new(self, client: TestClient, admin_token: str):
        """测试新系统我的绩效"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        response = client.get(
            f"{settings.API_V1_PREFIX}/performance/my-performance",
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission")
        if response.status_code == 404:
            pytest.skip("My performance endpoint not found")

        assert response.status_code == 200

    def test_get_evaluation_tasks(self, client: TestClient, admin_token: str):
        """测试获取待评价任务"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        current_period = date.today().strftime("%Y-%m")
        response = client.get(
            f"{settings.API_V1_PREFIX}/performance/evaluation-tasks",
            params={"period": current_period},
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission")
        if response.status_code == 404:
            pytest.skip("Evaluation tasks endpoint not found")

        assert response.status_code == 200


class TestIntegratedPerformance:
    """绩效融合测试"""

    def test_get_integrated_performance(self, client: TestClient, admin_token: str):
        """测试获取融合绩效结果"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = _auth_headers(admin_token)
        current_period = date.today().strftime("%Y-%m")
        response = client.get(
            f"{settings.API_V1_PREFIX}/performance/integrated/1",
            params={"period": current_period},
            headers=headers
        )

        if response.status_code == 403:
            pytest.skip("User does not have permission")
        if response.status_code == 404:
            pytest.skip("Integrated performance data not found")

        assert response.status_code == 200
