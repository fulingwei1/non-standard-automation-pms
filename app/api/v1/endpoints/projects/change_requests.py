# -*- coding: utf-8 -*-
"""
项目变更管理端点
"""

from typing import Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.schemas import list_response, success_response
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.user import User
from app.models.enums import (
    ChangeStatusEnum,
    ChangeTypeEnum,
    ChangeSourceEnum,
)
from app.schemas.change_request import (
    ChangeRequestCreate,
    ChangeRequestUpdate,
    ChangeRequestResponse,
    ChangeRequestListResponse,
    ChangeApprovalRequest,
    ChangeApprovalRecordResponse,
    ChangeStatusUpdateRequest,
    ChangeImplementationRequest,
    ChangeVerificationRequest,
    ChangeCloseRequest,
)
from app.services.project_change_requests import ProjectChangeRequestsService

router = APIRouter()


@router.post("/")
def create_change_request(
    *,
    db: Session = Depends(deps.get_db),
    change_in: ChangeRequestCreate,
    current_user: User = Depends(security.require_permission("change:create")),
) -> Any:
    """提交变更请求"""
    service = ProjectChangeRequestsService(db)
    change_request = service.create_change_request(change_in, current_user)
    
    response = ChangeRequestResponse.model_validate(change_request)
    return success_response(data=response, message="变更请求提交成功")


@router.get("/")
def list_change_requests(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    project_id: Optional[int] = Query(None, description="项目ID"),
    change_type: Optional[ChangeTypeEnum] = Query(None, description="变更类型"),
    change_source: Optional[ChangeSourceEnum] = Query(None, description="变更来源"),
    status: Optional[ChangeStatusEnum] = Query(None, description="状态"),
    submitter_id: Optional[int] = Query(None, description="提交人ID"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(security.require_permission("change:read")),
) -> Any:
    """获取变更请求列表"""
    service = ProjectChangeRequestsService(db)
    changes = service.list_change_requests(
        offset=pagination.offset,
        limit=pagination.limit,
        project_id=project_id,
        change_type=change_type,
        change_source=change_source,
        status=status,
        submitter_id=submitter_id,
        search=search,
    )
    
    # 转换为响应模型
    change_responses = [ChangeRequestListResponse.model_validate(c) for c in changes]
    
    return list_response(items=change_responses, message="获取变更请求列表成功")


@router.get("/{change_id}")
def get_change_request(
    change_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("change:read")),
) -> Any:
    """获取变更请求详情"""
    service = ProjectChangeRequestsService(db)
    change_request = service.get_change_request(change_id)
    
    response = ChangeRequestResponse.model_validate(change_request)
    return success_response(data=response, message="获取变更请求详情成功")


@router.put("/{change_id}")
def update_change_request(
    *,
    change_id: int,
    db: Session = Depends(deps.get_db),
    change_in: ChangeRequestUpdate,
    current_user: User = Depends(security.require_permission("change:update")),
) -> Any:
    """更新变更请求"""
    service = ProjectChangeRequestsService(db)
    change_request = service.update_change_request(change_id, change_in)
    
    response = ChangeRequestResponse.model_validate(change_request)
    return success_response(data=response, message="变更请求更新成功")


@router.post("/{change_id}/approve")
def approve_change_request(
    *,
    change_id: int,
    db: Session = Depends(deps.get_db),
    approval_in: ChangeApprovalRequest,
    current_user: User = Depends(security.require_permission("change:approve")),
) -> Any:
    """审批变更请求"""
    service = ProjectChangeRequestsService(db)
    change_request = service.approve_change_request(change_id, approval_in, current_user)
    
    response = ChangeRequestResponse.model_validate(change_request)
    return success_response(data=response, message="审批完成")


@router.get("/{change_id}/approvals")
def get_approval_records(
    change_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("change:read")),
) -> Any:
    """获取审批记录"""
    service = ProjectChangeRequestsService(db)
    records = service.get_approval_records(change_id)
    
    record_responses = [ChangeApprovalRecordResponse.model_validate(r) for r in records]
    return list_response(items=record_responses, message="获取审批记录成功")


@router.post("/{change_id}/status")
def update_change_status(
    *,
    change_id: int,
    db: Session = Depends(deps.get_db),
    status_in: ChangeStatusUpdateRequest,
    current_user: User = Depends(security.require_permission("change:update")),
) -> Any:
    """更新变更状态"""
    service = ProjectChangeRequestsService(db)
    change_request, old_status = service.update_change_status(change_id, status_in)
    
    response = ChangeRequestResponse.model_validate(change_request)
    return success_response(
        data=response,
        message=f"状态已从 {old_status} 更新为 {status_in.new_status.value}"
    )


@router.post("/{change_id}/implement")
def update_implementation_info(
    *,
    change_id: int,
    db: Session = Depends(deps.get_db),
    impl_in: ChangeImplementationRequest,
    current_user: User = Depends(security.require_permission("change:update")),
) -> Any:
    """更新实施信息"""
    service = ProjectChangeRequestsService(db)
    change_request = service.update_implementation_info(change_id, impl_in)
    
    response = ChangeRequestResponse.model_validate(change_request)
    return success_response(data=response, message="实施信息更新成功")


@router.post("/{change_id}/verify")
def verify_change_request(
    *,
    change_id: int,
    db: Session = Depends(deps.get_db),
    verify_in: ChangeVerificationRequest,
    current_user: User = Depends(security.require_permission("change:verify")),
) -> Any:
    """验证变更"""
    service = ProjectChangeRequestsService(db)
    change_request = service.verify_change_request(change_id, verify_in, current_user)
    
    response = ChangeRequestResponse.model_validate(change_request)
    return success_response(data=response, message="变更验证完成")


@router.post("/{change_id}/close")
def close_change_request(
    *,
    change_id: int,
    db: Session = Depends(deps.get_db),
    close_in: ChangeCloseRequest,
    current_user: User = Depends(security.require_permission("change:close")),
) -> Any:
    """关闭变更"""
    service = ProjectChangeRequestsService(db)
    change_request = service.close_change_request(change_id, close_in)
    
    response = ChangeRequestResponse.model_validate(change_request)
    return success_response(data=response, message="变更已关闭")


@router.get("/statistics/summary")
def get_change_statistics(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    current_user: User = Depends(security.require_permission("change:read")),
) -> Any:
    """获取变更统计信息"""
    service = ProjectChangeRequestsService(db)
    statistics = service.get_statistics(
        project_id=project_id,
        start_date=start_date,
        end_date=end_date,
    )
    
    return success_response(data=statistics, message="获取统计信息成功")
