# -*- coding: utf-8 -*-
"""
工作日志基础操作端点
"""

import logging
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.work_log import WorkLog
from app.schemas.common import ResponseModel
from app.schemas.work_log import (
    MentionOptionsResponse,
    MentionResponse,
    WorkLogCreate,
    WorkLogListResponse,
    WorkLogResponse,
)
from app.services.work_log_service import WorkLogService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/work-logs", response_model=ResponseModel[WorkLogResponse], status_code=status.HTTP_201_CREATED)
def create_work_log(
    *,
    db: Session = Depends(deps.get_db),
    work_log_in: WorkLogCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建工作日志
    """
    try:
        service = WorkLogService(db)
        work_log = service.create_work_log(current_user.id, work_log_in)

        # 构建响应
        mentions = []
        for mention in work_log.mentions:
            mentions.append(MentionResponse(
                id=mention.id,
                mention_type=mention.mention_type,
                mention_id=mention.mention_id,
                mention_name=mention.mention_name
            ))

        response = WorkLogResponse(
            id=work_log.id,
            user_id=work_log.user_id,
            user_name=work_log.user_name,
            work_date=work_log.work_date,
            content=work_log.content,
            status=work_log.status,
            mentions=mentions,
            created_at=work_log.created_at,
            updated_at=work_log.updated_at
        )

        return ResponseModel(
            code=201,
            message="工作日志创建成功",
            data=response
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建工作日志失败: {str(e)}")


@router.get("/work-logs", response_model=ResponseModel[WorkLogListResponse])
def get_work_logs(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工作日志列表
    """
    query = db.query(WorkLog)

    # 权限控制：普通用户只能查看自己的工作日志，管理员可以查看所有
    if not current_user.is_superuser:
        query = query.filter(WorkLog.user_id == current_user.id)
    elif user_id:
        query = query.filter(WorkLog.user_id == user_id)

    # 日期范围筛选
    if start_date:
        query = query.filter(WorkLog.work_date >= start_date)
    if end_date:
        query = query.filter(WorkLog.work_date <= end_date)

    # 状态筛选
    if status:
        query = query.filter(WorkLog.status == status)

    # 总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    work_logs = query.order_by(desc(WorkLog.work_date), desc(WorkLog.created_at)).offset(offset).limit(page_size).all()

    # 构建响应
    items = []
    for work_log in work_logs:
        mentions = []
        for mention in work_log.mentions:
            mentions.append(MentionResponse(
                id=mention.id,
                mention_type=mention.mention_type,
                mention_id=mention.mention_id,
                mention_name=mention.mention_name
            ))

        items.append(WorkLogResponse(
            id=work_log.id,
            user_id=work_log.user_id,
            user_name=work_log.user_name,
            work_date=work_log.work_date,
            content=work_log.content,
            status=work_log.status,
            mentions=mentions,
            timesheet_id=work_log.timesheet_id,
            created_at=work_log.created_at,
            updated_at=work_log.updated_at
        ))

    return ResponseModel(
        code=200,
        message="success",
        data=WorkLogListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )
    )


@router.get("/work-logs/mentions/options", response_model=ResponseModel[MentionOptionsResponse])
def get_mention_options(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取可@的项目/设备/人员列表（用于下拉选择）
    """
    service = WorkLogService(db)
    options = service.get_mention_options(current_user.id)

    return ResponseModel(
        code=200,
        message="success",
        data=options
    )
