# -*- coding: utf-8 -*-
"""
GLM API 包装服务
"""

import logging
from typing import Optional

from app.services.ai_planning.glm_service import GLMService

logger = logging.getLogger(__name__)

# 全局GLM服务实例
_glm_service = None


def get_glm_service() -> GLMService:
    """获取GLM服务单例"""
    global _glm_service
    if _glm_service is None:
        _glm_service = GLMService()
    return _glm_service


async def call_glm_api(
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    system_prompt: Optional[str] = None
) -> str:
    """
    调用GLM API
    
    Args:
        prompt: 用户提示
        temperature: 温度参数
        max_tokens: 最大token数
        system_prompt: 系统提示（可选）
        
    Returns:
        AI响应内容
    """
    service = get_glm_service()
    
    if not service.is_available():
        logger.warning("GLM服务不可用，返回模拟响应")
        return _generate_mock_response(prompt)
    
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    messages.append({"role": "user", "content": prompt})
    
    response = service.chat(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    if response:
        return response
    else:
        logger.error("GLM API调用失败，返回模拟响应")
        return _generate_mock_response(prompt)


def _generate_mock_response(prompt: str) -> str:
    """生成模拟响应（当GLM不可用时）"""
    return """
{
  "level": "MEDIUM",
  "description": "这是一个模拟的AI分析结果（GLM服务暂时不可用）",
  "confidence": 70,
  "analysis": "系统正在使用备用分析模式"
}
"""
