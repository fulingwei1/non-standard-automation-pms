# -*- coding: utf-8 -*-
"""
工作日志详情操作端点
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.models.work_log import WorkLog
from app.schemas.common import ResponseModel
from app.schemas.work_log import (
    MentionResponse,
    WorkLogResponse,
    WorkLogUpdate,
)
from app.services.work_log_service import WorkLogService

router = APIRouter()


@router.get("/work-logs/{work_log_id}", response_model=ResponseModel[WorkLogResponse])
def get_work_log(
    *,
    db: Session = Depends(deps.get_db),
    work_log_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取单个工作日志详情
    """
    work_log = db.query(WorkLog).filter(WorkLog.id == work_log_id).first()
    if not work_log:
        raise HTTPException(status_code=404, detail="工作日志不存在")

    # 权限控制：只能查看自己的工作日志，除非是管理员
    if not current_user.is_superuser and work_log.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此工作日志")

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
        code=200,
        message="success",
        data=response
    )


@router.put("/work-logs/{work_log_id}", response_model=ResponseModel[WorkLogResponse])
def update_work_log(
    *,
    db: Session = Depends(deps.get_db),
    work_log_id: int,
    work_log_in: WorkLogUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新工作日志（仅限草稿状态）
    """
    try:
        service = WorkLogService(db)
        work_log = service.update_work_log(work_log_id, current_user.id, work_log_in)

        # 重新加载提及
        db.refresh(work_log)

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
            code=200,
            message="工作日志更新成功",
            data=response
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新工作日志失败: {str(e)}")


@router.delete("/work-logs/{work_log_id}", response_model=ResponseModel)
def delete_work_log(
    *,
    db: Session = Depends(deps.get_db),
    work_log_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除工作日志（仅限草稿状态）
    """
    work_log = db.query(WorkLog).filter(WorkLog.id == work_log_id).first()
    if not work_log:
        raise HTTPException(status_code=404, detail="工作日志不存在")

    # 权限控制：只能删除自己的工作日志
    if work_log.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能删除自己的工作日志")

    # 只能删除草稿状态的日志
    if work_log.status != 'DRAFT':
        raise HTTPException(status_code=400, detail="只能删除草稿状态的工作日志")

    db.delete(work_log)
    db.commit()

    return ResponseModel(
        code=200,
        message="工作日志删除成功"
    )
