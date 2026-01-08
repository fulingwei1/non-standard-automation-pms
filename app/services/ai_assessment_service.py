# -*- coding: utf-8 -*-
"""
AI分析服务（可选）

使用通义千问API进行技术评估的AI辅助分析
如果未配置API密钥，服务将跳过AI分析
"""

import os
import json
import logging
from typing import Optional, Dict, Any
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# 通义千问API配置
ALIBABA_API_KEY = os.getenv("ALIBABA_API_KEY", "")
ALIBABA_MODEL = os.getenv("ALIBABA_MODEL", "qwen-plus")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"


class AIAssessmentService:
    """AI分析服务"""
    
    def __init__(self):
        self.api_key = ALIBABA_API_KEY
        self.model = ALIBABA_MODEL
        self.enabled = bool(self.api_key)
    
    def is_available(self) -> bool:
        """检查AI服务是否可用"""
        return self.enabled
    
    async def analyze_requirement(self, requirement_data: Dict[str, Any]) -> Optional[str]:
        """
        分析需求并生成AI分析报告
        
        Args:
            requirement_data: 需求数据字典
            
        Returns:
            Optional[str]: AI分析报告文本，如果服务不可用则返回None
        """
        if not self.is_available():
            logger.info("AI分析服务未配置，跳过AI分析")
            return None
        
        try:
            prompt = self._build_analysis_prompt(requirement_data)
            analysis = await self._call_qwen(prompt)
            return analysis
        except Exception as e:
            logger.error(f"AI分析失败: {e}", exc_info=True)
            return None
    
    def _build_analysis_prompt(self, requirement_data: Dict[str, Any]) -> str:
        """构建分析提示词"""
        project_name = requirement_data.get('project_name') or requirement_data.get('projectName', '未填写')
        industry = requirement_data.get('industry', '未填写')
        customer_name = requirement_data.get('customer_name') or requirement_data.get('customerName', '未填写')
        budget_value = requirement_data.get('budget_value') or requirement_data.get('budgetValue')
        budget_status = requirement_data.get('budget_status') or requirement_data.get('budgetStatus', '未填写')
        tech_requirements = requirement_data.get('tech_requirements') or requirement_data.get('techRequirements', '未填写')
        delivery_months = requirement_data.get('delivery_months') or requirement_data.get('deliveryMonths')
        requirement_maturity = requirement_data.get('requirement_maturity') or requirement_data.get('requirementMaturity')
        
        prompt = f"""
作为一个专业的售前技术顾问和项目经理，请对以下项目进行深度分析并给出评估建议：

### 项目基本信息
- 项目名称：{project_name}
- 所属行业：{industry}
- 客户名称：{customer_name}
- 预算状态：{budget_status}
{f'- 预算金额：{budget_value} 万元' if budget_value else ''}
{f'- 交付周期：{delivery_months} 个月' if delivery_months else ''}
{f'- 需求成熟度：{requirement_maturity} 级（1-5级）' if requirement_maturity else ''}

### 技术需求
{tech_requirements}

请从以下几个维度进行专业分析：

1. **项目可行性评估**
   - 技术可行性分析
   - 技术难点识别
   - 技术风险点

2. **需求成熟度评估**
   - 需求完整性分析
   - 缺失的关键信息
   - 需求变更风险

3. **风险点识别**
   - 技术风险
   - 商务风险
   - 交付风险
   - 客户关系风险

4. **建议的技术方案方向**
   - 推荐的技术路线
   - 关键技术选型建议
   - 需要注意的技术细节

5. **立项建议**
   - 是否推荐立项
   - 立项条件（如有）
   - 需要补充的信息

请用中文回复，并给出具体、可操作的建议。
"""
        return prompt
    
    async def _call_qwen(self, prompt: str) -> str:
        """调用通义千问API"""
        if not self.api_key:
            raise ValueError("未配置 ALIBABA_API_KEY")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个资深的售前工程师与项目经理，擅长非标自动化、储能与新能源行业的项目评估与技术咨询。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(BASE_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            else:
                raise ValueError(f"API返回格式异常: {data}")
    
    async def analyze_case_similarity(self, current_project: Dict[str, Any],
                                     historical_cases: list) -> Optional[str]:
        """
        分析案例相似度
        
        Args:
            current_project: 当前项目数据
            historical_cases: 历史案例列表
            
        Returns:
            Optional[str]: 相似度分析报告
        """
        if not self.is_available():
            return None
        
        try:
            prompt = self._build_similarity_prompt(current_project, historical_cases)
            analysis = await self._call_qwen(prompt)
            return analysis
        except Exception as e:
            logger.error(f"案例相似度分析失败: {e}", exc_info=True)
            return None
    
    def _build_similarity_prompt(self, current_project: Dict[str, Any],
                                historical_cases: list) -> str:
        """构建相似度分析提示词"""
        project_info = f"""
项目名称：{current_project.get('project_name', '未填写')}
行业：{current_project.get('industry', '未填写')}
产品类型：{current_project.get('product_type', '未填写')}
预算：{current_project.get('budget_value', '未填写')}
"""
        
        cases_text = "\n".join([
            f"{i+1}. {case.get('project_name', '')} - {case.get('core_failure_reason', '')}"
            for i, case in enumerate(historical_cases[:5])
        ])
        
        prompt = f"""
请分析以下当前项目与历史案例的相似度，并给出参考建议：

### 当前项目
{project_info}

### 历史案例
{cases_text}

请分析：
1. 与哪些历史案例最相似，相似度如何
2. 可以借鉴的经验和教训
3. 需要注意的风险点和预警信号
4. 建议采取的风险规避措施

请用中文回复，并给出具体、可操作的建议。
"""
        return prompt






