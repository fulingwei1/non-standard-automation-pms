# -*- coding: utf-8 -*-
"""
工作日志AI分析服务统一导出

通过多重继承组合所有功能模块
"""

import asyncio
from datetime import date
from typing import Any, Dict

from sqlalchemy.orm import Session

from .ai_analysis import AIAnalysisMixin
from .core import WorkLogAICore
from .project_matching import ProjectMatchingMixin
from .rule_engine import RuleEngineMixin


class WorkLogAIService(
    WorkLogAICore,
    ProjectMatchingMixin,
    AIAnalysisMixin,
    RuleEngineMixin,
):
    """工作日志AI分析服务（组合所有功能模块）"""

    def __init__(self, db: Session):
        WorkLogAICore.__init__(self, db)


# 便捷函数
def analyze_work_log_content(
    db: Session,
    content: str,
    user_id: int,
    work_date: date
) -> Dict[str, Any]:
    """
    分析工作日志内容的便捷函数

    Args:
        db: 数据库会话
        content: 工作日志内容
        user_id: 用户ID
        work_date: 工作日期

    Returns:
        分析结果
    """
    service = WorkLogAIService(db)

    # 如果是异步环境，使用await
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果事件循环正在运行，使用同步方式（规则引擎）
            return service._analyze_with_rules(
                content,
                service._get_user_projects(user_id),
                work_date
            )
        else:
            # 如果事件循环未运行，可以创建新的
            return loop.run_until_complete(
                service.analyze_work_log(content, user_id, work_date)
            )
    except RuntimeError:
        # 没有事件循环，使用同步方式（规则引擎）
        return service._analyze_with_rules(
            content,
            service._get_user_projects(user_id),
            work_date
        )


__all__ = ["WorkLogAIService", "analyze_work_log_content"]
