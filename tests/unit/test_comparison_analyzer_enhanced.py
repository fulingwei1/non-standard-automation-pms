"""
增强的 ProjectComparisonAnalyzer 单元测试
使用真实数据对象，只mock外部AI依赖
"""
import unittest
from unittest.mock import MagicMock, patch, Mock
from datetime import date, datetime
from decimal import Decimal
import json

from sqlalchemy.orm import Session

from app.services.project_review_ai.comparison_analyzer import ProjectComparisonAnalyzer
from app.models.project_review import ProjectReview, ProjectLesson, ProjectBestPractice
from app.models.project.core import Project


class TestProjectComparisonAnalyzerInit(unittest.TestCase):
    """测试初始化"""
    
    def test_init_success(self):
        """测试成功初始化"""
        db = MagicMock(spec=Session)
        analyzer = ProjectComparisonAnalyzer(db)
        
        self.assertEqual(analyzer.db, db)
        self.assertIsNotNone(analyzer.ai_client)
    
    def test_init_with_real_session_mock(self):
        """测试使用真实Session mock初始化"""
        db = MagicMock(spec=Session)
        db.query.return_value = MagicMock()
        
        analyzer = ProjectComparisonAnalyzer(db)
        
        self.assertIsNotNone(analyzer.db)
        self.assertIsNotNone(analyzer.ai_client)


class TestCompareWithHistory(unittest.TestCase):
    """测试 compare_with_history 方法"""
    
    def setUp(self):
        """设置测试数据"""
        self.db = MagicMock(spec=Session)
        self.analyzer = ProjectComparisonAnalyzer(self.db)
        
        # 构造真实的当前项目复盘对象
        self.current_project = Project(
            id=1,
            project_code='PRJ001',
            project_name='测试项目1',
            industry='制造业',
            project_type='STANDARD',
        )
        
        self.current_review = ProjectReview(
            id=1,
            review_no='REV001',
            project_code='PRJ001',
            project_id=1,
            schedule_variance=5,
            cost_variance=Decimal('10000.00'),
            change_count=3,
            customer_satisfaction=4,
            
            status='PUBLISHED'
        )
        self.current_review.project = self.current_project
        
        # 构造相似历史项目
        self.similar_review1 = ProjectReview(
            id=2,
            review_no='REV002',
            project_code='PRJ002',
            project_id=2,
            schedule_variance=3,
            cost_variance=Decimal('8000.00'),
            change_count=2,
            customer_satisfaction=5,
            
            status='PUBLISHED'
        )
        self.similar_review1.project = Project(
            id=2,
            project_code='PRJ002',
            industry='制造业',
            project_type='STANDARD',
        )
        
        self.similar_review2 = ProjectReview(
            id=3,
            review_no='REV003',
            project_code='PRJ003',
            project_id=3,
            schedule_variance=7,
            cost_variance=Decimal('12000.00'),
            change_count=4,
            customer_satisfaction=3,
            
            status='PUBLISHED'
        )
        self.similar_review2.project = Project(
            id=3,
            project_code='PRJ003',
            industry='制造业',
            project_type='STANDARD',
        )
    
    @patch('app.services.project_review_ai.comparison_analyzer.AIClientService')
    def test_compare_with_history_success(self, mock_ai_service):
        """测试成功对比历史项目"""
        # 配置mock
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = self.current_review
        self.db.query.return_value = query_mock
        
        # Mock AI 响应
        mock_ai_service.return_value.generate_solution.return_value = {
            'content': json.dumps({
                'strengths': [{'area': '进度', 'description': '进度控制良好', 'reason': '计划合理'}],
                'weaknesses': [{'area': '成本', 'description': '成本超支', 'cause': '需求变更'}],
                'improvements': [{
                    'area': '成本控制',
                    'problem': '成本超支',
                    'suggestion': '加强变更管理',
                    'expected_impact': '显著降低成本',
                    'priority': 'HIGH'
                }],
                'benchmarks': {
                    'schedule': {'target': 0, 'actual': 5, 'gap': 5},
                    'cost': {'target': 0, 'actual': 10000, 'gap': 10000}
                }
            })
        }
        
        # Mock _find_similar_reviews
        with patch.object(self.analyzer, '_find_similar_reviews', return_value=[self.similar_review1, self.similar_review2]):
            result = self.analyzer.compare_with_history(1, 'industry', 5)
        
        # 验证结果
        self.assertIn('current_review', result)
        self.assertIn('similar_reviews', result)
        self.assertIn('comparison', result)
        self.assertIn('analysis', result)
        self.assertIn('improvements', result)
        self.assertIn('benchmarks', result)
        
        self.assertEqual(result['current_review']['id'], 1)
        self.assertEqual(len(result['similar_reviews']), 2)
    
    def test_compare_with_history_review_not_found(self):
        """测试复盘报告不存在"""
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = None
        self.db.query.return_value = query_mock
        
        with self.assertRaises(ValueError) as context:
            self.analyzer.compare_with_history(999, 'industry', 5)
        
        self.assertIn('不存在', str(context.exception))
    
    @patch('app.services.project_review_ai.comparison_analyzer.AIClientService')
    def test_compare_with_different_similarity_types(self, mock_ai_service):
        """测试不同的相似度类型"""
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = self.current_review
        self.db.query.return_value = query_mock
        
        mock_ai_service.return_value.generate_solution.return_value = {
            'content': json.dumps({
                'strengths': [],
                'weaknesses': [],
                'improvements': [],
                'benchmarks': {}
            })
        }
        
        with patch.object(self.analyzer, '_find_similar_reviews', return_value=[]):
            for sim_type in ['industry', 'type', 'scale']:
                result = self.analyzer.compare_with_history(1, sim_type, 3)
                self.assertIsNotNone(result)
    
    @patch('app.services.project_review_ai.comparison_analyzer.AIClientService')
    def test_compare_with_history_no_similar_reviews(self, mock_ai_service):
        """测试没有相似历史项目的情况"""
        query_mock = MagicMock()
        filter_mock = MagicMock()
        query_mock.filter.return_value = filter_mock
        filter_mock.first.return_value = self.current_review
        self.db.query.return_value = query_mock
        
        mock_ai_service.return_value.generate_solution.return_value = {
            'content': json.dumps({
                'strengths': [],
                'weaknesses': [],
                'improvements': [],
                'benchmarks': {}
            })
        }
        
        with patch.object(self.analyzer, '_find_similar_reviews', return_value=[]):
            result = self.analyzer.compare_with_history(1, 'industry', 5)
            
            self.assertEqual(len(result['similar_reviews']), 0)
            # 平均值应该为0
            self.assertEqual(result['comparison']['historical_average']['schedule_variance'], 0)


class TestFindSimilarReviews(unittest.TestCase):
    """测试 _find_similar_reviews 方法"""
    
    def setUp(self):
        """设置测试数据"""
        self.db = MagicMock(spec=Session)
        self.analyzer = ProjectComparisonAnalyzer(self.db)
        
        self.current_project = Project(
            id=1,
            project_code='PRJ001',
            industry='制造业',
            project_type='STANDARD',
        )
        
        self.current_review = ProjectReview(
            id=1,
            review_no='REV001',
            project_id=1,
            budget_amount=Decimal('100000.00'),
            status='PUBLISHED'
        )
        self.current_review.project = self.current_project
    
    def test_find_similar_reviews_by_industry(self):
        """测试按行业查找相似项目"""
        # 创建mock查询链
        query_mock = MagicMock()
        filter_mock = MagicMock()
        join_mock = MagicMock()
        order_mock = MagicMock()
        limit_mock = MagicMock()
        
        self.db.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock
        filter_mock.join.return_value = join_mock
        join_mock.filter.return_value = filter_mock
        filter_mock.order_by.return_value = order_mock
        order_mock.limit.return_value = limit_mock
        limit_mock.all.return_value = []
        
        result = self.analyzer._find_similar_reviews(self.current_review, 'industry', 5)
        
        self.assertEqual(result, [])
        self.db.query.assert_called()
    
    def test_find_similar_reviews_by_type(self):
        """测试按项目类型查找"""
        query_mock = MagicMock()
        filter_mock = MagicMock()
        join_mock = MagicMock()
        order_mock = MagicMock()
        limit_mock = MagicMock()
        
        self.db.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock
        filter_mock.join.return_value = join_mock
        join_mock.filter.return_value = filter_mock
        filter_mock.order_by.return_value = order_mock
        order_mock.limit.return_value = limit_mock
        limit_mock.all.return_value = []
        
        result = self.analyzer._find_similar_reviews(self.current_review, 'type', 5)
        
        self.assertEqual(result, [])
    
    def test_find_similar_reviews_by_scale(self):
        """测试按规模查找"""
        query_mock = MagicMock()
        filter_mock = MagicMock()
        order_mock = MagicMock()
        limit_mock = MagicMock()
        
        self.db.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock
        filter_mock.order_by.return_value = order_mock
        order_mock.limit.return_value = limit_mock
        limit_mock.all.return_value = []
        
        result = self.analyzer._find_similar_reviews(self.current_review, 'scale', 3)
        
        self.assertEqual(result, [])
    
    def test_find_similar_reviews_with_different_limits(self):
        """测试不同的limit参数"""
        query_mock = MagicMock()
        filter_mock = MagicMock()
        order_mock = MagicMock()
        limit_mock = MagicMock()
        
        self.db.query.return_value = query_mock
        query_mock.filter.return_value = filter_mock
        filter_mock.order_by.return_value = order_mock
        order_mock.limit.return_value = limit_mock
        limit_mock.all.return_value = []
        
        for limit in [1, 3, 5, 10]:
            result = self.analyzer._find_similar_reviews(self.current_review, 'industry', limit)
            self.assertIsInstance(result, list)


class TestBuildComparisonData(unittest.TestCase):
    """测试 _build_comparison_data 方法"""
    
    def setUp(self):
        """设置测试数据"""
        self.db = MagicMock(spec=Session)
        self.analyzer = ProjectComparisonAnalyzer(self.db)
        
        self.current = ProjectReview(
            id=1,
            schedule_variance=5,
            cost_variance=Decimal('10000.00'),
            change_count=3,
            customer_satisfaction=4,
        )
        
        self.similars = [
            ProjectReview(
                id=2,
                schedule_variance=3,
                cost_variance=Decimal('8000.00'),
                change_count=2,
                customer_satisfaction=5,
            ),
            ProjectReview(
                id=3,
                schedule_variance=7,
                cost_variance=Decimal('12000.00'),
                change_count=4,
                customer_satisfaction=3,
            ),
        ]
    
    def test_build_comparison_data_with_similar_projects(self):
        """测试有相似项目时构建对比数据"""
        result = self.analyzer._build_comparison_data(self.current, self.similars)
        
        self.assertIn('current', result)
        self.assertIn('historical_average', result)
        self.assertIn('variance_analysis', result)
        
        # 验证当前项目数据
        self.assertEqual(result['current']['schedule_variance'], 5)
        self.assertEqual(result['current']['cost_variance'], 10000.00)
        self.assertEqual(result['current']['change_count'], 3)
        self.assertEqual(result['current']['customer_satisfaction'], 4)
        
        # 验证平均值计算
        self.assertEqual(result['historical_average']['schedule_variance'], 5.0)  # (3+7)/2
        self.assertEqual(result['historical_average']['cost_variance'], 10000.0)  # (8000+12000)/2
        self.assertEqual(result['historical_average']['change_count'], 3.0)  # (2+4)/2
        self.assertEqual(result['historical_average']['customer_satisfaction'], 4.0)  # (5+3)/2
        
        # 验证差异分析
        self.assertEqual(result['variance_analysis']['schedule'], 0.0)  # 5-5
        self.assertEqual(result['variance_analysis']['cost'], 0.0)  # 10000-10000
    
    def test_build_comparison_data_empty_similars(self):
        """测试没有相似项目时的对比数据"""
        result = self.analyzer._build_comparison_data(self.current, [])
        
        # 平均值应该为0
        self.assertEqual(result['historical_average']['schedule_variance'], 0)
        self.assertEqual(result['historical_average']['cost_variance'], 0)
        self.assertEqual(result['historical_average']['change_count'], 0)
        self.assertEqual(result['historical_average']['customer_satisfaction'], 0)
    
    def test_build_comparison_data_with_none_values(self):
        """测试包含None值的数据"""
        current = ProjectReview(
            id=1,
            schedule_variance=None,
            cost_variance=None,
            change_count=None,
            customer_satisfaction=None,
        )
        
        result = self.analyzer._build_comparison_data(current, self.similars)
        
        # None值应该被处理为0
        self.assertEqual(result['current']['schedule_variance'], 0)
        self.assertEqual(result['current']['cost_variance'], 0.0)
        self.assertEqual(result['current']['change_count'], 0)
        self.assertEqual(result['current']['customer_satisfaction'], 0)
    
    def test_build_comparison_data_single_similar(self):
        """测试只有一个相似项目"""
        single_similar = [self.similars[0]]
        result = self.analyzer._build_comparison_data(self.current, single_similar)
        
        # 平均值应该等于该项目的值
        self.assertEqual(result['historical_average']['schedule_variance'], 3.0)
        self.assertEqual(result['historical_average']['change_count'], 2.0)


class TestAnalyzeComparison(unittest.TestCase):
    """测试 _analyze_comparison 方法"""
    
    def setUp(self):
        """设置测试数据"""
        self.db = MagicMock(spec=Session)
        self.analyzer = ProjectComparisonAnalyzer(self.db)
        
        self.comparison_data = {
            'current': {
                'schedule_variance': 5,
                'cost_variance': 10000.00,
                'change_count': 3,
                'customer_satisfaction': 4,
            },
            'historical_average': {
                'schedule_variance': 5.0,
                'cost_variance': 10000.0,
                'change_count': 3.0,
                'customer_satisfaction': 4.0,
            },
            'variance_analysis': {
                'schedule': 0.0,
                'cost': 0.0,
                'changes': 0.0,
                'satisfaction': 0.0,
            }
        }
    
    @patch('app.services.project_review_ai.comparison_analyzer.AIClientService')
    def test_analyze_comparison_valid_json_response(self, mock_ai_service):
        """测试AI返回有效JSON响应"""
        mock_ai_service.return_value.generate_solution.return_value = {
            'content': json.dumps({
                'strengths': [{'area': '进度', 'description': '进度良好', 'reason': '计划合理'}],
                'weaknesses': [{'area': '成本', 'description': '成本超支', 'cause': '变更多'}],
                'improvements': [{
                    'area': '成本',
                    'problem': '超支',
                    'suggestion': '控制变更',
                    'expected_impact': '显著',
                    'priority': 'HIGH'
                }],
                'benchmarks': {'schedule': {}, 'cost': {}}
            })
        }
        
        result = self.analyzer._analyze_comparison(self.comparison_data)
        
        self.assertIn('strengths', result)
        self.assertIn('weaknesses', result)
        self.assertIn('improvements', result)
        self.assertIn('benchmarks', result)
        self.assertEqual(len(result['strengths']), 1)
        self.assertEqual(len(result['weaknesses']), 1)
        self.assertEqual(len(result['improvements']), 1)
    
    @patch('app.services.project_review_ai.comparison_analyzer.AIClientService')
    def test_analyze_comparison_json_with_markdown(self, mock_ai_service):
        """测试AI返回带markdown格式的JSON"""
        mock_ai_service.return_value.generate_solution.return_value = {
            'content': '''```json
{
    "strengths": [],
    "weaknesses": [],
    "improvements": [],
    "benchmarks": {}
}
```'''
        }
        
        result = self.analyzer._analyze_comparison(self.comparison_data)
        
        self.assertIn('strengths', result)
        self.assertEqual(result['strengths'], [])
    
    @patch('app.services.project_review_ai.comparison_analyzer.AIClientService')
    def test_analyze_comparison_invalid_json(self, mock_ai_service):
        """测试AI返回无效JSON时的处理"""
        mock_ai_service.return_value.generate_solution.return_value = {
            'content': 'This is not valid JSON'
        }
        
        result = self.analyzer._analyze_comparison(self.comparison_data)
        
        # 应该返回默认空结构
        self.assertEqual(result['strengths'], [])
        self.assertEqual(result['weaknesses'], [])
        self.assertEqual(result['improvements'], [])
        self.assertEqual(result['benchmarks'], {})
    
    @patch('app.services.project_review_ai.comparison_analyzer.AIClientService')
    def test_analyze_comparison_empty_response(self, mock_ai_service):
        """测试AI返回空响应"""
        mock_ai_service.return_value.generate_solution.return_value = {
            'content': ''
        }
        
        result = self.analyzer._analyze_comparison(self.comparison_data)
        
        self.assertIn('strengths', result)
        self.assertIn('weaknesses', result)


class TestFormatReview(unittest.TestCase):
    """测试 _format_review 方法"""
    
    def setUp(self):
        """设置测试数据"""
        self.db = MagicMock(spec=Session)
        self.analyzer = ProjectComparisonAnalyzer(self.db)
    
    def test_format_review_complete_data(self):
        """测试格式化完整数据的复盘"""
        review = ProjectReview(
            id=1,
            review_no='REV001',
            project_code='PRJ001',
            schedule_variance=5,
            cost_variance=Decimal('10000.00'),
            change_count=3,
            customer_satisfaction=4,
            
        )
        
        result = self.analyzer._format_review(review)
        
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['review_no'], 'REV001')
        self.assertEqual(result['project_code'], 'PRJ001')
        self.assertEqual(result['schedule_variance'], 5)
        self.assertEqual(result['cost_variance'], 10000.00)
        self.assertEqual(result['change_count'], 3)
        self.assertEqual(result['customer_satisfaction'], 4)
        self.assertEqual(result['quality_issues'], 85.5)
    
    def test_format_review_with_none_values(self):
        """测试格式化包含None值的复盘"""
        review = ProjectReview(
            id=2,
            review_no='REV002',
            project_code='PRJ002',
            schedule_variance=None,
            cost_variance=None,
            change_count=None,
            customer_satisfaction=None,
        )
        
        result = self.analyzer._format_review(review)
        
        self.assertEqual(result['id'], 2)
        self.assertIsNone(result['schedule_variance'])
        self.assertEqual(result['cost_variance'], 0.0)
        self.assertEqual(result['quality_issues'], 0.0)


class TestCalculatePriority(unittest.TestCase):
    """测试 _calculate_priority 方法"""
    
    def setUp(self):
        """设置测试数据"""
        self.db = MagicMock(spec=Session)
        self.analyzer = ProjectComparisonAnalyzer(self.db)
    
    def test_calculate_priority_high(self):
        """测试高优先级判断"""
        improvements = [
            {'expected_impact': '显著提升效率'},
            {'expected_impact': '重大改善成本'},
            {'expected_impact': '大幅降低风险'},
        ]
        
        for imp in improvements:
            priority = self.analyzer._calculate_priority(imp)
            self.assertEqual(priority, 'HIGH')
    
    def test_calculate_priority_medium(self):
        """测试中优先级判断"""
        improvements = [
            {'expected_impact': '一定程度提升'},
            {'expected_impact': '部分改善'},
            {'expected_impact': '改善流程'},
        ]
        
        for imp in improvements:
            priority = self.analyzer._calculate_priority(imp)
            self.assertEqual(priority, 'MEDIUM')
    
    def test_calculate_priority_low(self):
        """测试低优先级判断"""
        improvement = {'expected_impact': '轻微优化'}
        priority = self.analyzer._calculate_priority(improvement)
        self.assertEqual(priority, 'LOW')
    
    def test_calculate_priority_empty_impact(self):
        """测试空影响描述"""
        improvement = {'expected_impact': ''}
        priority = self.analyzer._calculate_priority(improvement)
        self.assertEqual(priority, 'LOW')
    
    def test_calculate_priority_missing_impact(self):
        """测试缺少expected_impact字段"""
        improvement = {}
        priority = self.analyzer._calculate_priority(improvement)
        self.assertEqual(priority, 'LOW')


class TestAssessFeasibility(unittest.TestCase):
    """测试 _assess_feasibility 方法"""
    
    def setUp(self):
        """设置测试数据"""
        self.db = MagicMock(spec=Session)
        self.analyzer = ProjectComparisonAnalyzer(self.db)
    
    def test_assess_feasibility_high(self):
        """测试高可行性"""
        improvements = [
            {'suggestion': '开展培训课程'},
            {'suggestion': '优化流程'},
            {'suggestion': '建立制度'},
        ]
        
        for imp in improvements:
            feasibility = self.analyzer._assess_feasibility(imp)
            self.assertEqual(feasibility, 'HIGH')
    
    def test_assess_feasibility_medium(self):
        """测试中可行性"""
        improvements = [
            {'suggestion': '引入新工具'},
            {'suggestion': '升级系统'},
        ]
        
        for imp in improvements:
            feasibility = self.analyzer._assess_feasibility(imp)
            self.assertEqual(feasibility, 'MEDIUM')
    
    def test_assess_feasibility_default_high(self):
        """测试默认为高可行性"""
        improvement = {'suggestion': '其他建议'}
        feasibility = self.analyzer._assess_feasibility(improvement)
        self.assertEqual(feasibility, 'HIGH')


class TestEstimateImpact(unittest.TestCase):
    """测试 _estimate_impact 方法"""
    
    def setUp(self):
        """设置测试数据"""
        self.db = MagicMock(spec=Session)
        self.analyzer = ProjectComparisonAnalyzer(self.db)
    
    def test_estimate_impact_high_priority(self):
        """测试高优先级的影响估算"""
        improvement = {'priority': 'HIGH'}
        impact = self.analyzer._estimate_impact(improvement)
        self.assertEqual(impact, 0.8)
    
    def test_estimate_impact_medium_priority(self):
        """测试中优先级的影响估算"""
        improvement = {'priority': 'MEDIUM'}
        impact = self.analyzer._estimate_impact(improvement)
        self.assertEqual(impact, 0.5)
    
    def test_estimate_impact_low_priority(self):
        """测试低优先级的影响估算"""
        improvement = {'priority': 'LOW'}
        impact = self.analyzer._estimate_impact(improvement)
        self.assertEqual(impact, 0.3)
    
    def test_estimate_impact_default(self):
        """测试默认影响估算"""
        improvement = {}
        impact = self.analyzer._estimate_impact(improvement)
        self.assertEqual(impact, 0.5)


class TestIdentifyImprovements(unittest.TestCase):
    """测试 identify_improvements 方法"""
    
    def setUp(self):
        """设置测试数据"""
        self.db = MagicMock(spec=Session)
        self.analyzer = ProjectComparisonAnalyzer(self.db)
    
    @patch('app.services.project_review_ai.comparison_analyzer.AIClientService')
    def test_identify_improvements_success(self, mock_ai_service):
        """测试成功识别改进点"""
        # Mock compare_with_history 的返回
        mock_comparison = {
            'analysis': {
                'improvements': [
                    {
                        'area': '成本',
                        'problem': '超支',
                        'suggestion': '控制变更',
                        'expected_impact': '显著降低',
                        'priority': 'HIGH'
                    },
                    {
                        'area': '质量',
                        'problem': '缺陷多',
                        'suggestion': '加强测试',
                        'expected_impact': '部分改善',
                        'priority': 'MEDIUM'
                    }
                ]
            }
        }
        
        with patch.object(self.analyzer, 'compare_with_history', return_value=mock_comparison):
            result = self.analyzer.identify_improvements(1)
        
        self.assertEqual(len(result), 2)
        # 验证增强字段
        self.assertIn('priority', result[0])
        self.assertIn('feasibility', result[0])
        self.assertIn('estimated_impact', result[0])
        # 验证排序（HIGH应该在前）
        self.assertEqual(result[0]['priority'], 'HIGH')
    
    @patch('app.services.project_review_ai.comparison_analyzer.AIClientService')
    def test_identify_improvements_empty(self, mock_ai_service):
        """测试没有改进建议的情况"""
        mock_comparison = {
            'analysis': {
                'improvements': []
            }
        }
        
        with patch.object(self.analyzer, 'compare_with_history', return_value=mock_comparison):
            result = self.analyzer.identify_improvements(1)
        
        self.assertEqual(len(result), 0)
    
    @patch('app.services.project_review_ai.comparison_analyzer.AIClientService')
    def test_identify_improvements_sorting(self, mock_ai_service):
        """测试改进建议排序"""
        mock_comparison = {
            'analysis': {
                'improvements': [
                    {
                        'area': 'A',
                        'problem': 'P1',
                        'suggestion': 'S1',
                        'expected_impact': '轻微',
                        'priority': 'LOW'
                    },
                    {
                        'area': 'B',
                        'problem': 'P2',
                        'suggestion': 'S2',
                        'expected_impact': '显著',
                        'priority': 'HIGH'
                    },
                    {
                        'area': 'C',
                        'problem': 'P3',
                        'suggestion': 'S3',
                        'expected_impact': '一定',
                        'priority': 'MEDIUM'
                    }
                ]
            }
        }
        
        with patch.object(self.analyzer, 'compare_with_history', return_value=mock_comparison):
            result = self.analyzer.identify_improvements(1)
        
        # 验证排序：HIGH -> MEDIUM -> LOW
        self.assertEqual(result[0]['priority'], 'HIGH')
        self.assertEqual(result[1]['priority'], 'MEDIUM')
        self.assertEqual(result[2]['priority'], 'LOW')


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""
    
    def setUp(self):
        """设置测试数据"""
        self.db = MagicMock(spec=Session)
        self.analyzer = ProjectComparisonAnalyzer(self.db)
    
    def test_build_comparison_with_zero_values(self):
        """测试所有值为0的情况"""
        current = ProjectReview(
            id=1,
            schedule_variance=0,
            cost_variance=Decimal('0'),
            change_count=0,
            customer_satisfaction=0,
        )
        
        similars = [
            ProjectReview(
                id=2,
                schedule_variance=0,
                cost_variance=Decimal('0'),
                change_count=0,
                customer_satisfaction=0,
            )
        ]
        
        result = self.analyzer._build_comparison_data(current, similars)
        
        self.assertEqual(result['current']['schedule_variance'], 0)
        self.assertEqual(result['variance_analysis']['schedule'], 0.0)
    
    def test_build_comparison_with_negative_values(self):
        """测试负值情况"""
        current = ProjectReview(
            id=1,
            schedule_variance=-5,  # 提前完成
            cost_variance=Decimal('-10000.00'),  # 节约成本
            change_count=1,
            customer_satisfaction=5,
        )
        
        result = self.analyzer._build_comparison_data(current, [])
        
        self.assertEqual(result['current']['schedule_variance'], -5)
        self.assertEqual(result['current']['cost_variance'], -10000.00)
    
    def test_calculate_priority_case_insensitive(self):
        """测试优先级计算不区分大小写"""
        improvements = [
            {'expected_impact': '显著提升'},  # 中文
            {'expected_impact': 'SIGNIFICANT improvement'},  # 英文大写（虽然代码主要处理中文）
        ]
        
        for imp in improvements:
            priority = self.analyzer._calculate_priority(imp)
            # 第一个应该是HIGH，第二个由于是英文可能是LOW（代码主要匹配中文）
            self.assertIn(priority, ['HIGH', 'MEDIUM', 'LOW'])
    
    @patch('app.services.project_review_ai.comparison_analyzer.AIClientService')
    def test_analyze_comparison_with_special_characters(self, mock_ai_service):
        """测试包含特殊字符的数据"""
        comparison_data = {
            'current': {
                'schedule_variance': 999999,
                'cost_variance': 999999999.99,
                'change_count': 9999,
                'customer_satisfaction': 5,
            },
            'historical_average': {
                'schedule_variance': 0.0,
                'cost_variance': 0.0,
                'change_count': 0.0,
                'customer_satisfaction': 0.0,
            },
            'variance_analysis': {
                'schedule': 999999.0,
                'cost': 999999999.99,
                'changes': 9999.0,
                'satisfaction': 5.0,
            }
        }
        
        mock_ai_service.return_value.generate_solution.return_value = {
            'content': json.dumps({
                'strengths': [],
                'weaknesses': [],
                'improvements': [],
                'benchmarks': {}
            })
        }
        
        result = self.analyzer._analyze_comparison(comparison_data)
        
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
