# -*- coding: utf-8 -*-
"""
项目评价服务单元测试补充 (F组) - MagicMock方式

覆盖 ProjectEvaluationService 的关键方法:
- get_dimension_weights
- get_level_thresholds
- calculate_total_score
- determine_evaluation_level
- auto_calculate_novelty_score
- auto_calculate_amount_score
- auto_calculate_workload_score
- create_evaluation
- get_latest_evaluation
- get_bonus_coefficient
- get_difficulty_bonus_coefficient
- get_new_tech_bonus_coefficient
"""
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.models.enums import ProjectEvaluationLevelEnum
from app.services.project_evaluation_service import ProjectEvaluationService


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return ProjectEvaluationService(db)


# ============================================================
# get_dimension_weights 测试
# ============================================================

class TestGetDimensionWeights:

    def test_returns_defaults_when_no_config(self, service, db):
        """测试无配置时返回默认权重"""
        db.query.return_value.filter.return_value.all.return_value = []
        weights = service.get_dimension_weights()
        assert 'novelty' in weights
        assert 'new_tech' in weights
        assert 'difficulty' in weights
        assert 'workload' in weights
        assert 'amount' in weights

    def test_returns_db_weights(self, service, db):
        """测试从数据库获取权重"""
        dim = MagicMock(dimension_type='NOVELTY', default_weight=Decimal('20'))
        db.query.return_value.filter.return_value.all.return_value = [dim]
        weights = service.get_dimension_weights()
        assert 'novelty' in weights

    def test_normalizes_weights(self, service, db):
        """测试权重归一化"""
        dim1 = MagicMock(dimension_type='NOVELTY', default_weight=Decimal('30'))
        dim2 = MagicMock(dimension_type='NEW_TECH', default_weight=Decimal('30'))
        dim3 = MagicMock(dimension_type='DIFFICULTY', default_weight=Decimal('40'))
        db.query.return_value.filter.return_value.all.return_value = [dim1, dim2, dim3]

        weights = service.get_dimension_weights()
        # The total weight should still be valid
        total = sum(weights.values())
        assert abs(total - Decimal('1')) < Decimal('0.01')


# ============================================================
# get_level_thresholds 测试
# ============================================================

class TestGetLevelThresholds:

    def test_returns_defaults_when_no_config(self, service, db):
        """测试无配置时返回默认阈值"""
        db.query.return_value.filter.return_value.first.return_value = None
        thresholds = service.get_level_thresholds()
        assert ProjectEvaluationLevelEnum.S in thresholds
        assert ProjectEvaluationLevelEnum.A in thresholds
        assert ProjectEvaluationLevelEnum.D in thresholds

    def test_returns_db_thresholds(self, service, db):
        """测试从数据库获取阈值配置"""
        config = MagicMock(scoring_rules={'S': 90, 'A': 80, 'B': 70, 'C': 60, 'D': 0})
        db.query.return_value.filter.return_value.first.return_value = config
        thresholds = service.get_level_thresholds()
        assert ProjectEvaluationLevelEnum.S in thresholds
        assert thresholds[ProjectEvaluationLevelEnum.S] == Decimal('90')


# ============================================================
# calculate_total_score 测试
# ============================================================

class TestCalculateTotalScore:

    def test_with_default_weights(self, service, db):
        """测试使用默认权重计算总分"""
        db.query.return_value.filter.return_value.all.return_value = []
        score = service.calculate_total_score(
            novelty_score=Decimal('8'),
            new_tech_score=Decimal('7'),
            difficulty_score=Decimal('6'),
            workload_score=Decimal('9'),
            amount_score=Decimal('5'),
        )
        assert score > 0
        # 8*0.15 + 7*0.20 + 6*0.30 + 9*0.20 + 5*0.15 = 1.2+1.4+1.8+1.8+0.75 = 6.95
        assert abs(score - Decimal('6.95')) < Decimal('0.01')

    def test_with_custom_weights(self, service):
        """测试使用自定义权重"""
        weights = {
            'novelty': Decimal('0.2'),
            'new_tech': Decimal('0.2'),
            'difficulty': Decimal('0.2'),
            'workload': Decimal('0.2'),
            'amount': Decimal('0.2'),
        }
        score = service.calculate_total_score(
            novelty_score=Decimal('10'),
            new_tech_score=Decimal('10'),
            difficulty_score=Decimal('10'),
            workload_score=Decimal('10'),
            amount_score=Decimal('10'),
            weights=weights
        )
        assert score == Decimal('10')

    def test_min_score(self, service):
        """测试全零分"""
        weights = {k: Decimal('0.2') for k in ['novelty', 'new_tech', 'difficulty', 'workload', 'amount']}
        score = service.calculate_total_score(
            Decimal('0'), Decimal('0'), Decimal('0'), Decimal('0'), Decimal('0'),
            weights=weights
        )
        assert score == Decimal('0')


# ============================================================
# determine_evaluation_level 测试
# ============================================================

class TestDetermineEvaluationLevel:

    def test_s_level(self, service, db):
        """测试S级评定"""
        db.query.return_value.filter.return_value.first.return_value = None
        level = service.determine_evaluation_level(Decimal('95'))
        assert level == ProjectEvaluationLevelEnum.S.value

    def test_a_level(self, service, db):
        """测试A级评定"""
        db.query.return_value.filter.return_value.first.return_value = None
        level = service.determine_evaluation_level(Decimal('85'))
        assert level == ProjectEvaluationLevelEnum.A.value

    def test_b_level(self, service, db):
        """测试B级评定"""
        db.query.return_value.filter.return_value.first.return_value = None
        level = service.determine_evaluation_level(Decimal('75'))
        assert level == ProjectEvaluationLevelEnum.B.value

    def test_c_level(self, service, db):
        """测试C级评定"""
        db.query.return_value.filter.return_value.first.return_value = None
        level = service.determine_evaluation_level(Decimal('65'))
        assert level == ProjectEvaluationLevelEnum.C.value

    def test_d_level(self, service, db):
        """测试D级评定"""
        db.query.return_value.filter.return_value.first.return_value = None
        level = service.determine_evaluation_level(Decimal('55'))
        assert level == ProjectEvaluationLevelEnum.D.value


# ============================================================
# auto_calculate_novelty_score 测试
# ============================================================

class TestAutoCalculateNoveltyScore:

    def test_no_similar_projects(self, service, db):
        """测试无相似项目（全新项目）"""
        project = MagicMock(id=1, project_type='TYPE_A', product_category='CAT_B', industry='汽车')
        db.query.return_value.filter.return_value.all.return_value = []
        score = service.auto_calculate_novelty_score(project)
        assert score == Decimal('2.0')

    def test_three_or_more_completed(self, service, db):
        """测试3次以上完成项目（标准项目）"""
        project = MagicMock(id=1, project_type='TYPE_A', product_category='CAT_B', industry='汽车')
        similar = [MagicMock(stage='S9') for _ in range(4)]  # 4 completed
        db.query.return_value.filter.return_value.all.return_value = similar
        score = service.auto_calculate_novelty_score(project)
        assert score == Decimal('9.0')

    def test_one_to_two_completed(self, service, db):
        """测试1-2次完成项目（类似项目）"""
        project = MagicMock(id=1, project_type='TYPE_A', product_category='CAT_B', industry='汽车')
        similar = [MagicMock(stage='S9'), MagicMock(stage='S5')]  # 1 completed
        db.query.return_value.filter.return_value.all.return_value = similar
        score = service.auto_calculate_novelty_score(project)
        assert score == Decimal('6.0')

    def test_similar_but_no_completed(self, service, db):
        """测试有类似项目但无完成（有经验）"""
        project = MagicMock(id=1, project_type='TYPE_A', product_category='CAT_B', industry='汽车')
        similar = [MagicMock(stage='S3')]  # not completed
        db.query.return_value.filter.return_value.all.return_value = similar
        score = service.auto_calculate_novelty_score(project)
        assert score == Decimal('4.0')


# ============================================================
# auto_calculate_amount_score 测试
# ============================================================

class TestAutoCalculateAmountScore:

    def test_large_project(self, service):
        """测试超大项目（>500万）"""
        project = MagicMock(contract_amount=Decimal('6000000'))
        score = service.auto_calculate_amount_score(project)
        assert score == Decimal('2.0')

    def test_big_project(self, service):
        """测试大项目（200-500万）"""
        project = MagicMock(contract_amount=Decimal('3000000'))
        score = service.auto_calculate_amount_score(project)
        assert score == Decimal('5.0')

    def test_medium_project(self, service):
        """测试中等项目（50-200万）"""
        project = MagicMock(contract_amount=Decimal('1000000'))
        score = service.auto_calculate_amount_score(project)
        assert score == Decimal('7.5')

    def test_small_project(self, service):
        """测试小项目（<50万）"""
        project = MagicMock(contract_amount=Decimal('200000'))
        score = service.auto_calculate_amount_score(project)
        assert score == Decimal('9.5')

    def test_no_amount(self, service):
        """测试无合同金额（默认0，属于小项目）"""
        project = MagicMock(contract_amount=None)
        score = service.auto_calculate_amount_score(project)
        assert score == Decimal('9.5')  # 0 < 500000


# ============================================================
# create_evaluation 测试
# ============================================================

class TestCreateEvaluation:

    def test_create_evaluation_returns_object(self, service, db):
        """测试创建评价记录"""
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.first.return_value = None

        with patch('app.services.project_evaluation_service.ProjectEvaluation') as MockEval:
            evaluation_obj = MagicMock()
            MockEval.return_value = evaluation_obj
            result = service.create_evaluation(
                project_id=1,
                novelty_score=Decimal('8'),
                new_tech_score=Decimal('7'),
                difficulty_score=Decimal('6'),
                workload_score=Decimal('9'),
                amount_score=Decimal('5'),
                evaluator_id=1,
                evaluator_name='张三',
            )
        assert result is evaluation_obj
        assert MockEval.called

    def test_evaluation_code_generated(self, service, db):
        """测试评价编号生成"""
        code = service.generate_evaluation_code()
        assert code.startswith("PE")
        assert len(code) > 2


# ============================================================
# get_latest_evaluation 测试
# ============================================================

class TestGetLatestEvaluation:

    def test_returns_none_when_no_evaluation(self, service, db):
        """测试无评价记录时返回None"""
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = service.get_latest_evaluation(1)
        assert result is None

    def test_returns_latest_evaluation(self, service, db):
        """测试返回最新评价"""
        evaluation = MagicMock(status='CONFIRMED')
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = evaluation
        result = service.get_latest_evaluation(1)
        assert result == evaluation


# ============================================================
# get_bonus_coefficient 测试
# ============================================================

class TestGetBonusCoefficient:

    def test_no_evaluation_returns_default(self, service, db):
        """测试无评价时返回默认系数1.0"""
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        project = MagicMock(id=1)
        result = service.get_bonus_coefficient(project)
        assert result == Decimal('1.0')

    def test_s_level_coefficient(self, service, db):
        """测试S级项目系数1.5"""
        evaluation = MagicMock(evaluation_level=ProjectEvaluationLevelEnum.S)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = evaluation
        project = MagicMock(id=1)
        result = service.get_bonus_coefficient(project)
        assert result == Decimal('1.5')

    def test_a_level_coefficient(self, service, db):
        """测试A级项目系数1.3"""
        evaluation = MagicMock(evaluation_level=ProjectEvaluationLevelEnum.A)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = evaluation
        project = MagicMock(id=1)
        result = service.get_bonus_coefficient(project)
        assert result == Decimal('1.3')

    def test_d_level_coefficient(self, service, db):
        """测试D级项目系数0.9"""
        evaluation = MagicMock(evaluation_level=ProjectEvaluationLevelEnum.D)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = evaluation
        project = MagicMock(id=1)
        result = service.get_bonus_coefficient(project)
        assert result == Decimal('0.9')


# ============================================================
# get_difficulty_bonus_coefficient 测试
# ============================================================

class TestGetDifficultyBonusCoefficient:

    def test_no_evaluation(self, service, db):
        """测试无评价时返回1.0"""
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        project = MagicMock(id=1)
        result = service.get_difficulty_bonus_coefficient(project)
        assert result == Decimal('1.0')

    def test_extreme_difficulty(self, service, db):
        """测试极高难度（<=3分）系数1.5"""
        evaluation = MagicMock(difficulty_score=Decimal('2'))
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = evaluation
        project = MagicMock(id=1)
        result = service.get_difficulty_bonus_coefficient(project)
        assert result == Decimal('1.5')

    def test_low_difficulty(self, service, db):
        """测试低难度（>8分）系数1.0"""
        evaluation = MagicMock(difficulty_score=Decimal('9'))
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = evaluation
        project = MagicMock(id=1)
        result = service.get_difficulty_bonus_coefficient(project)
        assert result == Decimal('1.0')


# ============================================================
# get_new_tech_bonus_coefficient 测试
# ============================================================

class TestGetNewTechBonusCoefficient:

    def test_no_evaluation(self, service, db):
        """测试无评价时返回1.0"""
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        project = MagicMock(id=1)
        result = service.get_new_tech_bonus_coefficient(project)
        assert result == Decimal('1.0')

    def test_lots_of_new_tech(self, service, db):
        """测试大量新技术（<=3分）系数1.4"""
        evaluation = MagicMock(new_tech_score=Decimal('2'))
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = evaluation
        project = MagicMock(id=1)
        result = service.get_new_tech_bonus_coefficient(project)
        assert result == Decimal('1.4')

    def test_some_new_tech(self, service, db):
        """测试部分新技术（4-6分）系数1.2"""
        evaluation = MagicMock(new_tech_score=Decimal('5'))
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = evaluation
        project = MagicMock(id=1)
        result = service.get_new_tech_bonus_coefficient(project)
        assert result == Decimal('1.2')

    def test_no_new_tech(self, service, db):
        """测试无新技术（>6分）系数1.0"""
        evaluation = MagicMock(new_tech_score=Decimal('8'))
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = evaluation
        project = MagicMock(id=1)
        result = service.get_new_tech_bonus_coefficient(project)
        assert result == Decimal('1.0')
