# -*- coding: utf-8 -*-
"""
用户同步端点

包含员工同步、账号创建、激活状态管理、密码重置
"""

import logging
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.organization import Employee
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.permission_audit_service import PermissionAuditService
from app.services.user_sync_service import UserSyncService
from app.utils.db_helpers import get_or_404, save_obj, delete_obj

from .models import BatchToggleActiveRequest, SyncEmployeesRequest, ToggleActiveRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/sync-from-employees", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def sync_users_from_employees(
    *,
    db: Session = Depends(deps.get_db),
    sync_request: SyncEmployeesRequest = Body(default=SyncEmployeesRequest()),
    current_user: User = Depends(security.require_permission("system:user:create")),
) -> Any:
    """批量同步员工到用户表"""
    result = UserSyncService.sync_all_employees(
        db=db,
        only_active=sync_request.only_active,
        auto_activate=sync_request.auto_activate,
        department_filter=sync_request.department_filter,
    )

    return ResponseModel(
        code=200,
        message=f"同步完成：创建 {result['created']} 个账号，跳过 {result['skipped']} 个",
        data=result
    )


@router.post("/create-from-employee/{employee_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def create_user_from_employee(
    *,
    db: Session = Depends(deps.get_db),
    employee_id: int,
    auto_activate: bool = Query(False, description="是否自动激活"),
    current_user: User = Depends(security.require_permission("system:user:create")),
) -> Any:
    """从单个员工创建用户账号"""
    employee = get_or_404(db, Employee, employee_id, "员工不存在")

    existing_usernames = set(u.username for u in db.query(User.username).all())

    user, password = UserSyncService.create_user_from_employee(
        db=db,
        employee=employee,
        existing_usernames=existing_usernames,
        auto_activate=auto_activate,
    )

    if not user:
        raise HTTPException(status_code=400, detail=password)

    db.commit()

    return ResponseModel(
        code=200,
        message="用户创建成功",
        data={
            "user_id": user.id,
            "username": user.username,
            "initial_password": password,
            "is_active": user.is_active,
        }
    )


@router.put("/{user_id}/toggle-active", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def toggle_user_active(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    toggle_request: ToggleActiveRequest,
    request: Request,
    current_user: User = Depends(security.require_permission("system:user:update")),
) -> Any:
    """切换用户激活状态"""
    target_active = toggle_request.is_active
    if target_active is None:
        user = get_or_404(db, User, user_id, "用户不存在")
        target_active = not bool(user.is_active)

    success, message = UserSyncService.toggle_user_active(
        db=db, user_id=user_id, is_active=target_active,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    try:
        action = PermissionAuditService.ACTION_USER_ACTIVATED if target_active else PermissionAuditService.ACTION_USER_DEACTIVATED
        PermissionAuditService.log_user_operation(
            db=db, operator_id=current_user.id, user_id=user_id, action=action,
            changes={"is_active": target_active},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    except Exception:
        logger.warning("审计日志记录失败，不影响主流程", exc_info=True)

    return ResponseModel(code=200, message=message)


@router.put("/{user_id}/reset-password", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def reset_user_password(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    request: Request,
    current_user: User = Depends(security.require_permission("system:user:update")),
) -> Any:
    """重置用户密码为初始密码"""
    success, result = UserSyncService.reset_user_password(db=db, user_id=user_id)

    if not success:
        raise HTTPException(status_code=400, detail=result)

    try:
        PermissionAuditService.log_user_operation(
            db=db, operator_id=current_user.id, user_id=user_id, action="PASSWORD_RESET",
            changes={"password": "重置为初始密码"},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    except Exception:
        logger.warning("审计日志记录失败，不影响主流程", exc_info=True)

    return ResponseModel(code=200, message="密码重置成功", data={"new_password": result})


@router.post("/batch-toggle-active", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_toggle_user_active(
    *,
    db: Session = Depends(deps.get_db),
    batch_request: BatchToggleActiveRequest,
    request: Request,
    current_user: User = Depends(security.require_permission("system:user:update")),
) -> Any:
    """批量切换用户激活状态"""
    result = UserSyncService.batch_toggle_active(
        db=db, user_ids=batch_request.user_ids, is_active=batch_request.is_active
    )

    try:
        action = PermissionAuditService.ACTION_USER_ACTIVATED if batch_request.is_active else PermissionAuditService.ACTION_USER_DEACTIVATED
        for user_id in batch_request.user_ids:
            PermissionAuditService.log_user_operation(
                db=db, operator_id=current_user.id, user_id=user_id, action=action,
                changes={"is_active": batch_request.is_active, "batch": True},
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent")
            )
    except Exception:
        logger.warning("审计日志记录失败，不影响主流程", exc_info=True)

    status_text = "激活" if batch_request.is_active else "禁用"
    return ResponseModel(
        code=200,
        message=f"批量{status_text}完成：成功 {result['success']} 个，失败 {result['failed']} 个",
        data=result
    )
