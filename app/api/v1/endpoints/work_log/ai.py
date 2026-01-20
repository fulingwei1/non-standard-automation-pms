# -*- coding: utf-8 -*-
"""
工作日志AI分析端点
"""

import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.work_log_ai import WorkLogAIService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/work-logs/ai-analyze", response_model=ResponseModel)
def analyze_work_log_with_ai(
    *,
    db: Session = Depends(deps.get_db),
    content: str = Body(..., description="工作日志内容"),
    work_date: date = Body(..., description="工作日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    AI分析工作日志内容，自动提取工作项、工时和项目关联

    返回分析结果，包括：
    - work_items: 工作项列表（每个包含工作内容、工时、项目ID等）
    - suggested_projects: 建议的项目列表
    - total_hours: 总工时
    - confidence: 置信度
    """
    try:
        service = WorkLogAIService(db)

        # 使用AI服务分析（同步调用）
        result = service.analyze_work_log(content, current_user.id, work_date)

        return ResponseModel(
            code=200,
            message="分析完成",
            data=result
        )
    except Exception as e:
        logger.error(f"AI分析失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"分析工作日志失败: {str(e)}")


@router.get("/work-logs/suggested-projects", response_model=ResponseModel)
def get_suggested_projects(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取用户参与的项目列表（用于智能推荐）

    返回用户参与的项目，按历史填报频率排序
    """
    try:
        service = WorkLogAIService(db)
        projects = service.get_user_projects_for_suggestion(current_user.id)

        return ResponseModel(
            code=200,
            message="success",
            data={
                "projects": projects,
                "total": len(projects)
            }
        )
    except Exception as e:
        logger.error(f"获取建议项目失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取建议项目失败: {str(e)}")
