# -*- coding: utf-8 -*-
"""
AI项目规划助手 API测试
"""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.v1.ai_planning import router as ai_planning_router
from app.core.auth import get_current_user
from app.dependencies import get_db
from app.models import Project
from app.models.ai_planning import AIProjectPlanTemplate, AIWbsSuggestion


def _unique_code(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8].upper()}"


@pytest.fixture
def ai_planning_client(db: Session):
    app = FastAPI()

    def override_get_db():
        yield db

    async def override_get_current_user():
        return SimpleNamespace(id=1, username="tester")

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.include_router(ai_planning_router, prefix="/api/v1")

    with TestClient(app) as client:
        yield client


@pytest.fixture
def sample_project(db: Session):
    """创建测试项目"""
    project = Project(
        project_code=_unique_code("API_TEST"),
        project_name="API测试项目",
        project_type="WEB_DEV",
        status="ST01",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@pytest.fixture
def mock_plan_generator(monkeypatch):
    async def fake_generate_plan(self, **kwargs):
        return SimpleNamespace(
            id=123,
            template_code="TPL_API_001",
            template_name=f"{kwargs['project_name']}计划模板",
            estimated_duration_days=30,
            estimated_effort_hours=240.0,
            estimated_cost=50000.0,
            confidence_score=88.5,
            phases='[{"name":"需求分析"}]',
            milestones='[{"name":"立项"}]',
            required_roles='[{"role":"开发"}]',
            risk_factors='[{"risk":"需求变更"}]',
        )

    monkeypatch.setattr(
        "app.api.v1.ai_planning.AIProjectPlanGenerator.generate_plan", fake_generate_plan
    )


@pytest.fixture
def mock_wbs_decomposer(monkeypatch):
    async def fake_decompose_project(self, project_id, template_id=None, max_level=3):
        return [
            SimpleNamespace(
                id=1,
                wbs_code="1",
                task_name="需求分析",
                wbs_level=1,
                parent_wbs_id=None,
                estimated_duration_days=5,
                estimated_effort_hours=40,
                complexity="MEDIUM",
                is_critical_path=True,
            )
        ]

    monkeypatch.setattr(
        "app.api.v1.ai_planning.AIWbsDecomposer.decompose_project", fake_decompose_project
    )


@pytest.fixture
def mock_resource_optimizer(monkeypatch):
    async def fake_allocate_resources(self, wbs_suggestion_id, available_user_ids=None, constraints=None):
        return [
            SimpleNamespace(
                id=1,
                user_id=1,
                allocation_type="PRIMARY",
                overall_match_score=92.5,
                skill_match_score=90.0,
                availability_score=95.0,
                estimated_cost=8000.0,
                recommendation_reason="技能匹配度高",
            )
        ]

    monkeypatch.setattr(
        "app.api.v1.ai_planning.AIResourceOptimizer.allocate_resources", fake_allocate_resources
    )


@pytest.fixture
def mock_schedule_optimizer(monkeypatch):
    def fake_optimize_schedule(self, project_id, start_date=None, constraints=None):
        return {
            "project_id": project_id,
            "start_date": str(start_date or "2026-03-01"),
            "total_duration_days": 20,
            "end_date": "2026-03-21",
            "gantt_data": [
                {
                    "task_id": 1,
                    "task_name": "需求分析",
                    "wbs_code": "1",
                    "level": 1,
                    "parent_id": None,
                    "start_date": "2026-03-01",
                    "end_date": "2026-03-05",
                    "duration_days": 5,
                    "is_critical": True,
                    "progress": 0,
                }
            ],
            "critical_path": [{"task_id": 1, "task_name": "需求分析"}],
            "critical_path_length": 1,
            "resource_load": {},
            "conflicts": [],
            "recommendations": [],
            "optimization_summary": {"status": "ok"},
        }

    monkeypatch.setattr(
        "app.api.v1.ai_planning.AIScheduleOptimizer.optimize_schedule", fake_optimize_schedule
    )


class TestAIPlanningAPI:
    """AI项目规划API测试"""

    def test_generate_plan_api(self, ai_planning_client: TestClient, mock_plan_generator):
        response = ai_planning_client.post(
            "/api/v1/ai-planning/generate-plan",
            json={
                "project_name": "测试项目",
                "project_type": "WEB_DEV",
                "requirements": "开发一个电商网站",
                "industry": "电商",
                "complexity": "MEDIUM",
                "use_template": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["template_id"] == 123
        assert data["estimated_duration_days"] == 30

    def test_list_templates_api(self, ai_planning_client: TestClient, db: Session):
        template = AIProjectPlanTemplate(
            template_code=_unique_code("API_TPL"),
            template_name="API测试模板",
            project_type="WEB_DEV",
            is_active=True,
            estimated_duration_days=15,
        )
        db.add(template)
        db.commit()

        response = ai_planning_client.get(
            "/api/v1/ai-planning/templates",
            params={"project_type": "WEB_DEV"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(item["template_id"] == template.id for item in data)

    def test_get_template_detail_api(self, ai_planning_client: TestClient, db: Session):
        template = AIProjectPlanTemplate(
            template_code=_unique_code("API_TPL"),
            template_name="API测试模板",
            project_type="WEB_DEV",
            is_active=True,
            estimated_duration_days=20,
        )
        db.add(template)
        db.commit()
        db.refresh(template)

        response = ai_planning_client.get(f"/api/v1/ai-planning/templates/{template.id}")

        assert response.status_code == 200
        assert response.json()["template_id"] == template.id

    def test_decompose_wbs_api(
        self,
        ai_planning_client: TestClient,
        sample_project,
        mock_wbs_decomposer,
    ):
        response = ai_planning_client.post(
            "/api/v1/ai-planning/decompose-wbs",
            json={"project_id": sample_project.id, "max_level": 2},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_tasks"] == 1
        assert len(data["suggestions"]) == 1

    def test_get_wbs_suggestions_api(self, ai_planning_client: TestClient, sample_project):
        response = ai_planning_client.get(f"/api/v1/ai-planning/wbs/{sample_project.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == sample_project.id
        assert "suggestions" in data

    def test_accept_wbs_api(self, ai_planning_client: TestClient, db: Session, sample_project):
        wbs = AIWbsSuggestion(
            suggestion_code=_unique_code("API_WBS"),
            project_id=sample_project.id,
            wbs_level=1,
            wbs_code="1",
            task_name="测试任务",
            estimated_duration_days=10,
            is_active=True,
        )
        db.add(wbs)
        db.commit()
        db.refresh(wbs)

        response = ai_planning_client.patch(f"/api/v1/ai-planning/wbs/{wbs.id}/accept")

        assert response.status_code == 200
        assert response.json()["wbs_id"] == wbs.id

    def test_reject_wbs_api(self, ai_planning_client: TestClient, db: Session, sample_project):
        wbs = AIWbsSuggestion(
            suggestion_code=_unique_code("API_WBS"),
            project_id=sample_project.id,
            wbs_level=1,
            wbs_code="1",
            task_name="测试任务",
            estimated_duration_days=10,
            is_active=True,
        )
        db.add(wbs)
        db.commit()
        db.refresh(wbs)

        response = ai_planning_client.patch(
            f"/api/v1/ai-planning/wbs/{wbs.id}/reject",
            params={"reason": "不符合需求"},
        )

        assert response.status_code == 200
        assert response.json()["wbs_id"] == wbs.id

    def test_allocate_resources_api(
        self,
        ai_planning_client: TestClient,
        db: Session,
        sample_project,
        mock_resource_optimizer,
    ):
        wbs = AIWbsSuggestion(
            suggestion_code=_unique_code("API_WBS_RES"),
            project_id=sample_project.id,
            wbs_level=1,
            wbs_code="1",
            task_name="测试任务",
            estimated_duration_days=10,
            is_active=True,
        )
        db.add(wbs)
        db.commit()
        db.refresh(wbs)

        response = ai_planning_client.post(
            "/api/v1/ai-planning/allocate-resources",
            json={"wbs_suggestion_id": wbs.id, "available_user_ids": None, "constraints": None},
        )

        assert response.status_code == 200
        assert response.json()["total_recommendations"] == 1

    def test_get_resource_allocations_api(self, ai_planning_client: TestClient, sample_project):
        response = ai_planning_client.get(f"/api/v1/ai-planning/allocations/{sample_project.id}")

        assert response.status_code == 200
        assert response.json()["project_id"] == sample_project.id

    def test_optimize_schedule_api(
        self,
        ai_planning_client: TestClient,
        sample_project,
        mock_schedule_optimizer,
    ):
        response = ai_planning_client.post(
            "/api/v1/ai-planning/optimize-schedule",
            json={"project_id": sample_project.id, "start_date": "2026-03-01", "constraints": None},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_duration_days"] == 20
        assert "gantt_data" in data
        assert "critical_path" in data

    def test_get_project_schedule_api(
        self,
        ai_planning_client: TestClient,
        sample_project,
        mock_schedule_optimizer,
    ):
        response = ai_planning_client.get(f"/api/v1/ai-planning/schedule/{sample_project.id}")

        assert response.status_code == 200
        assert response.json()["project_id"] == sample_project.id

    def test_get_accuracy_statistics_api(self, ai_planning_client: TestClient):
        response = ai_planning_client.get("/api/v1/ai-planning/statistics/accuracy")

        assert response.status_code == 200
        data = response.json()
        assert "wbs_accuracy" in data
        assert "resource_allocation_accuracy" in data

    def test_get_performance_statistics_api(self, ai_planning_client: TestClient):
        response = ai_planning_client.get("/api/v1/ai-planning/statistics/performance")

        assert response.status_code == 200
        data = response.json()
        assert "avg_generation_time_seconds" in data
        assert "success_rate" in data

    def test_api_error_handling(self, ai_planning_client: TestClient):
        response = ai_planning_client.get("/api/v1/ai-planning/templates/99999")

        assert response.status_code == 404

    def test_api_validation(self, ai_planning_client: TestClient):
        response = ai_planning_client.post(
            "/api/v1/ai-planning/generate-plan",
            json={"project_name": "测试"},
        )

        assert response.status_code == 422
