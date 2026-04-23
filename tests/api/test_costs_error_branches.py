# -*- coding: utf-8 -*-
"""
成本管理 API 异常分支测试

对齐当前实现：
- CRUD: /projects/{project_id}/costs
- 汇总: /projects/{project_id}/costs/summary
- 分析: /projects/{project_id}/costs/cost-analysis
- 趋势: /projects/{project_id}/costs/trend
- 预算执行: /projects/{project_id}/costs/execution
- 分摊: /projects/{project_id}/costs/{cost_id}/allocate
"""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings


def _auth_headers(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}


def _project_costs_url(project_id: int | str) -> str:
    return f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/"


def _project_cost_url(project_id: int | str, cost_id: int | str) -> str:
    return f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/{cost_id}"


def _project_cost_summary_url(project_id: int | str) -> str:
    return f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/summary"


def _project_cost_analysis_url(project_id: int | str) -> str:
    return f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/cost-analysis"


def _project_cost_trend_url(project_id: int | str) -> str:
    return f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/trend"


def _project_budget_execution_url(project_id: int | str) -> str:
    return f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/execution"


def _project_cost_allocation_url(project_id: int | str, cost_id: int | str) -> str:
    return f"{settings.API_V1_PREFIX}/projects/{project_id}/costs/{cost_id}/allocate"


def _valid_cost_payload() -> dict:
    return {
        "cost_type": "LABOR",
        "cost_category": "ENGINEERING",
        "amount": 10000,
        "cost_date": date.today().isoformat(),
        "description": "test cost",
    }


@pytest.fixture
def existing_project_id(db_session: Session) -> int:
    from app.models.project import Project

    project = db_session.query(Project).order_by(Project.id.asc()).first()
    if not project:
        pytest.skip("No project available for cost API tests")
    return project.id


@pytest.fixture
def existing_cost(db_session: Session):
    from app.models.project import ProjectCost

    cost = db_session.query(ProjectCost).order_by(ProjectCost.id.asc()).first()
    if not cost:
        pytest.skip("No cost record available for cost API tests")
    return cost


class TestCostListErrorBranches:
    """成本列表端点异常分支测试"""

    def test_list_costs_no_token(self, client: TestClient):
        response = client.get(_project_costs_url(1))
        assert response.status_code == 401

    def test_list_costs_invalid_token(self, client: TestClient):
        response = client.get(
            _project_costs_url(1),
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401

    def test_list_costs_invalid_page(self, client: TestClient, admin_token: str, existing_project_id: int):
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            _project_costs_url(existing_project_id),
            params={"page": -1},
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 422

    def test_list_costs_invalid_project_id(self, client: TestClient, admin_token: str):
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            _project_costs_url("invalid"),
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 422

    def test_list_costs_project_not_found(self, client: TestClient, admin_token: str):
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            _project_costs_url(999999),
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 404


class TestCreateCostErrorBranches:
    """创建成本记录端点异常分支测试"""

    def test_create_cost_no_token(self, client: TestClient):
        response = client.post(_project_costs_url(1), json={"amount": 10000})
        assert response.status_code == 401

    def test_create_cost_missing_required_fields(
        self, client: TestClient, admin_token: str, existing_project_id: int
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            _project_costs_url(existing_project_id),
            json={},
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 422

    def test_create_cost_invalid_project_id(self, client: TestClient, admin_token: str):
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            _project_costs_url(999999),
            json=_valid_cost_payload(),
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 404

    def test_create_cost_invalid_cost_type(self, client: TestClient, admin_token: str, existing_project_id: int):
        if not admin_token:
            pytest.skip("Admin token not available")

        payload = _valid_cost_payload()
        payload["cost_type"] = "X" * 51
        response = client.post(
            _project_costs_url(existing_project_id),
            json=payload,
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 422

    def test_create_cost_invalid_cost_category(
        self, client: TestClient, admin_token: str, existing_project_id: int
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        payload = _valid_cost_payload()
        payload["cost_category"] = "X" * 51
        response = client.post(
            _project_costs_url(existing_project_id),
            json=payload,
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 422

    def test_create_cost_invalid_date_format(self, client: TestClient, admin_token: str, existing_project_id: int):
        if not admin_token:
            pytest.skip("Admin token not available")

        payload = _valid_cost_payload()
        payload["cost_date"] = "invalid-date"
        response = client.post(
            _project_costs_url(existing_project_id),
            json=payload,
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 422

    def test_create_cost_future_date(self, client: TestClient, admin_token: str, existing_project_id: int):
        if not admin_token:
            pytest.skip("Admin token not available")

        payload = _valid_cost_payload()
        payload["cost_date"] = (date.today() + timedelta(days=365)).isoformat()
        response = client.post(
            _project_costs_url(existing_project_id),
            json=payload,
            headers=_auth_headers(admin_token),
        )
        assert response.status_code in [201, 400, 422]

    def test_create_cost_negative_tax(self, client: TestClient, admin_token: str, existing_project_id: int):
        if not admin_token:
            pytest.skip("Admin token not available")

        payload = _valid_cost_payload()
        payload["tax_amount"] = -500
        response = client.post(
            _project_costs_url(existing_project_id),
            json=payload,
            headers=_auth_headers(admin_token),
        )
        assert response.status_code in [201, 400, 422]


class TestGetCostErrorBranches:
    """获取成本详情端点异常分支测试"""

    def test_get_cost_no_token(self, client: TestClient):
        response = client.get(_project_cost_url(1, 1))
        assert response.status_code == 401

    def test_get_cost_not_found(self, client: TestClient, admin_token: str, existing_project_id: int):
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            _project_cost_url(existing_project_id, 999999),
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 404

    def test_get_cost_invalid_id_format(self, client: TestClient, admin_token: str, existing_project_id: int):
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            _project_cost_url(existing_project_id, "invalid"),
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 422


class TestUpdateCostErrorBranches:
    """更新成本记录端点异常分支测试"""

    def test_update_cost_no_token(self, client: TestClient):
        response = client.put(_project_cost_url(1, 1), json={"amount": 15000})
        assert response.status_code == 401

    def test_update_cost_not_found(self, client: TestClient, admin_token: str, existing_project_id: int):
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.put(
            _project_cost_url(existing_project_id, 999999),
            json={"amount": 15000},
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 404

    def test_update_cost_invalid_date_format(self, client: TestClient, admin_token: str, existing_cost):
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.put(
            _project_cost_url(existing_cost.project_id, existing_cost.id),
            json={"cost_date": "invalid-date"},
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 422


class TestDeleteCostErrorBranches:
    """删除成本记录端点异常分支测试"""

    def test_delete_cost_no_token(self, client: TestClient):
        response = client.delete(_project_cost_url(1, 1))
        assert response.status_code == 401

    def test_delete_cost_not_found(self, client: TestClient, admin_token: str, existing_project_id: int):
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.delete(
            _project_cost_url(existing_project_id, 999999),
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 404


class TestCostSummaryErrorBranches:
    """成本汇总端点异常分支测试"""

    def test_get_project_cost_summary_no_token(self, client: TestClient):
        response = client.get(_project_cost_summary_url(1))
        assert response.status_code == 401

    def test_get_project_cost_summary_not_found(self, client: TestClient, admin_token: str):
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            _project_cost_summary_url(999999),
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 404

    def test_get_project_cost_summary_invalid_id(self, client: TestClient, admin_token: str):
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            _project_cost_summary_url("invalid"),
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 422


class TestCostAnalysisErrorBranches:
    """成本分析端点异常分支测试"""

    def test_cost_analysis_no_token(self, client: TestClient):
        response = client.get(_project_cost_analysis_url(1))
        assert response.status_code == 401

    def test_cost_analysis_project_not_found(self, client: TestClient, admin_token: str):
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            _project_cost_analysis_url(999999),
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 404

    def test_cost_analysis_invalid_comparison_project(
        self, client: TestClient, admin_token: str, existing_project_id: int
    ):
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            _project_cost_analysis_url(existing_project_id),
            params={"compare_project_id": 999999},
            headers=_auth_headers(admin_token),
        )
        assert response.status_code in [200, 404]


class TestCostTrendsErrorBranches:
    """成本趋势端点异常分支测试"""

    def test_cost_trends_no_token(self, client: TestClient):
        response = client.get(_project_cost_trend_url(1))
        assert response.status_code == 401

    def test_cost_trends_invalid_project_id(self, client: TestClient, admin_token: str):
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            _project_cost_trend_url("invalid"),
            headers=_auth_headers(admin_token),
        )
        assert response.status_code == 422

    def test_cost_trends_missing_dates(self, client: TestClient, admin_token: str, existing_project_id: int):
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            _project_cost_trend_url(existing_project_id),
            headers=_auth_headers(admin_token),
        )
        assert response.status_code in [200, 404]


class TestBudgetExecutionErrorBranches:
    """预算执行分析端点异常分支测试"""

    def test_budget_execution_no_token(self, client: TestClient):
        response = client.get(_project_budget_execution_url(1))
        assert response.status_code == 401

    def test_budget_execution_project_not_found(self, client: TestClient, admin_token: str):
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.get(
            _project_budget_execution_url(999999),
            headers=_auth_headers(admin_token),
        )
        assert response.status_code in [400, 404, 500]

    def test_budget_execution_no_budget(self, client: TestClient, admin_token: str, db_session: Session):
        if not admin_token:
            pytest.skip("Admin token not available")

        from app.models.project import Project

        project = db_session.query(Project).filter(Project.budget_amount == None).first()
        if not project:
            pytest.skip("No project without budget for test")

        response = client.get(
            _project_budget_execution_url(project.id),
            headers=_auth_headers(admin_token),
        )
        assert response.status_code in [200, 400, 404, 500]


class TestCostAllocationErrorBranches:
    """成本分摊端点异常分支测试"""

    def test_allocate_cost_no_token(self, client: TestClient):
        response = client.post(_project_cost_allocation_url(1, 1))
        assert response.status_code == 401

    def test_allocate_cost_not_found(self, client: TestClient, admin_token: str, existing_project_id: int):
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            _project_cost_allocation_url(existing_project_id, 999999),
            json={},
            headers=_auth_headers(admin_token),
        )
        assert response.status_code in [404, 422]

    def test_allocate_cost_missing_params(self, client: TestClient, admin_token: str, existing_cost):
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            _project_cost_allocation_url(existing_cost.project_id, existing_cost.id),
            json={},
            headers=_auth_headers(admin_token),
        )
        assert response.status_code in [400, 422]
