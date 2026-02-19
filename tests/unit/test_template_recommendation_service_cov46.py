# -*- coding: utf-8 -*-
"""第四十六批 - 模板推荐服务单元测试"""
import pytest

pytest.importorskip("app.services.template_recommendation_service",
                    reason="依赖不满足，跳过")

from unittest.mock import MagicMock
from app.services.template_recommendation_service import TemplateRecommendationService


def _make_template(
    tid=1,
    project_type="NPD",
    product_category="电子",
    industry="制造",
    usage_count=10,
):
    t = MagicMock()
    t.id = tid
    t.template_code = f"T{tid:03d}"
    t.template_name = f"模板{tid}"
    t.description = f"描述{tid}"
    t.project_type = project_type
    t.product_category = product_category
    t.industry = industry
    t.usage_count = usage_count
    return t


class TestCalculateScore:
    def test_base_score_is_ten(self):
        db = MagicMock()
        svc = TemplateRecommendationService(db)
        t = _make_template(usage_count=0)
        score = svc._calculate_score(t, None, None, None)
        assert score == 10.0

    def test_project_type_match_adds_30(self):
        db = MagicMock()
        svc = TemplateRecommendationService(db)
        t = _make_template(project_type="NPD")
        score = svc._calculate_score(t, "NPD", None, None)
        assert score >= 40.0

    def test_all_match_gives_high_score(self):
        db = MagicMock()
        svc = TemplateRecommendationService(db)
        t = _make_template(project_type="NPD", product_category="电子", industry="制造", usage_count=0)
        score = svc._calculate_score(t, "NPD", "电子", "制造")
        assert score == pytest.approx(85.0)

    def test_usage_count_zero_adds_nothing(self):
        db = MagicMock()
        svc = TemplateRecommendationService(db)
        t = _make_template(usage_count=0)
        score = svc._calculate_score(t, None, None, None)
        assert score == 10.0


class TestGetRecommendationReasons:
    def test_reasons_match_project_type(self):
        db = MagicMock()
        svc = TemplateRecommendationService(db)
        t = _make_template(project_type="NPD")
        reasons = svc._get_recommendation_reasons(t, "NPD", None, None)
        assert any("NPD" in r for r in reasons)

    def test_returns_generic_when_no_match(self):
        db = MagicMock()
        svc = TemplateRecommendationService(db)
        t = _make_template(project_type="NPD", usage_count=0)
        reasons = svc._get_recommendation_reasons(t, None, None, None)
        assert "通用模板推荐" in reasons


class TestRecommendTemplates:
    def test_returns_list_limited_by_limit(self):
        db = MagicMock()
        templates = [_make_template(tid=i, project_type="NPD") for i in range(1, 8)]
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = templates

        svc = TemplateRecommendationService(db)
        results = svc.recommend_templates(project_type="NPD", limit=3)
        assert len(results) <= 3

    def test_returns_empty_when_no_matches_and_no_popular(self):
        db = MagicMock()
        # query chain for project_type match returns empty, fallback popular also empty
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        svc = TemplateRecommendationService(db)
        results = svc.recommend_templates()
        assert results == []
