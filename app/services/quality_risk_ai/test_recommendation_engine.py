# -*- coding: utf-8 -*-
"""
测试推荐引擎
基于质量风险分析结果，生成测试计划推荐
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class TestRecommendationEngine:
    """测试推荐引擎"""
    
    # 测试类型映射
    TEST_TYPES_MAP = {
        'BUG': ['功能测试', '回归测试', '集成测试'],
        'PERFORMANCE': ['性能测试', '压力测试', '负载测试'],
        'STABILITY': ['稳定性测试', '长时运行测试', '边界测试'],
        'COMPATIBILITY': ['兼容性测试', '多环境测试', '跨平台测试']
    }
    
    def generate_recommendations(
        self,
        risk_analysis: Dict[str, Any],
        project_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成测试推荐
        
        Args:
            risk_analysis: 质量风险分析结果
            project_info: 项目信息
            
        Returns:
            测试推荐结果
        """
        risk_level = risk_analysis.get('risk_level', 'LOW')
        risk_score = risk_analysis.get('risk_score', 0)
        risk_category = risk_analysis.get('risk_category')
        
        # 确定测试重点区域
        focus_areas = self._identify_focus_areas(risk_analysis)
        
        # 确定优先级
        priority = self._determine_priority(risk_level, risk_score)
        
        # 推荐测试类型
        test_types = self._recommend_test_types(risk_category, risk_analysis)
        
        # 生成测试场景
        test_scenarios = self._generate_test_scenarios(risk_analysis)
        
        # 计算资源需求
        resource_recommendation = self._calculate_resource_needs(
            risk_level, 
            len(focus_areas),
            project_info
        )
        
        # 生成AI推荐理由
        ai_reasoning = self._generate_reasoning(risk_analysis, focus_areas)
        
        return {
            'focus_areas': focus_areas,
            'priority_modules': self._extract_priority_modules(risk_analysis),
            'risk_modules': self._extract_risk_modules(risk_analysis),
            'test_types': test_types,
            'test_scenarios': test_scenarios,
            'test_coverage_target': self._calculate_coverage_target(risk_level),
            'recommended_testers': resource_recommendation['testers'],
            'recommended_days': resource_recommendation['days'],
            'priority_level': priority,
            'ai_reasoning': ai_reasoning,
            'risk_summary': self._generate_risk_summary(risk_analysis)
        }
    
    def _identify_focus_areas(self, risk_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """识别测试重点区域"""
        focus_areas = []
        
        # 从风险信号中提取
        for signal in risk_analysis.get('risk_signals', []):
            focus_areas.append({
                'area': signal.get('module', '未知模块'),
                'reason': '检测到质量风险信号',
                'risk_score': signal.get('risk_score', 0),
                'priority': 'HIGH' if signal.get('risk_score', 0) > 50 else 'MEDIUM'
            })
        
        # 从预测问题中提取
        for issue in risk_analysis.get('predicted_issues', []):
            if issue.get('probability', 0) > 60:
                focus_areas.append({
                    'area': issue.get('issue', ''),
                    'reason': '高概率问题预测',
                    'probability': issue.get('probability', 0),
                    'priority': 'HIGH'
                })
        
        # 去重和排序
        unique_areas = {}
        for area in focus_areas:
            key = area['area']
            if key not in unique_areas or area.get('risk_score', 0) > unique_areas[key].get('risk_score', 0):
                unique_areas[key] = area
        
        return list(unique_areas.values())
    
    def _determine_priority(self, risk_level: str, risk_score: float) -> str:
        """确定测试优先级"""
        if risk_level == 'CRITICAL' or risk_score >= 80:
            return 'URGENT'
        elif risk_level == 'HIGH' or risk_score >= 60:
            return 'HIGH'
        elif risk_level == 'MEDIUM' or risk_score >= 30:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _recommend_test_types(
        self,
        risk_category: str,
        risk_analysis: Dict[str, Any]
    ) -> List[str]:
        """推荐测试类型"""
        test_types = set()
        
        # 基于风险类别
        if risk_category and risk_category in self.TEST_TYPES_MAP:
            test_types.update(self.TEST_TYPES_MAP[risk_category])
        
        # 基于关键词
        keywords = risk_analysis.get('risk_keywords', {})
        for category, keyword_list in keywords.items():
            if keyword_list and category in self.TEST_TYPES_MAP:
                test_types.update(self.TEST_TYPES_MAP[category])
        
        # 默认测试类型
        if not test_types:
            test_types = {'功能测试', '回归测试'}
        
        return list(test_types)
    
    def _generate_test_scenarios(self, risk_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """生成测试场景建议"""
        scenarios = []
        
        # 基于预测问题生成场景
        for issue in risk_analysis.get('predicted_issues', []):
            scenarios.append({
                'scenario': issue.get('issue', ''),
                'description': issue.get('impact', ''),
                'priority': 'HIGH' if issue.get('probability', 0) > 70 else 'MEDIUM',
                'suggested_action': issue.get('suggested_action', '')
            })
        
        # 基于异常模式生成场景
        for pattern in risk_analysis.get('abnormal_patterns', []):
            scenarios.append({
                'scenario': f"{pattern.get('name', '')}场景测试",
                'description': f"验证{pattern.get('name', '')}问题是否已修复",
                'priority': pattern.get('severity', 'MEDIUM'),
                'suggested_action': '重点测试相关功能点'
            })
        
        return scenarios[:10]  # 最多返回10个场景
    
    def _calculate_resource_needs(
        self,
        risk_level: str,
        focus_area_count: int,
        project_info: Dict[str, Any]
    ) -> Dict[str, int]:
        """计算资源需求"""
        
        # 基础资源
        base_testers = 1
        base_days = 3
        
        # 根据风险等级调整
        risk_multipliers = {
            'CRITICAL': 2.5,
            'HIGH': 2.0,
            'MEDIUM': 1.5,
            'LOW': 1.0
        }
        multiplier = risk_multipliers.get(risk_level, 1.0)
        
        # 根据重点区域数量调整
        area_factor = min(focus_area_count / 3, 2.0)  # 最多2倍
        
        recommended_testers = max(1, int(base_testers * multiplier * area_factor))
        recommended_days = max(3, int(base_days * multiplier * area_factor))
        
        return {
            'testers': recommended_testers,
            'days': recommended_days
        }
    
    def _calculate_coverage_target(self, risk_level: str) -> float:
        """计算目标测试覆盖率"""
        coverage_targets = {
            'CRITICAL': 95.0,
            'HIGH': 85.0,
            'MEDIUM': 75.0,
            'LOW': 65.0
        }
        return coverage_targets.get(risk_level, 70.0)
    
    def _extract_priority_modules(self, risk_analysis: Dict[str, Any]) -> List[str]:
        """提取优先测试模块"""
        modules = []
        
        for signal in risk_analysis.get('risk_signals', []):
            module = signal.get('module')
            if module and module not in modules:
                modules.append(module)
        
        return modules[:5]  # 最多5个优先模块
    
    def _extract_risk_modules(self, risk_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取高风险模块"""
        risk_modules = []
        
        for signal in risk_analysis.get('risk_signals', []):
            if signal.get('risk_score', 0) > 50:
                risk_modules.append({
                    'module': signal.get('module'),
                    'risk_score': signal.get('risk_score'),
                    'date': signal.get('date'),
                    'user': signal.get('user')
                })
        
        # 按风险评分排序
        risk_modules.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return risk_modules[:10]
    
    def _generate_reasoning(
        self,
        risk_analysis: Dict[str, Any],
        focus_areas: List[Dict[str, Any]]
    ) -> str:
        """生成AI推荐理由"""
        
        risk_level = risk_analysis.get('risk_level', 'UNKNOWN')
        risk_score = risk_analysis.get('risk_score', 0)
        
        reasoning_parts = [
            f"基于AI分析，当前质量风险等级为 {risk_level}，风险评分 {risk_score}/100。"
        ]
        
        if focus_areas:
            reasoning_parts.append(
                f"识别出 {len(focus_areas)} 个测试重点区域，建议优先关注。"
            )
        
        predicted_issues = risk_analysis.get('predicted_issues', [])
        if predicted_issues:
            high_prob_issues = [i for i in predicted_issues if i.get('probability', 0) > 70]
            if high_prob_issues:
                reasoning_parts.append(
                    f"预测到 {len(high_prob_issues)} 个高概率问题，需要重点测试验证。"
                )
        
        keywords = risk_analysis.get('risk_keywords', {})
        if 'CRITICAL' in keywords or 'BUG' in keywords:
            reasoning_parts.append(
                "工作日志中检测到严重问题关键词，建议加强测试覆盖。"
            )
        
        return ' '.join(reasoning_parts)
    
    def _generate_risk_summary(self, risk_analysis: Dict[str, Any]) -> str:
        """生成风险汇总说明"""
        
        risk_level = risk_analysis.get('risk_level', 'UNKNOWN')
        risk_category = risk_analysis.get('risk_category', '未知')
        rework_prob = risk_analysis.get('rework_probability', 0)
        impact_days = risk_analysis.get('estimated_impact_days', 0)
        
        summary = f"风险等级: {risk_level}, 类别: {risk_category}"
        
        if rework_prob > 0:
            summary += f", 返工概率: {rework_prob}%"
        
        if impact_days > 0:
            summary += f", 预估影响: {impact_days}天"
        
        keywords = risk_analysis.get('risk_keywords', {})
        if keywords:
            keyword_summary = ', '.join([f"{k}({len(v)})" for k, v in keywords.items()])
            summary += f"\n检测到的风险关键词: {keyword_summary}"
        
        return summary
