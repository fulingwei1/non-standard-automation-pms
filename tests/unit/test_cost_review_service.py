# -*- coding: utf-8 -*-
"""
Tests for cost_review_service
"""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import Mock
from sqlalchemy.orm import Session

from app.models.budget import ProjectBudget
from app.models.project import Project, ProjectCost
from app.models.project_review import ProjectReview


class TestGenerateCostReviewReport:
    """Test suite for generate_cost_review_report method."""

    @pytest.fixture
    def db_session(self):
        """Create mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def mock_project(self):
        """Create mock project."""
        project = Mock(spec=Project)
        project.id = 1
        project.project_name = "测试项目"
        project.stage = "S9"
        project.status = "ST30"
        project.planned_start_date = date(2025, 1, 1)
        project.planned_end_date = date(2025, 12, 31)
        project.actual_start_date = date(2025, 1, 15)
        project.actual_end_date = date(2026, 1, 10)
        project.budget_amount = Decimal("1000000")
        project.actual_cost = Decimal("950000")
        return project

    @pytest.fixture
    def mock_budget(self):
        """Create mock budget."""
        budget = Mock(spec=ProjectBudget)
        budget.total_amount = Decimal("1000000")
        budget.version = 2
        return budget

    def test_generate_cost_review_project_not_found(self, db_session):
        """Test review generation when project doesn't exist."""
        from app.services.cost_review_service import CostReviewService

        db_session.query = Mock(
            return_value=Mock(
                filter=Mock(return_value=Mock(first=Mock(return_value=None)))
            )
        )

        with pytest.raises(ValueError, match="项目不存在"):
            CostReviewService.generate_cost_review_report(
                db_session, project_id=999, reviewer_id=1
            )

    def test_generate_cost_review_project_not_completed(self, db_session, mock_project):
        """Test review generation when project is not completed."""
        from app.services.cost_review_service import CostReviewService

        mock_project.stage = "S5"
        mock_project.status = "ST10"

        def mock_query_side_effect(model):
            if model == Project:
                return Mock(
                    filter=Mock(
                        return_value=Mock(first=Mock(return_value=mock_project))
                    )
                )
            else:
                return Mock()

        db_session.query = Mock(side_effect=mock_query_side_effect)

        with pytest.raises(ValueError, match="项目未结项"):
            CostReviewService.generate_cost_review_report(
                db_session, project_id=1, reviewer_id=1
            )

    def test_generate_cost_review_existing_review(self, db_session, mock_project):
        """Test review generation when review already exists."""
        from app.services.cost_review_service import CostReviewService

        mock_existing_review = Mock(spec=ProjectReview)
        mock_existing_review.id = 100

        def mock_query_side_effect(model):
            if model == Project:
                return Mock(
                    filter=Mock(
                        return_value=Mock(first=Mock(return_value=mock_project))
                    )
                )
            elif model == ProjectReview:
                return Mock(
                    filter=Mock(
                        return_value=Mock(first=Mock(return_value=mock_existing_review))
                    )
                )
            else:
                return Mock()

        db_session.query = Mock(side_effect=mock_query_side_effect)

        with pytest.raises(ValueError, match="已存在结项复盘报告"):
            CostReviewService.generate_cost_review_report(
                db_session, project_id=1, reviewer_id=1
            )

    def test_generate_cost_review_success(self, db_session, mock_project, mock_budget):
        """Test successful cost review report generation."""
        from app.services.cost_review_service import CostReviewService

        def mock_query_side_effect(model):
            if model == Project:
                return Mock(
                    filter=Mock(
                        return_value=Mock(first=Mock(return_value=mock_project))
                    )
                )
            elif model == ProjectBudget:
                return Mock(
                    filter=Mock(return_value=Mock(first=Mock(return_value=mock_budget)))
                )
            elif model == ProjectReview:
                return Mock(
                    filter=Mock(return_value=Mock(first=Mock(return_value=None)))
                )
            elif model == ProjectCost:
                return Mock(filter=Mock(return_value=Mock(all=Mock(return_value=[]))))
            else:
                return Mock()

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = CostReviewService.generate_cost_review_report(
            db_session, project_id=1, reviewer_id=1, review_date=date(2026, 1, 20)
        )

        assert result is not None
        assert result.project_id == 1
        assert result.reviewer_id == 1
        assert result.review_type == "POST_MORTEM"


class TestCostReviewService:
    """Test suite for CostReviewService class utilities."""

    def test_generate_review_no(self):
        """Test _generate_review_no method."""
        from app.services.cost_review_service import CostReviewService

        db = Mock(spec=Session)
        mock_review = Mock()
        mock_review.id = 50

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.scalar = Mock(return_value=mock_review.id)

        db.query = Mock(return_value=mock_query)

        result = CostReviewService._generate_review_no(db, "POST_MORTEM")

        assert result is not None

    def test_generate_review_no_with_no_existing(self):
        """Test _generate_review_no when no existing review."""
        from app.services.cost_review_service import CostReviewService

        db = Mock(spec=Session)

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.scalar = Mock(return_value=None)

        db.query = Mock(return_value=mock_query)

        result = CostReviewService._generate_review_no(db, "POST_MORTEM")

        assert result is not None
