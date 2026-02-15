# -*- coding: utf-8 -*-
"""
质量风险关键词提取器单元测试
"""

import pytest
from app.services.quality_risk_ai.risk_keyword_extractor import RiskKeywordExtractor


class TestRiskKeywordExtractor:
    """测试关键词提取器"""
    
    @pytest.fixture
    def extractor(self):
        """创建提取器实例"""
        return RiskKeywordExtractor()
    
    def test_extract_bug_keywords(self, extractor):
        """测试BUG关键词提取"""
        text = "今天修复了一个严重的bug，解决了崩溃问题"
        result = extractor.extract_keywords(text)
        
        assert 'BUG' in result
        assert 'bug' in result['BUG']
        assert '问题' in result['BUG']
    
    def test_extract_performance_keywords(self, extractor):
        """测试性能关键词提取"""
        text = "系统运行很慢，需要优化性能，存在卡顿现象"
        result = extractor.extract_keywords(text)
        
        assert 'PERFORMANCE' in result
        assert '慢' in result['PERFORMANCE']
        assert '性能' in result['PERFORMANCE']
        assert '卡顿' in result['PERFORMANCE']
    
    def test_extract_stability_keywords(self, extractor):
        """测试稳定性关键词提取"""
        text = "功能不稳定，偶现闪退，难以复现"
        result = extractor.extract_keywords(text)
        
        assert 'STABILITY' in result
        assert '不稳定' in result['STABILITY']
        assert '偶现' in result['STABILITY']
    
    def test_extract_multiple_categories(self, extractor):
        """测试多类别关键词提取"""
        text = "发现严重bug，系统性能差，运行不稳定"
        result = extractor.extract_keywords(text)
        
        assert len(result) >= 3
        assert 'BUG' in result
        assert 'PERFORMANCE' in result
        assert 'STABILITY' in result or 'CRITICAL' in result
    
    def test_detect_frequent_fix_pattern(self, extractor):
        """测试频繁修复模式检测"""
        text = "修复了之前的bug，又发现新问题需要解决"
        patterns = extractor.detect_patterns(text)
        
        assert len(patterns) > 0
        pattern_names = [p['name'] for p in patterns]
        assert '频繁修复' in pattern_names
    
    def test_detect_rework_pattern(self, extractor):
        """测试返工模式检测"""
        text = "再次修改代码逻辑，重新调整接口"
        patterns = extractor.detect_patterns(text)
        
        pattern_names = [p['name'] for p in patterns]
        assert '多次返工' in pattern_names
    
    def test_detect_blocking_pattern(self, extractor):
        """测试阻塞问题模式检测"""
        text = "遇到阻塞问题，无法继续开发"
        patterns = extractor.detect_patterns(text)
        
        pattern_names = [p['name'] for p in patterns]
        assert '阻塞问题' in pattern_names
    
    def test_calculate_risk_score_low(self, extractor):
        """测试低风险评分计算"""
        keywords = {'BUG': ['bug']}
        patterns = []
        
        score = extractor.calculate_risk_score(keywords, patterns)
        
        assert 0 <= score < 25
    
    def test_calculate_risk_score_medium(self, extractor):
        """测试中风险评分计算"""
        keywords = {
            'BUG': ['bug', '错误'],
            'PERFORMANCE': ['慢', '卡']
        }
        patterns = [
            {'severity': 'MEDIUM', 'count': 1}
        ]
        
        score = extractor.calculate_risk_score(keywords, patterns)
        
        assert 25 <= score < 50
    
    def test_calculate_risk_score_high(self, extractor):
        """测试高风险评分计算"""
        keywords = {
            'CRITICAL': ['严重', '致命'],
            'BUG': ['bug', '错误', '缺陷'],
            'REWORK': ['返工', '重做']
        }
        patterns = [
            {'severity': 'HIGH', 'count': 2},
            {'severity': 'MEDIUM', 'count': 1}
        ]
        
        score = extractor.calculate_risk_score(keywords, patterns)
        
        assert score >= 50
    
    def test_determine_risk_level_low(self, extractor):
        """测试低风险等级判定"""
        level = extractor.determine_risk_level(20)
        assert level == 'LOW'
    
    def test_determine_risk_level_medium(self, extractor):
        """测试中风险等级判定"""
        level = extractor.determine_risk_level(35)
        assert level == 'MEDIUM'
    
    def test_determine_risk_level_high(self, extractor):
        """测试高风险等级判定"""
        level = extractor.determine_risk_level(60)
        assert level == 'HIGH'
    
    def test_determine_risk_level_critical(self, extractor):
        """测试严重风险等级判定"""
        level = extractor.determine_risk_level(80)
        assert level == 'CRITICAL'
    
    def test_analyze_text_complete(self, extractor):
        """测试完整文本分析"""
        text = """
        今天修复了登录模块的一个严重bug，系统偶现崩溃。
        性能优化仍存在问题，运行速度很慢。
        需要重新调整代码逻辑，进行返工。
        """
        
        result = extractor.analyze_text(text)
        
        assert 'risk_keywords' in result
        assert 'abnormal_patterns' in result
        assert 'risk_score' in result
        assert 'risk_level' in result
        assert result['risk_score'] > 0
        assert result['risk_level'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    
    def test_empty_text(self, extractor):
        """测试空文本"""
        result = extractor.analyze_text("")
        
        assert result['risk_score'] == 0
        assert result['risk_level'] == 'LOW'
    
    def test_normal_work_log(self, extractor):
        """测试正常工作日志（无风险）"""
        text = "完成了用户界面设计，实现了列表展示功能"
        result = extractor.analyze_text(text)
        
        assert result['risk_score'] == 0 or result['risk_score'] < 10
        assert result['risk_level'] == 'LOW'
