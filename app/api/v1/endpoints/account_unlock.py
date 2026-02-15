# -*- coding: utf-8 -*-
"""
账户解锁管理 API endpoints（管理员功能）
"""

import logging
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.account_lockout_service import AccountLockoutService
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)


class UnlockAccountRequest(BaseModel):
    """解锁账户请求"""
    username: str = Field(..., description="要解锁的用户名")


class RemoveIPBlacklistRequest(BaseModel):
    """移除IP黑名单请求"""
    ip: str = Field(..., description="要移除的IP地址")


class LoginHistoryQuery(BaseModel):
    """登录历史查询"""
    username: str = Field(..., description="用户名")
    limit: int = Field(50, ge=1, le=500, description="返回记录数")


@router.get("/locked-accounts", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_locked_accounts(
    current_user: User = Depends(security.get_current_active_superuser),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    获取所有被锁定的账户列表（管理员功能）
    
    需要管理员权限
    """
    try:
        locked_accounts = AccountLockoutService.get_locked_accounts(db)
        return ResponseModel(
            code=200,
            message="获取成功",
            data={"locked_accounts": locked_accounts, "total": len(locked_accounts)}
        )
    except Exception as e:
        logger.error(f"获取锁定账户列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取锁定账户列表失败"
        )


@router.post("/unlock", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def unlock_account(
    unlock_data: UnlockAccountRequest,
    current_user: User = Depends(security.get_current_active_superuser),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    手动解锁账户（管理员功能）
    
    需要管理员权限
    """
    try:
        success = AccountLockoutService.unlock_account(
            username=unlock_data.username,
            admin_user=current_user.username,
            db=db
        )
        
        if success:
            return ResponseModel(
                code=200,
                message=f"账户 {unlock_data.username} 已成功解锁"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="解锁失败，账户可能未被锁定或Redis不可用"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解锁账户失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解锁账户失败: {str(e)}"
        )


@router.post("/login-history", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_login_history(
    query: LoginHistoryQuery,
    current_user: User = Depends(security.get_current_active_superuser),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    获取用户登录历史记录（管理员功能）
    
    需要管理员权限
    """
    try:
        history = AccountLockoutService.get_login_history(
            username=query.username,
            limit=query.limit,
            db=db
        )
        return ResponseModel(
            code=200,
            message="获取成功",
            data={"history": history, "total": len(history)}
        )
    except Exception as e:
        logger.error(f"获取登录历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取登录历史失败: {str(e)}"
        )


@router.get("/ip-blacklist", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_ip_blacklist(
    current_user: User = Depends(security.get_current_active_superuser),
) -> Any:
    """
    获取IP黑名单（管理员功能）
    
    需要管理员权限
    """
    try:
        blacklisted_ips = AccountLockoutService.get_blacklisted_ips()
        return ResponseModel(
            code=200,
            message="获取成功",
            data={"blacklisted_ips": blacklisted_ips, "total": len(blacklisted_ips)}
        )
    except Exception as e:
        logger.error(f"获取IP黑名单失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取IP黑名单失败: {str(e)}"
        )


@router.post("/remove-ip-blacklist", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def remove_ip_blacklist(
    remove_data: RemoveIPBlacklistRequest,
    current_user: User = Depends(security.get_current_active_superuser),
) -> Any:
    """
    从黑名单中移除IP（管理员功能）
    
    需要管理员权限
    """
    try:
        success = AccountLockoutService.remove_ip_from_blacklist(
            ip=remove_data.ip,
            admin_user=current_user.username
        )
        
        if success:
            return ResponseModel(
                code=200,
                message=f"IP {remove_data.ip} 已从黑名单移除"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="移除失败，Redis不可用"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"移除IP黑名单失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"移除IP黑名单失败: {str(e)}"
        )


@router.get("/lockout-status/{username}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def check_lockout_status(
    username: str,
    current_user: User = Depends(security.get_current_active_superuser),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    检查指定账户的锁定状态（管理员功能）
    
    需要管理员权限
    """
    try:
        status_info = AccountLockoutService.check_lockout(username, db)
        return ResponseModel(
            code=200,
            message="查询成功",
            data=status_info
        )
    except Exception as e:
        logger.error(f"查询锁定状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询锁定状态失败: {str(e)}"
        )
