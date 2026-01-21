# -*- coding: utf-8 -*-
"""
Tests for cost_review_service service
Covers: app/services/cost_review_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 87 lines
Batch: 3
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.cost_review_service import CostReviewService
from app.models.project import Project
from app.models.user import User
from app.models.project_review import ProjectReview


@pytest.fixture
def test_project_completed(db_session: Session):
    """创建已结项的项目"""
    project = Project(
        project_code="PJ001",
        project_name="测试项目",
        stage="S9",
        status="ST30",
        budget_amount=Decimal("100000.00"),
        actual_cost=Decimal("95000.00"),
        planned_start_date=date.today() - timedelta(days=180),
        planned_end_date=date.today() - timedelta(days=30),
        actual_start_date=date.today() - timedelta(days=180),
        actual_end_date=date.today() - timedelta(days=30)
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_reviewer(db_session: Session):
    """创建复盘负责人"""
    user = User(
        username="reviewer",
        real_name="复盘负责人",
        email="reviewer@example.com",
        hashed_password="hashed",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestCostReviewService:
    """Test suite for CostReviewService."""

    def test_generate_cost_review_report_project_not_found(self, db_session):
        """测试生成成本复盘报告 - 项目不存在"""
        with pytest.raises(ValueError, match="项目不存在"):
            CostReviewService.generate_cost_review_report(
                db_session,
                project_id=99999,
                reviewer_id=1
            )

    def test_generate_cost_review_report_not_completed(self, db_session):
        """测试生成成本复盘报告 - 项目未结项"""
        project = Project(
            project_code="PJ002",
            project_name="未结项项目",
            stage="S5",
            status="ST10"
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        
        with pytest.raises(ValueError, match="项目未结项"):
            CostReviewService.generate_cost_review_report(
                db_session,
                project_id=project.id,
                reviewer_id=1
            )

    def test_generate_cost_review_report_already_exists(self, db_session, test_project_completed, test_reviewer):
        """测试生成成本复盘报告 - 已存在报告"""
        # 创建已有报告
        existing_review = ProjectReview(
            review_no="REV-240120-001",
            project_id=test_project_completed.id,
            review_type="POST_MORTEM",
            status="DRAFT"
        )
        db_session.add(existing_review)
        db_session.commit()
        
        with pytest.raises(ValueError, match="已存在结项复盘报告"):
            CostReviewService.generate_cost_review_report(
                db_session,
                project_id=test_project_completed.id,
                reviewer_id=test_reviewer.id
            )

    def test_generate_cost_review_report_success(self, db_session, test_project_completed, test_reviewer):
        """测试生成成本复盘报告 - 成功场景"""
        result = CostReviewService.generate_cost_review_report(
            db_session,
            project_id=test_project_completed.id,
            reviewer_id=test_reviewer.id
        )
        
        assert result is not None
        assert isinstance(result, ProjectReview)
        assert result.project_id == test_project_completed.id
        assert result.review_type == "POST_MORTEM"
        assert result.reviewer_id == test_reviewer.id
        assert result.review_no is not None
        assert result.status == "DRAFT"

    def test_generate_cost_review_report_with_custom_date(self, db_session, test_project_completed, test_reviewer):
        """测试生成成本复盘报告 - 自定义日期"""
        review_date = date.today() - timedelta(days=5)
        
        result = CostReviewService.generate_cost_review_report(
            db_session,
            project_id=test_project_completed.id,
            reviewer_id=test_reviewer.id,
            review_date=review_date
        )
        
        assert result is not None
        assert result.review_date == review_date

    def test_generate_review_no_first(self, db_session):
        """测试生成复盘编号 - 第一个"""
        result = CostReviewService._generate_review_no(db_session)
        
        assert result is not None
        assert result.startswith("REV-")
        assert len(result.split("-")) == 3

    def test_generate_review_no_sequential(self, db_session, test_project_completed, test_reviewer):
        """测试生成复盘编号 - 连续编号"""
        # 创建第一个报告
        review1 = CostReviewService.generate_cost_review_report(
            db_session,
            project_id=test_project_completed.id,
            reviewer_id=test_reviewer.id
        )
        
        # 创建第二个项目
        project2 = Project(
            project_code="PJ003",
            project_name="测试项目3",
            stage="S9",
            status="ST30"
        )
        db_session.add(project2)
        db_session.commit()
        db_session.refresh(project2)
        
        # 创建第二个报告
        review2 = CostReviewService.generate_cost_review_report(
            db_session,
            project_id=project2.id,
            reviewer_id=test_reviewer.id
        )
        
        assert review2.review_no != review1.review_no

    def test_generate_cost_summary_over_budget(self):
        """测试生成成本总结 - 超预算"""
        budget = Decimal("100000.00")
        actual = Decimal("115000.00")
        variance = actual - budget
        
        result = CostReviewService._generate_cost_summary(
            budget, actual, variance,
            {}, {}, 0
        )
        
        assert "超出预算" in result
        assert "严重超支" in result

    def test_generate_cost_summary_under_budget(self):
        """测试生成成本总结 - 低于预算"""
        budget = Decimal("100000.00")
        actual = Decimal("90000.00")
        variance = actual - budget
        
        result = CostReviewService._generate_cost_summary(
            budget, actual, variance,
            {}, {}, 0
        )
        
        assert "低于预算" in result or "成本控制良好" in result

    def test_generate_cost_summary_with_ecn(self):
        """测试生成成本总结 - 有ECN变更"""
        budget = Decimal("100000.00")
        actual = Decimal("105000.00")
        variance = actual - budget
        
        result = CostReviewService._generate_cost_summary(
            budget, actual, variance,
            {}, {}, 5
        )
        
        assert "工程变更" in result
        assert "5" in result
