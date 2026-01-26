# -*- coding: utf-8 -*-
"""
AI分析模块
提供使用AI分析工作日志的功能（同步和异步版本）
"""

import logging
from datetime import date
from typing import Any, Dict, List

import httpx

from .ai_prompt import AIPromptMixin
from .core import ALIBABA_API_KEY, ALIBABA_BASE_URL, ALIBABA_MODEL

logger = logging.getLogger(__name__)


class AIAnalysisMixin(AIPromptMixin):
    """AI分析功能混入类"""

    def _analyze_with_ai_sync(
        self,
        content: str,
        user_projects: List[Dict[str, Any]],
        work_date: date
    ) -> Dict[str, Any]:
        """
        使用AI分析工作日志内容（同步版本）

        Args:
            content: 工作日志内容
            user_projects: 用户参与的项目列表
            work_date: 工作日期

        Returns:
            分析结果
        """
        try:
            import httpx
        except ImportError:
            logger.error("httpx未安装，无法使用AI分析功能")
            raise ValueError("AI分析功能需要安装httpx库")

        # 构建AI提示词
        prompt = self._build_ai_prompt(content, user_projects, work_date)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ALIBABA_API_KEY}",
        }

        payload = {
            "model": ALIBABA_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的工时分析助手，擅长从工作日志中提取工作项、工时和项目关联信息。请严格按照JSON格式输出结果。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,  # 降低温度，提高准确性
        }

        # 使用同步HTTP客户端
        with httpx.Client(timeout=30.0) as client:
            response = client.post(ALIBABA_BASE_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                ai_response = data["choices"][0]["message"]["content"]
                return self._parse_ai_response(ai_response, user_projects)
            else:
                raise ValueError(f"AI API返回格式异常: {data}")

    async def _analyze_with_ai(
        self,
        content: str,
        user_projects: List[Dict[str, Any]],
        work_date: date
    ) -> Dict[str, Any]:
        """
        使用AI分析工作日志内容（异步版本）

        Args:
            content: 工作日志内容
            user_projects: 用户参与的项目列表
            work_date: 工作日期

        Returns:
            分析结果
        """
        # 构建AI提示词
        prompt = self._build_ai_prompt(content, user_projects, work_date)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ALIBABA_API_KEY}",
        }

        payload = {
            "model": ALIBABA_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的工时分析助手，擅长从工作日志中提取工作项、工时和项目关联信息。请严格按照JSON格式输出结果。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,  # 降低温度，提高准确性
            "response_format": {"type": "json_object"}  # 强制JSON输出
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(ALIBABA_BASE_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                ai_response = data["choices"][0]["message"]["content"]
                return self._parse_ai_response(ai_response, user_projects)
            else:
                raise ValueError(f"AI API返回格式异常: {data}")
