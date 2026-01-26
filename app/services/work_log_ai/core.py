# -*- coding: utf-8 -*-
"""
工作日志AI分析服务 - 核心类
"""

import logging
import os
from datetime import date
from typing import Any, Dict

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# AI API配置（支持多种AI服务）
ALIBABA_API_KEY = os.getenv("ALIBABA_API_KEY", "")
ALIBABA_MODEL = os.getenv("ALIBABA_MODEL", "qwen-plus")
ALIBABA_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

# 如果未配置AI服务，使用规则引擎作为fallback
USE_AI = bool(ALIBABA_API_KEY)


class WorkLogAICore:
    """工作日志AI分析服务核心类"""

    def __init__(self, db: Session):
        self.db = db
        self.use_ai = USE_AI

    def analyze_work_log(
        self,
        content: str,
        user_id: int,
        work_date: date
    ) -> Dict[str, Any]:
        """
        分析工作日志内容，提取工作项、工时和项目关联（同步版本）

        Args:
            content: 工作日志内容
            user_id: 用户ID
            work_date: 工作日期

        Returns:
            分析结果字典，包含：
            - work_items: 工作项列表（每个包含工作内容、工时、项目ID等）
            - suggested_projects: 建议的项目列表
            - total_hours: 总工时
            - confidence: 置信度（0-1）
        """
        # 获取用户参与的项目列表
        user_projects = self._get_user_projects(user_id)

        if self.use_ai:
            # 使用AI分析（同步版本）
            try:
                result = self._analyze_with_ai_sync(content, user_projects, work_date)
                return result
            except Exception as e:
                logger.warning(f"AI分析失败，使用规则引擎: {str(e)}")
                # Fallback到规则引擎
                return self._analyze_with_rules(content, user_projects, work_date)
        else:
            # 使用规则引擎分析
            return self._analyze_with_rules(content, user_projects, work_date)
