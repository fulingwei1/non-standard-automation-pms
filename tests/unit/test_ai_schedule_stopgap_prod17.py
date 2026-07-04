# -*- coding: utf-8 -*-
"""PROD-17: AI 排程/优化不能在无证据时吐模板假数据。"""
from datetime import date
from unittest.mock import MagicMock

from app.services.schedule_generation_service import ScheduleGenerationService
from app.services.schedule_optimization_service import ScheduleOptimizationService


def _project(**kwargs):
    project = MagicMock()
    project.id = kwargs.get("id", 1)
    project.project_name = kwargs.get("project_name", "样机项目")
    project.product_category = kwargs.get("product_category", "非标自动化")
    project.industry = kwargs.get("industry", "锂电")
    project.planned_start_date = kwargs.get("planned_start_date", date(2026, 7, 1))
    project.planned_end_date = kwargs.get("planned_end_date", date(2026, 9, 1))
    project.created_at = kwargs.get("created_at", date(2026, 1, 1))
    return project


def _query_project_then_similar(project, similar_projects):
    project_query = MagicMock()
    project_query.filter.return_value.first.return_value = project

    similar_query = MagicMock()
    similar_query.filter.return_value.limit.return_value.all.return_value = similar_projects
    similar_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
        similar_projects
    )

    return [project_query, similar_query]


def test_schedule_generation_refuses_to_generate_when_no_historical_samples():
    db = MagicMock()
    db.query.side_effect = _query_project_then_similar(_project(), [])
    service = ScheduleGenerationService(db)

    result = service.generate_schedule(project_id=1)

    assert result["status"] == "unavailable"
    assert result["reason"] == "insufficient_historical_samples"
    assert result["sample_count"] == 0
    assert "tasks" not in result, "无历史样本时不能继续吐模板任务计划"
    assert "total_days" not in result, "无历史样本时不能继续吐默认 60 天工期"


def test_schedule_generation_uses_real_historical_duration_when_samples_exist():
    db = MagicMock()
    similar = [
        _project(id=2, planned_start_date=date(2026, 1, 1), planned_end_date=date(2026, 2, 10)),
        _project(id=3, planned_start_date=date(2026, 2, 1), planned_end_date=date(2026, 3, 23)),
        _project(id=4, planned_start_date=date(2026, 3, 1), planned_end_date=date(2026, 4, 30)),
    ]
    db.query.side_effect = _query_project_then_similar(_project(), similar)
    service = ScheduleGenerationService(db)

    result = service.generate_schedule(project_id=1)

    assert result["status"] == "success"
    assert result["historical_sample_count"] == 3
    assert result["history_confidence"] == "MEDIUM"
    assert result["data_source"] == "historical_projects"
    assert result["total_days"] > 0
    assert result["tasks"], "有历史样本时才允许生成计划"


def test_schedule_optimization_refuses_template_savings_when_no_similar_projects():
    db = MagicMock()
    db.query.side_effect = _query_project_then_similar(_project(), [])
    service = ScheduleOptimizationService(db)

    result = service.analyze_optimization_potential(project_id=1)

    assert result["status"] == "unavailable"
    assert result["reason"] == "insufficient_similar_projects"
    assert result["similar_projects_count"] == 0
    assert result["time_savings"]["total_savings_days"] == 0
    assert result["optimization_analysis"] == {}
    assert result["automation_suggestions"] == []


def test_schedule_optimization_reports_real_sample_count_when_available():
    db = MagicMock()
    similar = [_project(id=2), _project(id=3), _project(id=4)]
    db.query.side_effect = _query_project_then_similar(_project(), similar)
    service = ScheduleOptimizationService(db)

    result = service.analyze_optimization_potential(project_id=1)

    assert result["status"] == "success"
    assert result["similar_projects_count"] == 3
    assert result["time_savings"]["total_savings_days"] > 0
    assert result["overall_optimization_score"] > 0
