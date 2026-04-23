# -*- coding: utf-8 -*-
"""team_generation_service 深度测试"""

from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.services.team_generation_service import TeamGenerationService


class FakeQuery:
    def __init__(self, first_value=None, all_value=None):
        self._first_value = first_value
        self._all_value = all_value or []

    def filter(self, *args, **kwargs):
        return self

    def outerjoin(self, *args, **kwargs):
        return self

    def all(self):
        return self._all_value

    def first(self):
        return self._first_value


class TestTeamGenerationServiceDeep:
    def test_generate_team_plan_returns_error_when_project_missing(self):
        db = Mock()
        db.query.return_value = FakeQuery(first_value=None)
        service = TeamGenerationService(db)

        result = service.generate_team_plan(1)

        assert result == {"error": "项目不存在"}

    def test_analyze_project_requirements_large_vision(self):
        service = TeamGenerationService(Mock())
        project = SimpleNamespace(product_category="vision", industry="汽车", contract_amount=6000000)

        result = service._analyze_project_requirements(project)

        assert result["scale"] == "LARGE"
        assert result["tech_complexity"] == "EXPERT"
        assert "IATF16949" in result["industry_requirements"]

    def test_determine_roles_for_large_ict_project(self):
        service = TeamGenerationService(Mock())

        result = service._determine_roles({"scale": "LARGE", "product_category": "ICT"}, SimpleNamespace())

        assert result["ELEC_ENG"]["count"] == 2
        assert result["MECH_ENG"]["count"] == 1
        assert result["SERVICE_ENG"]["customer_facing"] is True

    def test_calculate_role_match_handles_invalid_skill_json_and_overload(self):
        service = TeamGenerationService(Mock())
        engineer = SimpleNamespace()
        capacity = SimpleNamespace(
            skill_tags="not-json",
            ai_skill_level="BASIC",
            multi_project_capacity=1,
            standardization_score=5.0,
            workload_status="OVERLOAD",
        )
        role_info = {
            "required_skills": ["项目管理", "客户沟通"],
            "ai_level": "ADVANCED",
            "multi_project_min": 3,
            "standardization_min": 7.0,
        }

        result = service._calculate_role_match(engineer, capacity, "PM", role_info, SimpleNamespace())

        assert result["score"] == 13.0
        assert result["reason"] == ""

    def test_calculate_role_match_high_match(self):
        service = TeamGenerationService(Mock())
        engineer = SimpleNamespace()
        capacity = SimpleNamespace(
            skill_tags='["系统设计", "技术评审", "项目管理"]',
            ai_skill_level="ADVANCED",
            multi_project_capacity=6,
            standardization_score=8.5,
            workload_status="NORMAL",
        )
        role_info = {
            "required_skills": ["系统设计", "技术评审"],
            "ai_level": "ADVANCED",
            "multi_project_min": 3,
            "standardization_min": 7.0,
        }

        result = service._calculate_role_match(engineer, capacity, "TECH_LEAD", role_info, SimpleNamespace())

        assert result["score"] == 100
        assert "技能匹配" in result["reason"]
        assert "AI 能力达标" in result["reason"]

    def test_match_engineers_for_role_filters_low_scores_and_sorts(self):
        db = Mock()
        users = [
            (SimpleNamespace(id=1, real_name="A", username="a", department="D"), SimpleNamespace()),
            (SimpleNamespace(id=2, real_name="B", username="b", department="D"), SimpleNamespace()),
            (SimpleNamespace(id=3, real_name="C", username="c", department="D"), None),
        ]
        db.query.return_value = FakeQuery(all_value=users)
        service = TeamGenerationService(db)
        service._calculate_role_match = Mock(side_effect=[
            {"score": 61, "reason": "ok"},
            {"score": 88, "reason": "better"},
        ])
        service._estimate_hours = Mock(return_value=12)

        result = service._match_engineers_for_role("PM", {"required_skills": []}, SimpleNamespace())

        assert [r["engineer_id"] for r in result] == [2, 1]
        assert result[0]["role_name"] == "项目经理"

    def test_create_team_plan_generates_advantages_and_risks(self):
        service = TeamGenerationService(Mock())
        project = SimpleNamespace(id=1, project_name="P1")
        role_assignments = {
            "PM": {
                "engineer_id": 1,
                "engineer_name": "张三",
                "estimated_hours": 40,
                "capacity": SimpleNamespace(ai_skill_level="ADVANCED", multi_project_capacity=5, workload_status="NORMAL"),
            },
            "TECH_LEAD": {
                "engineer_id": 2,
                "engineer_name": "李四",
                "estimated_hours": 24,
                "capacity": SimpleNamespace(ai_skill_level="BASIC", multi_project_capacity=2, workload_status="OVERLOAD"),
            },
        }

        result = service._create_team_plan(project, role_assignments, {})

        assert result["total_members"] == 2
        assert result["estimated_duration_days"] == 4
        assert "包含 AI 高级用户，效率有保障" in result["advantages"]
        assert result["risks"]
        assert result["recommendations"] == ["建议确认过载工程师的时间安排"]

    def test_save_team_plan_creates_plan_and_members(self):
        db = Mock()
        service = TeamGenerationService(db)
        team_data = {
            "project_id": 1,
            "project_name": "P1",
            "total_members": 2,
            "total_estimated_hours": 64,
            "estimated_duration_days": 4,
            "overall_score": 88.5,
            "skill_coverage": 85,
            "capacity_balance": 80,
            "cost_efficiency": 80,
            "role_assignments": {
                "PM": {"engineer_id": 1, "engineer_name": "张三", "role_name": "项目经理", "estimated_hours": 40, "match_score": 90, "match_reason": "好"},
                "TECH_LEAD": {"engineer_id": 2, "engineer_name": "李四", "role_name": "技术负责人", "estimated_hours": 24, "match_score": 87, "match_reason": "稳"},
            },
            "advantages": ["匹配度高"],
            "risks": [],
            "recommendations": ["尽快确认"]
        }

        def fake_plan(**kwargs):
            data = SimpleNamespace(**kwargs)
            data.id = 99
            return data

        with patch("app.services.team_generation_service.ProjectTeamPlan", side_effect=fake_plan), patch(
            "app.services.team_generation_service.ProjectTeamMember",
            side_effect=lambda **kwargs: SimpleNamespace(**kwargs),
        ):
            plan = service.save_team_plan(team_data, submitted_by=7)

        assert plan.project_id == 1
        assert db.flush.called
        assert db.commit.called
        assert db.refresh.called
        assert db.add.call_count == 3
