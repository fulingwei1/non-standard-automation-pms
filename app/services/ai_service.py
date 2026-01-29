# -*- coding: utf-8 -*-
"""
AI 服务模块
提供 Kimi AI 相关功能
"""

import json
import logging
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """AI 服务类，提供 Kimi API 调用功能"""
    
    def __init__(self):
        self.api_key = settings.KIMI_API_KEY
        self.base_url = settings.KIMI_API_BASE
        self.model = settings.KIMI_MODEL
        self.max_tokens = settings.KIMI_MAX_TOKENS
        self.temperature = settings.KIMI_TEMPERATURE
        self.timeout = settings.KIMI_TIMEOUT
        self.enabled = settings.KIMI_ENABLED and self.api_key is not None
        
        if self.enabled:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=self.timeout
            )
        else:
            self.client = None
            logger.warning("Kimi AI 服务未启用或缺少 API Key")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        调用 Kimi 聊天完成接口
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            model: 模型名称，默认使用配置中的模型
            max_tokens: 最大token数，默认使用配置中的值
            temperature: 温度参数，默认使用配置中的值
            stream: 是否流式返回
            
        Returns:
            API 响应数据
            
        Raises:
            HTTPException: API 调用失败
        """
        if not self.enabled:
            raise HTTPException(status_code=503, detail="AI 服务未启用")
        
        if not self.client:
            raise HTTPException(status_code=500, detail="AI 客户端未初始化")
        
        try:
            payload = {
                "model": model or self.model,
                "messages": messages,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
                "stream": stream
            }
            
            response = await self.client.post("/chat/completions", json=payload)
            
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                logger.error(f"Kimi API 错误: {response.status_code} - {error_data}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"AI API 调用失败: {error_data.get('error', {}).get('message', '未知错误')}"
                )
            
            return response.json()
            
        except httpx.TimeoutException:
            logger.error("Kimi API 请求超时")
            raise HTTPException(status_code=504, detail="AI 服务请求超时")
            
        except httpx.RequestError as e:
            logger.error(f"Kimi API 请求错误: {e}")
            raise HTTPException(status_code=502, detail=f"AI 服务请求失败: {str(e)}")
            
        except Exception as e:
            logger.error(f"Kimi API 未知错误: {e}")
            raise HTTPException(status_code=500, detail=f"AI 服务内部错误: {str(e)}")

    async def simple_chat(self, prompt: str, context: Optional[str] = None) -> str:
        """
        简单聊天接口
        
        Args:
            prompt: 用户提示词
            context: 可选的上下文信息
            
        Returns:
            AI 响应文本
        """
        messages = []
        
        if context:
            messages.append({"role": "system", "content": context})
        
        messages.append({"role": "user", "content": prompt})
        
        response = await self.chat_completion(messages)
        
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            logger.error(f"解析 Kimi 响应失败: {e}")
            raise HTTPException(status_code=500, detail="AI 响应格式错误")

    async def project_analysis(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        项目分析功能
        
        Args:
            project_data: 项目数据
            
        Returns:
            分析结果
        """
        prompt = f"""
        请分析以下非标自动化项目信息，提供专业的分析建议：
        
        项目信息：
        {json.dumps(project_data, ensure_ascii=False, indent=2)}
        
        请从以下维度进行分析：
        1. 项目风险评估
        2. 技术难点识别
        3. 资源配置建议
        4. 进度风险预警
        5. 成本控制建议
        
        请以JSON格式返回分析结果：
        {{
            "risk_level": "高/中/低",
            "main_risks": ["风险1", "风险2"],
            "technical_challenges": ["挑战1", "挑战2"],
            "resource_suggestions": ["建议1", "建议2"],
            "schedule_risks": ["风险1", "风险2"],
            "cost_recommendations": ["建议1", "建议2"],
            "overall_summary": "整体分析总结"
        }}
        """
        
        response_text = await self.simple_chat(
            prompt=prompt,
            context="你是一个专业的非标自动化项目管理专家，擅长项目风险分析和决策支持。"
        )
        
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # 如果JSON解析失败，返回原始文本
            return {"raw_analysis": response_text}

    async def close(self):
        """关闭HTTP客户端"""
        if self.client:
            await self.client.aclose()


# 全局AI服务实例
ai_service = AIService()


async def get_ai_service() -> AIService:
    """
    获取AI服务实例
    
    Returns:
        AIService实例
    """
    return ai_service


async def analyze_project_with_ai(project_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    使用AI分析项目的便捷函数
    
    Args:
        project_data: 项目数据
        
    Returns:
        AI分析结果
    """
    service = await get_ai_service()
    return await service.project_analysis(project_data)


async def chat_with_ai(prompt: str, context: Optional[str] = None) -> str:
    """
    与AI聊天的便捷函数
    
    Args:
        prompt: 用户提示
        context: 可选上下文
        
    Returns:
        AI响应
    """
    service = await get_ai_service()
    return await service.simple_chat(prompt, context)