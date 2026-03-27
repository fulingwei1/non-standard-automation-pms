# -*- coding: utf-8 -*-
"""
项目物料进度可视化端点

端点:
  GET  /{project_id}/material-progress           项目物料进度总览
  GET  /{project_id}/bom-progress                BOM 物料明细进度
  GET  /{project_id}/shortage-tracker            缺料跟踪看板
  POST /{project_id}/material-progress/subscribe 订阅物料进度通知
  GET  /{project_id}/material-progress/subscribe 查看订阅状态
  DELETE /{project_id}/material-progress/subscribe 取消订阅
"""

from typing import Any

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.material_progress import (
    BomProgressResponse,
    MaterialProgressOverview,
    MaterialProgressSubscribeRequest,
    MaterialProgressSubscription,
    ShortageTrackerResponse,
)
from app.services import material_progress_service

router = APIRouter()


@router.get(
    "/material-progress",
    response_model=ResponseModel[MaterialProgressOverview],
    status_code=status.HTTP_200_OK,
    summary="项目物料进度总览",
)
def get_material_progress(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int = Path(..., description="项目ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目整体物料进度，包括齐套率、关键物料、趋势和预计齐套日期。
    """
    data = material_progress_service.get_material_progress_overview(
        db, project_id, current_user
    )
    return ResponseModel(code=200, message="success", data=data)


@router.get(
    "/bom-progress",
    response_model=ResponseModel[BomProgressResponse],
    status_code=status.HTTP_200_OK,
    summary="BOM 物料明细进度",
)
def get_bom_progress(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int = Path(..., description="项目ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取每个 BOM 的齐套状态和每个物料行的进度明细。
    """
    data = material_progress_service.get_bom_progress(db, project_id, current_user)
    return ResponseModel(code=200, message="success", data=data)


@router.get(
    "/shortage-tracker",
    response_model=ResponseModel[ShortageTrackerResponse],
    status_code=status.HTTP_200_OK,
    summary="缺料跟踪看板",
)
def get_shortage_tracker(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int = Path(..., description="项目ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    缺料清单、处理进度、影响天数和责任人跟踪。
    """
    data = material_progress_service.get_shortage_tracker(db, project_id, current_user)
    return ResponseModel(code=200, message="success", data=data)


@router.post(
    "/material-progress/subscribe",
    response_model=ResponseModel[MaterialProgressSubscription],
    status_code=status.HTTP_200_OK,
    summary="订阅物料进度通知",
)
def subscribe_material_progress(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int = Path(..., description="项目ID"),
    body: MaterialProgressSubscribeRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    订阅/更新物料进度通知。支持齐套率变化、关键物料到货、缺料预警。
    """
    sub = material_progress_service.subscribe_material_progress(
        db, project_id, current_user, body.model_dump()
    )
    return ResponseModel(code=200, message="订阅成功", data=sub)


@router.get(
    "/material-progress/subscribe",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="查看物料进度订阅状态",
)
def get_subscription_status(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int = Path(..., description="项目ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """查看当前用户对该项目的物料进度订阅状态。"""
    sub = material_progress_service.get_subscription(db, project_id, current_user)
    if sub:
        return ResponseModel(code=200, message="success", data={
            "subscribed": True,
            "notify_kitting_change": sub.notify_kitting_change,
            "notify_key_material_arrival": sub.notify_key_material_arrival,
            "notify_shortage_alert": sub.notify_shortage_alert,
            "kitting_change_threshold": float(sub.kitting_change_threshold or 5),
        })
    return ResponseModel(code=200, message="success", data={"subscribed": False})


@router.delete(
    "/material-progress/subscribe",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="取消订阅物料进度通知",
)
def unsubscribe_material_progress(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int = Path(..., description="项目ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """取消订阅物料进度通知。"""
    result = material_progress_service.unsubscribe_material_progress(
        db, project_id, current_user
    )
    if result:
        return ResponseModel(code=200, message="已取消订阅")
    return ResponseModel(code=200, message="未找到订阅记录")
