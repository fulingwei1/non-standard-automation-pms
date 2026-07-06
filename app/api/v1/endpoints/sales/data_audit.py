# -*- coding: utf-8 -*-
"""
销售数据审核 API

提供数据变更审核的接口，包括：
- 提交审核请求
- 获取待审核列表
- 审核通过/驳回
- 撤销审核请求
- 查询审核历史
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.sales.data_audit import (
    DataAuditPriorityEnum,
    DataChangeType,
    SalesDataAuditRequest,
)
from app.models.sales.operation_log import SalesOperationType
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.services.sales.data_audit_service import SalesDataAuditService
from app.services.sales.operation_log_service import SalesOperationLogService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-audit", tags=["销售数据审核"])


# ==================== 请求模型 ====================


class SubmitAuditRequest(BaseModel):
    """提交审核请求"""

    entity_type: str = Field(..., description="实体类型：OPPORTUNITY/CONTRACT/CUSTOMER/QUOTE")
    entity_id: int = Field(..., description="实体ID")
    entity_code: Optional[str] = Field(None, description="实体编码")
    old_value: Dict[str, Any] = Field(..., description="变更前值")
    new_value: Dict[str, Any] = Field(..., description="变更后值")
    change_type: str = Field(
        DataChangeType.FIELD_UPDATE, description="变更类型"
    )
    change_reason: Optional[str] = Field(None, description="变更原因")
    priority: str = Field(
        DataAuditPriorityEnum.NORMAL.value, description="优先级：LOW/NORMAL/HIGH/URGENT"
    )


class ReviewActionRequest(BaseModel):
    """审核操作请求"""

    action: str = Field(..., description="操作类型：approve/reject")
    comment: Optional[str] = Field(None, description="审核意见（驳回时必填）")
    apply_immediately: bool = Field(True, description="审核通过后是否立即应用变更")


class CancelAuditRequest(BaseModel):
    """撤销审核请求"""

    reason: Optional[str] = Field(None, description="撤销原因")


# ==================== 响应模型 ====================


class AuditRequestResponse(BaseModel):
    """审核请求响应"""

    id: int
    entity_type: str
    entity_id: int
    entity_code: Optional[str] = None
    change_type: str
    change_reason: Optional[str] = None
    old_value: Dict[str, Any]
    new_value: Dict[str, Any]
    changed_fields: Optional[List[str]] = None
    status: str
    priority: str
    requester_id: int
    requester_name: Optional[str] = None
    requester_dept: Optional[str] = None
    requested_at: datetime
    reviewer_id: Optional[int] = None
    reviewer_name: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_comment: Optional[str] = None
    applied_at: Optional[datetime] = None

    class Config:
        from_attributes = True


def _audit_request_operation_value(audit_request: SalesDataAuditRequest) -> dict[str, Any]:
    return {
        "audit_request_id": audit_request.id,
        "audit_status": audit_request.status,
        "entity_type": audit_request.entity_type,
        "entity_id": audit_request.entity_id,
        "entity_code": audit_request.entity_code,
        "change_type": audit_request.change_type,
        "change_reason": audit_request.change_reason,
        "priority": audit_request.priority,
        "changed_fields": audit_request.changed_fields or [],
        "requested_change": audit_request.new_value,
        "original_value": audit_request.old_value,
        "requester_id": audit_request.requester_id,
        "reviewer_id": audit_request.reviewer_id,
        "review_comment": audit_request.review_comment,
        "applied_at": audit_request.applied_at.isoformat() if audit_request.applied_at else None,
    }


def _log_data_audit_operation(
    db: Session,
    audit_request: SalesDataAuditRequest,
    operation_type: str,
    operator: User,
    *,
    old_status: str | None = None,
    operation_desc: str,
    remark: str | None = None,
) -> None:
    new_value = _audit_request_operation_value(audit_request)
    old_value = (
        {
            **new_value,
            "audit_status": old_status,
            "reviewer_id": None,
            "review_comment": None,
            "applied_at": None,
        }
        if old_status
        else {}
    )
    changed_fields = (
        ["audit_status"]
        if old_status and old_status != audit_request.status
        else audit_request.changed_fields or []
    )
    SalesOperationLogService.log_operation(
        db,
        entity_type=audit_request.entity_type,
        entity_id=audit_request.entity_id,
        operation_type=operation_type,
        operator=operator,
        entity_code=audit_request.entity_code,
        operation_desc=operation_desc,
        old_value=old_value,
        new_value=new_value,
        changed_fields=changed_fields,
        remark=remark or audit_request.change_reason,
    )


# ==================== API 端点 ====================


@router.post("/submit", response_model=ResponseModel)
def submit_audit_request(
    *,
    db: Session = Depends(deps.get_db),
    request: SubmitAuditRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交数据审核请求

    当修改敏感字段（如金额、负责人等）时，需要提交审核请求。
    审核通过后变更才会生效。
    """
    service = SalesDataAuditService(db)

    try:
        audit_request = service.submit_audit_request(
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            old_value=request.old_value,
            new_value=request.new_value,
            requester=current_user,
            entity_code=request.entity_code,
            change_type=request.change_type,
            change_reason=request.change_reason,
            priority=request.priority,
        )
        _log_data_audit_operation(
            db,
            audit_request,
            SalesOperationType.SUBMIT,
            current_user,
            operation_desc="提交销售数据审核",
            remark=request.change_reason,
        )

        db.commit()

        return ResponseModel(
            code=200,
            message="审核请求已提交",
            data={
                "request_id": audit_request.id,
                "entity_type": audit_request.entity_type,
                "entity_id": audit_request.entity_id,
                "status": audit_request.status,
            },
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pending", response_model=PaginatedResponse[AuditRequestResponse])
def get_pending_requests(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    entity_type: Optional[str] = Query(None, description="实体类型筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    current_user: User = Depends(security.require_permission("sales:data_audit:review")),
) -> Any:
    """
    获取待审核请求列表

    返回所有待审核的数据变更请求，按优先级和时间排序。
    """
    service = SalesDataAuditService(db)

    requests, total = service.get_pending_requests(
        entity_type=entity_type,
        priority=priority,
        skip=pagination.offset,
        limit=pagination.limit,
    )

    items = []
    for req in requests:
        item = AuditRequestResponse(
            id=req.id,
            entity_type=req.entity_type,
            entity_id=req.entity_id,
            entity_code=req.entity_code,
            change_type=req.change_type,
            change_reason=req.change_reason,
            old_value=req.old_value,
            new_value=req.new_value,
            changed_fields=req.changed_fields,
            status=req.status,
            priority=req.priority,
            requester_id=req.requester_id,
            requester_name=req.requester.real_name if req.requester else None,
            requester_dept=req.requester_dept,
            requested_at=req.requested_at,
        )
        items.append(item)

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )


@router.post("/{request_id}/review", response_model=ResponseModel)
def review_audit_request(
    request_id: int,
    *,
    db: Session = Depends(deps.get_db),
    request: ReviewActionRequest,
    current_user: User = Depends(security.require_permission("sales:data_audit:review")),
) -> Any:
    """
    审核请求

    对数据变更请求进行审核通过或驳回操作。
    """
    service = SalesDataAuditService(db)

    try:
        old_status = service.get_request_detail(request_id).status
        if request.action == "approve":
            audit_request = service.approve_request(
                request_id=request_id,
                reviewer=current_user,
                comment=request.comment,
                apply_immediately=request.apply_immediately,
            )
            message = "审核通过"
            operation_type = SalesOperationType.APPROVE
            operation_desc = "通过销售数据审核"
        elif request.action == "reject":
            if not request.comment:
                raise HTTPException(status_code=400, detail="驳回时必须填写原因")
            audit_request = service.reject_request(
                request_id=request_id,
                reviewer=current_user,
                comment=request.comment,
            )
            message = "审核驳回"
            operation_type = SalesOperationType.REJECT
            operation_desc = "驳回销售数据审核"
        else:
            raise HTTPException(status_code=400, detail=f"不支持的操作: {request.action}")

        _log_data_audit_operation(
            db,
            audit_request,
            operation_type,
            current_user,
            old_status=old_status,
            operation_desc=operation_desc,
            remark=request.comment,
        )
        db.commit()

        return ResponseModel(
            code=200,
            message=message,
            data={
                "request_id": audit_request.id,
                "status": audit_request.status,
                "applied": audit_request.applied_at is not None,
            },
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{request_id}/cancel", response_model=ResponseModel)
def cancel_audit_request(
    request_id: int,
    *,
    db: Session = Depends(deps.get_db),
    request: CancelAuditRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    撤销审核请求

    申请人可以撤销自己提交的待审核请求。
    """
    service = SalesDataAuditService(db)

    try:
        old_status = service.get_request_detail(request_id).status
        audit_request = service.cancel_request(
            request_id=request_id,
            user=current_user,
            reason=request.reason,
        )
        _log_data_audit_operation(
            db,
            audit_request,
            SalesOperationType.STATUS_CHANGE,
            current_user,
            old_status=old_status,
            operation_desc="撤销销售数据审核",
            remark=request.reason,
        )

        db.commit()

        return ResponseModel(
            code=200,
            message="审核请求已撤销",
            data={"request_id": audit_request.id, "status": audit_request.status},
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{request_id}", response_model=ResponseModel)
def get_audit_request_detail(
    request_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取审核请求详情
    """
    service = SalesDataAuditService(db)

    try:
        req = service.get_request_detail(request_id)

        return ResponseModel(
            code=200,
            message="success",
            data=AuditRequestResponse(
                id=req.id,
                entity_type=req.entity_type,
                entity_id=req.entity_id,
                entity_code=req.entity_code,
                change_type=req.change_type,
                change_reason=req.change_reason,
                old_value=req.old_value,
                new_value=req.new_value,
                changed_fields=req.changed_fields,
                status=req.status,
                priority=req.priority,
                requester_id=req.requester_id,
                requester_name=req.requester.real_name if req.requester else None,
                requester_dept=req.requester_dept,
                requested_at=req.requested_at,
                reviewer_id=req.reviewer_id,
                reviewer_name=req.reviewer.real_name if req.reviewer else None,
                reviewed_at=req.reviewed_at,
                review_comment=req.review_comment,
                applied_at=req.applied_at,
            ).model_dump(),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/history/{entity_type}/{entity_id}", response_model=PaginatedResponse[AuditRequestResponse])
def get_entity_audit_history(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取实体的审核历史

    查看指定实体的所有审核请求记录。
    """
    service = SalesDataAuditService(db)

    requests, total = service.get_entity_audit_history(
        entity_type=entity_type,
        entity_id=entity_id,
        skip=pagination.offset,
        limit=pagination.limit,
    )

    items = []
    for req in requests:
        item = AuditRequestResponse(
            id=req.id,
            entity_type=req.entity_type,
            entity_id=req.entity_id,
            entity_code=req.entity_code,
            change_type=req.change_type,
            change_reason=req.change_reason,
            old_value=req.old_value,
            new_value=req.new_value,
            changed_fields=req.changed_fields,
            status=req.status,
            priority=req.priority,
            requester_id=req.requester_id,
            requester_name=req.requester.real_name if req.requester else None,
            requester_dept=req.requester_dept,
            requested_at=req.requested_at,
            reviewer_id=req.reviewer_id,
            reviewer_name=req.reviewer.real_name if req.reviewer else None,
            reviewed_at=req.reviewed_at,
            review_comment=req.review_comment,
            applied_at=req.applied_at,
        )
        items.append(item)

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )


@router.get("/check-required", response_model=ResponseModel)
def check_audit_required(
    entity_type: str = Query(..., description="实体类型"),
    changed_fields: str = Query(..., description="变更字段列表，逗号分隔"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    检查变更是否需要审核

    前端在提交变更前调用此接口，判断是否需要走审核流程。
    """
    service = SalesDataAuditService(db)

    fields = [f.strip() for f in changed_fields.split(",") if f.strip()]
    requires_audit = service.requires_audit(entity_type, fields)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "requires_audit": requires_audit,
            "entity_type": entity_type,
            "changed_fields": fields,
        },
    )
