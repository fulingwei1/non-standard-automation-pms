# -*- coding: utf-8 -*-
"""PROJ-26: team generation must use initiation context and real experience signals."""

import json
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.models.engineer_capacity import EngineerCapacity, EngineerTaskAssignment
from app.models.pmo import PmoProjectInitiation
from app.models.project import Project
from app.models.user import User
from app.services.team_generation_service import TeamGenerationService


class _Query:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *args, **kwargs):
        return self

    def outerjoin(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        return self.rows

    def first(self):
        return self.rows[0] if self.rows else None


class _TeamDb:
    def __init__(self, project=None, initiation=None, engineer_pairs=None, assignments=None):
        self.project = project
        self.initiation = initiation
        self.engineer_pairs = engineer_pairs or []
        self.assignments = assignments or []

    def query(self, *models):
        if models == (Project,):
            return _Query([self.project] if self.project else [])
        if models == (PmoProjectInitiation,):
            return _Query([self.initiation] if self.initiation else [])
        if models == (User, EngineerCapacity):
            return _Query(self.engineer_pairs)
        if models == (EngineerTaskAssignment,):
            return _Query(self.assignments)
        return _Query([])


def _project(**overrides):
    data = {
        "id": 7,
        "project_name": "视觉检测线项目",
        "product_category": "",
        "industry": "",
        "contract_amount": Decimal("100000"),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def _initiation(**overrides):
    data = {
        "id": 11,
        "project_id": 7,
        "status": "APPROVED",
        "estimated_hours": 320,
        "resource_requirements": "需要视觉算法、软件开发和现场调试资源",
        "technical_difficulty": "HIGH",
        "project_level": "A",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def _engineer_pair():
    user = SimpleNamespace(
        id=101,
        username="eng101",
        real_name="高工",
        department="工程部",
        is_active=True,
    )
    capacity = SimpleNamespace(
        skill_tags=json.dumps(
            [
                "项目管理",
                "客户沟通",
                "系统设计",
                "技术评审",
                "视觉算法",
                "光学调试",
                "软件开发",
                "上位机",
                "快速诊断",
            ],
            ensure_ascii=False,
        ),
        ai_skill_level="EXPERT",
        multi_project_capacity=6,
        standardization_score=9.0,
        workload_status="NORMAL",
        avg_quality_score=9.0,
        on_time_delivery_rate=98.0,
        rework_rate=0.0,
    )
    return user, capacity


def _assignment(**overrides):
    data = {
        "engineer_id": 101,
        "project_id": 1,
        "task_type": "视觉算法",
        "status": "COMPLETED",
        "quality_score": 9.0,
        "is_on_time": True,
        "has_rework": False,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_team_plan_uses_approved_initiation_context_for_roles_and_hours():
    user, capacity = _engineer_pair()
    service = TeamGenerationService(
        _TeamDb(
            project=_project(),
            initiation=_initiation(),
            engineer_pairs=[(user, capacity)],
            assignments=[_assignment() for _ in range(5)],
        )
    )

    plan = service.generate_team_plan(project_id=7)

    assert plan["requirements"]["source"] == "pmo_initiation"
    assert plan["requirements"]["initiation_id"] == 11
    assert "VISION_ENG" in plan["role_assignments"]
    assert "SOFTWARE_ENG" in plan["role_assignments"]
    assert plan["total_estimated_hours"] == pytest.approx(320.0)


def test_role_match_experience_score_uses_history_instead_of_fixed_full_score():
    user, capacity = _engineer_pair()
    role_info = {
        "required_skills": ["视觉算法"],
        "min_experience": 5,
        "ai_level": "NONE",
    }
    project = _project()

    low_history = TeamGenerationService(
        _TeamDb(assignments=[], engineer_pairs=[(user, capacity)])
    )._calculate_role_match(user, capacity, "VISION_ENG", role_info, project)
    strong_history = TeamGenerationService(
        _TeamDb(
            assignments=[_assignment() for _ in range(5)],
            engineer_pairs=[(user, capacity)],
        )
    )._calculate_role_match(user, capacity, "VISION_ENG", role_info, project)

    assert strong_history["score"] > low_history["score"]
    assert "经验" in strong_history["reason"]
