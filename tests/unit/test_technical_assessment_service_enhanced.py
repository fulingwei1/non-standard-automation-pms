# -*- coding: utf-8 -*-
"""
技术评估服务增强单元测试

测试覆盖：
- 评分计算逻辑
- 相似案例匹配
- 评估结果生成
- 一票否决检查
- 边界条件和异常处理
"""

import json
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.models.enums import (
    AssessmentDecisionEnum,
    AssessmentSourceTypeEnum,
    AssessmentStatusEnum,
)
from app.models.sales import FailureCase, Lead, Opportunity, ScoringRule, TechnicalAssessment
from app.services.technical_assessment_service import TechnicalAssessmentService


class TestTechnicalAssessmentService(unittest.TestCase):
    """技术评估服务测试类"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = TechnicalAssessmentService(db=self.db)
        
        # 准备基础测试数据
        self.requirement_data = {
            'industry': '汽车',
            'productTypes': ['视觉检测', '机械手'],
            'targetTakt': 30,
            'budgetStatus': '已批准',
            'tech_maturity': '成熟',
            'process_difficulty': '中等',
            'precision_requirement': '高',
            'sample_support': '充足',
            'budget_status': '已批准',
            'price_sensitivity': '中',
            'gross_margin_safety': '安全',
            'payment_terms': '标准',
            'resource_occupancy': '低',
            'has_similar_case': True,
            'delivery_feasibility': '可行',
            'delivery_months': 6,
            'change_risk': '低',
            'customer_nature': '大型企业',
            'customer_potential': '高',
            'relationship_depth': '深',
            'contact_level': '决策层',
            'requirement_maturity': 4,
            'has_sow': True
        }
        
        # 准备评分规则配置
        self.rules_config = {
            'evaluation_criteria': {
                'tech_maturity': {
                    'field': 'tech_maturity',
                    'max_points': 10,
                    'options': [
                        {'value': '成熟', 'points': 10},
                        {'value': '中等', 'points': 6},
                        {'value': '不成熟', 'points': 2}
                    ]
                },
                'process_difficulty': {
                    'field': 'process_difficulty',
                    'max_points': 10,
                    'options': [
                        {'value': '简单', 'points': 10},
                        {'value': '中等', 'points': 6},
                        {'value': '困难', 'points': 2}
                    ]
                },
                'precision_requirement': {
                    'field': 'precision_requirement',
                    'max_points': 10,
                    'options': [
                        {'value': '低', 'points': 10},
                        {'value': '中', 'points': 6},
                        {'value': '高', 'points': 2}
                    ]
                },
                'sample_support': {
                    'field': 'sample_support',
                    'max_points': 10,
                    'options': [
                        {'value': '充足', 'points': 10},
                        {'value': '一般', 'points': 6},
                        {'value': '缺乏', 'points': 2}
                    ]
                },
                'budget_status': {
                    'field': 'budget_status',
                    'max_points': 10,
                    'options': [
                        {'value': '已批准', 'points': 10},
                        {'value': '待批准', 'points': 6},
                        {'value': '未申请', 'points': 2}
                    ]
                },
                'price_sensitivity': {
                    'field': 'price_sensitivity',
                    'max_points': 10,
                    'options': [
                        {'value': '低', 'points': 10},
                        {'value': '中', 'points': 6},
                        {'value': '高', 'points': 2}
                    ]
                },
                'gross_margin_safety': {
                    'field': 'gross_margin_safety',
                    'max_points': 10,
                    'options': [
                        {'value': '安全', 'points': 10},
                        {'value': '一般', 'points': 6},
                        {'value': '风险', 'points': 2}
                    ]
                },
                'payment_terms': {
                    'field': 'payment_terms',
                    'max_points': 10,
                    'options': [
                        {'value': '标准', 'points': 10},
                        {'value': '一般', 'points': 6},
                        {'value': '苛刻', 'points': 2}
                    ]
                },
                'resource_occupancy': {
                    'field': 'resource_occupancy',
                    'max_points': 10,
                    'options': [
                        {'value': '低', 'points': 10},
                        {'value': '中', 'points': 6},
                        {'value': '高', 'points': 2}
                    ]
                },
                'has_similar_case': {
                    'field': 'has_similar_case',
                    'max_points': 10,
                    'options': [
                        {'value': True, 'points': 10},
                        {'value': False, 'points': 0}
                    ]
                },
                'delivery_feasibility': {
                    'field': 'delivery_feasibility',
                    'max_points': 10,
                    'options': [
                        {'value': '可行', 'points': 10},
                        {'value': '一般', 'points': 6},
                        {'value': '困难', 'points': 2}
                    ]
                },
                'delivery_months': {
                    'field': 'delivery_months',
                    'max_points': 10,
                    'options': [
                        {'value': 6, 'points': 10},
                        {'value': 12, 'points': 6},
                        {'value': 18, 'points': 2}
                    ]
                },
                'change_risk': {
                    'field': 'change_risk',
                    'max_points': 10,
                    'options': [
                        {'value': '低', 'points': 10},
                        {'value': '中', 'points': 6},
                        {'value': '高', 'points': 2}
                    ]
                },
                'customer_nature': {
                    'field': 'customer_nature',
                    'max_points': 10,
                    'options': [
                        {'value': '大型企业', 'points': 10},
                        {'value': '中型企业', 'points': 6},
                        {'value': '小型企业', 'points': 2}
                    ]
                },
                'customer_potential': {
                    'field': 'customer_potential',
                    'max_points': 10,
                    'options': [
                        {'value': '高', 'points': 10},
                        {'value': '中', 'points': 6},
                        {'value': '低', 'points': 2}
                    ]
                },
                'relationship_depth': {
                    'field': 'relationship_depth',
                    'max_points': 10,
                    'options': [
                        {'value': '深', 'points': 10},
                        {'value': '中', 'points': 6},
                        {'value': '浅', 'points': 2}
                    ]
                },
                'contact_level': {
                    'field': 'contact_level',
                    'max_points': 10,
                    'options': [
                        {'value': '决策层', 'points': 10},
                        {'value': '管理层', 'points': 6},
                        {'value': '执行层', 'points': 2}
                    ]
                }
            },
            'veto_rules': [
                {
                    'name': '无预算否决',
                    'condition': {'field': 'budget_status', 'operator': '==', 'value': '无预算'},
                    'reason': '客户未申请预算，项目无法启动'
                },
                {
                    'name': '技术不可行否决',
                    'condition': {'field': 'tech_feasibility', 'operator': '==', 'value': '不可行'},
                    'reason': '技术不可行，无法交付'
                }
            ],
            'scales': {
                'decision_thresholds': [
                    {'min_score': 80, 'decision': '推荐立项'},
                    {'min_score': 60, 'decision': '有条件立项'},
                    {'min_score': 40, 'decision': '暂缓'},
                    {'min_score': 0, 'decision': '不建议立项'}
                ],
                'score_levels': {
                    'HIGH': '>=80',
                    'MEDIUM': '60-79',
                    'LOW': '<60'
                }
            }
        }

    # ========== 测试 _get_active_scoring_rule() ==========
    
    def test_get_active_scoring_rule_success(self):
        """测试成功获取启用的评分规则"""
        mock_rule = MagicMock(spec=ScoringRule)
        mock_rule.id = 1
        mock_rule.is_active = True
        
        query_mock = MagicMock()
        query_mock.filter.return_value.order_by.return_value.first.return_value = mock_rule
        self.db.query.return_value = query_mock
        
        result = self.service._get_active_scoring_rule()
        
        self.assertEqual(result, mock_rule)
        self.db.query.assert_called_once_with(ScoringRule)

    def test_get_active_scoring_rule_no_active_rule(self):
        """测试无启用的评分规则"""
        query_mock = MagicMock()
        query_mock.filter.return_value.order_by.return_value.first.return_value = None
        self.db.query.return_value = query_mock
        
        result = self.service._get_active_scoring_rule()
        
        self.assertIsNone(result)

    # ========== 测试 _calculate_scores() ==========
    
    def test_calculate_scores_all_dimensions(self):
        """测试计算所有五个维度的分数"""
        dimension_scores, total_score = self.service._calculate_scores(
            self.requirement_data, 
            self.rules_config
        )
        
        # 验证返回的维度
        self.assertIn('technology', dimension_scores)
        self.assertIn('business', dimension_scores)
        self.assertIn('resource', dimension_scores)
        self.assertIn('delivery', dimension_scores)
        self.assertIn('customer', dimension_scores)
        
        # 验证总分是所有维度分数之和
        expected_total = sum(dimension_scores.values())
        self.assertEqual(total_score, expected_total)
        
        # 验证每个维度分数在合理范围内 (0-20)
        for dimension, score in dimension_scores.items():
            self.assertGreaterEqual(score, 0, f"{dimension} score should be >= 0")
            self.assertLessEqual(score, 20, f"{dimension} score should be <= 20")

    def test_calculate_scores_empty_requirement_data(self):
        """测试空需求数据的分数计算"""
        dimension_scores, total_score = self.service._calculate_scores({}, self.rules_config)
        
        # 所有维度分数应为0
        for dimension, score in dimension_scores.items():
            self.assertEqual(score, 0, f"{dimension} should be 0 for empty data")
        
        self.assertEqual(total_score, 0)

    def test_calculate_scores_partial_data(self):
        """测试部分需求数据的分数计算"""
        partial_data = {
            'tech_maturity': '成熟',
            'budget_status': '已批准'
        }
        
        dimension_scores, total_score = self.service._calculate_scores(
            partial_data, 
            self.rules_config
        )
        
        # 技术和商务维度应有分数，其他为0
        self.assertGreater(dimension_scores['technology'], 0)
        self.assertGreater(dimension_scores['business'], 0)

    # ========== 测试 _score_dimension() ==========
    
    def test_score_dimension_full_score(self):
        """测试单个维度满分计算"""
        tech_criteria = ['tech_maturity', 'process_difficulty', 'precision_requirement', 'sample_support']
        score = self.service._score_dimension(
            self.requirement_data,
            self.rules_config['evaluation_criteria'],
            tech_criteria
        )
        
        # 应该得到较高分数
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 20)

    def test_score_dimension_missing_criteria(self):
        """测试缺少评分标准的维度"""
        score = self.service._score_dimension(
            self.requirement_data,
            self.rules_config['evaluation_criteria'],
            ['non_existent_key']
        )
        
        self.assertEqual(score, 0)

    def test_score_dimension_no_matching_options(self):
        """测试没有匹配选项的维度"""
        data = {'tech_maturity': 'unknown_value'}
        score = self.service._score_dimension(
            data,
            self.rules_config['evaluation_criteria'],
            ['tech_maturity']
        )
        
        self.assertEqual(score, 0)

    def test_score_dimension_normalization(self):
        """测试维度分数归一化到20分制"""
        # 单个标准，满分10分，应归一化为20分
        criteria = {
            'test_field': {
                'field': 'test_field',
                'max_points': 10,
                'options': [{'value': 'max', 'points': 10}]
            }
        }
        data = {'test_field': 'max'}
        
        score = self.service._score_dimension(data, criteria, ['test_field'])
        
        self.assertEqual(score, 20)

    # ========== 测试 _match_value() ==========
    
    def test_match_value_exact_mode(self):
        """测试精确匹配模式"""
        criterion = {'match_mode': 'exact'}
        option = {'value': 'test_value'}
        
        result = self.service._match_value('test_value', option, criterion)
        self.assertTrue(result)
        
        result = self.service._match_value('other_value', option, criterion)
        self.assertFalse(result)

    def test_match_value_contains_mode(self):
        """测试包含关键词匹配模式"""
        criterion = {'match_mode': 'contains'}
        option = {'keywords': ['关键词1', '关键词2']}
        
        result = self.service._match_value('这是包含关键词1的文本', option, criterion)
        self.assertTrue(result)
        
        result = self.service._match_value('这是不包含的文本', option, criterion)
        self.assertFalse(result)

    def test_match_value_default_exact_mode(self):
        """测试默认使用精确匹配模式"""
        criterion = {}  # 无match_mode，应默认为exact
        option = {'value': 'test'}
        
        result = self.service._match_value('test', option, criterion)
        self.assertTrue(result)

    # ========== 测试 _check_veto_rules() ==========
    
    def test_check_veto_rules_no_trigger(self):
        """测试一票否决未触发"""
        veto_triggered, veto_rules = self.service._check_veto_rules(
            self.requirement_data, 
            self.rules_config
        )
        
        self.assertFalse(veto_triggered)
        self.assertEqual(len(veto_rules), 0)

    def test_check_veto_rules_triggered(self):
        """测试一票否决被触发"""
        data = {'budget_status': '无预算'}
        
        veto_triggered, veto_rules = self.service._check_veto_rules(
            data, 
            self.rules_config
        )
        
        self.assertTrue(veto_triggered)
        self.assertEqual(len(veto_rules), 1)
        self.assertEqual(veto_rules[0]['rule_name'], '无预算否决')

    def test_check_veto_rules_multiple_triggers(self):
        """测试多个一票否决同时触发"""
        data = {
            'budget_status': '无预算',
            'tech_feasibility': '不可行'
        }
        
        veto_triggered, veto_rules = self.service._check_veto_rules(
            data, 
            self.rules_config
        )
        
        self.assertTrue(veto_triggered)
        self.assertEqual(len(veto_rules), 2)

    def test_check_veto_rules_operator_not_equal(self):
        """测试一票否决规则的!=操作符"""
        rules = {
            'veto_rules': [{
                'name': '测试规则',
                'condition': {'field': 'status', 'operator': '!=', 'value': '正常'},
                'reason': '状态异常'
            }]
        }
        
        veto_triggered, veto_rules = self.service._check_veto_rules(
            {'status': '异常'}, 
            rules
        )
        
        self.assertTrue(veto_triggered)

    def test_check_veto_rules_operator_in(self):
        """测试一票否决规则的in操作符"""
        rules = {
            'veto_rules': [{
                'name': '测试规则',
                'condition': {'field': 'status', 'operator': 'in', 'value': ['异常', '错误']},
                'reason': '状态在黑名单中'
            }]
        }
        
        veto_triggered, veto_rules = self.service._check_veto_rules(
            {'status': '异常'}, 
            rules
        )
        
        self.assertTrue(veto_triggered)

    def test_check_veto_rules_missing_field(self):
        """测试一票否决规则字段缺失"""
        veto_triggered, veto_rules = self.service._check_veto_rules(
            {'other_field': 'value'}, 
            self.rules_config
        )
        
        self.assertFalse(veto_triggered)
        self.assertEqual(len(veto_rules), 0)

    # ========== 测试 _match_similar_cases() ==========
    
    def test_match_similar_cases_with_matches(self):
        """测试匹配到相似案例"""
        mock_case = MagicMock(spec=FailureCase)
        mock_case.case_code = 'CASE001'
        mock_case.project_name = '测试项目'
        mock_case.industry = '汽车'
        mock_case.product_types = '["视觉检测"]'
        mock_case.takt_time_s = 28
        mock_case.budget_status = '已批准'
        mock_case.customer_project_status = '立项'
        mock_case.spec_status = '完成'
        mock_case.core_failure_reason = '技术难度超预期'
        mock_case.early_warning_signals = '["需求频繁变更"]'
        mock_case.lesson_learned = '需加强前期调研'
        
        query_mock = MagicMock()
        query_mock.filter.return_value.limit.return_value.all.return_value = [mock_case]
        self.db.query.return_value = query_mock
        
        similar_cases = self.service._match_similar_cases(self.requirement_data)
        
        self.assertIsInstance(similar_cases, list)
        self.assertGreater(len(similar_cases), 0)
        self.assertEqual(similar_cases[0]['case_code'], 'CASE001')

    def test_match_similar_cases_no_matches(self):
        """测试没有匹配的相似案例"""
        query_mock = MagicMock()
        query_mock.filter.return_value.limit.return_value.all.return_value = []
        self.db.query.return_value = query_mock
        
        similar_cases = self.service._match_similar_cases(self.requirement_data)
        
        self.assertEqual(len(similar_cases), 0)

    def test_match_similar_cases_low_similarity(self):
        """测试低相似度案例被过滤"""
        mock_case = MagicMock(spec=FailureCase)
        mock_case.industry = '不同行业'
        mock_case.product_types = None
        mock_case.takt_time_s = None
        mock_case.budget_status = None
        
        query_mock = MagicMock()
        query_mock.filter.return_value.limit.return_value.all.return_value = [mock_case]
        self.db.query.return_value = query_mock
        
        similar_cases = self.service._match_similar_cases(self.requirement_data)
        
        # 相似度低于0.3，应被过滤
        self.assertEqual(len(similar_cases), 0)

    # ========== 测试 _calculate_similarity() ==========
    
    def test_calculate_similarity_perfect_match(self):
        """测试完全匹配的相似度"""
        mock_case = MagicMock(spec=FailureCase)
        mock_case.industry = '汽车'
        mock_case.product_types = '["视觉检测", "机械手"]'
        mock_case.takt_time_s = 30
        mock_case.budget_status = '已批准'
        mock_case.customer_project_status = '立项'
        mock_case.spec_status = '完成'
        
        similarity = self.service._calculate_similarity(self.requirement_data, mock_case)
        
        # 完全匹配应该有很高的相似度
        self.assertGreater(similarity, 0.5)

    def test_calculate_similarity_no_match(self):
        """测试完全不匹配的相似度"""
        mock_case = MagicMock(spec=FailureCase)
        mock_case.industry = '不同行业'
        mock_case.product_types = None
        mock_case.takt_time_s = None
        mock_case.budget_status = None
        mock_case.customer_project_status = None
        mock_case.spec_status = None
        
        similarity = self.service._calculate_similarity(self.requirement_data, mock_case)
        
        self.assertEqual(similarity, 0.0)

    def test_calculate_similarity_takt_within_range(self):
        """测试节拍在±20%范围内的相似度"""
        mock_case = MagicMock(spec=FailureCase)
        mock_case.industry = None
        mock_case.product_types = None
        mock_case.takt_time_s = 32  # 30 * 1.067, 在20%范围内
        mock_case.budget_status = None
        mock_case.customer_project_status = None
        mock_case.spec_status = None
        
        similarity = self.service._calculate_similarity(self.requirement_data, mock_case)
        
        # 应该有节拍匹配的分数
        self.assertGreater(similarity, 0)

    # ========== 测试 _generate_decision() ==========
    
    def test_generate_decision_recommend(self):
        """测试推荐立项决策"""
        decision = self.service._generate_decision(85, self.rules_config)
        
        self.assertEqual(decision, AssessmentDecisionEnum.RECOMMEND.value)

    def test_generate_decision_conditional(self):
        """测试有条件立项决策"""
        decision = self.service._generate_decision(65, self.rules_config)
        
        self.assertEqual(decision, AssessmentDecisionEnum.CONDITIONAL.value)

    def test_generate_decision_defer(self):
        """测试暂缓决策"""
        decision = self.service._generate_decision(45, self.rules_config)
        
        self.assertEqual(decision, AssessmentDecisionEnum.DEFER.value)

    def test_generate_decision_not_recommend(self):
        """测试不建议立项决策"""
        decision = self.service._generate_decision(25, self.rules_config)
        
        self.assertEqual(decision, AssessmentDecisionEnum.NOT_RECOMMEND.value)

    def test_generate_decision_boundary_score(self):
        """测试边界分数的决策"""
        # 测试刚好达到阈值
        decision = self.service._generate_decision(80, self.rules_config)
        self.assertEqual(decision, AssessmentDecisionEnum.RECOMMEND.value)
        
        decision = self.service._generate_decision(60, self.rules_config)
        self.assertEqual(decision, AssessmentDecisionEnum.CONDITIONAL.value)

    # ========== 测试 _generate_risks() ==========
    
    def test_generate_risks_low_dimension_scores(self):
        """测试低维度分数生成风险"""
        dimension_scores = {
            'technology': 8,  # 低于10，高风险
            'business': 12,   # 10-15，中等风险
            'resource': 16,   # 高于15，无风险
            'delivery': 5,    # 低于10，高风险
            'customer': 18
        }
        
        risks = self.service._generate_risks(
            self.requirement_data, 
            dimension_scores, 
            self.rules_config
        )
        
        # 应该生成多个风险
        self.assertGreater(len(risks), 0)
        
        # 验证风险等级
        high_risks = [r for r in risks if r['level'] == 'HIGH']
        medium_risks = [r for r in risks if r['level'] == 'MEDIUM']
        
        self.assertGreater(len(high_risks), 0)
        self.assertGreater(len(medium_risks), 0)

    def test_generate_risks_low_requirement_maturity(self):
        """测试低需求成熟度生成风险"""
        data = {'requirement_maturity': 2}
        dimension_scores = {k: 20 for k in ['technology', 'business', 'resource', 'delivery', 'customer']}
        
        risks = self.service._generate_risks(data, dimension_scores, self.rules_config)
        
        # 应该有需求成熟度风险
        maturity_risks = [r for r in risks if r['dimension'] == 'requirement']
        self.assertGreater(len(maturity_risks), 0)

    def test_generate_risks_missing_sow(self):
        """测试缺少SOW生成风险"""
        data = {'has_sow': False}
        dimension_scores = {k: 20 for k in ['technology', 'business', 'resource', 'delivery', 'customer']}
        
        risks = self.service._generate_risks(data, dimension_scores, self.rules_config)
        
        # 应该有SOW缺失风险
        sow_risks = [r for r in risks if 'SOW' in r['description']]
        self.assertGreater(len(sow_risks), 0)

    def test_generate_risks_all_high_scores(self):
        """测试所有维度高分无风险"""
        dimension_scores = {k: 18 for k in ['technology', 'business', 'resource', 'delivery', 'customer']}
        data = {'requirement_maturity': 5, 'has_sow': True}
        
        risks = self.service._generate_risks(data, dimension_scores, self.rules_config)
        
        # 可能没有维度风险，但可能有其他风险
        dimension_risks = [r for r in risks if r['dimension'] in dimension_scores.keys()]
        self.assertEqual(len(dimension_risks), 0)

    # ========== 测试 _generate_conditions() ==========
    
    def test_generate_conditions_conditional_decision(self):
        """测试有条件立项生成条件"""
        risks = [
            {'level': 'HIGH', 'description': '技术风险高'},
            {'level': 'MEDIUM', 'description': '商务风险中等'}
        ]
        
        conditions = self.service._generate_conditions(
            AssessmentDecisionEnum.CONDITIONAL.value,
            risks,
            {}
        )
        
        # 应该生成条件
        self.assertGreater(len(conditions), 0)
        self.assertIn('技术风险高', conditions[0])

    def test_generate_conditions_recommend_decision(self):
        """测试推荐立项不生成条件"""
        conditions = self.service._generate_conditions(
            AssessmentDecisionEnum.RECOMMEND.value,
            [],
            {}
        )
        
        self.assertEqual(len(conditions), 0)

    def test_generate_conditions_with_open_items(self):
        """测试包含未决事项的条件生成"""
        # Mock未决事项查询
        from app.models.sales import OpenItem
        mock_item = MagicMock()
        
        # 创建一个新的db mock来处理不同的查询
        original_query = self.db.query
        
        def query_side_effect(model):
            if model == OpenItem:
                query_mock = MagicMock()
                query_mock.filter.return_value.all.return_value = [mock_item, mock_item]
                return query_mock
            return original_query(model)
        
        self.db.query = MagicMock(side_effect=query_side_effect)
        
        data = {'source_type': 'LEAD', 'source_id': 1}
        risks = [{'level': 'HIGH', 'description': '高风险'}]
        
        conditions = self.service._generate_conditions(
            AssessmentDecisionEnum.CONDITIONAL.value,
            risks,
            data
        )
        
        # 应该包含未决事项条件
        open_item_conditions = [c for c in conditions if '未决事项' in c]
        self.assertGreater(len(open_item_conditions), 0)

    # ========== 测试 _update_source_assessment() ==========
    
    def test_update_source_assessment_lead(self):
        """测试更新Lead的评估关联"""
        mock_lead = MagicMock(spec=Lead)
        mock_lead.id = 1
        
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = mock_lead
        self.db.query.return_value = query_mock
        
        self.service._update_source_assessment(
            AssessmentSourceTypeEnum.LEAD.value,
            1,
            100
        )
        
        self.assertEqual(mock_lead.assessment_id, 100)
        self.assertEqual(mock_lead.assessment_status, AssessmentStatusEnum.COMPLETED.value)
        self.db.commit.assert_called_once()

    def test_update_source_assessment_opportunity(self):
        """测试更新Opportunity的评估关联"""
        mock_opp = MagicMock(spec=Opportunity)
        mock_opp.id = 1
        
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = mock_opp
        self.db.query.return_value = query_mock
        
        self.service._update_source_assessment(
            AssessmentSourceTypeEnum.OPPORTUNITY.value,
            1,
            100
        )
        
        self.assertEqual(mock_opp.assessment_id, 100)
        self.assertEqual(mock_opp.assessment_status, AssessmentStatusEnum.COMPLETED.value)
        self.db.commit.assert_called_once()

    def test_update_source_assessment_not_found(self):
        """测试更新不存在的来源对象"""
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = None
        self.db.query.return_value = query_mock
        
        # 不应该抛出异常
        self.service._update_source_assessment(
            AssessmentSourceTypeEnum.LEAD.value,
            999,
            100
        )
        
        self.db.commit.assert_called_once()

    # ========== 测试 evaluate() 主方法 ==========
    
    def test_evaluate_success(self):
        """测试成功执行完整评估流程"""
        # Mock评分规则
        mock_rule = MagicMock(spec=ScoringRule)
        mock_rule.rules_json = json.dumps(self.rules_config)
        
        query_mock = MagicMock()
        query_mock.filter.return_value.order_by.return_value.first.return_value = mock_rule
        query_mock.filter.return_value.limit.return_value.all.return_value = []
        self.db.query.return_value = query_mock
        
        # Mock Lead查询
        mock_lead = MagicMock(spec=Lead)
        
        def side_effect(model):
            if model == ScoringRule:
                return query_mock
            elif model == Lead:
                lead_query = MagicMock()
                lead_query.filter.return_value.first.return_value = mock_lead
                return lead_query
            else:
                return query_mock
        
        self.db.query.side_effect = side_effect
        
        # 执行评估
        result = self.service.evaluate(
            source_type=AssessmentSourceTypeEnum.LEAD.value,
            source_id=1,
            evaluator_id=1,
            requirement_data=self.requirement_data,
            ai_analysis='AI分析结果'
        )
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.source_type, AssessmentSourceTypeEnum.LEAD.value)
        self.assertEqual(result.source_id, 1)
        self.assertEqual(result.evaluator_id, 1)
        self.assertEqual(result.status, AssessmentStatusEnum.COMPLETED)
        self.assertIsNotNone(result.total_score)
        self.assertIsNotNone(result.decision)
        
        # 验证数据库操作
        self.db.add.assert_called_once()
        self.db.flush.assert_called_once()

    def test_evaluate_no_scoring_rule(self):
        """测试无评分规则时抛出异常"""
        query_mock = MagicMock()
        query_mock.filter.return_value.order_by.return_value.first.return_value = None
        self.db.query.return_value = query_mock
        
        with self.assertRaises(ValueError) as context:
            self.service.evaluate(
                source_type=AssessmentSourceTypeEnum.LEAD.value,
                source_id=1,
                evaluator_id=1,
                requirement_data=self.requirement_data
            )
        
        self.assertIn('未找到启用的评分规则', str(context.exception))

    def test_evaluate_with_veto_triggered(self):
        """测试触发一票否决的评估"""
        # Mock评分规则
        mock_rule = MagicMock(spec=ScoringRule)
        mock_rule.rules_json = json.dumps(self.rules_config)
        
        query_mock = MagicMock()
        query_mock.filter.return_value.order_by.return_value.first.return_value = mock_rule
        query_mock.filter.return_value.limit.return_value.all.return_value = []
        
        mock_lead = MagicMock(spec=Lead)
        
        def side_effect(model):
            if model == ScoringRule:
                return query_mock
            elif model == Lead:
                lead_query = MagicMock()
                lead_query.filter.return_value.first.return_value = mock_lead
                return lead_query
            else:
                return query_mock
        
        self.db.query.side_effect = side_effect
        
        # 触发一票否决的数据
        veto_data = self.requirement_data.copy()
        veto_data['budget_status'] = '无预算'
        
        result = self.service.evaluate(
            source_type=AssessmentSourceTypeEnum.LEAD.value,
            source_id=1,
            evaluator_id=1,
            requirement_data=veto_data
        )
        
        # 验证一票否决被触发
        self.assertTrue(result.veto_triggered)
        self.assertIsNotNone(result.veto_rules)


if __name__ == '__main__':
    unittest.main()
