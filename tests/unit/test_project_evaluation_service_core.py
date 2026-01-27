# -*- coding: utf-8 -*-
"""
项目评价服务单元测试

测试 ProjectEvaluationService 类的核心方法
"""

from decimal import Decimal

import pytest
from unittest.mock import Mock, MagicMock

from app.models.enums import ProjectEvaluationLevelEnum
from app.models.project import Project
from app.models.project_evaluation import ProjectEvaluation, ProjectEvaluationDimension
from app.services.project_evaluation_service import ProjectEvaluationService


class TestProjectEvaluationService:
    """项目评价服务测试类"""

    @pytest.fixture
    def db_session(self):
        """模拟数据库会话"""
        return MagicMock()

    @pytest.fixture
    def service(self, db_session):
        """创建服务实例"""
        return ProjectEvaluationService(db_session)

    @pytest.fixture
    def mock_project(self):
        """创建模拟项目对象"""
        project = Mock(spec=Project)
        project.id = 1
        project.project_code = "PJ-TEST-001"
        project.project_name = "测试项目"
        project.project_type = "ICT"
        project.product_category = "TEST"
        project.industry = "制造"
        project.contract_amount = Decimal("1000000")
        project.is_archived = False
        return project

    @pytest.fixture
    def mock_evaluator(self):
        """创建模拟评价人"""
        evaluator = Mock()
        evaluator.id = 1
        evaluator.real_name = "测试评价人"
        evaluator.username = "evaluator"
        return evaluator

    def test_get_dimension_weights_from_db(self, service, db_session):
        """从数据库获取权重配置"""
        dim1 = Mock(spec=ProjectEvaluationDimension)
        dim1.dimension_type = "novelty"
        dim1.default_weight = Decimal("15")

        dim2 = Mock(spec=ProjectEvaluationDimension)
        dim2.dimension_type = "new_tech"
        dim2.default_weight = Decimal("20")

        db_session.query.return_value.filter.return_value.all.return_value = [
        dim1,
        dim2,
        ]

        weights = service.get_dimension_weights()

        assert weights["novelty"] == Decimal("0.42857142857142855")
        assert weights["new_tech"] == Decimal("0.571428571428571415")

    def test_get_dimension_weights_default(self, service, db_session):
        """使用默认权重配置"""
        db_session.query.return_value.filter.return_value.all.return_value = []

        weights = service.get_dimension_weights()

        assert weights["novelty"] == Decimal("0.15")
        assert weights["new_tech"] == Decimal("0.20")
        assert weights["difficulty"] == Decimal("0.30")
        assert weights["workload"] == Decimal("0.20")
        assert weights["amount"] == Decimal("0.15")

    def test_calculate_total_score(self, service, db_session):
        """计算综合得分"""
        db_session.query.return_value.filter.return_value.all.return_value = []

        total = service.calculate_total_score(
        novelty_score=Decimal("80"),
        new_tech_score=Decimal("90"),
        difficulty_score=Decimal("85"),
        workload_score=Decimal("75"),
        amount_score=Decimal("70"),
        )

        assert float(total) == pytest.approx(80.25, rel=1e-3)

    def test_determine_evaluation_level_s(self, service, db_session):
        """S级评价"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        level = service.determine_evaluation_level(Decimal("92"))
        assert level == ProjectEvaluationLevelEnum.S.value

    def test_determine_evaluation_level_d(self, service, db_session):
        """D级评价"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        level = service.determine_evaluation_level(Decimal("50"))
        assert level == ProjectEvaluationLevelEnum.D.value

    def test_auto_calculate_novelty_score_no_similar(
        self, service, db_session, mock_project
    ):
        """没有相似项目"""
        db_session.query.return_value.filter.return_value.all.return_value = []

        score = service.auto_calculate_novelty_score(mock_project)
        assert score == Decimal("2.0")

    def test_auto_calculate_amount_score_medium(self, service, mock_project):
        """中等项目金额得分"""
        mock_project.contract_amount = Decimal("1000000")

        score = service.auto_calculate_amount_score(mock_project)
        assert score == Decimal("7.5")

    def test_auto_calculate_workload_score_no_timesheet(
        self, service, db_session, mock_project
    ):
        """没有工时数据"""
        db_session.query.return_value.filter.return_value.scalar.return_value = None

        score = service.auto_calculate_workload_score(mock_project)
        assert score is None

    def test_get_bonus_coefficient_level_s(self, service, db_session):
        """S级项目奖金系数"""
        evaluation = Mock(spec=ProjectEvaluation)
        evaluation.evaluation_level = ProjectEvaluationLevelEnum.S.value

        db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = evaluation

        coefficient = service.get_bonus_coefficient(Mock(id=1))
        assert coefficient == Decimal("1.5")

    def test_get_bonus_coefficient_no_evaluation(self, service, db_session):
        """没有评价记录"""
        db_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        coefficient = service.get_bonus_coefficient(Mock(id=1))
        assert coefficient == Decimal("1.0")
