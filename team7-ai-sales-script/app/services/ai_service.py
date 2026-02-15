import openai
import httpx
from typing import Dict, Any, Optional, List
from app.config import settings


class AIService:
    """AI服务基类，支持OpenAI和Kimi"""

    def __init__(self):
        self.provider = settings.AI_PROVIDER
        if self.provider == "openai":
            openai.api_key = settings.OPENAI_API_KEY
        elif self.provider == "kimi":
            self.kimi_api_key = settings.KIMI_API_KEY
            self.kimi_base_url = "https://api.moonshot.cn/v1"

    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """统一的聊天补全接口"""
        if self.provider == "openai":
            return await self._openai_chat(messages, model or "gpt-4", temperature, max_tokens)
        elif self.provider == "kimi":
            return await self._kimi_chat(messages, model or "moonshot-v1-8k", temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")

    async def _openai_chat(
        self, 
        messages: List[Dict[str, str]], 
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """OpenAI GPT-4调用"""
        try:
            response = await openai.ChatCompletion.acreate(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    async def _kimi_chat(
        self, 
        messages: List[Dict[str, str]], 
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Kimi API调用"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.kimi_api_key}",
                    "Content-Type": "application/json",
                }
                data = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                response = await client.post(
                    f"{self.kimi_base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30.0,
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            raise Exception(f"Kimi API error: {str(e)}")

    async def analyze_customer_profile(self, communication_notes: str) -> Dict[str, Any]:
        """分析客户画像"""
        prompt = f"""
你是一位资深销售专家。请分析以下客户沟通记录，提取客户画像信息。

沟通记录：
{communication_notes}

请以JSON格式返回以下信息：
{{
    "customer_type": "technical|commercial|decision_maker|mixed",
    "focus_points": ["price", "quality", "delivery", "service"],
    "decision_style": "rational|emotional|authoritative",
    "analysis": "详细分析说明"
}}

要求：
1. customer_type: 识别客户类型（技术型/商务型/决策型/混合型）
2. focus_points: 客户关注点（价格/质量/交期/服务），可多选
3. decision_style: 决策风格（理性/感性/权威）
4. analysis: 详细的分析说明（200字以内）
"""
        
        messages = [
            {"role": "system", "content": "你是一位专业的销售顾问和客户分析专家。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.5)
        
        # 解析JSON响应
        import json
        try:
            # 尝试提取JSON部分
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            result = json.loads(json_str)
            return result
        except json.JSONDecodeError:
            # 如果解析失败，返回默认值
            return {
                "customer_type": "mixed",
                "focus_points": ["quality", "service"],
                "decision_style": "rational",
                "analysis": response
            }

    async def recommend_sales_script(
        self, 
        scenario: str, 
        customer_type: Optional[str] = None,
        focus_points: Optional[List[str]] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """推荐销售话术"""
        scenario_map = {
            "first_contact": "首次接触",
            "needs_discovery": "需求挖掘",
            "solution_presentation": "方案讲解",
            "price_negotiation": "价格谈判",
            "objection_handling": "异议处理",
            "closing": "成交"
        }
        
        scenario_name = scenario_map.get(scenario, scenario)
        customer_info = f"客户类型：{customer_type or '未知'}\n客户关注点：{', '.join(focus_points) if focus_points else '未知'}"
        context_info = f"\n当前情况：{context}" if context else ""
        
        prompt = f"""
你是一位资深销售专家。请为以下销售场景推荐合适的话术。

场景：{scenario_name}
{customer_info}{context_info}

请以JSON格式返回：
{{
    "recommended_scripts": ["话术1", "话术2", "话术3"],
    "response_strategy": "整体策略说明",
    "success_cases": [
        {{
            "case_title": "案例标题",
            "description": "简要描述",
            "result": "成功结果"
        }}
    ]
}}

要求：
1. 推荐3-5条具体话术，针对性强，易于执行
2. 提供整体应对策略（150字以内）
3. 引用1-2个成功案例
"""
        
        messages = [
            {"role": "system", "content": "你是一位专业的B2B销售顾问，擅长话术设计和销售策略。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.6)
        
        import json
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            result = json.loads(json_str)
            return result
        except json.JSONDecodeError:
            return {
                "recommended_scripts": [response],
                "response_strategy": "根据具体情况灵活调整",
                "success_cases": []
            }

    async def handle_objection(
        self, 
        objection_type: str,
        customer_type: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """处理客户异议"""
        customer_info = f"\n客户类型：{customer_type}" if customer_type else ""
        context_info = f"\n详细情况：{context}" if context else ""
        
        prompt = f"""
你是一位资深销售专家。客户提出了异议，请提供专业的应对策略。

异议类型：{objection_type}{customer_info}{context_info}

请以JSON格式返回：
{{
    "response_strategy": "应对策略总结",
    "recommended_scripts": ["应对话术1", "应对话术2", "应对话术3"],
    "key_points": ["关键点1", "关键点2"],
    "success_cases": [
        {{
            "case_title": "案例标题",
            "objection": "客户异议",
            "resolution": "解决方法",
            "result": "最终结果"
        }}
    ]
}}

要求：
1. 提供清晰的应对策略
2. 3-5条具体应对话术
3. 列出2-3个关键应对要点
4. 引用1-2个成功处理案例
"""
        
        messages = [
            {"role": "system", "content": "你是一位专业的销售顾问，擅长异议处理和客户说服。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.6)
        
        import json
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            result = json.loads(json_str)
            return result
        except json.JSONDecodeError:
            return {
                "response_strategy": response,
                "recommended_scripts": [],
                "key_points": [],
                "success_cases": []
            }

    async def guide_sales_progress(
        self,
        current_situation: str,
        customer_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """销售进程指导"""
        customer_info = f"\n客户类型：{customer_type}" if customer_type else ""
        
        prompt = f"""
你是一位资深销售教练。请分析当前销售进度，并提供下一步行动指导。

当前情况：
{current_situation}{customer_info}

请以JSON格式返回：
{{
    "current_stage": "当前阶段（需求确认/方案设计/报价/谈判/成交）",
    "next_actions": ["下一步行动1", "下一步行动2", "下一步行动3"],
    "key_milestones": ["里程碑1", "里程碑2"],
    "recommendations": "详细建议",
    "risks": ["潜在风险1", "潜在风险2"],
    "timeline": "预计时间线"
}}

要求：
1. 准确识别当前销售阶段
2. 提供3-5个具体可执行的下一步行动
3. 列出2-3个关键里程碑
4. 给出详细的推进建议（200字以内）
5. 识别潜在风险
6. 给出预计时间线
"""
        
        messages = [
            {"role": "system", "content": "你是一位专业的销售教练，擅长销售流程管理和进度把控。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.5)
        
        import json
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            result = json.loads(json_str)
            return result
        except json.JSONDecodeError:
            return {
                "current_stage": "分析中",
                "next_actions": [response],
                "key_milestones": [],
                "recommendations": response,
                "risks": [],
                "timeline": "待定"
            }
