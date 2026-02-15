# -*- coding: utf-8 -*-
"""
质量风险AI分析器
使用GLM-5大模型分析工作日志，识别质量风险
"""

import os
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session

from .risk_keyword_extractor import RiskKeywordExtractor

logger = logging.getLogger(__name__)

# GLM-5 配置
GLM_API_KEY = os.getenv('GLM_API_KEY', '')
GLM_BASE_URL = os.getenv('GLM_BASE_URL', 'https://open.bigmodel.cn/api/paas/v4/chat/completions')
GLM_MODEL = os.getenv('GLM_MODEL', 'glm-4-flash')


class QualityRiskAnalyzer:
    """质量风险AI分析器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.keyword_extractor = RiskKeywordExtractor()
    
    def analyze_work_logs(
        self,
        work_logs: List[Dict[str, Any]],
        project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        分析工作日志，识别质量风险
        
        Args:
            work_logs: 工作日志列表
            project_context: 项目上下文信息（可选）
            
        Returns:
            分析结果
        """
        if not work_logs:
            return {
                'risk_level': 'LOW',
                'risk_score': 0.0,
                'risk_signals': [],
                'predicted_issues': [],
                'ai_analysis': {},
                'ai_confidence': 0.0
            }
        
        # 步骤1: 关键词分析（快速筛选）
        keyword_analysis = self._analyze_with_keywords(work_logs)
        
        # 步骤2: 如果风险评分较高，使用AI深度分析
        if keyword_analysis['risk_score'] >= 30 and GLM_API_KEY:
            try:
                ai_analysis = self._analyze_with_glm(work_logs, project_context)
                # 合并分析结果
                return self._merge_analysis_results(keyword_analysis, ai_analysis)
            except Exception as e:
                logger.warning(f"GLM分析失败，使用关键词分析结果: {e}")
                return keyword_analysis
        else:
            # 风险较低或无AI配置，仅返回关键词分析
            return keyword_analysis
    
    def _analyze_with_keywords(self, work_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        使用关键词提取器分析工作日志
        
        Args:
            work_logs: 工作日志列表
            
        Returns:
            关键词分析结果
        """
        all_keywords = {}
        all_patterns = []
        total_score = 0.0
        risk_signals = []
        
        for log in work_logs:
            content = log.get('work_content', '') + ' ' + log.get('work_result', '')
            
            analysis = self.keyword_extractor.analyze_text(content)
            
            # 合并关键词
            for category, keywords in analysis['risk_keywords'].items():
                if category not in all_keywords:
                    all_keywords[category] = []
                all_keywords[category].extend(keywords)
            
            # 收集异常模式
            all_patterns.extend(analysis['abnormal_patterns'])
            
            # 累加评分
            total_score += analysis['risk_score']
            
            # 记录风险信号
            if analysis['risk_score'] > 20:
                risk_signals.append({
                    'date': log.get('work_date'),
                    'user': log.get('user_name'),
                    'module': log.get('task_name'),
                    'risk_score': analysis['risk_score'],
                    'keywords': analysis['risk_keywords']
                })
        
        # 去重关键词
        for category in all_keywords:
            all_keywords[category] = list(set(all_keywords[category]))
        
        # 平均评分
        avg_score = total_score / len(work_logs) if work_logs else 0.0
        
        risk_level = self.keyword_extractor.determine_risk_level(avg_score)
        
        return {
            'risk_level': risk_level,
            'risk_score': round(avg_score, 2),
            'risk_signals': risk_signals,
            'risk_keywords': all_keywords,
            'abnormal_patterns': all_patterns,
            'predicted_issues': self._predict_issues_from_keywords(all_keywords, all_patterns),
            'ai_analysis': {
                'method': 'KEYWORD_BASED',
                'logs_analyzed': len(work_logs)
            },
            'ai_confidence': 60.0,  # 关键词分析置信度固定为60%
            'analysis_model': 'KEYWORD_EXTRACTOR'
        }
    
    def _analyze_with_glm(
        self,
        work_logs: List[Dict[str, Any]],
        project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        使用GLM-5进行深度分析
        
        Args:
            work_logs: 工作日志列表
            project_context: 项目上下文
            
        Returns:
            AI分析结果
        """
        import httpx
        
        # 构建提示词
        prompt = self._build_analysis_prompt(work_logs, project_context)
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {GLM_API_KEY}'
        }
        
        payload = {
            'model': GLM_MODEL,
            'messages': [
                {
                    'role': 'system',
                    'content': '你是一个专业的软件质量分析专家，擅长从工作日志中识别质量风险、预测问题并提供测试建议。请严格按照JSON格式输出分析结果。'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.3,
            'response_format': {'type': 'json_object'}
        }
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(GLM_BASE_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if 'choices' in data and len(data['choices']) > 0:
                ai_response = data['choices'][0]['message']['content']
                return self._parse_glm_response(ai_response)
            else:
                raise ValueError(f'GLM API返回格式异常: {data}')
    
    def _build_analysis_prompt(
        self,
        work_logs: List[Dict[str, Any]],
        project_context: Optional[Dict[str, Any]]
    ) -> str:
        """构建GLM分析提示词"""
        
        # 格式化工作日志
        logs_summary = []
        for log in work_logs[:20]:  # 最多分析20条
            logs_summary.append(
                f"日期: {log.get('work_date')}\n"
                f"模块: {log.get('task_name', '未知')}\n"
                f"内容: {log.get('work_content', '')}\n"
                f"结果: {log.get('work_result', '')}\n"
            )
        
        context_info = ''
        if project_context:
            context_info = f"\n项目信息:\n- 项目名称: {project_context.get('project_name')}\n- 阶段: {project_context.get('stage')}\n"
        
        prompt = f"""请分析以下工作日志，识别质量风险并预测可能出现的问题。

{context_info}

工作日志（最近{len(work_logs)}条）:
{chr(10).join(logs_summary)}

请按照以下JSON格式输出分析结果：
{{
    "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
    "risk_score": 0-100的数值,
    "risk_category": "BUG|PERFORMANCE|STABILITY|COMPATIBILITY",
    "risk_signals": [
        {{"signal": "风险信号描述", "severity": "严重程度"}}
    ],
    "predicted_issues": [
        {{
            "issue": "预测的问题",
            "probability": 0-100,
            "impact": "影响描述",
            "suggested_action": "建议措施"
        }}
    ],
    "rework_probability": 0-100的返工概率,
    "estimated_impact_days": 预估影响天数,
    "ai_reasoning": "AI分析推理过程",
    "confidence": 0-100的置信度
}}
"""
        return prompt
    
    def _parse_glm_response(self, response_text: str) -> Dict[str, Any]:
        """解析GLM响应"""
        try:
            result = json.loads(response_text)
            
            return {
                'risk_level': result.get('risk_level', 'MEDIUM'),
                'risk_score': float(result.get('risk_score', 50)),
                'risk_category': result.get('risk_category'),
                'risk_signals': result.get('risk_signals', []),
                'predicted_issues': result.get('predicted_issues', []),
                'rework_probability': float(result.get('rework_probability', 0)),
                'estimated_impact_days': int(result.get('estimated_impact_days', 0)),
                'ai_analysis': {
                    'method': 'GLM_BASED',
                    'reasoning': result.get('ai_reasoning', ''),
                    'model': GLM_MODEL
                },
                'ai_confidence': float(result.get('confidence', 70)),
                'analysis_model': GLM_MODEL
            }
        except json.JSONDecodeError as e:
            logger.error(f"解析GLM响应失败: {e}, 响应内容: {response_text}")
            raise ValueError(f"无法解析AI响应: {e}")
    
    def _merge_analysis_results(
        self,
        keyword_result: Dict[str, Any],
        ai_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并关键词分析和AI分析结果"""
        
        # 取最高风险等级
        risk_levels = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
        kw_level_val = risk_levels.get(keyword_result['risk_level'], 1)
        ai_level_val = risk_levels.get(ai_result['risk_level'], 1)
        final_level = max(kw_level_val, ai_level_val)
        final_level_name = [k for k, v in risk_levels.items() if v == final_level][0]
        
        # 综合评分（加权平均）
        final_score = (keyword_result['risk_score'] * 0.4 + ai_result['risk_score'] * 0.6)
        
        return {
            'risk_level': final_level_name,
            'risk_score': round(final_score, 2),
            'risk_category': ai_result.get('risk_category'),
            'risk_signals': keyword_result['risk_signals'] + ai_result.get('risk_signals', []),
            'risk_keywords': keyword_result['risk_keywords'],
            'abnormal_patterns': keyword_result['abnormal_patterns'],
            'predicted_issues': ai_result.get('predicted_issues', []),
            'rework_probability': ai_result.get('rework_probability', 0),
            'estimated_impact_days': ai_result.get('estimated_impact_days', 0),
            'ai_analysis': {
                'keyword_analysis': keyword_result['ai_analysis'],
                'ai_deep_analysis': ai_result['ai_analysis']
            },
            'ai_confidence': ai_result['ai_confidence'],
            'analysis_model': ai_result['analysis_model']
        }
    
    def _predict_issues_from_keywords(
        self,
        keywords: Dict[str, List[str]],
        patterns: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """基于关键词预测问题"""
        
        predicted_issues = []
        
        if 'BUG' in keywords and len(keywords['BUG']) > 3:
            predicted_issues.append({
                'issue': '模块存在较多缺陷，可能需要大量返工',
                'probability': 70,
                'impact': '影响交付进度和质量',
                'suggested_action': '加强代码审查和单元测试'
            })
        
        if 'PERFORMANCE' in keywords:
            predicted_issues.append({
                'issue': '性能问题可能导致用户体验下降',
                'probability': 60,
                'impact': '影响系统可用性',
                'suggested_action': '进行性能测试和优化'
            })
        
        if 'STABILITY' in keywords:
            predicted_issues.append({
                'issue': '稳定性问题可能导致生产环境故障',
                'probability': 65,
                'impact': '严重影响系统稳定性',
                'suggested_action': '增加稳定性测试场景'
            })
        
        for pattern in patterns:
            if pattern['severity'] in ['CRITICAL', 'HIGH']:
                predicted_issues.append({
                    'issue': f"检测到{pattern['name']}模式，风险较高",
                    'probability': 75,
                    'impact': '可能导致项目延期',
                    'suggested_action': f"重点关注{pattern['name']}相关问题"
                })
        
        return predicted_issues
