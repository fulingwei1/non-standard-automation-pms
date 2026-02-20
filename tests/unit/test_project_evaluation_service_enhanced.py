# -*- coding: utf-8 -*-
"""
项目评价服务增强测试
全面测试 ProjectEvaluationService 的所有核心方法和边界条件
"""

import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.models.enums import ProjectEvaluationLevelEnum
from app.models.project import Project
from app.models.project_evaluation import ProjectEvaluation, ProjectEvaluationDimension
from app.services.project_evaluation_service import ProjectEvaluationService


class TestProjectEvaluationService(unittest.TestCase):
    """项目评价服务测试类"""

    def setUp(self):
        """每个测试前的准备"""
        self.db = MagicMock()
        self.service = ProjectEvaluationService(self.db)

    def tearDown(self):
        """每个测试后的清理"""
        self.db.reset_mock()

    # ==================== get_dimension_weights 测试 ====================

    def test_get_dimension_weights_from_db(self):
        """测试从数据库获取维度权重"""
        # Mock 数据库返回的维度数据
        mock_dim1 = MagicMock()
        mock_dim1.dimension_type = 'NOVELTY'
        mock_dim1.default_weight = Decimal('15')
        
        mock_dim2 = MagicMock()
        mock_dim2.dimension_type = 'NEW_TECH'
        mock_dim2.default_weight = Decimal('20')
        
        mock_dim3 = MagicMock()
        mock_dim3.dimension_type = 'DIFFICULTY'
        mock_dim3.default_weight = Decimal('30')
        
        mock_dim4 = MagicMock()
        mock_dim4.dimension_type = 'WORKLOAD'
        mock_dim4.default_weight = Decimal('20')
        
        mock_dim5 = MagicMock()
        mock_dim5.dimension_type = 'AMOUNT'
        mock_dim5.default_weight = Decimal('15')
        
        self.db.query.return_value.filter.return_value.all.return_value = [
            mock_dim1, mock_dim2, mock_dim3, mock_dim4, mock_dim5
        ]
        
        weights = self.service.get_dimension_weights()
        
        self.assertEqual(weights['novelty'], Decimal('0.15'))
        self.assertEqual(weights['new_tech'], Decimal('0.20'))
        self.assertEqual(weights['difficulty'], Decimal('0.30'))
        self.assertEqual(weights['workload'], Decimal('0.20'))
        self.assertEqual(weights['amount'], Decimal('0.15'))

    def test_get_dimension_weights_empty_db(self):
        """测试数据库为空时返回默认权重"""
        self.db.query.return_value.filter.return_value.all.return_value = []
        
        weights = self.service.get_dimension_weights()
        
        self.assertEqual(weights, self.service.DEFAULT_WEIGHTS)

    def test_get_dimension_weights_normalization(self):
        """测试权重归一化"""
        # Mock 权重总和不为100的数据
        mock_dim1 = MagicMock()
        mock_dim1.dimension_type = 'NOVELTY'
        mock_dim1.default_weight = Decimal('10')
        
        mock_dim2 = MagicMock()
        mock_dim2.dimension_type = 'NEW_TECH'
        mock_dim2.default_weight = Decimal('20')
        
        self.db.query.return_value.filter.return_value.all.return_value = [
            mock_dim1, mock_dim2
        ]
        
        weights = self.service.get_dimension_weights()
        
        # 权重应该被归一化（10/30 = 0.333..., 20/30 = 0.666...）
        total = weights['novelty'] + weights['new_tech']
        self.assertAlmostEqual(float(total), 1.0, places=2)

    # ==================== get_level_thresholds 测试 ====================

    def test_get_level_thresholds_from_db(self):
        """测试从数据库获取等级阈值"""
        mock_config = MagicMock()
        mock_config.scoring_rules = {
            'S': 90,
            'A': 80,
            'B': 70,
            'C': 60,
            'D': 0
        }
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_config
        
        thresholds = self.service.get_level_thresholds()
        
        self.assertEqual(thresholds[ProjectEvaluationLevelEnum.S], Decimal('90'))
        self.assertEqual(thresholds[ProjectEvaluationLevelEnum.A], Decimal('80'))
        self.assertEqual(thresholds[ProjectEvaluationLevelEnum.B], Decimal('70'))
        self.assertEqual(thresholds[ProjectEvaluationLevelEnum.C], Decimal('60'))
        self.assertEqual(thresholds[ProjectEvaluationLevelEnum.D], Decimal('0'))

    def test_get_level_thresholds_no_config(self):
        """测试没有配置时返回默认阈值"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        thresholds = self.service.get_level_thresholds()
        
        self.assertEqual(thresholds, self.service.DEFAULT_LEVEL_THRESHOLDS)

    def test_get_level_thresholds_invalid_config(self):
        """测试配置格式错误时返回默认阈值"""
        mock_config = MagicMock()
        mock_config.scoring_rules = "invalid"
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_config
        
        thresholds = self.service.get_level_thresholds()
        
        self.assertEqual(thresholds, self.service.DEFAULT_LEVEL_THRESHOLDS)

    # ==================== calculate_total_score 测试 ====================

    def test_calculate_total_score_default_weights(self):
        """测试使用默认权重计算总分"""
        with patch.object(self.service, 'get_dimension_weights', return_value=self.service.DEFAULT_WEIGHTS):
            total = self.service.calculate_total_score(
                novelty_score=Decimal('8'),
                new_tech_score=Decimal('7'),
                difficulty_score=Decimal('6'),
                workload_score=Decimal('8'),
                amount_score=Decimal('9')
            )
            
            # 8*0.15 + 7*0.20 + 6*0.30 + 8*0.20 + 9*0.15 = 1.2 + 1.4 + 1.8 + 1.6 + 1.35 = 7.35
            self.assertEqual(total, Decimal('7.35'))

    def test_calculate_total_score_custom_weights(self):
        """测试使用自定义权重计算总分"""
        custom_weights = {
            'novelty': Decimal('0.2'),
            'new_tech': Decimal('0.2'),
            'difficulty': Decimal('0.2'),
            'workload': Decimal('0.2'),
            'amount': Decimal('0.2')
        }
        
        total = self.service.calculate_total_score(
            novelty_score=Decimal('5'),
            new_tech_score=Decimal('5'),
            difficulty_score=Decimal('5'),
            workload_score=Decimal('5'),
            amount_score=Decimal('5'),
            weights=custom_weights
        )
        
        # 5*0.2 + 5*0.2 + 5*0.2 + 5*0.2 + 5*0.2 = 5.0
        self.assertEqual(total, Decimal('5.0'))

    def test_calculate_total_score_zero_scores(self):
        """测试所有分数为0的情况"""
        total = self.service.calculate_total_score(
            novelty_score=Decimal('0'),
            new_tech_score=Decimal('0'),
            difficulty_score=Decimal('0'),
            workload_score=Decimal('0'),
            amount_score=Decimal('0')
        )
        
        self.assertEqual(total, Decimal('0'))

    def test_calculate_total_score_max_scores(self):
        """测试所有分数为10的情况"""
        total = self.service.calculate_total_score(
            novelty_score=Decimal('10'),
            new_tech_score=Decimal('10'),
            difficulty_score=Decimal('10'),
            workload_score=Decimal('10'),
            amount_score=Decimal('10'),
            weights=self.service.DEFAULT_WEIGHTS
        )
        
        # 10*0.15 + 10*0.20 + 10*0.30 + 10*0.20 + 10*0.15 = 10.0
        self.assertEqual(total, Decimal('10.0'))

    # ==================== determine_evaluation_level 测试 ====================

    def test_determine_evaluation_level_s(self):
        """测试S级评价"""
        with patch.object(self.service, 'get_level_thresholds', 
                         return_value=self.service.DEFAULT_LEVEL_THRESHOLDS):
            level = self.service.determine_evaluation_level(Decimal('95'))
            self.assertEqual(level, 'S')

    def test_determine_evaluation_level_a(self):
        """测试A级评价"""
        with patch.object(self.service, 'get_level_thresholds',
                         return_value=self.service.DEFAULT_LEVEL_THRESHOLDS):
            level = self.service.determine_evaluation_level(Decimal('85'))
            self.assertEqual(level, 'A')

    def test_determine_evaluation_level_b(self):
        """测试B级评价"""
        with patch.object(self.service, 'get_level_thresholds',
                         return_value=self.service.DEFAULT_LEVEL_THRESHOLDS):
            level = self.service.determine_evaluation_level(Decimal('75'))
            self.assertEqual(level, 'B')

    def test_determine_evaluation_level_c(self):
        """测试C级评价"""
        with patch.object(self.service, 'get_level_thresholds',
                         return_value=self.service.DEFAULT_LEVEL_THRESHOLDS):
            level = self.service.determine_evaluation_level(Decimal('65'))
            self.assertEqual(level, 'C')

    def test_determine_evaluation_level_d(self):
        """测试D级评价"""
        with patch.object(self.service, 'get_level_thresholds',
                         return_value=self.service.DEFAULT_LEVEL_THRESHOLDS):
            level = self.service.determine_evaluation_level(Decimal('50'))
            self.assertEqual(level, 'D')

    def test_determine_evaluation_level_boundary(self):
        """测试边界值"""
        with patch.object(self.service, 'get_level_thresholds',
                         return_value=self.service.DEFAULT_LEVEL_THRESHOLDS):
            # 正好等于阈值应该是对应等级
            level = self.service.determine_evaluation_level(Decimal('90'))
            self.assertEqual(level, 'S')

    # ==================== auto_calculate_novelty_score 测试 ====================

    def test_auto_calculate_novelty_score_no_similar_projects(self):
        """测试没有相似项目时的新旧得分"""
        mock_project = MagicMock()
        mock_project.id = 1
        
        self.db.query.return_value.filter.return_value.all.return_value = []
        
        score = self.service.auto_calculate_novelty_score(mock_project)
        
        self.assertEqual(score, Decimal('2.0'))

    def test_auto_calculate_novelty_score_many_completed(self):
        """测试有多个已完成相似项目时的得分"""
        mock_project = MagicMock()
        mock_project.id = 1
        
        # Mock 3个已完成的相似项目
        mock_similar1 = MagicMock()
        mock_similar1.stage = 'S9'
        mock_similar2 = MagicMock()
        mock_similar2.stage = 'S9'
        mock_similar3 = MagicMock()
        mock_similar3.stage = 'S9'
        
        self.db.query.return_value.filter.return_value.all.return_value = [
            mock_similar1, mock_similar2, mock_similar3
        ]
        
        score = self.service.auto_calculate_novelty_score(mock_project)
        
        self.assertEqual(score, Decimal('9.0'))

    def test_auto_calculate_novelty_score_few_completed(self):
        """测试有少量已完成相似项目时的得分"""
        mock_project = MagicMock()
        mock_project.id = 1
        
        # Mock 1个已完成的相似项目
        mock_similar1 = MagicMock()
        mock_similar1.stage = 'S9'
        mock_similar2 = MagicMock()
        mock_similar2.stage = 'S5'
        
        self.db.query.return_value.filter.return_value.all.return_value = [
            mock_similar1, mock_similar2
        ]
        
        score = self.service.auto_calculate_novelty_score(mock_project)
        
        self.assertEqual(score, Decimal('6.0'))

    def test_auto_calculate_novelty_score_none_completed(self):
        """测试有相似项目但未完成时的得分"""
        mock_project = MagicMock()
        mock_project.id = 1
        
        # Mock 相似项目但都未完成
        mock_similar1 = MagicMock()
        mock_similar1.stage = 'S5'
        mock_similar2 = MagicMock()
        mock_similar2.stage = 'S3'
        
        self.db.query.return_value.filter.return_value.all.return_value = [
            mock_similar1, mock_similar2
        ]
        
        score = self.service.auto_calculate_novelty_score(mock_project)
        
        self.assertEqual(score, Decimal('4.0'))

    # ==================== auto_calculate_amount_score 测试 ====================

    def test_auto_calculate_amount_score_very_large(self):
        """测试超大金额项目得分"""
        mock_project = MagicMock()
        mock_project.contract_amount = Decimal('6000000')
        
        score = self.service.auto_calculate_amount_score(mock_project)
        
        self.assertEqual(score, Decimal('2.0'))

    def test_auto_calculate_amount_score_large(self):
        """测试大金额项目得分"""
        mock_project = MagicMock()
        mock_project.contract_amount = Decimal('3000000')
        
        score = self.service.auto_calculate_amount_score(mock_project)
        
        self.assertEqual(score, Decimal('5.0'))

    def test_auto_calculate_amount_score_medium(self):
        """测试中等金额项目得分"""
        mock_project = MagicMock()
        mock_project.contract_amount = Decimal('1000000')
        
        score = self.service.auto_calculate_amount_score(mock_project)
        
        self.assertEqual(score, Decimal('7.5'))

    def test_auto_calculate_amount_score_small(self):
        """测试小金额项目得分"""
        mock_project = MagicMock()
        mock_project.contract_amount = Decimal('300000')
        
        score = self.service.auto_calculate_amount_score(mock_project)
        
        self.assertEqual(score, Decimal('9.5'))

    def test_auto_calculate_amount_score_zero(self):
        """测试金额为0的情况"""
        mock_project = MagicMock()
        mock_project.contract_amount = Decimal('0')
        
        score = self.service.auto_calculate_amount_score(mock_project)
        
        self.assertEqual(score, Decimal('9.5'))

    def test_auto_calculate_amount_score_none(self):
        """测试金额为None的情况"""
        mock_project = MagicMock()
        mock_project.contract_amount = None
        
        score = self.service.auto_calculate_amount_score(mock_project)
        
        self.assertEqual(score, Decimal('9.5'))

    # ==================== auto_calculate_workload_score 测试 ====================

    @patch('app.models.timesheet.Timesheet')
    def test_auto_calculate_workload_score_very_large(self, mock_timesheet_class):
        """测试超大工作量得分"""
        mock_project = MagicMock()
        mock_project.id = 1
        
        # Mock Timesheet.total_hours attribute
        mock_timesheet_class.total_hours = MagicMock()
        
        # Mock 查询返回 10000小时 (1250人天)
        self.db.query.return_value.filter.return_value.scalar.return_value = 10000
        
        score = self.service.auto_calculate_workload_score(mock_project)
        
        self.assertEqual(score, Decimal('2'))

    @patch('app.models.timesheet.Timesheet')
    def test_auto_calculate_workload_score_large(self, mock_timesheet_class):
        """测试大工作量得分"""
        mock_project = MagicMock()
        mock_project.id = 1
        
        # Mock Timesheet.total_hours attribute
        mock_timesheet_class.total_hours = MagicMock()
        
        # Mock 查询返回 5000小时 (625人天)
        self.db.query.return_value.filter.return_value.scalar.return_value = 5000
        
        score = self.service.auto_calculate_workload_score(mock_project)
        
        self.assertEqual(score, Decimal('5'))

    @patch('app.models.timesheet.Timesheet')
    def test_auto_calculate_workload_score_medium(self, mock_timesheet_class):
        """测试中等工作量得分"""
        mock_project = MagicMock()
        mock_project.id = 1
        
        # Mock Timesheet.total_hours attribute
        mock_timesheet_class.total_hours = MagicMock()
        
        # Mock 查询返回 2000小时 (250人天)
        self.db.query.return_value.filter.return_value.scalar.return_value = 2000
        
        score = self.service.auto_calculate_workload_score(mock_project)
        
        self.assertEqual(score, Decimal('7.5'))

    @patch('app.models.timesheet.Timesheet')
    def test_auto_calculate_workload_score_small(self, mock_timesheet_class):
        """测试小工作量得分"""
        mock_project = MagicMock()
        mock_project.id = 1
        
        # Mock Timesheet.total_hours attribute
        mock_timesheet_class.total_hours = MagicMock()
        
        # Mock 查询返回 800小时 (100人天)
        self.db.query.return_value.filter.return_value.scalar.return_value = 800
        
        score = self.service.auto_calculate_workload_score(mock_project)
        
        self.assertEqual(score, Decimal('9.5'))

    @patch('app.models.timesheet.Timesheet')
    def test_auto_calculate_workload_score_no_data(self, mock_timesheet_class):
        """测试没有工时数据时返回None"""
        mock_project = MagicMock()
        mock_project.id = 1
        
        # Mock Timesheet.total_hours attribute
        mock_timesheet_class.total_hours = MagicMock()
        
        # Mock 查询返回 0 或 None
        self.db.query.return_value.filter.return_value.scalar.return_value = 0
        
        score = self.service.auto_calculate_workload_score(mock_project)
        
        self.assertIsNone(score)

    # ==================== generate_evaluation_code 测试 ====================

    def test_generate_evaluation_code(self):
        """测试生成评价编号"""
        code = self.service.generate_evaluation_code()
        
        # 验证格式：PE + 14位数字时间戳
        self.assertTrue(code.startswith('PE'))
        self.assertEqual(len(code), 16)  # PE + 14 digits
        self.assertTrue(code[2:].isdigit())

    # ==================== create_evaluation 测试 ====================

    def test_create_evaluation_basic(self):
        """测试创建基本评价记录"""
        with patch.object(self.service, 'calculate_total_score', return_value=Decimal('8.5')), \
             patch.object(self.service, 'determine_evaluation_level', return_value='A'), \
             patch.object(self.service, 'get_dimension_weights', return_value=self.service.DEFAULT_WEIGHTS), \
             patch.object(self.service, 'generate_evaluation_code', return_value='PE20260221010530'):
            
            evaluation = self.service.create_evaluation(
                project_id=1,
                novelty_score=Decimal('8'),
                new_tech_score=Decimal('7'),
                difficulty_score=Decimal('9'),
                workload_score=Decimal('8'),
                amount_score=Decimal('9'),
                evaluator_id=100,
                evaluator_name='测试评价人'
            )
            
            self.assertEqual(evaluation.project_id, 1)
            self.assertEqual(evaluation.novelty_score, Decimal('8'))
            self.assertEqual(evaluation.total_score, Decimal('8.5'))
            self.assertEqual(evaluation.evaluation_level, 'A')
            self.assertEqual(evaluation.evaluator_id, 100)
            self.assertEqual(evaluation.status, 'DRAFT')

    def test_create_evaluation_with_details(self):
        """测试创建带详情的评价记录"""
        with patch.object(self.service, 'calculate_total_score', return_value=Decimal('8.5')), \
             patch.object(self.service, 'determine_evaluation_level', return_value='A'), \
             patch.object(self.service, 'get_dimension_weights', return_value=self.service.DEFAULT_WEIGHTS), \
             patch.object(self.service, 'generate_evaluation_code', return_value='PE20260221010530'):
            
            evaluation_detail = {'reason': '优秀项目'}
            evaluation_note = '测试备注'
            
            evaluation = self.service.create_evaluation(
                project_id=1,
                novelty_score=Decimal('8'),
                new_tech_score=Decimal('7'),
                difficulty_score=Decimal('9'),
                workload_score=Decimal('8'),
                amount_score=Decimal('9'),
                evaluator_id=100,
                evaluator_name='测试评价人',
                evaluation_detail=evaluation_detail,
                evaluation_note=evaluation_note
            )
            
            self.assertEqual(evaluation.evaluation_detail, evaluation_detail)
            self.assertEqual(evaluation.evaluation_note, evaluation_note)

    # ==================== get_latest_evaluation 测试 ====================

    def test_get_latest_evaluation_exists(self):
        """测试获取最新评价记录"""
        mock_evaluation = MagicMock()
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_evaluation
        
        result = self.service.get_latest_evaluation(project_id=1)
        
        self.assertEqual(result, mock_evaluation)

    def test_get_latest_evaluation_not_exists(self):
        """测试项目没有评价记录"""
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        
        result = self.service.get_latest_evaluation(project_id=1)
        
        self.assertIsNone(result)

    # ==================== get_bonus_coefficient 测试 ====================

    def test_get_bonus_coefficient_s_level(self):
        """测试S级项目奖金系数"""
        mock_evaluation = MagicMock()
        mock_evaluation.evaluation_level = ProjectEvaluationLevelEnum.S
        
        with patch.object(self.service, 'get_latest_evaluation', return_value=mock_evaluation):
            mock_project = MagicMock()
            mock_project.id = 1
            
            coefficient = self.service.get_bonus_coefficient(mock_project)
            
            self.assertEqual(coefficient, Decimal('1.5'))

    def test_get_bonus_coefficient_a_level(self):
        """测试A级项目奖金系数"""
        mock_evaluation = MagicMock()
        mock_evaluation.evaluation_level = ProjectEvaluationLevelEnum.A
        
        with patch.object(self.service, 'get_latest_evaluation', return_value=mock_evaluation):
            mock_project = MagicMock()
            coefficient = self.service.get_bonus_coefficient(mock_project)
            self.assertEqual(coefficient, Decimal('1.3'))

    def test_get_bonus_coefficient_no_evaluation(self):
        """测试没有评价时的默认系数"""
        with patch.object(self.service, 'get_latest_evaluation', return_value=None):
            mock_project = MagicMock()
            coefficient = self.service.get_bonus_coefficient(mock_project)
            self.assertEqual(coefficient, Decimal('1.0'))

    # ==================== get_difficulty_bonus_coefficient 测试 ====================

    def test_get_difficulty_bonus_coefficient_extreme(self):
        """测试极高难度系数"""
        mock_evaluation = MagicMock()
        mock_evaluation.difficulty_score = Decimal('2')
        
        with patch.object(self.service, 'get_latest_evaluation', return_value=mock_evaluation):
            mock_project = MagicMock()
            coefficient = self.service.get_difficulty_bonus_coefficient(mock_project)
            self.assertEqual(coefficient, Decimal('1.5'))

    def test_get_difficulty_bonus_coefficient_high(self):
        """测试高难度系数"""
        mock_evaluation = MagicMock()
        mock_evaluation.difficulty_score = Decimal('5')
        
        with patch.object(self.service, 'get_latest_evaluation', return_value=mock_evaluation):
            mock_project = MagicMock()
            coefficient = self.service.get_difficulty_bonus_coefficient(mock_project)
            self.assertEqual(coefficient, Decimal('1.3'))

    def test_get_difficulty_bonus_coefficient_no_evaluation(self):
        """测试没有评价时的默认难度系数"""
        with patch.object(self.service, 'get_latest_evaluation', return_value=None):
            mock_project = MagicMock()
            coefficient = self.service.get_difficulty_bonus_coefficient(mock_project)
            self.assertEqual(coefficient, Decimal('1.0'))

    # ==================== get_new_tech_bonus_coefficient 测试 ====================

    def test_get_new_tech_bonus_coefficient_high(self):
        """测试大量新技术系数"""
        mock_evaluation = MagicMock()
        mock_evaluation.new_tech_score = Decimal('2')
        
        with patch.object(self.service, 'get_latest_evaluation', return_value=mock_evaluation):
            mock_project = MagicMock()
            coefficient = self.service.get_new_tech_bonus_coefficient(mock_project)
            self.assertEqual(coefficient, Decimal('1.4'))

    def test_get_new_tech_bonus_coefficient_medium(self):
        """测试部分新技术系数"""
        mock_evaluation = MagicMock()
        mock_evaluation.new_tech_score = Decimal('5')
        
        with patch.object(self.service, 'get_latest_evaluation', return_value=mock_evaluation):
            mock_project = MagicMock()
            coefficient = self.service.get_new_tech_bonus_coefficient(mock_project)
            self.assertEqual(coefficient, Decimal('1.2'))

    def test_get_new_tech_bonus_coefficient_low(self):
        """测试少量新技术系数"""
        mock_evaluation = MagicMock()
        mock_evaluation.new_tech_score = Decimal('8')
        
        with patch.object(self.service, 'get_latest_evaluation', return_value=mock_evaluation):
            mock_project = MagicMock()
            coefficient = self.service.get_new_tech_bonus_coefficient(mock_project)
            self.assertEqual(coefficient, Decimal('1.0'))

    def test_get_new_tech_bonus_coefficient_no_evaluation(self):
        """测试没有评价时的默认新技术系数"""
        with patch.object(self.service, 'get_latest_evaluation', return_value=None):
            mock_project = MagicMock()
            coefficient = self.service.get_new_tech_bonus_coefficient(mock_project)
            self.assertEqual(coefficient, Decimal('1.0'))


if __name__ == '__main__':
    unittest.main()
