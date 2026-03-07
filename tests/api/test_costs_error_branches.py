# -*- coding: utf-8 -*-
"""
成本管理API异常分支测试

补充成本管理端点的异常处理分支测试,提升分支覆盖率
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings


class TestCostListErrorBranches:
    """成本列表端点异常分支测试"""

    def test_list_costs_no_token(self, client: TestClient):
        """无Token访问"""
        response = client.get(f"{settings.API_V1_PREFIX}/costs/")
        assert response.status_code == 401

    def test_list_costs_invalid_token(self, client: TestClient):
        """无效Token"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_list_costs_invalid_page(self, client: TestClient, admin_token: str):
        """无效页码"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/",
            params={"page": -1},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 422]

    def test_list_costs_invalid_project_id(self, client: TestClient, admin_token: str):
        """无效项目ID"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/",
            params={"project_id": "invalid"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422

    def test_list_costs_invalid_date_format(self, client: TestClient, admin_token: str):
        """无效日期格式"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/",
            params={"start_date": "invalid-date"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 422]

    def test_list_costs_end_before_start(self, client: TestClient, admin_token: str):
        """结束日期早于开始日期"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/",
            params={
                "start_date": "2025-12-31",
                "end_date": "2025-01-01"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 可能返回空结果或错误
        assert response.status_code in [200, 400, 422]


class TestCreateCostErrorBranches:
    """创建成本记录端点异常分支测试"""

    def test_create_cost_no_token(self, client: TestClient):
        """无Token创建"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/costs/",
            json={"amount": 10000}
        )
        assert response.status_code == 401

    def test_create_cost_missing_required_fields(self, client: TestClient, admin_token: str):
        """缺少必填字段"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/costs/",
            json={},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422

    def test_create_cost_missing_project_id(self, client: TestClient, admin_token: str):
        """缺少项目ID"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/costs/",
            json={
                "amount": 10000,
                "cost_date": date.today().isoformat()
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422

    def test_create_cost_invalid_project_id(self, client: TestClient, admin_token: str):
        """项目不存在"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/costs/",
            json={
                "project_id": 999999,
                "amount": 10000,
                "cost_date": date.today().isoformat()
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 404, 422]

    @pytest.mark.parametrize("invalid_amount", [
        -1000,  # 负数
        0,  # 零
        -0.01,  # 负小数
        999999999999999,  # 超大值
    ])
    def test_create_cost_invalid_amount(
        self, client: TestClient, admin_token: str, invalid_amount
    ):
        """无效金额"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/costs/",
            json={
                "project_id": 1,
                "amount": invalid_amount,
                "cost_date": date.today().isoformat()
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 422]

    def test_create_cost_invalid_cost_type(self, client: TestClient, admin_token: str):
        """无效成本类型"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/costs/",
            json={
                "project_id": 1,
                "amount": 10000,
                "cost_type": "INVALID_TYPE",
                "cost_date": date.today().isoformat()
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422

    def test_create_cost_invalid_cost_category(self, client: TestClient, admin_token: str):
        """无效成本类别"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/costs/",
            json={
                "project_id": 1,
                "amount": 10000,
                "cost_category": "INVALID_CATEGORY",
                "cost_date": date.today().isoformat()
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422

    def test_create_cost_invalid_date_format(self, client: TestClient, admin_token: str):
        """无效日期格式"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/costs/",
            json={
                "project_id": 1,
                "amount": 10000,
                "cost_date": "invalid-date"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422

    def test_create_cost_future_date(self, client: TestClient, admin_token: str):
        """未来日期"""
        if not admin_token:
            pytest.skip("Admin token not available")

        future_date = (date.today() + timedelta(days=365)).isoformat()
        response = client.post(
            f"{settings.API_V1_PREFIX}/costs/",
            json={
                "project_id": 1,
                "amount": 10000,
                "cost_date": future_date
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 可能允许或禁止
        assert response.status_code in [200, 201, 400, 422]

    def test_create_cost_negative_tax(self, client: TestClient, admin_token: str):
        """负数税额"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/costs/",
            json={
                "project_id": 1,
                "amount": 10000,
                "tax_amount": -500,
                "cost_date": date.today().isoformat()
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 422]


class TestGetCostErrorBranches:
    """获取成本详情端点异常分支测试"""

    def test_get_cost_no_token(self, client: TestClient):
        """无Token访问"""
        response = client.get(f"{settings.API_V1_PREFIX}/costs/1")
        assert response.status_code == 401

    def test_get_cost_not_found(self, client: TestClient, admin_token: str):
        """成本记录不存在"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/999999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404

    def test_get_cost_invalid_id_format(self, client: TestClient, admin_token: str):
        """无效ID格式"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/invalid",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422


class TestUpdateCostErrorBranches:
    """更新成本记录端点异常分支测试"""

    def test_update_cost_no_token(self, client: TestClient):
        """无Token更新"""
        response = client.put(
            f"{settings.API_V1_PREFIX}/costs/1",
            json={"amount": 15000}
        )
        assert response.status_code == 401

    def test_update_cost_not_found(self, client: TestClient, admin_token: str):
        """更新不存在的成本"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.put(
            f"{settings.API_V1_PREFIX}/costs/999999",
            json={"amount": 15000},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404

    def test_update_cost_invalid_amount(self, client: TestClient, admin_token: str, db_session: Session):
        """更新为无效金额"""
        if not admin_token:
            pytest.skip("Admin token not available")

        from app.models.project import ProjectCost
        cost = db_session.query(ProjectCost).first()
        if not cost:
            pytest.skip("No cost record for test")

        response = client.put(
            f"{settings.API_V1_PREFIX}/costs/{cost.id}",
            json={"amount": -5000},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 422]


class TestDeleteCostErrorBranches:
    """删除成本记录端点异常分支测试"""

    def test_delete_cost_no_token(self, client: TestClient):
        """无Token删除"""
        response = client.delete(f"{settings.API_V1_PREFIX}/costs/1")
        assert response.status_code == 401

    def test_delete_cost_not_found(self, client: TestClient, admin_token: str):
        """删除不存在的成本"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.delete(
            f"{settings.API_V1_PREFIX}/costs/999999",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404


class TestCostSummaryErrorBranches:
    """成本汇总端点异常分支测试"""

    def test_get_project_cost_summary_no_token(self, client: TestClient):
        """无Token访问汇总"""
        response = client.get(f"{settings.API_V1_PREFIX}/costs/projects/1/costs/summary")
        assert response.status_code == 401

    def test_get_project_cost_summary_not_found(self, client: TestClient, admin_token: str):
        """项目不存在"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/projects/999999/costs/summary",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404

    def test_get_project_cost_summary_invalid_id(self, client: TestClient, admin_token: str):
        """无效项目ID"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/projects/invalid/costs/summary",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422


class TestCostAnalysisErrorBranches:
    """成本分析端点异常分支测试"""

    def test_cost_analysis_no_token(self, client: TestClient):
        """无Token访问"""
        response = client.get(f"{settings.API_V1_PREFIX}/costs/projects/1/cost-analysis")
        assert response.status_code == 401

    def test_cost_analysis_project_not_found(self, client: TestClient, admin_token: str):
        """项目不存在"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/projects/999999/cost-analysis",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404

    def test_cost_analysis_invalid_comparison_project(self, client: TestClient, admin_token: str):
        """对比项目不存在"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/projects/1/cost-analysis",
            params={"compare_project_id": 999999},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 可能忽略不存在的对比项目或返回错误
        assert response.status_code in [200, 404]


class TestCostTrendsErrorBranches:
    """成本趋势端点异常分支测试"""

    def test_cost_trends_no_token(self, client: TestClient):
        """无Token访问"""
        response = client.get(f"{settings.API_V1_PREFIX}/costs/cost-trends")
        assert response.status_code == 401

    def test_cost_trends_invalid_group_by(self, client: TestClient, admin_token: str):
        """无效分组方式"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/cost-trends",
            params={"group_by": "invalid_group"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 422]

    def test_cost_trends_missing_dates(self, client: TestClient, admin_token: str):
        """缺少日期范围"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/cost-trends",
            params={"group_by": "day"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 可能要求必须提供日期范围
        assert response.status_code in [200, 400, 422]


class TestBudgetExecutionErrorBranches:
    """预算执行分析端点异常分支测试"""

    def test_budget_execution_no_token(self, client: TestClient):
        """无Token访问"""
        response = client.get(f"{settings.API_V1_PREFIX}/costs/budget/projects/1/execution")
        assert response.status_code == 401

    def test_budget_execution_project_not_found(self, client: TestClient, admin_token: str):
        """项目不存在"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/budget/projects/999999/execution",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 404]

    def test_budget_execution_no_budget(self, client: TestClient, admin_token: str, db_session: Session):
        """项目没有预算"""
        if not admin_token:
            pytest.skip("Admin token not available")

        from app.models.project import Project
        project = db_session.query(Project).filter(
            Project.budget_amount == None
        ).first()

        if not project:
            pytest.skip("No project without budget for test")

        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/budget/projects/{project.id}/execution",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 可能返回错误或空数据
        assert response.status_code in [200, 400]


class TestCostAllocationErrorBranches:
    """成本分摊端点异常分支测试"""

    def test_allocate_cost_no_token(self, client: TestClient):
        """无Token访问"""
        response = client.post(f"{settings.API_V1_PREFIX}/costs/allocation/1/allocate")
        assert response.status_code == 401

    def test_allocate_cost_not_found(self, client: TestClient, admin_token: str):
        """成本不存在"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/costs/allocation/999999/allocate",
            json={},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [404, 422]

    def test_allocate_cost_missing_params(self, client: TestClient, admin_token: str, db_session: Session):
        """缺少必要参数"""
        if not admin_token:
            pytest.skip("Admin token not available")

        from app.models.project import ProjectCost
        cost = db_session.query(ProjectCost).first()
        if not cost:
            pytest.skip("No cost record for test")

        response = client.post(
            f"{settings.API_V1_PREFIX}/costs/allocation/{cost.id}/allocate",
            json={},  # 缺少rule_id或allocation_targets
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 422]
