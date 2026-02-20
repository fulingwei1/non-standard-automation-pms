# -*- coding: utf-8 -*-
"""
ECN模块集成/同步 API endpoints

包含：同步到BOM、同步到项目、同步到采购、批量操作
"""

import logging
from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.ecn import EcnTaskCreate
from app.services.ecn_integration import EcnIntegrationService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ecns/{ecn_id}/sync-to-bom", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def sync_ecn_to_bom(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    将ECN变更同步到BOM
    根据受影响物料自动更新BOM
    """
    service = EcnIntegrationService(db)
    try:
        result = service.sync_to_bom(ecn_id)
        return ResponseModel(
            code=200,
            message=f"已同步{result['updated_count']}个物料变更到BOM",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ecns/{ecn_id}/sync-to-project", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def sync_ecn_to_project(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    将ECN变更同步到项目
    更新项目成本和工期
    """
    service = EcnIntegrationService(db)
    try:
        result = service.sync_to_project(ecn_id)
        return ResponseModel(
            code=200,
            message="ECN变更已同步到项目",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ecns/{ecn_id}/sync-to-purchase", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def sync_ecn_to_purchase(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    将ECN变更同步到采购订单
    根据受影响订单自动更新采购订单状态
    """
    service = EcnIntegrationService(db)
    try:
        result = service.sync_to_purchase(ecn_id, current_user.id)
        return ResponseModel(
            code=200,
            message=f"已同步{result['updated_count']}个采购订单变更",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 批量操作 ====================

@router.post("/ecns/batch-sync-to-bom", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_sync_ecns_to_bom(
    *,
    db: Session = Depends(deps.get_db),
    ecn_ids: List[int] = Body(..., description="ECN ID列表"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量同步ECN变更到BOM
    """
    service = EcnIntegrationService(db)
    result = service.batch_sync_to_bom(ecn_ids)
    
    return ResponseModel(
        code=200,
        message=f"批量同步完成：成功{result['success_count']}个，失败{result['fail_count']}个",
        data=result
    )


@router.post("/ecns/batch-sync-to-project", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_sync_ecns_to_project(
    *,
    db: Session = Depends(deps.get_db),
    ecn_ids: List[int] = Body(..., description="ECN ID列表"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量同步ECN变更到项目
    """
    service = EcnIntegrationService(db)
    result = service.batch_sync_to_project(ecn_ids)
    
    return ResponseModel(
        code=200,
        message=f"批量同步完成：成功{result['success_count']}个，失败{result['fail_count']}个",
        data=result
    )


@router.post("/ecns/batch-sync-to-purchase", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_sync_ecns_to_purchase(
    *,
    db: Session = Depends(deps.get_db),
    ecn_ids: List[int] = Body(..., description="ECN ID列表"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量同步ECN变更到采购
    """
    service = EcnIntegrationService(db)
    result = service.batch_sync_to_purchase(ecn_ids, current_user.id)
    
    return ResponseModel(
        code=200,
        message=f"批量同步完成：成功{result['success_count']}个，失败{result['fail_count']}个",
        data=result
    )


@router.post("/ecns/{ecn_id}/batch-create-tasks", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_create_ecn_tasks(
    *,
    db: Session = Depends(deps.get_db),
    ecn_id: int,
    tasks: List[EcnTaskCreate] = Body(..., description="任务列表"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量创建ECN执行任务
    """
    service = EcnIntegrationService(db)
    try:
        result = service.batch_create_tasks(ecn_id, tasks)
        return ResponseModel(
            code=200,
            message=f"批量创建任务成功：共{result['created_count']}个",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
