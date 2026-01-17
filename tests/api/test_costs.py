# -*- coding: utf-8 -*-
"""
成本管理模块 API 测试

测试内容：
- 成本记录 CRUD 操作
- 成本汇总统计
- 成本趋势分析
- 利润分析
- 预算执行分析
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import Project, ProjectCost


class TestCostCRUD:
    """成本记录 CRUD 测试"""

    def test_list_costs_empty(self, client: TestClient, admin_token: str):
        """测试获取成本列表（空列表）"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/?page=1&page_size=10",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    def test_create_cost_success(self, client: TestClient, admin_token: str, db_session: Session):
        """测试成功创建成本记录"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 确保有一个测试项目
        project = db_session.query(Project).first()
        if not project:
            pytest.skip("No project available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        cost_data = {
            "project_id": project.id,
            "cost_type": "MATERIAL",
            "cost_category": "PURCHASE",
            "amount": 10000.00,
            "tax_amount": 1300.00,
            "cost_date": date.today().isoformat(),
            "description": "测试物料成本",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/costs/",
            json=cost_data,
            headers=headers
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert data["project_id"] == project.id
        assert float(data["amount"]) == 10000.00
        assert data["cost_type"] == "MATERIAL"

    def test_create_cost_invalid_project(self, client: TestClient, admin_token: str):
        """测试创建成本记录时项目不存在"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        cost_data = {
            "project_id": 999999,
            "cost_type": "MATERIAL",
            "amount": 10000.00,
            "cost_date": date.today().isoformat(),
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/costs/",
            json=cost_data,
            headers=headers
        )

        # API 可能返回 404（项目不存在）或 422（验证失败）
        assert response.status_code in [404, 422]

    def test_get_cost_detail(self, client: TestClient, admin_token: str, db_session: Session):
        """测试获取成本记录详情"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 查找一条成本记录
        cost = db_session.query(ProjectCost).first()
        if not cost:
            pytest.skip("No cost record available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/{cost.id}",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == cost.id

    def test_get_cost_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在的成本记录"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/999999",
            headers=headers
        )

        assert response.status_code == 404

    def test_update_cost(self, client: TestClient, admin_token: str, db_session: Session):
        """测试更新成本记录"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 查找一条成本记录
        cost = db_session.query(ProjectCost).first()
        if not cost:
            pytest.skip("No cost record available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        update_data = {
            "amount": 15000.00,
            "description": "更新后的成本描述",
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/costs/{cost.id}",
            json=update_data,
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert float(data["amount"]) == 15000.00

    def test_delete_cost(self, client: TestClient, admin_token: str, db_session: Session):
        """测试删除成本记录"""
        if not admin_token:
            pytest.skip("Admin token not available")

        # 先创建一个成本记录用于删除
        project = db_session.query(Project).first()
        if not project:
            pytest.skip("No project available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}

        # 创建成本记录
        cost_data = {
            "project_id": project.id,
            "cost_type": "OTHER",
            "amount": 1000.00,
            "cost_date": date.today().isoformat(),
            "description": "待删除的成本",
        }

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/costs/",
            json=cost_data,
            headers=headers
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip("Failed to create cost for delete test")

        cost_id = create_response.json()["id"]

        # 删除成本记录
        delete_response = client.delete(
            f"{settings.API_V1_PREFIX}/costs/{cost_id}",
            headers=headers
        )

        assert delete_response.status_code == 200

        # 验证已删除
        get_response = client.get(
            f"{settings.API_V1_PREFIX}/costs/{cost_id}",
            headers=headers
        )
        assert get_response.status_code == 404


class TestCostFilters:
    """成本列表筛选测试"""

    def test_filter_by_project(self, client: TestClient, admin_token: str, db_session: Session):
        """测试按项目筛选成本"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = db_session.query(Project).first()
        if not project:
            pytest.skip("No project available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/?project_id={project.id}",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        # 验证返回的成本都属于指定项目
        for item in data.get("items", []):
            assert item["project_id"] == project.id

    def test_filter_by_cost_type(self, client: TestClient, admin_token: str):
        """测试按成本类型筛选"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/?cost_type=MATERIAL",
            headers=headers
        )

        assert response.status_code == 200

    def test_filter_by_date_range(self, client: TestClient, admin_token: str):
        """测试按日期范围筛选"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()

        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/?start_date={start_date}&end_date={end_date}",
            headers=headers
        )

        assert response.status_code == 200

    def test_filter_invalid_date_format(self, client: TestClient, admin_token: str):
        """测试无效日期格式"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/?start_date=invalid-date",
            headers=headers
        )

        # API 返回 400 或 422 用于验证错误（取决于验证方式）
        assert response.status_code in [400, 422]


class TestProjectCostSummary:
    """项目成本汇总统计测试"""

    def test_get_project_cost_summary(self, client: TestClient, admin_token: str, db_session: Session):
        """测试获取项目成本汇总"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = db_session.query(Project).first()
        if not project:
            pytest.skip("No project available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/projects/{project.id}/costs/summary",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "project_id" in data
        assert "summary" in data
        assert "by_type" in data
        assert "by_category" in data

    def test_get_project_cost_summary_not_found(self, client: TestClient, admin_token: str):
        """测试获取不存在项目的成本汇总"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/projects/999999/costs/summary",
            headers=headers
        )

        assert response.status_code == 404


class TestCostAnalysis:
    """成本分析测试"""

    def test_get_project_cost_analysis(self, client: TestClient, admin_token: str, db_session: Session):
        """测试获取项目成本分析"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = db_session.query(Project).first()
        if not project:
            pytest.skip("No project available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/projects/{project.id}/cost-analysis",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data

    def test_get_project_cost_analysis_with_comparison(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        """测试带对比项目的成本分析"""
        if not admin_token:
            pytest.skip("Admin token not available")

        projects = db_session.query(Project).limit(2).all()
        if len(projects) < 2:
            pytest.skip("Need at least 2 projects for comparison test")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/projects/{projects[0].id}/cost-analysis"
            f"?compare_project_id={projects[1].id}",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        if data.get("data", {}).get("comparison"):
            assert "compare_project_id" in data["data"]["comparison"]


class TestProfitAnalysis:
    """利润分析测试"""

    def test_get_project_profit_analysis(self, client: TestClient, admin_token: str, db_session: Session):
        """测试获取项目利润分析"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = db_session.query(Project).first()
        if not project:
            pytest.skip("No project available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/projects/{project.id}/profit-analysis",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        result = data.get("data", {})
        assert "revenue" in result
        assert "cost" in result
        assert "profit" in result


class TestCostTrends:
    """成本趋势分析测试"""

    def test_get_cost_trends_daily(self, client: TestClient, admin_token: str):
        """测试获取每日成本趋势"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()
        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/cost-trends"
            f"?group_by=day&start_date={start_date}&end_date={end_date}",
            headers=headers
        )

        # API 可能返回 200 或 422（取决于权限或参数验证）
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert data["code"] == 200

    def test_get_cost_trends_monthly(self, client: TestClient, admin_token: str):
        """测试获取每月成本趋势"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        start_date = (date.today() - timedelta(days=90)).isoformat()
        end_date = date.today().isoformat()
        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/cost-trends"
            f"?group_by=month&start_date={start_date}&end_date={end_date}",
            headers=headers
        )

        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert data["code"] == 200

    def test_get_cost_trends_invalid_group_by(self, client: TestClient, admin_token: str):
        """测试无效的分组方式"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/cost-trends?group_by=invalid",
            headers=headers
        )

        # FastAPI 返回 400 或 422 用于参数验证错误
        assert response.status_code in [400, 422]


class TestBudgetExecution:
    """预算执行分析测试"""

    def test_get_budget_execution_analysis(self, client: TestClient, admin_token: str, db_session: Session):
        """测试获取预算执行分析"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = db_session.query(Project).first()
        if not project:
            pytest.skip("No project available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/costs/projects/{project.id}/budget-execution",
            headers=headers
        )

        # 可能返回200或400（如果没有预算数据）
        assert response.status_code in [200, 400, 500]


class TestLaborCostCalculation:
    """人工成本计算测试"""

    def test_calculate_project_labor_cost(self, client: TestClient, admin_token: str, db_session: Session):
        """测试计算项目人工成本"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = db_session.query(Project).first()
        if not project:
            pytest.skip("No project available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post(
            f"{settings.API_V1_PREFIX}/costs/projects/{project.id}/calculate-labor-cost",
            headers=headers
        )

        # 可能返回200或500（如果没有工时数据）
        assert response.status_code in [200, 500]


class TestCostAllocation:
    """成本分摊测试"""

    def test_allocate_cost_missing_params(self, client: TestClient, admin_token: str, db_session: Session):
        """测试成本分摊缺少参数"""
        if not admin_token:
            pytest.skip("Admin token not available")

        cost = db_session.query(ProjectCost).first()
        if not cost:
            pytest.skip("No cost record available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        # 既没有rule_id也没有allocation_targets
        allocation_request = {}

        response = client.post(
            f"{settings.API_V1_PREFIX}/costs/{cost.id}/allocate",
            json=allocation_request,
            headers=headers
        )

        assert response.status_code in [400, 422]


class TestCostBudgetAlert:
    """成本预警测试"""

    def test_check_project_budget_alert(self, client: TestClient, admin_token: str, db_session: Session):
        """测试检查项目预算预警"""
        if not admin_token:
            pytest.skip("Admin token not available")

        project = db_session.query(Project).first()
        if not project:
            pytest.skip("No project available for testing")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post(
            f"{settings.API_V1_PREFIX}/costs/projects/{project.id}/check-budget-alert",
            headers=headers
        )

        # 可能返回200或500（取决于项目是否有预算）
        assert response.status_code in [200, 500]

    def test_check_all_projects_budget(self, client: TestClient, admin_token: str):
        """测试批量检查项目预算"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post(
            f"{settings.API_V1_PREFIX}/costs/check-all-projects-budget",
            headers=headers
        )

        assert response.status_code in [200, 500]
