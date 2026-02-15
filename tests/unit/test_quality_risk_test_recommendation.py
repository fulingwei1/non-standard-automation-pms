# -*- coding: utf-8 -*-
"""
测试推荐引擎单元测试
"""

import pytest
from app.services.quality_risk_ai.test_recommendation_engine import TestRecommendationEngine


class TestTestRecommendationEngine:
    """测试推荐引擎测试"""
    
    @pytest.fixture
    def engine(self):
        """创建推荐引擎实例"""
        return TestRecommendationEngine()
    
    @pytest.fixture
    def sample_risk_analysis(self):
        """样例风险分析结果"""
        return {
            'risk_level': 'HIGH',
            'risk_score': 65.0,
            'risk_category': 'BUG',
            'risk_signals': [
                {
                    'module': '登录模块',
                    'risk_score': 70,
                    'date': '2026-02-15'
                },
                {
                    'module': '支付模块',
                    'risk_score': 60,
                    'date': '2026-02-14'
                }
            ],
            'risk_keywords': {
                'BUG': ['bug', '错误', '缺陷'],
                'PERFORMANCE': ['慢']
            },
            'predicted_issues': [
                {
                    'issue': '登录功能可能存在缺陷',
                    'probability': 75,
                    'impact': '影响用户登录',
                    'suggested_action': '加强测试'
                }
            ],
            'abnormal_patterns': [
                {
                    'name': '频繁修复',
                    'severity': 'HIGH',
                    'count': 2
                }
            ]
        }
    
    def test_generate_recommendations(self, engine, sample_risk_analysis):
        """测试生成完整推荐"""
        project_info = {'project_id': 1}
        
        result = engine.generate_recommendations(sample_risk_analysis, project_info)
        
        assert 'focus_areas' in result
        assert 'test_types' in result
        assert 'priority_level' in result
        assert 'recommended_testers' in result
        assert 'recommended_days' in result
        assert 'ai_reasoning' in result
    
    def test_identify_focus_areas(self, engine, sample_risk_analysis):
        """测试识别测试重点区域"""
        focus_areas = engine._identify_focus_areas(sample_risk_analysis)
        
        assert len(focus_areas) > 0
        assert any('登录模块' in area['area'] for area in focus_areas)
    
    def test_determine_priority_urgent(self, engine):
        """测试紧急优先级判定"""
        priority = engine._determine_priority('CRITICAL', 85)
        assert priority == 'URGENT'
    
    def test_determine_priority_high(self, engine):
        """测试高优先级判定"""
        priority = engine._determine_priority('HIGH', 65)
        assert priority == 'HIGH'
    
    def test_determine_priority_medium(self, engine):
        """测试中优先级判定"""
        priority = engine._determine_priority('MEDIUM', 40)
        assert priority == 'MEDIUM'
    
    def test_determine_priority_low(self, engine):
        """测试低优先级判定"""
        priority = engine._determine_priority('LOW', 20)
        assert priority == 'LOW'
    
    def test_recommend_test_types_bug(self, engine):
        """测试BUG类型的测试推荐"""
        test_types = engine._recommend_test_types('BUG', {'risk_keywords': {'BUG': ['bug']}})
        
        assert '功能测试' in test_types or '回归测试' in test_types
    
    def test_recommend_test_types_performance(self, engine):
        """测试性能类型的测试推荐"""
        test_types = engine._recommend_test_types('PERFORMANCE', {'risk_keywords': {'PERFORMANCE': ['慢']}})
        
        assert '性能测试' in test_types or '压力测试' in test_types
    
    def test_generate_test_scenarios(self, engine, sample_risk_analysis):
        """测试生成测试场景"""
        scenarios = engine._generate_test_scenarios(sample_risk_analysis)
        
        assert len(scenarios) > 0
        assert all('scenario' in s and 'priority' in s for s in scenarios)
    
    def test_calculate_resource_needs_critical(self, engine):
        """测试严重风险的资源需求计算"""
        result = engine._calculate_resource_needs('CRITICAL', 5, {})
        
        assert result['testers'] >= 2
        assert result['days'] >= 5
    
    def test_calculate_resource_needs_low(self, engine):
        """测试低风险的资源需求计算"""
        result = engine._calculate_resource_needs('LOW', 2, {})
        
        assert result['testers'] >= 1
        assert result['days'] >= 3
    
    def test_calculate_coverage_target(self, engine):
        """测试覆盖率目标计算"""
        assert engine._calculate_coverage_target('CRITICAL') >= 90
        assert engine._calculate_coverage_target('HIGH') >= 80
        assert engine._calculate_coverage_target('MEDIUM') >= 70
        assert engine._calculate_coverage_target('LOW') >= 60
    
    def test_extract_priority_modules(self, engine, sample_risk_analysis):
        """测试提取优先模块"""
        modules = engine._extract_priority_modules(sample_risk_analysis)
        
        assert len(modules) > 0
        assert '登录模块' in modules
    
    def test_extract_risk_modules(self, engine, sample_risk_analysis):
        """测试提取高风险模块"""
        risk_modules = engine._extract_risk_modules(sample_risk_analysis)
        
        assert len(risk_modules) > 0
        assert all('module' in m and 'risk_score' in m for m in risk_modules)
    
    def test_generate_reasoning(self, engine, sample_risk_analysis):
        """测试生成推荐理由"""
        focus_areas = [{'area': '登录模块', 'risk_score': 70}]
        reasoning = engine._generate_reasoning(sample_risk_analysis, focus_areas)
        
        assert len(reasoning) > 0
        assert 'HIGH' in reasoning or '风险' in reasoning
    
    def test_generate_risk_summary(self, engine, sample_risk_analysis):
        """测试生成风险汇总"""
        summary = engine._generate_risk_summary(sample_risk_analysis)
        
        assert len(summary) > 0
        assert 'HIGH' in summary or 'BUG' in summary
