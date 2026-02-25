# -*- coding: utf-8 -*-
"""
AI赢率预测服务 - 集成GPT-4/Kimi API
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class AIWinRatePredictionService:
    """AI赢率预测服务"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.kimi_api_key = os.getenv("KIMI_API_KEY")
        self.use_kimi = os.getenv("USE_KIMI_API", "false").lower() == "true"
        
    async def predict_with_ai(
        self,
        ticket_data: Dict[str, Any],
        historical_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        使用AI进行赢率预测
        
        Args:
            ticket_data: 售前工单数据
            historical_data: 历史数据（可选）
            
        Returns:
            {
                'win_rate_score': float,
                'confidence_interval': str,
                'influencing_factors': list,
                'competitor_analysis': dict,
                'improvement_suggestions': dict,
                'ai_analysis_report': str
            }
        """
        try:
            # 选择使用的API
            if self.use_kimi and self.kimi_api_key:
                return await self._predict_with_kimi(ticket_data, historical_data)
            elif self.openai_api_key:
                return await self._predict_with_openai(ticket_data, historical_data)
            else:
                logger.warning("未配置AI API密钥，使用默认预测")
                return self._fallback_prediction(ticket_data)
                
        except Exception as e:
            logger.error(f"AI预测失败: {e}")
            return self._fallback_prediction(ticket_data)
    
    async def _predict_with_openai(
        self,
        ticket_data: Dict[str, Any],
        historical_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """使用OpenAI GPT-4进行预测"""
        
        prompt = self._build_prediction_prompt(ticket_data, historical_data)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一个专业的销售赢率预测专家，擅长分析项目特征并预测成交概率。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            
            if response.status_code != 200:
                logger.error(f"OpenAI API请求失败: {response.status_code} - {response.text}")
                return self._fallback_prediction(ticket_data)
            
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            
            return self._parse_ai_response(ai_response, ticket_data)
    
    async def _predict_with_kimi(
        self,
        ticket_data: Dict[str, Any],
        historical_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """使用Kimi API进行预测"""
        
        prompt = self._build_prediction_prompt(ticket_data, historical_data)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.moonshot.cn/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.kimi_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "moonshot-v1-8k",
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一个专业的销售赢率预测专家，擅长分析项目特征并预测成交概率。"
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Kimi API请求失败: {response.status_code} - {response.text}")
                return self._fallback_prediction(ticket_data)
            
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            
            return self._parse_ai_response(ai_response, ticket_data)
    
    def _build_prediction_prompt(
        self,
        ticket_data: Dict[str, Any],
        historical_data: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """构建AI预测提示词"""
        
        prompt = f"""
请分析以下售前项目信息，预测其成交概率并提供详细建议。

## 项目基本信息
- 工单编号: {ticket_data.get('ticket_no', 'N/A')}
- 工单标题: {ticket_data.get('title', 'N/A')}
- 客户名称: {ticket_data.get('customer_name', 'N/A')}
- 项目金额: {ticket_data.get('estimated_amount', 'N/A')}
- 工单类型: {ticket_data.get('ticket_type', 'N/A')}
- 紧急程度: {ticket_data.get('urgency', 'N/A')}

## 客户信息
- 是否老客户: {ticket_data.get('is_repeat_customer', False)}
- 历史合作次数: {ticket_data.get('cooperation_count', 0)}
- 历史成功次数: {ticket_data.get('success_count', 0)}

## 竞争态势
- 竞争对手数量: {ticket_data.get('competitor_count', 'N/A')}
- 主要竞争对手: {ticket_data.get('main_competitors', 'N/A')}

## 技术评估
- 需求成熟度: {ticket_data.get('requirement_maturity', 'N/A')}
- 技术可行性: {ticket_data.get('technical_feasibility', 'N/A')}
- 商务可行性: {ticket_data.get('business_feasibility', 'N/A')}
- 交付风险: {ticket_data.get('delivery_risk', 'N/A')}
- 客户关系: {ticket_data.get('customer_relationship', 'N/A')}

## 销售人员
- 销售人员ID: {ticket_data.get('salesperson_id', 'N/A')}
- 历史赢率: {ticket_data.get('salesperson_win_rate', 'N/A')}
"""
        
        if historical_data:
            prompt += f"\n## 历史相似案例\n"
            for i, case in enumerate(historical_data[:5], 1):
                prompt += f"\n案例{i}: 赢率={case.get('win_rate', 'N/A')}, 结果={case.get('result', 'N/A')}\n"
        
        prompt += """

请以JSON格式输出分析结果，包含以下字段：
{
    "win_rate_score": 0-100的数值,
    "confidence_interval": "例如: 65-75%",
    "influencing_factors": [
        {"factor": "因素名称", "impact": "正面/负面", "score": 1-10, "description": "详细说明"}
    ],
    "competitor_analysis": {
        "competitors": ["竞争对手列表"],
        "our_advantages": ["我方优势"],
        "competitor_advantages": ["竞对优势"],
        "differentiation_strategy": ["差异化策略建议"]
    },
    "improvement_suggestions": {
        "short_term": ["1周内的行动建议"],
        "mid_term": ["1个月内的策略建议"],
        "milestones": ["关键里程碑监控点"]
    },
    "analysis_summary": "综合分析总结（200字以内）"
}
"""
        
        return prompt
    
    def _parse_ai_response(self, ai_response: str, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析AI响应"""
        
        try:
            # 尝试提取JSON
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = ai_response[start_idx:end_idx]
                parsed_data = json.loads(json_str)
                
                return {
                    'win_rate_score': float(parsed_data.get('win_rate_score', 50.0)),
                    'confidence_interval': parsed_data.get('confidence_interval', '45-55%'),
                    'influencing_factors': parsed_data.get('influencing_factors', []),
                    'competitor_analysis': parsed_data.get('competitor_analysis', {}),
                    'improvement_suggestions': parsed_data.get('improvement_suggestions', {}),
                    'ai_analysis_report': parsed_data.get('analysis_summary', ai_response)
                }
            else:
                logger.warning("无法从AI响应中提取JSON，使用默认值")
                return self._fallback_prediction(ticket_data)
                
        except Exception as e:
            logger.error(f"解析AI响应失败: {e}")
            return self._fallback_prediction(ticket_data)
    
    def _fallback_prediction(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """默认预测（当AI服务不可用时）"""
        
        # 基于规则的简单预测
        base_score = 50.0
        
        # 根据客户历史调整
        if ticket_data.get('is_repeat_customer'):
            base_score += 15.0
        
        # 根据竞争对手数量调整
        competitor_count = ticket_data.get('competitor_count', 3)
        if competitor_count <= 1:
            base_score += 10.0
        elif competitor_count >= 5:
            base_score -= 15.0
        
        # 根据销售人员历史赢率调整
        salesperson_win_rate = ticket_data.get('salesperson_win_rate', 0.5)
        base_score += (salesperson_win_rate - 0.5) * 30
        
        # 确保在0-100范围内
        win_rate_score = max(0.0, min(100.0, base_score))
        
        return {
            'win_rate_score': round(win_rate_score, 2),
            'confidence_interval': f"{int(win_rate_score-5)}-{int(win_rate_score+5)}%",
            'influencing_factors': [
                {
                    'factor': '客户类型',
                    'impact': 'positive' if ticket_data.get('is_repeat_customer') else 'neutral',
                    'score': 8 if ticket_data.get('is_repeat_customer') else 5,
                    'description': '老客户' if ticket_data.get('is_repeat_customer') else '新客户'
                },
                {
                    'factor': '竞争态势',
                    'impact': 'negative' if competitor_count >= 4 else 'neutral',
                    'score': 7 if competitor_count >= 4 else 5,
                    'description': f'竞争对手数量: {competitor_count}'
                }
            ],
            'competitor_analysis': {
                'competitors': [],
                'our_advantages': ['技术实力', '服务质量'],
                'competitor_advantages': ['未知'],
                'differentiation_strategy': ['深挖客户需求', '突出技术优势']
            },
            'improvement_suggestions': {
                'short_term': ['加强客户沟通', '完善技术方案'],
                'mid_term': ['建立长期合作关系', '提升竞争力'],
                'milestones': ['方案评审', '报价提交', '合同签订']
            },
            'ai_analysis_report': '基于规则的预测分析（AI服务暂时不可用）'
        }


__all__ = ["AIWinRatePredictionService"]
