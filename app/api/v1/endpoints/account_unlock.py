# -*- coding: utf-8 -*-
"""Account lockout administration endpoints."""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.account_lockout_service import AccountLockoutService

router = APIRouter()


class AccountUnlockRequest(BaseModel):
    """Manual account unlock request."""

    reason: Optional[str] = Field(default=None, description="解锁原因")


def _ensure_super_admin(current_user: User) -> None:
    if not getattr(current_user, "is_superuser", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要超级管理员权限")


@router.get("/locked-accounts", response_model=ResponseModel[list[dict]])
def list_locked_accounts(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_super_admin),
) -> ResponseModel[list[dict]]:
    """List currently locked accounts."""

    _ensure_super_admin(current_user)
    accounts = AccountLockoutService.get_locked_accounts(db)
    return ResponseModel(code=200, message="获取锁定账号成功", data=accounts)


@router.get("/{username}/status", response_model=ResponseModel[dict])
def get_account_lockout_status(
    *,
    username: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_super_admin),
) -> ResponseModel[dict]:
    """Get lockout status for one account."""

    _ensure_super_admin(current_user)
    result = AccountLockoutService.check_lockout(username, db)
    return ResponseModel(code=200, message="获取账号锁定状态成功", data=result)


@router.get("/{username}/history", response_model=ResponseModel[list[dict]])
def get_account_login_history(
    *,
    username: str,
    limit: int = Query(50, ge=1, le=200, description="返回记录数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_super_admin),
) -> ResponseModel[list[dict]]:
    """Get account login history."""

    _ensure_super_admin(current_user)
    history = AccountLockoutService.get_login_history(username, limit=limit, db=db)
    return ResponseModel(code=200, message="获取登录历史成功", data=history)


@router.post("/{username}/unlock", response_model=dict)
def unlock_account(
    *,
    username: str,
    request: Optional[AccountUnlockRequest] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_super_admin),
) -> dict[str, Any]:
    """Manually unlock one account."""

    _ensure_super_admin(current_user)
    admin_name = getattr(current_user, "username", None) or getattr(
        current_user, "real_name", None
    )
    unlocked = AccountLockoutService.unlock_account(
        username,
        admin_user=admin_name,
        db=db,
    )
    status_after = AccountLockoutService.check_lockout(username, db)
    return {
        "username": username,
        "unlocked": unlocked,
        "reason": request.reason if request else None,
        "status": status_after,
    }
