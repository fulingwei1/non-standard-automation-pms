# -*- coding: utf-8 -*-
"""
项目列表成本显示增强 - 单元测试
测试项目列表API的成本功能（include_cost, 排序, 过滤）
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectCost
from app.models.project.financial import FinancialProjectCost
from app.models.user import User
from app.schemas.project import ProjectCostSummary


class TestProjectCostListEnhancement:
    """项目列表成本显示增强测试"""

    @pytest.fixture
    def test_projects(self, db: Session) -> list:
        """创建测试项目数据"""
        projects = []
        
        # 项目1：正常预算内
        p1 = Project(
            project_code="TEST-001",
            project_name="正常项目",
            budget_amount=Decimal("1000000"),
            actual_cost=Decimal("750000"),  # 75% 预算使用率
            stage="S3",
            health="H1",
            progress_pct=Decimal("60"),
            is_active=True,
        )
        db.add(p1)
        
        # 项目2：超支项目
        p2 = Project(
            project_code="TEST-002",
            project_name="超支项目",
            budget_amount=Decimal("500000"),
            actual_cost=Decimal("650000"),  # 130% 超支
            stage="S4",
            health="H3",
            progress_pct=Decimal("80"),
            is_active=True,
        )
        db.add(p2)
        
        # 项目3：预算告急
        p3 = Project(
            project_code="TEST-003",
            project_name="预算告急项目",
            budget_amount=Decimal("800000"),
            actual_cost=Decimal("760000"),  # 95% 预算使用率
            stage="S3",
            health="H2",
            progress_pct=Decimal("70"),
            is_active=True,
        )
        db.add(p3)
        
        # 项目4：低成本项目
        p4 = Project(
            project_code="TEST-004",
            project_name="低成本项目",
            budget_amount=Decimal("300000"),
            actual_cost=Decimal("150000"),  # 50% 预算使用率
            stage="S2",
            health="H1",
            progress_pct=Decimal("40"),
            is_active=True,
        )
        db.add(p4)
        
        db.commit()
        
        # 刷新以获取ID
        for p in [p1, p2, p3, p4]:
            db.refresh(p)
            projects.append(p)
        
        return projects

    @pytest.fixture
    def test_project_costs(self, db: Session, test_projects: list) -> None:
        """创建测试成本明细数据"""
        p1, p2, p3, p4 = test_projects
        
        # 项目1的成本明细
        costs_p1 = [
            ProjectCost(
                project_id=p1.id,
                cost_type="LABOR",
                cost_category="人工",
                amount=Decimal("400000"),
                cost_date=date.today() - timedelta(days=30),
            ),
            ProjectCost(
                project_id=p1.id,
                cost_type="MATERIAL",
                cost_category="材料",
                amount=Decimal("250000"),
                cost_date=date.today() - timedelta(days=20),
            ),
            ProjectCost(
                project_id=p1.id,
                cost_type="EQUIPMENT",
                cost_category="设备",
                amount=Decimal("100000"),
                cost_date=date.today() - timedelta(days=10),
            ),
        ]
        
        # 项目2的成本明细（超支项目）
        costs_p2 = [
            ProjectCost(
                project_id=p2.id,
                cost_type="LABOR",
                cost_category="人工",
                amount=Decimal("450000"),
                cost_date=date.today() - timedelta(days=30),
            ),
            FinancialProjectCost(
                project_id=p2.id,
                cost_type="MATERIAL",
                cost_category="材料",
                amount=Decimal("200000"),
                cost_date=date.today() - timedelta(days=15),
                uploaded_by=1,
            ),
        ]
        
        for cost in costs_p1 + costs_p2:
            db.add(cost)
        
        db.commit()

    def test_project_list_without_cost(
        self, client: TestClient, auth_headers: dict
    ):
        """测试项目列表（不包含成本）"""
        response = client.get(
            "/api/v1/projects/",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        
        # 默认不包含成本摘要
        if data["items"]:
            assert data["items"][0].get("cost_summary") is None

    def test_project_list_with_cost(
        self, 
        client: TestClient, 
        auth_headers: dict,
        test_projects: list,
        test_project_costs: None,
    ):
        """测试项目列表（包含成本）"""
        response = client.get(
            "/api/v1/projects/?include_cost=true",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] >= 4
        items = data["items"]
        
        # 至少有一个项目包含成本摘要
        assert any(item.get("cost_summary") is not None for item in items)
        
        # 验证成本摘要结构
        for item in items:
            if item.get("cost_summary"):
                cost_summary = item["cost_summary"]
                
                # 必须包含的字段
                assert "total_cost" in cost_summary
                assert "budget" in cost_summary
                assert "budget_used_pct" in cost_summary
                assert "overrun" in cost_summary
                assert "variance" in cost_summary
                assert "variance_pct" in cost_summary
                
                # 验证数据类型
                assert isinstance(cost_summary["overrun"], bool)
                assert float(cost_summary["budget_used_pct"]) >= 0
                
                # 成本明细（可选）
                if cost_summary.get("cost_breakdown"):
                    breakdown = cost_summary["cost_breakdown"]
                    assert "labor" in breakdown
                    assert "material" in breakdown
                    assert "equipment" in breakdown
                    assert "travel" in breakdown
                    assert "other" in breakdown

    def test_project_list_overrun_only(
        self,
        client: TestClient,
        auth_headers: dict,
        test_projects: list,
    ):
        """测试仅显示超支项目"""
        response = client.get(
            "/api/v1/projects/?overrun_only=true&include_cost=true",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        items = data["items"]
        
        # 所有返回的项目都应该是超支项目
        for item in items:
            if item.get("cost_summary"):
                assert item["cost_summary"]["overrun"] is True

    def test_project_list_sort_by_cost_desc(
        self,
        client: TestClient,
        auth_headers: dict,
        test_projects: list,
    ):
        """测试按成本倒序排序"""
        response = client.get(
            "/api/v1/projects/?sort=cost_desc&include_cost=true",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        items = data["items"]
        
        # 验证排序（成本倒序）
        costs = [
            float(item["cost_summary"]["total_cost"]) 
            for item in items 
            if item.get("cost_summary")
        ]
        
        if len(costs) > 1:
            assert costs == sorted(costs, reverse=True)

    def test_project_list_sort_by_cost_asc(
        self,
        client: TestClient,
        auth_headers: dict,
        test_projects: list,
    ):
        """测试按成本正序排序"""
        response = client.get(
            "/api/v1/projects/?sort=cost_asc&include_cost=true",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        items = data["items"]
        
        # 验证排序（成本正序）
        costs = [
            float(item["cost_summary"]["total_cost"]) 
            for item in items 
            if item.get("cost_summary")
        ]
        
        if len(costs) > 1:
            assert costs == sorted(costs)

    def test_project_list_sort_by_budget_used_pct(
        self,
        client: TestClient,
        auth_headers: dict,
        test_projects: list,
    ):
        """测试按预算使用率排序"""
        response = client.get(
            "/api/v1/projects/?sort=budget_used_pct&include_cost=true",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        items = data["items"]
        
        # 验证排序（预算使用率倒序）
        usage_rates = [
            float(item["cost_summary"]["budget_used_pct"]) 
            for item in items 
            if item.get("cost_summary")
        ]
        
        if len(usage_rates) > 1:
            assert usage_rates == sorted(usage_rates, reverse=True)

    def test_project_cost_summary_accuracy(
        self,
        client: TestClient,
        auth_headers: dict,
        test_projects: list,
        test_project_costs: None,
    ):
        """测试成本摘要数据准确性"""
        # 获取项目1（正常项目）
        p1 = test_projects[0]
        
        response = client.get(
            f"/api/v1/projects/?include_cost=true&keyword={p1.project_code}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] >= 1
        item = data["items"][0]
        
        cost_summary = item["cost_summary"]
        
        # 验证成本数据
        assert float(cost_summary["total_cost"]) == 750000.0
        assert float(cost_summary["budget"]) == 1000000.0
        assert float(cost_summary["budget_used_pct"]) == 75.0
        assert cost_summary["overrun"] is False
        assert float(cost_summary["variance"]) == -250000.0
        assert float(cost_summary["variance_pct"]) == -25.0
        
        # 验证成本明细
        breakdown = cost_summary["cost_breakdown"]
        assert float(breakdown["labor"]) == 400000.0
        assert float(breakdown["material"]) == 250000.0
        assert float(breakdown["equipment"]) == 100000.0

    def test_project_cost_overrun_detection(
        self,
        client: TestClient,
        auth_headers: dict,
        test_projects: list,
    ):
        """测试超支项目检测"""
        # 获取项目2（超支项目）
        p2 = test_projects[1]
        
        response = client.get(
            f"/api/v1/projects/?include_cost=true&keyword={p2.project_code}",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] >= 1
        item = data["items"][0]
        
        cost_summary = item["cost_summary"]
        
        # 验证超支检测
        assert cost_summary["overrun"] is True
        assert float(cost_summary["total_cost"]) > float(cost_summary["budget"])
        assert float(cost_summary["budget_used_pct"]) > 100.0
        assert float(cost_summary["variance"]) > 0

    def test_project_list_performance(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
    ):
        """测试性能（100个项目 < 1秒）"""
        import time
        
        # 创建100个测试项目
        projects = []
        for i in range(100):
            p = Project(
                project_code=f"PERF-{i:03d}",
                project_name=f"性能测试项目{i}",
                budget_amount=Decimal(str(100000 + i * 1000)),
                actual_cost=Decimal(str(80000 + i * 800)),
                stage="S3",
                is_active=True,
            )
            projects.append(p)
        
        db.bulk_save_objects(projects)
        db.commit()
        
        # 测试查询性能
        start_time = time.time()
        
        response = client.get(
            "/api/v1/projects/?include_cost=true&page_size=100",
            headers=auth_headers,
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 100
        
        # 验证性能要求：100个项目 < 1秒
        assert elapsed_time < 1.0, f"查询耗时 {elapsed_time:.2f}秒，超过1秒限制"

    def test_combined_filters(
        self,
        client: TestClient,
        auth_headers: dict,
        test_projects: list,
    ):
        """测试组合过滤（成本 + 其他筛选条件）"""
        response = client.get(
            "/api/v1/projects/?include_cost=true&stage=S3&sort=cost_desc",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        items = data["items"]
        
        # 验证阶段筛选
        for item in items:
            assert item["stage"] == "S3"
        
        # 验证排序
        if len(items) > 1:
            costs = [
                float(item["cost_summary"]["total_cost"]) 
                for item in items 
                if item.get("cost_summary")
            ]
            if len(costs) > 1:
                assert costs == sorted(costs, reverse=True)


class TestProjectCostAggregationService:
    """项目成本聚合服务测试"""

    def test_get_projects_cost_summary(
        self,
        db: Session,
        test_projects: list,
        test_project_costs: None,
    ):
        """测试批量获取成本摘要"""
        from app.services.project_cost_aggregation_service import ProjectCostAggregationService
        
        service = ProjectCostAggregationService(db)
        project_ids = [p.id for p in test_projects[:2]]  # 测试前2个项目
        
        summaries = service.get_projects_cost_summary(project_ids, include_breakdown=True)
        
        assert len(summaries) == 2
        
        for project_id, summary in summaries.items():
            assert isinstance(summary, ProjectCostSummary)
            assert summary.total_cost >= 0
            assert summary.budget >= 0
            assert summary.budget_used_pct >= 0
            assert isinstance(summary.overrun, bool)

    def test_cost_type_mapping(self):
        """测试成本类型映射"""
        from app.services.project_cost_aggregation_service import ProjectCostAggregationService
        
        service = ProjectCostAggregationService(None)
        
        # 测试各种成本类型映射
        assert service._map_cost_type("LABOR") == "labor"
        assert service._map_cost_type("人工") == "labor"
        assert service._map_cost_type("MATERIAL") == "material"
        assert service._map_cost_type("材料") == "material"
        assert service._map_cost_type("EQUIPMENT") == "equipment"
        assert service._map_cost_type("设备") == "equipment"
        assert service._map_cost_type("TRAVEL") == "travel"
        assert service._map_cost_type("差旅") == "travel"
        assert service._map_cost_type("OTHER") == "other"
        assert service._map_cost_type("未知类型") == "other"
        assert service._map_cost_type(None) == "other"

    def test_empty_project_list(self, db: Session):
        """测试空项目列表"""
        from app.services.project_cost_aggregation_service import ProjectCostAggregationService
        
        service = ProjectCostAggregationService(db)
        summaries = service.get_projects_cost_summary([])
        
        assert summaries == {}

    def test_get_cost_summary_for_single_project(
        self,
        db: Session,
        test_projects: list,
        test_project_costs: None,
    ):
        """测试获取单个项目成本摘要"""
        from app.services.project_cost_aggregation_service import ProjectCostAggregationService
        
        service = ProjectCostAggregationService(db)
        p1 = test_projects[0]
        
        summary = service.get_cost_summary_for_project(p1.id, include_breakdown=True)
        
        assert summary is not None
        assert isinstance(summary, ProjectCostSummary)
        assert summary.total_cost == Decimal("750000.00")
        assert summary.budget == Decimal("1000000.00")
        assert summary.budget_used_pct == Decimal("75.00")
        assert summary.overrun is False
