# -*- coding: utf-8 -*-
"""
Tests for template_recommendation_service service
Covers: app/services/template_recommendation_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 171 lines
Batch: 2
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.template_recommendation_service import TemplateRecommendationService
from app.models.project import ProjectTemplate
from tests.conftest import _ensure_login_user


@pytest.fixture
def test_template1(db_session: Session):
    """创建测试模板1"""
    template = ProjectTemplate(
        template_code="TEMPLATE-001",
        template_name="测试模板1",
        description="测试模板描述1",
        project_type="AUTOMATION",
        product_category="ICT",
        industry="ELECTRONICS",
        is_active=True,
        usage_count=10
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


@pytest.fixture
def test_template2(db_session: Session):
    """创建测试模板2"""
    template = ProjectTemplate(
        template_code="TEMPLATE-002",
        template_name="测试模板2",
        description="测试模板描述2",
        project_type="AUTOMATION",
        product_category="FCT",
        industry="AUTOMOTIVE",
        is_active=True,
        usage_count=5
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


@pytest.fixture
def test_template3(db_session: Session):
    """创建测试模板3 - 高使用频率"""
    template = ProjectTemplate(
        template_code="TEMPLATE-003",
        template_name="测试模板3",
        description="测试模板描述3",
        project_type="MANUAL",
        product_category="ASSEMBLY",
        industry="MANUFACTURING",
        is_active=True,
        usage_count=100
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


@pytest.fixture
def test_template_inactive(db_session: Session):
    """创建非活跃模板"""
    template = ProjectTemplate(
        template_code="TEMPLATE-INACTIVE",
        template_name="非活跃模板",
        description="非活跃模板描述",
        project_type="AUTOMATION",
        product_category="ICT",
        industry="ELECTRONICS",
        is_active=False,
        usage_count=1
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


class TestTemplateRecommendationService:
    """Test suite for TemplateRecommendationService."""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = TemplateRecommendationService(db_session)
        assert service is not None
        assert service.db == db_session

    def test_recommend_templates_by_project_type(self, db_session, test_template1, test_template2):
        """测试根据项目类型推荐"""
        service = TemplateRecommendationService(db_session)
        
        result = service.recommend_templates(
        project_type="AUTOMATION",
        limit=5
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(r['template_id'] in [test_template1.id, test_template2.id] for r in result)
        assert all(r['match_type'] == 'project_type' for r in result)

    def test_recommend_templates_by_product_category(self, db_session, test_template1):
        """测试根据产品类别推荐"""
        service = TemplateRecommendationService(db_session)
        
        result = service.recommend_templates(
        product_category="ICT",
        limit=5
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert any(r['template_id'] == test_template1.id for r in result)
        assert any(r['match_type'] == 'product_category' for r in result)

    def test_recommend_templates_by_industry(self, db_session, test_template1):
        """测试根据行业推荐"""
        service = TemplateRecommendationService(db_session)
        
        result = service.recommend_templates(
        industry="ELECTRONICS",
        limit=5
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert any(r['template_id'] == test_template1.id for r in result)
        assert any(r['match_type'] == 'industry' for r in result)

    def test_recommend_templates_multiple_criteria(self, db_session, test_template1):
        """测试多条件推荐"""
        service = TemplateRecommendationService(db_session)
        
        result = service.recommend_templates(
        project_type="AUTOMATION",
        product_category="ICT",
        industry="ELECTRONICS",
        limit=5
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        # 应该包含完全匹配的模板
        assert any(r['template_id'] == test_template1.id for r in result)

    def test_recommend_templates_no_match(self, db_session, test_template1, test_template2):
        """测试无匹配推荐"""
        service = TemplateRecommendationService(db_session)
        
        result = service.recommend_templates(
        project_type="NONEXISTENT",
        product_category="NONEXISTENT",
        industry="NONEXISTENT",
        limit=5
        )
        
        assert isinstance(result, list)
        # 应该返回使用频率高的模板
        assert len(result) > 0
        assert all(r['match_type'] == 'usage_frequency' for r in result)

    def test_recommend_templates_limit(self, db_session, test_template1, test_template2, test_template3):
        """测试限制返回数量"""
        service = TemplateRecommendationService(db_session)
        
        result = service.recommend_templates(
        project_type="AUTOMATION",
        limit=2
        )
        
        assert isinstance(result, list)
        assert len(result) <= 2

    def test_recommend_templates_sorted_by_score(self, db_session, test_template1, test_template2, test_template3):
        """测试按评分排序"""
        service = TemplateRecommendationService(db_session)
        
        result = service.recommend_templates(
        project_type="AUTOMATION",
        limit=5
        )
        
        assert isinstance(result, list)
        if len(result) > 1:
            # 应该按评分降序排列
        scores = [r['score'] for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_recommend_templates_excludes_inactive(self, db_session, test_template1, test_template_inactive):
        """测试排除非活跃模板"""
        service = TemplateRecommendationService(db_session)
        
        result = service.recommend_templates(
        project_type="AUTOMATION",
        limit=5
        )
        
        assert isinstance(result, list)
        # 不应该包含非活跃模板
        assert all(r['template_id'] != test_template_inactive.id for r in result)

    def test_calculate_score_project_type_match(self, db_session, test_template1):
        """测试计算评分 - 项目类型匹配"""
        service = TemplateRecommendationService(db_session)
        
        score = service._calculate_score(
        template=test_template1,
        project_type="AUTOMATION",
        product_category=None,
        industry=None
        )
        
        assert score >= 40.0  # 基础分10 + 项目类型30

    def test_calculate_score_product_category_match(self, db_session, test_template1):
        """测试计算评分 - 产品类别匹配"""
        service = TemplateRecommendationService(db_session)
        
        score = service._calculate_score(
        template=test_template1,
        project_type=None,
        product_category="ICT",
        industry=None
        )
        
        assert score >= 35.0  # 基础分10 + 产品类别25

    def test_calculate_score_industry_match(self, db_session, test_template1):
        """测试计算评分 - 行业匹配"""
        service = TemplateRecommendationService(db_session)
        
        score = service._calculate_score(
        template=test_template1,
        project_type=None,
        product_category=None,
        industry="ELECTRONICS"
        )
        
        assert score >= 30.0  # 基础分10 + 行业20

    def test_calculate_score_all_matches(self, db_session, test_template1):
        """测试计算评分 - 全部匹配"""
        service = TemplateRecommendationService(db_session)
        
        score = service._calculate_score(
        template=test_template1,
        project_type="AUTOMATION",
        product_category="ICT",
        industry="ELECTRONICS"
        )
        
        assert score >= 70.0  # 基础分10 + 项目类型30 + 产品类别25 + 行业20

    def test_calculate_score_usage_count(self, db_session, test_template3):
        """测试计算评分 - 使用频率加分"""
        service = TemplateRecommendationService(db_session)
        
        score = service._calculate_score(
        template=test_template3,
        project_type=None,
        product_category=None,
        industry=None
        )
        
        # 基础分10 + 使用频率加分（最高15）
        assert score >= 10.0
        assert score <= 25.0

    def test_calculate_score_no_matches(self, db_session, test_template1):
        """测试计算评分 - 无匹配"""
        service = TemplateRecommendationService(db_session)
        
        score = service._calculate_score(
        template=test_template1,
        project_type="NONEXISTENT",
        product_category="NONEXISTENT",
        industry="NONEXISTENT"
        )
        
        # 只有基础分10 + 使用频率加分
        assert score >= 10.0

    def test_get_recommendation_reasons_project_type(self, db_session, test_template1):
        """测试获取推荐理由 - 项目类型"""
        service = TemplateRecommendationService(db_session)
        
        reasons = service._get_recommendation_reasons(
        template=test_template1,
        project_type="AUTOMATION",
        product_category=None,
        industry=None
        )
        
        assert isinstance(reasons, list)
        assert any("项目类型匹配" in r for r in reasons)

    def test_get_recommendation_reasons_product_category(self, db_session, test_template1):
        """测试获取推荐理由 - 产品类别"""
        service = TemplateRecommendationService(db_session)
        
        reasons = service._get_recommendation_reasons(
        template=test_template1,
        project_type=None,
        product_category="ICT",
        industry=None
        )
        
        assert isinstance(reasons, list)
        assert any("产品类别匹配" in r for r in reasons)

    def test_get_recommendation_reasons_industry(self, db_session, test_template1):
        """测试获取推荐理由 - 行业"""
        service = TemplateRecommendationService(db_session)
        
        reasons = service._get_recommendation_reasons(
        template=test_template1,
        project_type=None,
        product_category=None,
        industry="ELECTRONICS"
        )
        
        assert isinstance(reasons, list)
        assert any("行业匹配" in r for r in reasons)

    def test_get_recommendation_reasons_usage_count(self, db_session, test_template1):
        """测试获取推荐理由 - 使用频率"""
        service = TemplateRecommendationService(db_session)
        
        reasons = service._get_recommendation_reasons(
        template=test_template1,
        project_type=None,
        product_category=None,
        industry=None
        )
        
        assert isinstance(reasons, list)
        assert any("使用频率高" in r for r in reasons)

    def test_get_recommendation_reasons_no_matches(self, db_session):
        """测试获取推荐理由 - 无匹配"""
        template = ProjectTemplate(
        template_code="TEMPLATE-GENERIC",
        template_name="通用模板",
        description="通用模板描述",
        project_type=None,
        product_category=None,
        industry=None,
        is_active=True,
        usage_count=0
        )
        db_session.add(template)
        db_session.commit()
        db_session.refresh(template)
        
        service = TemplateRecommendationService(db_session)
        
        reasons = service._get_recommendation_reasons(
        template=template,
        project_type=None,
        product_category=None,
        industry=None
        )
        
        assert isinstance(reasons, list)
        assert any("通用模板推荐" in r for r in reasons)

    def test_recommend_templates_empty_database(self, db_session):
        """测试空数据库"""
        service = TemplateRecommendationService(db_session)
        
        result = service.recommend_templates(
        project_type="AUTOMATION",
        limit=5
        )
        
        assert isinstance(result, list)
        assert len(result) == 0

    def test_recommend_templates_no_criteria(self, db_session, test_template1, test_template2, test_template3):
        """测试无筛选条件"""
        service = TemplateRecommendationService(db_session)
        
        result = service.recommend_templates(
        limit=5
        )
        
        assert isinstance(result, list)
        # 应该返回使用频率高的模板
        assert len(result) > 0
        assert all(r['match_type'] == 'usage_frequency' for r in result)
