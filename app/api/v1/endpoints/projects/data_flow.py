# -*- coding: utf-8 -*-
"""项目全链路数据流通端点。"""

from typing import Any, Callable, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.project_data_flow_service import get_project_data_flow_service
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


def _build_response(operation: Callable[[], Dict[str, Any]], message: str) -> ResponseModel:
    result = operation()
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])

    return ResponseModel(code=200, message=message, data=result)


@router.post("/wbs-work-orders", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def create_work_orders_from_wbs(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """从项目 WBS 任务生成生产工单。"""
    check_project_access_or_raise(db, current_user, project_id)
    service = get_project_data_flow_service(db)
    return _build_response(
        lambda: service.create_work_orders_from_wbs(project_id),
        "WBS 已生成生产工单",
    )


@router.post("/bom-purchase-requests", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def create_purchase_requests_from_bom(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """从项目 BOM 生成采购申请。"""
    check_project_access_or_raise(db, current_user, project_id)
    service = get_project_data_flow_service(db)
    return _build_response(
        lambda: service.create_purchase_requests_from_bom(project_id),
        "BOM 已生成采购申请",
    )


@router.post("/delivery-schedule", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def create_delivery_schedule_from_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """从项目里程碑生成交付排产计划。"""
    check_project_access_or_raise(db, current_user, project_id)
    service = get_project_data_flow_service(db)
    return _build_response(
        lambda: service.create_delivery_schedule_from_project(
            project_id,
            initiator_id=current_user.id,
        ),
        "里程碑已生成交付排产计划",
    )


@router.post("/after-sales", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def transfer_to_after_sales(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """项目验收后转入售后服务。"""
    check_project_access_or_raise(db, current_user, project_id)
    service = get_project_data_flow_service(db)
    return _build_response(
        lambda: service.transfer_to_after_sales(project_id),
        "项目已转入售后服务",
    )
