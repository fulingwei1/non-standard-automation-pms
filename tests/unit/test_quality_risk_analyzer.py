# -*- coding: utf-8 -*-
"""
质量风险分析器单元测试

测试策略:
1. 只mock外部依赖 (db, httpx.Client)
2. 让业务逻辑真正执行
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date
import json

from app.services.quality_risk_ai.quality_risk_analyzer import QualityRiskAnalyzer


class TestQualityRiskAnalyzerInit(unittest.TestCase):
    """测试初始化"""
    
    def test_init_success(self):
        """测试正常初始化"""
        mock_db = MagicMock()
        analyzer = QualityRiskAnalyzer(mock_db)
        
        self.assertIsNotNone(analyzer)
        self.assertEqual(analyzer.db, mock_db)
        self.assertIsNotNone(analyzer.keyword_extractor)


class TestAnalyzeWorkLogs(unittest.TestCase):
    """测试主入口 analyze_work_logs"""
    
    def setUp(self):
        self.mock_db = MagicMock()
        self.analyzer = QualityRiskAnalyzer(self.mock_db)
    
    def test_analyze_empty_logs(self):
        """测试空日志列表"""
        result = self.analyzer.analyze_work_logs([])
        
        self.assertEqual(result['risk_level'], 'LOW')
        self.assertEqual(result['risk_score'], 0.0)
        self.assertEqual(result['risk_signals'], [])
        self.assertEqual(result['predicted_issues'], [])
        self.assertEqual(result['ai_analysis'], {})
        self.assertEqual(result['ai_confidence'], 0.0)
    
    def test_analyze_low_risk_logs(self):
        """测试低风险日志（不触发GLM）"""
        work_logs = [
            {
                'work_date': '2024-01-15',
                'user_name': '张三',
                'task_name': '开发用户模块',
                'work_content': '完成用户注册功能',
                'work_result': '开发完成，提交代码'
            }
        ]
        
        result = self.analyzer.analyze_work_logs(work_logs)
        
        self.assertIn(result['risk_level'], ['LOW', 'MEDIUM'])
        self.assertLess(result['risk_score'], 30)  # 低于GLM阈值
        self.assertEqual(result['analysis_model'], 'KEYWORD_EXTRACTOR')
        self.assertEqual(result['ai_confidence'], 60.0)
    
    def test_analyze_high_risk_logs_no_api_key(self):
        """测试高风险日志但无GLM API Key"""
        work_logs = [
            {
                'work_date': '2024-01-15',
                'user_name': '张三',
                'task_name': '修复Bug',
                'work_content': '修复严重bug，系统崩溃问题',
                'work_result': '修复失败，又出现新问题，需要返工'
            }
        ]
        
        # 清空API Key环境变量
        with patch.dict('os.environ', {'GLM_API_KEY': ''}, clear=False):
            result = self.analyzer.analyze_work_logs(work_logs)
        
        # 应该只使用关键词分析
        self.assertEqual(result['analysis_model'], 'KEYWORD_EXTRACTOR')
        self.assertGreater(result['risk_score'], 0)
    
    @patch('app.services.quality_risk_ai.quality_risk_analyzer.GLM_API_KEY', 'test-api-key')
    @patch('httpx.Client')
    def test_analyze_high_risk_logs_with_glm(self, mock_httpx_client):
        """测试高风险日志触发GLM分析"""
        work_logs = [
            {
                'work_date': '2024-01-15',
                'user_name': '张三',
                'task_name': '修复Bug',
                'work_content': '修复严重bug，系统崩溃问题',
                'work_result': '修复失败，又出现新问题，需要返工'
            }
        ]
        
        # Mock GLM API 响应
        mock_response = Mock()
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'risk_level': 'HIGH',
                        'risk_score': 85,
                        'risk_category': 'BUG',
                        'risk_signals': [{'signal': '频繁修复', 'severity': 'HIGH'}],
                        'predicted_issues': [{
                            'issue': '系统稳定性问题',
                            'probability': 80,
                            'impact': '影响用户体验',
                            'suggested_action': '增加测试'
                        }],
                        'rework_probability': 70,
                        'estimated_impact_days': 3,
                        'ai_reasoning': '检测到多次修复失败',
                        'confidence': 85
                    })
                }
            }]
        }
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.__enter__ = Mock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = Mock(return_value=False)
        mock_httpx_client.return_value = mock_client_instance
        
        result = self.analyzer.analyze_work_logs(work_logs)
        
        # 应该使用GLM分析并合并结果
        self.assertIn(result['risk_level'], ['HIGH', 'CRITICAL'])
        self.assertGreater(result['risk_score'], 30)
        self.assertIsNotNone(result.get('risk_category'))
        self.assertGreater(len(result['predicted_issues']), 0)
        self.assertEqual(result['ai_confidence'], 85.0)
    
    @patch('app.services.quality_risk_ai.quality_risk_analyzer.GLM_API_KEY', 'test-api-key')
    @patch('httpx.Client')
    def test_analyze_glm_failure_fallback(self, mock_httpx_client):
        """测试GLM调用失败时降级到关键词分析"""
        work_logs = [
            {
                'work_date': '2024-01-15',
                'user_name': '张三',
                'task_name': '修复Bug',
                'work_content': '修复严重bug，系统崩溃问题',
                'work_result': '修复失败，又出现新问题，需要返工'
            }
        ]
        
        # Mock GLM API 抛出异常
        mock_client_instance = Mock()
        mock_client_instance.post.side_effect = Exception('API调用失败')
        mock_client_instance.__enter__ = Mock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = Mock(return_value=False)
        mock_httpx_client.return_value = mock_client_instance
        
        result = self.analyzer.analyze_work_logs(work_logs)
        
        # 应该降级到关键词分析
        self.assertEqual(result['analysis_model'], 'KEYWORD_EXTRACTOR')
        self.assertEqual(result['ai_confidence'], 60.0)
    
    def test_analyze_with_project_context(self):
        """测试带项目上下文的分析"""
        work_logs = [
            {
                'work_date': '2024-01-15',
                'user_name': '张三',
                'task_name': '开发功能',
                'work_content': '完成功能开发',
                'work_result': '开发完成'
            }
        ]
        
        project_context = {
            'project_name': '测试项目',
            'stage': '开发阶段'
        }
        
        result = self.analyzer.analyze_work_logs(work_logs, project_context)
        
        self.assertIsNotNone(result)
        self.assertIn('risk_level', result)


class TestAnalyzeWithKeywords(unittest.TestCase):
    """测试关键词分析方法"""
    
    def setUp(self):
        self.mock_db = MagicMock()
        self.analyzer = QualityRiskAnalyzer(self.mock_db)
    
    def test_analyze_single_log(self):
        """测试单条日志分析"""
        work_logs = [
            {
                'work_date': '2024-01-15',
                'user_name': '张三',
                'task_name': '开发用户模块',
                'work_content': '完成用户注册功能',
                'work_result': '开发完成'
            }
        ]
        
        result = self.analyzer._analyze_with_keywords(work_logs)
        
        self.assertIn('risk_level', result)
        self.assertIn('risk_score', result)
        self.assertIn('risk_signals', result)
        self.assertIn('risk_keywords', result)
        self.assertIn('predicted_issues', result)
        self.assertEqual(result['ai_analysis']['method'], 'KEYWORD_BASED')
        self.assertEqual(result['ai_analysis']['logs_analyzed'], 1)
    
    def test_analyze_high_risk_keywords(self):
        """测试高风险关键词检测"""
        work_logs = [
            {
                'work_date': '2024-01-15',
                'user_name': '张三',
                'task_name': '修复Bug',
                'work_content': '修复严重bug，系统崩溃，性能问题',
                'work_result': '修复失败，需要返工'
            }
        ]
        
        result = self.analyzer._analyze_with_keywords(work_logs)
        
        self.assertGreater(result['risk_score'], 20)
        self.assertGreater(len(result['risk_signals']), 0)
        # 检查风险信号结构
        signal = result['risk_signals'][0]
        self.assertEqual(signal['date'], '2024-01-15')
        self.assertEqual(signal['user'], '张三')
        self.assertGreater(signal['risk_score'], 20)
    
    def test_analyze_multiple_logs(self):
        """测试多条日志分析"""
        work_logs = [
            {
                'work_date': '2024-01-15',
                'user_name': '张三',
                'task_name': '开发功能',
                'work_content': '开发完成',
                'work_result': '提交代码'
            },
            {
                'work_date': '2024-01-16',
                'user_name': '李四',
                'task_name': '修复bug',
                'work_content': '修复严重bug',
                'work_result': '问题解决'
            }
        ]
        
        result = self.analyzer._analyze_with_keywords(work_logs)
        
        self.assertEqual(result['ai_analysis']['logs_analyzed'], 2)
        # 评分应该是平均值
        self.assertIsInstance(result['risk_score'], float)
    
    def test_keyword_deduplication(self):
        """测试关键词去重"""
        work_logs = [
            {
                'work_date': '2024-01-15',
                'user_name': '张三',
                'task_name': '修复bug',
                'work_content': '修复bug bug bug',  # 重复关键词
                'work_result': '完成'
            }
        ]
        
        result = self.analyzer._analyze_with_keywords(work_logs)
        
        # 检查关键词是否去重
        if 'BUG' in result['risk_keywords']:
            bug_keywords = result['risk_keywords']['BUG']
            self.assertEqual(len(bug_keywords), len(set(bug_keywords)))


class TestPredictIssuesFromKeywords(unittest.TestCase):
    """测试基于关键词预测问题"""
    
    def setUp(self):
        self.mock_db = MagicMock()
        self.analyzer = QualityRiskAnalyzer(self.mock_db)
    
    def test_predict_bug_issues(self):
        """测试BUG关键词触发预测"""
        keywords = {
            'BUG': ['bug', 'defect', '缺陷', '错误']  # 4个关键词，超过阈值3
        }
        patterns = []
        
        result = self.analyzer._predict_issues_from_keywords(keywords, patterns)
        
        self.assertGreater(len(result), 0)
        bug_issue = next((i for i in result if '返工' in i['issue']), None)
        self.assertIsNotNone(bug_issue)
        self.assertEqual(bug_issue['probability'], 70)
    
    def test_predict_performance_issues(self):
        """测试性能关键词触发预测"""
        keywords = {
            'PERFORMANCE': ['性能', '慢']
        }
        patterns = []
        
        result = self.analyzer._predict_issues_from_keywords(keywords, patterns)
        
        perf_issue = next((i for i in result if '性能' in i['issue']), None)
        self.assertIsNotNone(perf_issue)
        self.assertEqual(perf_issue['probability'], 60)
    
    def test_predict_stability_issues(self):
        """测试稳定性关键词触发预测"""
        keywords = {
            'STABILITY': ['不稳定', '偶现']
        }
        patterns = []
        
        result = self.analyzer._predict_issues_from_keywords(keywords, patterns)
        
        stability_issue = next((i for i in result if '稳定性' in i['issue']), None)
        self.assertIsNotNone(stability_issue)
        self.assertEqual(stability_issue['probability'], 65)
    
    def test_predict_from_patterns(self):
        """测试基于异常模式预测"""
        keywords = {}
        patterns = [
            {'name': '频繁修复', 'severity': 'HIGH'},
            {'name': '多次返工', 'severity': 'CRITICAL'}
        ]
        
        result = self.analyzer._predict_issues_from_keywords(keywords, patterns)
        
        self.assertGreaterEqual(len(result), 2)
        for issue in result:
            self.assertIn('issue', issue)
            self.assertIn('probability', issue)
    
    def test_predict_no_issues(self):
        """测试无风险时的预测"""
        keywords = {}
        patterns = []
        
        result = self.analyzer._predict_issues_from_keywords(keywords, patterns)
        
        self.assertEqual(len(result), 0)


class TestBuildAnalysisPrompt(unittest.TestCase):
    """测试提示词构建"""
    
    def setUp(self):
        self.mock_db = MagicMock()
        self.analyzer = QualityRiskAnalyzer(self.mock_db)
    
    def test_build_prompt_basic(self):
        """测试基本提示词构建"""
        work_logs = [
            {
                'work_date': '2024-01-15',
                'task_name': '开发功能',
                'work_content': '完成用户模块',
                'work_result': '开发完成'
            }
        ]
        
        prompt = self.analyzer._build_analysis_prompt(work_logs, None)
        
        self.assertIn('2024-01-15', prompt)
        self.assertIn('开发功能', prompt)
        self.assertIn('完成用户模块', prompt)
        self.assertIn('JSON', prompt)
    
    def test_build_prompt_with_project_context(self):
        """测试带项目上下文的提示词"""
        work_logs = [
            {
                'work_date': '2024-01-15',
                'task_name': '开发功能',
                'work_content': '完成开发',
                'work_result': '完成'
            }
        ]
        project_context = {
            'project_name': '测试项目',
            'stage': '开发阶段'
        }
        
        prompt = self.analyzer._build_analysis_prompt(work_logs, project_context)
        
        self.assertIn('测试项目', prompt)
        self.assertIn('开发阶段', prompt)
    
    def test_build_prompt_max_logs(self):
        """测试最多分析20条日志"""
        work_logs = [
            {
                'work_date': f'2024-01-{i:02d}',
                'task_name': f'任务{i}',
                'work_content': f'内容{i}',
                'work_result': f'结果{i}'
            }
            for i in range(1, 30)  # 生成29条日志
        ]
        
        prompt = self.analyzer._build_analysis_prompt(work_logs, None)
        
        # 应该只包含前20条
        self.assertIn('2024-01-01', prompt)
        self.assertIn('2024-01-20', prompt)
        self.assertNotIn('2024-01-21', prompt)


class TestParseGLMResponse(unittest.TestCase):
    """测试GLM响应解析"""
    
    def setUp(self):
        self.mock_db = MagicMock()
        self.analyzer = QualityRiskAnalyzer(self.mock_db)
    
    def test_parse_valid_response(self):
        """测试解析有效响应"""
        response_text = json.dumps({
            'risk_level': 'HIGH',
            'risk_score': 85,
            'risk_category': 'BUG',
            'risk_signals': [{'signal': '频繁修复', 'severity': 'HIGH'}],
            'predicted_issues': [{
                'issue': '系统不稳定',
                'probability': 80,
                'impact': '影响用户',
                'suggested_action': '增加测试'
            }],
            'rework_probability': 70,
            'estimated_impact_days': 3,
            'ai_reasoning': '检测到多次修复',
            'confidence': 85
        })
        
        result = self.analyzer._parse_glm_response(response_text)
        
        self.assertEqual(result['risk_level'], 'HIGH')
        self.assertEqual(result['risk_score'], 85.0)
        self.assertEqual(result['risk_category'], 'BUG')
        self.assertEqual(result['ai_confidence'], 85.0)
        self.assertEqual(result['rework_probability'], 70.0)
        self.assertEqual(result['estimated_impact_days'], 3)
        self.assertIn('GLM_BASED', result['ai_analysis']['method'])
    
    def test_parse_response_with_defaults(self):
        """测试解析部分字段缺失的响应"""
        response_text = json.dumps({
            'risk_level': 'MEDIUM'
            # 其他字段缺失
        })
        
        result = self.analyzer._parse_glm_response(response_text)
        
        self.assertEqual(result['risk_level'], 'MEDIUM')
        self.assertEqual(result['risk_score'], 50.0)  # 默认值
        self.assertEqual(result['ai_confidence'], 70.0)  # 默认值
    
    def test_parse_invalid_json(self):
        """测试解析无效JSON"""
        response_text = 'invalid json{{'
        
        with self.assertRaises(ValueError):
            self.analyzer._parse_glm_response(response_text)


class TestMergeAnalysisResults(unittest.TestCase):
    """测试分析结果合并"""
    
    def setUp(self):
        self.mock_db = MagicMock()
        self.analyzer = QualityRiskAnalyzer(self.mock_db)
    
    def test_merge_higher_risk_level(self):
        """测试取更高的风险等级"""
        keyword_result = {
            'risk_level': 'MEDIUM',
            'risk_score': 40,
            'risk_signals': [],
            'risk_keywords': {'BUG': ['bug']},
            'abnormal_patterns': [],
            'ai_analysis': {'method': 'KEYWORD_BASED'}
        }
        ai_result = {
            'risk_level': 'HIGH',
            'risk_score': 80,
            'risk_category': 'BUG',
            'risk_signals': [],
            'predicted_issues': [],
            'rework_probability': 70,
            'estimated_impact_days': 3,
            'ai_analysis': {'method': 'GLM_BASED'},
            'ai_confidence': 85,
            'analysis_model': 'glm-4'
        }
        
        result = self.analyzer._merge_analysis_results(keyword_result, ai_result)
        
        self.assertEqual(result['risk_level'], 'HIGH')  # 取最高等级
    
    def test_merge_weighted_score(self):
        """测试加权评分"""
        keyword_result = {
            'risk_level': 'MEDIUM',
            'risk_score': 40,
            'risk_signals': [],
            'risk_keywords': {},
            'abnormal_patterns': [],
            'ai_analysis': {}
        }
        ai_result = {
            'risk_level': 'HIGH',
            'risk_score': 80,
            'risk_category': 'BUG',
            'risk_signals': [],
            'predicted_issues': [],
            'rework_probability': 70,
            'estimated_impact_days': 3,
            'ai_analysis': {},
            'ai_confidence': 85,
            'analysis_model': 'glm-4'
        }
        
        result = self.analyzer._merge_analysis_results(keyword_result, ai_result)
        
        # 40 * 0.4 + 80 * 0.6 = 16 + 48 = 64
        self.assertEqual(result['risk_score'], 64.0)
    
    def test_merge_signals_combined(self):
        """测试风险信号合并"""
        keyword_result = {
            'risk_level': 'MEDIUM',
            'risk_score': 40,
            'risk_signals': [{'signal': '关键词信号'}],
            'risk_keywords': {},
            'abnormal_patterns': [],
            'ai_analysis': {}
        }
        ai_result = {
            'risk_level': 'HIGH',
            'risk_score': 80,
            'risk_category': 'BUG',
            'risk_signals': [{'signal': 'AI信号'}],
            'predicted_issues': [],
            'rework_probability': 70,
            'estimated_impact_days': 3,
            'ai_analysis': {},
            'ai_confidence': 85,
            'analysis_model': 'glm-4'
        }
        
        result = self.analyzer._merge_analysis_results(keyword_result, ai_result)
        
        self.assertEqual(len(result['risk_signals']), 2)
    
    def test_merge_all_fields(self):
        """测试所有字段都正确合并"""
        keyword_result = {
            'risk_level': 'LOW',
            'risk_score': 20,
            'risk_signals': [],
            'risk_keywords': {'BUG': ['bug']},
            'abnormal_patterns': [{'name': '模式1'}],
            'ai_analysis': {'method': 'KEYWORD_BASED'}
        }
        ai_result = {
            'risk_level': 'CRITICAL',
            'risk_score': 95,
            'risk_category': 'CRITICAL',
            'risk_signals': [{'signal': 'AI信号'}],
            'predicted_issues': [{'issue': '严重问题'}],
            'rework_probability': 90,
            'estimated_impact_days': 5,
            'ai_analysis': {'method': 'GLM_BASED'},
            'ai_confidence': 90,
            'analysis_model': 'glm-4'
        }
        
        result = self.analyzer._merge_analysis_results(keyword_result, ai_result)
        
        self.assertEqual(result['risk_level'], 'CRITICAL')
        self.assertIn('risk_keywords', result)
        self.assertIn('abnormal_patterns', result)
        self.assertEqual(result['risk_category'], 'CRITICAL')
        self.assertEqual(result['rework_probability'], 90)
        self.assertEqual(result['estimated_impact_days'], 5)
        self.assertEqual(result['ai_confidence'], 90)
        self.assertEqual(result['analysis_model'], 'glm-4')


class TestAnalyzeWithGLM(unittest.TestCase):
    """测试GLM分析方法"""
    
    def setUp(self):
        self.mock_db = MagicMock()
        self.analyzer = QualityRiskAnalyzer(self.mock_db)
    
    @patch('app.services.quality_risk_ai.quality_risk_analyzer.GLM_API_KEY', 'test-api-key')
    @patch('app.services.quality_risk_ai.quality_risk_analyzer.GLM_BASE_URL', 'https://test.api.com')
    @patch('app.services.quality_risk_ai.quality_risk_analyzer.GLM_MODEL', 'test-model')
    @patch('httpx.Client')
    def test_analyze_with_glm_success(self, mock_httpx_client):
        """测试GLM分析成功"""
        work_logs = [
            {
                'work_date': '2024-01-15',
                'task_name': '修复bug',
                'work_content': '修复严重bug',
                'work_result': '问题解决'
            }
        ]
        
        # Mock API响应
        mock_response = Mock()
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'risk_level': 'HIGH',
                        'risk_score': 85,
                        'confidence': 85
                    })
                }
            }]
        }
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.__enter__ = Mock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = Mock(return_value=False)
        mock_httpx_client.return_value = mock_client_instance
        
        result = self.analyzer._analyze_with_glm(work_logs, None)
        
        self.assertEqual(result['risk_level'], 'HIGH')
        self.assertEqual(result['risk_score'], 85.0)
        
        # 验证API调用参数
        call_args = mock_client_instance.post.call_args
        self.assertEqual(call_args[0][0], 'https://test.api.com')
        payload = call_args[1]['json']
        self.assertEqual(payload['model'], 'test-model')
        self.assertEqual(payload['temperature'], 0.3)
    
    @patch('app.services.quality_risk_ai.quality_risk_analyzer.GLM_API_KEY', 'test-api-key')
    @patch('httpx.Client')
    def test_analyze_with_glm_api_error(self, mock_httpx_client):
        """测试GLM API错误"""
        work_logs = [
            {
                'work_date': '2024-01-15',
                'task_name': '开发',
                'work_content': '开发功能',
                'work_result': '完成'
            }
        ]
        
        # Mock API错误
        mock_client_instance = Mock()
        mock_client_instance.post.side_effect = Exception('网络错误')
        mock_client_instance.__enter__ = Mock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = Mock(return_value=False)
        mock_httpx_client.return_value = mock_client_instance
        
        with self.assertRaises(Exception):
            self.analyzer._analyze_with_glm(work_logs, None)
    
    @patch('app.services.quality_risk_ai.quality_risk_analyzer.GLM_API_KEY', 'test-api-key')
    @patch('httpx.Client')
    def test_analyze_with_glm_invalid_response_format(self, mock_httpx_client):
        """测试GLM返回格式异常"""
        work_logs = [
            {
                'work_date': '2024-01-15',
                'task_name': '开发',
                'work_content': '开发功能',
                'work_result': '完成'
            }
        ]
        
        # Mock 无效响应格式
        mock_response = Mock()
        mock_response.json.return_value = {'error': 'invalid'}  # 缺少choices字段
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.__enter__ = Mock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = Mock(return_value=False)
        mock_httpx_client.return_value = mock_client_instance
        
        with self.assertRaises(ValueError) as context:
            self.analyzer._analyze_with_glm(work_logs, None)
        
        self.assertIn('GLM API返回格式异常', str(context.exception))


if __name__ == '__main__':
    unittest.main()
