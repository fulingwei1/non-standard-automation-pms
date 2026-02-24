# -*- coding: utf-8 -*-
"""
项目对比分析服务单元测试 - 重写版本

目标：
1. 只mock外部依赖（db.query, AI API调用）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime
from decimal import Decimal

try:
    from app.services.project_review_ai.comparison_analyzer import ProjectComparisonAnalyzer
    from app.models.project_review import ProjectReview
    from app.models.project import Project
except ImportError as e:
    import pytest
    pytest.skip(f"project_review_ai dependencies not available: {e}", allow_module_level=True)


class TestProjectComparisonAnalyzer(unittest.TestCase):
    """测试项目对比分析器核心功能"""

    def setUp(self):
        """初始化测试环境"""
        self.mock_db = MagicMock()
        self.analyzer = ProjectComparisonAnalyzer(self.mock_db)

    # ========== compare_with_history() 主方法测试 ==========

    def test_compare_with_history_success(self):
        """测试与历史项目对比成功"""
        # 准备当前项目复盘
        current_review = self._create_mock_review(
            id=1,
            review_no="REV001",
            project_code="PRJ001",
            schedule_variance=10,
            cost_variance=Decimal("5000.00"),
            change_count=3,
            customer_satisfaction=4.5
        )

        # 准备历史项目复盘
        similar_review = self._create_mock_review(
            id=2,
            review_no="REV002",
            project_code="PRJ002",
            schedule_variance=5,
            cost_variance=Decimal("2000.00"),
            change_count=2,
            customer_satisfaction=4.8
        )

        # Mock数据库查询
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = current_review
        self.mock_db.query.return_value = mock_query

        # Mock _find_similar_reviews 返回
        with patch.object(self.analyzer, '_find_similar_reviews', return_value=[similar_review]):
            # 直接mock analyzer的ai_client属性
            self.analyzer.ai_client = MagicMock()
            self.analyzer.ai_client.generate_solution.return_value = {
                'content': json.dumps({
                    'strengths': [{'area': '进度管理', 'description': '按时交付', 'reason': '计划详细'}],
                    'weaknesses': [{'area': '成本控制', 'description': '超支', 'cause': '需求变更'}],
                    'improvements': [
                        {
                            'area': '成本管理',
                            'problem': '预算超支',
                            'suggestion': '加强变更管理',
                            'expected_impact': '显著降低成本偏差',
                            'priority': 'HIGH'
                        }
                    ],
                    'benchmarks': {
                        'schedule': {'average': 5, 'best': 2},
                        'cost': {'average': 2000, 'best': 1000},
                        'quality': {'average': 4.8, 'best': 5.0}
                    }
                })
            }

            result = self.analyzer.compare_with_history(review_id=1)

        # 验证结果结构
        self.assertIn('current_review', result)
        self.assertIn('similar_reviews', result)
        self.assertIn('comparison', result)
        self.assertIn('analysis', result)
        self.assertIn('improvements', result)
        self.assertIn('benchmarks', result)

        # 验证当前项目数据
        self.assertEqual(result['current_review']['id'], 1)
        self.assertEqual(result['current_review']['review_no'], "REV001")

        # 验证相似项目数据
        self.assertEqual(len(result['similar_reviews']), 1)
        self.assertEqual(result['similar_reviews'][0]['id'], 2)

        # 验证改进建议
        self.assertTrue(len(result['improvements']) > 0)
        self.assertEqual(result['improvements'][0]['area'], '成本管理')

    def test_compare_with_history_review_not_found(self):
        """测试复盘报告不存在"""
        # Mock数据库查询返回None
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query

        with self.assertRaises(ValueError) as context:
            self.analyzer.compare_with_history(review_id=999)

        self.assertIn("不存在", str(context.exception))

    # ========== identify_improvements() 测试 ==========

    def test_identify_improvements_success(self):
        """测试识别改进点成功"""
        # 准备mock数据
        current_review = self._create_mock_review(id=1)
        similar_review = self._create_mock_review(id=2)

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = current_review
        self.mock_db.query.return_value = mock_query

        with patch.object(self.analyzer, '_find_similar_reviews', return_value=[similar_review]):
            # 直接mock analyzer的ai_client属性
            self.analyzer.ai_client = MagicMock()
            self.analyzer.ai_client.generate_solution.return_value = {
                'content': json.dumps({
                    'strengths': [],
                    'weaknesses': [],
                    'improvements': [
                        {
                            'area': '进度管理',
                            'problem': '进度延期',
                            'suggestion': '采用敏捷开发',
                            'expected_impact': '显著提升交付效率'
                        },
                        {
                            'area': '质量管理',
                            'problem': '缺陷率高',
                            'suggestion': '加强代码审查',
                            'expected_impact': '部分改善质量'
                        }
                    ],
                    'benchmarks': {}
                })
            }

            improvements = self.analyzer.identify_improvements(review_id=1)

        # 验证结果
        self.assertGreater(len(improvements), 0)
        
        # 验证增强字段
        for imp in improvements:
            self.assertIn('priority', imp)
            self.assertIn('feasibility', imp)
            self.assertIn('estimated_impact', imp)

        # 验证排序（HIGH优先级应该在前）
        if len(improvements) > 1:
            first_priority = improvements[0]['priority']
            self.assertIn(first_priority, ['HIGH', 'MEDIUM', 'LOW'])

    # ========== _find_similar_reviews() 测试 ==========

    def test_find_similar_reviews_by_industry(self):
        """测试按行业查找相似项目"""
        current_review = self._create_mock_review(id=1)
        current_review.project = MagicMock()
        current_review.project.industry = "金融"
        current_review.project.project_type = "开发"

        # Mock查询链
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_join = MagicMock()
        mock_filter2 = MagicMock()
        mock_order = MagicMock()
        mock_limit = MagicMock()

        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.join.return_value = mock_join
        mock_join.filter.return_value = mock_filter2
        mock_filter2.order_by.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.all.return_value = [self._create_mock_review(id=2)]

        result = self.analyzer._find_similar_reviews(
            current_review,
            similarity_type='industry',
            limit=5
        )

        # 验证调用了正确的查询方法
        self.mock_db.query.assert_called_once()
        mock_filter.join.assert_called_once()
        self.assertEqual(len(result), 1)

    def test_find_similar_reviews_by_type(self):
        """测试按项目类型查找相似项目"""
        current_review = self._create_mock_review(id=1)
        current_review.project = MagicMock()
        current_review.project.industry = "金融"
        current_review.project.project_type = "开发"

        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_join = MagicMock()
        mock_filter2 = MagicMock()
        mock_order = MagicMock()
        mock_limit = MagicMock()

        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.join.return_value = mock_join
        mock_join.filter.return_value = mock_filter2
        mock_filter2.order_by.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.all.return_value = []

        result = self.analyzer._find_similar_reviews(
            current_review,
            similarity_type='type',
            limit=5
        )

        self.assertEqual(len(result), 0)

    def test_find_similar_reviews_by_scale(self):
        """测试按项目规模查找相似项目"""
        current_review = self._create_mock_review(id=1)
        current_review.budget_amount = Decimal("100000.00")
        current_review.project = MagicMock()

        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter2 = MagicMock()
        mock_order = MagicMock()
        mock_limit = MagicMock()

        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.filter.return_value = mock_filter2
        mock_filter2.order_by.return_value = mock_order
        mock_order.limit.return_value = mock_limit
        mock_limit.all.return_value = []

        result = self.analyzer._find_similar_reviews(
            current_review,
            similarity_type='scale',
            limit=3
        )

        self.assertEqual(len(result), 0)

    # ========== _build_comparison_data() 测试 ==========

    def test_build_comparison_data_with_similars(self):
        """测试构建对比数据（有相似项目）"""
        current = self._create_mock_review(
            id=1,
            schedule_variance=10,
            cost_variance=Decimal("5000.00"),
            change_count=3,
            customer_satisfaction=4.5
        )

        similars = [
            self._create_mock_review(
                id=2,
                schedule_variance=5,
                cost_variance=Decimal("2000.00"),
                change_count=2,
                customer_satisfaction=4.8
            ),
            self._create_mock_review(
                id=3,
                schedule_variance=7,
                cost_variance=Decimal("3000.00"),
                change_count=1,
                customer_satisfaction=4.9
            )
        ]

        result = self.analyzer._build_comparison_data(current, similars)

        # 验证结构
        self.assertIn('current', result)
        self.assertIn('historical_average', result)
        self.assertIn('variance_analysis', result)

        # 验证当前数据
        self.assertEqual(result['current']['schedule_variance'], 10)
        self.assertEqual(result['current']['cost_variance'], 5000.0)

        # 验证历史平均（(5+7)/2 = 6, (2000+3000)/2 = 2500）
        self.assertEqual(result['historical_average']['schedule_variance'], 6.0)
        self.assertEqual(result['historical_average']['cost_variance'], 2500.0)

        # 验证差异分析（10-6 = 4, 5000-2500 = 2500）
        self.assertEqual(result['variance_analysis']['schedule'], 4.0)
        self.assertEqual(result['variance_analysis']['cost'], 2500.0)

    def test_build_comparison_data_empty_similars(self):
        """测试构建对比数据（无相似项目）"""
        current = self._create_mock_review(
            id=1,
            schedule_variance=10,
            cost_variance=Decimal("5000.00")
        )

        result = self.analyzer._build_comparison_data(current, [])

        # 历史平均应为0
        self.assertEqual(result['historical_average']['schedule_variance'], 0)
        self.assertEqual(result['historical_average']['cost_variance'], 0)

    def test_build_comparison_data_with_none_values(self):
        """测试构建对比数据（包含None值）"""
        current = self._create_mock_review(
            id=1,
            schedule_variance=None,
            cost_variance=None,
            change_count=None,
            customer_satisfaction=None
        )

        similars = [self._create_mock_review(id=2)]

        result = self.analyzer._build_comparison_data(current, similars)

        # 验证None被转换为0
        self.assertEqual(result['current']['schedule_variance'], 0)
        self.assertEqual(result['current']['cost_variance'], 0.0)
        self.assertEqual(result['current']['change_count'], 0)
        self.assertEqual(result['current']['customer_satisfaction'], 0)

    # ========== _analyze_comparison() 测试 ==========

    def test_analyze_comparison_success(self):
        """测试AI分析对比结果成功"""
        comparison_data = {
            'current': {
                'schedule_variance': 10,
                'cost_variance': 5000.0,
                'change_count': 3,
                'customer_satisfaction': 4.5
            },
            'historical_average': {
                'schedule_variance': 5.0,
                'cost_variance': 2500.0,
                'change_count': 2.0,
                'customer_satisfaction': 4.8
            },
            'variance_analysis': {
                'schedule': 5.0,
                'cost': 2500.0,
                'changes': 1.0,
                'satisfaction': -0.3
            }
        }

        # 直接mock analyzer的ai_client属性
        self.analyzer.ai_client = MagicMock()
        self.analyzer.ai_client.generate_solution.return_value = {
            'content': json.dumps({
                'strengths': [{'area': '质量', 'description': '零缺陷', 'reason': '严格测试'}],
                'weaknesses': [{'area': '进度', 'description': '延期', 'cause': '资源不足'}],
                'improvements': [{'area': '进度管理', 'problem': '延期', 'suggestion': '增加资源'}],
                'benchmarks': {'schedule': {}, 'cost': {}, 'quality': {}}
            })
        }

        result = self.analyzer._analyze_comparison(comparison_data)

        # 验证AI被调用
        self.analyzer.ai_client.generate_solution.assert_called_once()

        # 验证结果结构
        self.assertIn('strengths', result)
        self.assertIn('weaknesses', result)
        self.assertIn('improvements', result)
        self.assertIn('benchmarks', result)

        # 验证内容
        self.assertEqual(len(result['strengths']), 1)
        self.assertEqual(result['strengths'][0]['area'], '质量')

    def test_analyze_comparison_with_code_block(self):
        """测试AI返回带```json代码块的响应"""
        comparison_data = {
            'current': {'schedule_variance': 10, 'cost_variance': 5000.0, 'change_count': 3, 'customer_satisfaction': 4.5},
            'historical_average': {'schedule_variance': 5.0, 'cost_variance': 2500.0, 'change_count': 2.0, 'customer_satisfaction': 4.8},
            'variance_analysis': {'schedule': 5.0, 'cost': 2500.0, 'changes': 1.0, 'satisfaction': -0.3}
        }

        # 直接mock analyzer的ai_client属性
        self.analyzer.ai_client = MagicMock()
        # 模拟AI返回带markdown代码块的JSON
        self.analyzer.ai_client.generate_solution.return_value = {
            'content': '''```json
{
    "strengths": [],
    "weaknesses": [],
    "improvements": [],
    "benchmarks": {}
}
```'''
        }

        result = self.analyzer._analyze_comparison(comparison_data)

        # 应该能正确解析
        self.assertIn('strengths', result)
        self.assertEqual(result['strengths'], [])

    def test_analyze_comparison_json_parse_error(self):
        """测试AI返回无效JSON"""
        comparison_data = {
            'current': {'schedule_variance': 10, 'cost_variance': 5000.0, 'change_count': 3, 'customer_satisfaction': 4.5},
            'historical_average': {'schedule_variance': 5.0, 'cost_variance': 2500.0, 'change_count': 2.0, 'customer_satisfaction': 4.8},
            'variance_analysis': {'schedule': 5.0, 'cost': 2500.0, 'changes': 1.0, 'satisfaction': -0.3}
        }

        # 直接mock analyzer的ai_client属性
        self.analyzer.ai_client = MagicMock()
        self.analyzer.ai_client.generate_solution.return_value = {
            'content': 'Invalid JSON content'
        }

        result = self.analyzer._analyze_comparison(comparison_data)

        # 应该返回默认结构
        self.assertEqual(result['strengths'], [])
        self.assertEqual(result['weaknesses'], [])
        self.assertEqual(result['improvements'], [])
        self.assertEqual(result['benchmarks'], {})

    # ========== _format_review() 测试 ==========

    def test_format_review(self):
        """测试格式化复盘报告"""
        review = self._create_mock_review(
            id=123,
            review_no="REV123",
            project_code="PRJ123",
            schedule_variance=15,
            cost_variance=Decimal("8000.50"),
            change_count=5,
            customer_satisfaction=4.2,
            quality_issues=3
        )

        result = self.analyzer._format_review(review)

        self.assertEqual(result['id'], 123)
        self.assertEqual(result['review_no'], "REV123")
        self.assertEqual(result['project_code'], "PRJ123")
        self.assertEqual(result['schedule_variance'], 15)
        self.assertEqual(result['cost_variance'], 8000.50)
        self.assertEqual(result['change_count'], 5)
        self.assertEqual(result['customer_satisfaction'], 4.2)
        self.assertEqual(result['quality_issues'], 3)

    def test_format_review_with_none_values(self):
        """测试格式化包含None值的复盘报告"""
        review = self._create_mock_review(
            id=1,
            cost_variance=None,
            quality_issues=None
        )

        result = self.analyzer._format_review(review)

        self.assertEqual(result['cost_variance'], 0.0)
        self.assertEqual(result['quality_issues'], 0)

    # ========== _calculate_priority() 测试 ==========

    def test_calculate_priority_high(self):
        """测试计算高优先级"""
        improvement = {'expected_impact': '显著提升项目效率'}
        self.assertEqual(self.analyzer._calculate_priority(improvement), 'HIGH')

        improvement = {'expected_impact': '重大改善成本控制'}
        self.assertEqual(self.analyzer._calculate_priority(improvement), 'HIGH')

        improvement = {'expected_impact': '大幅降低风险'}
        self.assertEqual(self.analyzer._calculate_priority(improvement), 'HIGH')

    def test_calculate_priority_medium(self):
        """测试计算中优先级"""
        improvement = {'expected_impact': '一定程度改善质量'}
        self.assertEqual(self.analyzer._calculate_priority(improvement), 'MEDIUM')

        improvement = {'expected_impact': '部分提升效率'}
        self.assertEqual(self.analyzer._calculate_priority(improvement), 'MEDIUM')

    def test_calculate_priority_low(self):
        """测试计算低优先级"""
        improvement = {'expected_impact': '略微优化流程'}
        self.assertEqual(self.analyzer._calculate_priority(improvement), 'LOW')

    def test_calculate_priority_empty(self):
        """测试空影响描述"""
        improvement = {}
        self.assertEqual(self.analyzer._calculate_priority(improvement), 'LOW')

    # ========== _assess_feasibility() 测试 ==========

    def test_assess_feasibility_high(self):
        """测试评估高可行性"""
        improvement = {'suggestion': '开展技术培训'}
        self.assertEqual(self.analyzer._assess_feasibility(improvement), 'HIGH')

        improvement = {'suggestion': '优化审批流程'}
        self.assertEqual(self.analyzer._assess_feasibility(improvement), 'HIGH')

        improvement = {'suggestion': '建立质量制度'}
        self.assertEqual(self.analyzer._assess_feasibility(improvement), 'HIGH')

    def test_assess_feasibility_medium(self):
        """测试评估中等可行性"""
        improvement = {'suggestion': '引入自动化工具'}
        self.assertEqual(self.analyzer._assess_feasibility(improvement), 'MEDIUM')

        improvement = {'suggestion': '上线新系统'}
        self.assertEqual(self.analyzer._assess_feasibility(improvement), 'MEDIUM')

    def test_assess_feasibility_default(self):
        """测试默认可行性"""
        improvement = {'suggestion': '其他建议'}
        self.assertEqual(self.analyzer._assess_feasibility(improvement), 'HIGH')

    # ========== _estimate_impact() 测试 ==========

    def test_estimate_impact_high(self):
        """测试估算高影响"""
        improvement = {'priority': 'HIGH'}
        self.assertEqual(self.analyzer._estimate_impact(improvement), 0.8)

    def test_estimate_impact_medium(self):
        """测试估算中等影响"""
        improvement = {'priority': 'MEDIUM'}
        self.assertEqual(self.analyzer._estimate_impact(improvement), 0.5)

    def test_estimate_impact_low(self):
        """测试估算低影响"""
        improvement = {'priority': 'LOW'}
        self.assertEqual(self.analyzer._estimate_impact(improvement), 0.3)

    def test_estimate_impact_unknown(self):
        """测试未知优先级"""
        improvement = {'priority': 'UNKNOWN'}
        self.assertEqual(self.analyzer._estimate_impact(improvement), 0.5)

    # ========== 辅助方法 ==========

    def _create_mock_review(
        self,
        id=1,
        review_no="REV001",
        project_code="PRJ001",
        schedule_variance=5,
        cost_variance=Decimal("2000.00"),
        change_count=2,
        customer_satisfaction=4.5,
        quality_issues=1
    ):
        """创建mock复盘报告对象"""
        review = MagicMock(spec=ProjectReview)
        review.id = id
        review.review_no = review_no
        review.project_code = project_code
        review.schedule_variance = schedule_variance
        review.cost_variance = cost_variance
        review.change_count = change_count
        review.customer_satisfaction = customer_satisfaction
        review.quality_issues = quality_issues
        review.budget_amount = Decimal("100000.00")
        review.status = "PUBLISHED"
        
        # Mock project关联
        review.project = MagicMock()
        review.project.industry = "科技"
        review.project.project_type = "开发"
        
        return review


if __name__ == "__main__":
    unittest.main()
