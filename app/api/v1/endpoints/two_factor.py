# -*- coding: utf-8 -*-
"""
双因素认证（2FA）API路由

端点：
  POST /api/v1/auth/2fa/setup        - 获取2FA二维码（未启用前）
  POST /api/v1/auth/2fa/enable       - 启用2FA
  POST /api/v1/auth/2fa/verify       - 验证2FA码（登录时）
  POST /api/v1/auth/2fa/disable      - 禁用2FA
  GET  /api/v1/auth/2fa/backup-codes - 获取备用码信息
  POST /api/v1/auth/2fa/backup-codes/regenerate - 重新生成备用码
"""

import logging
from typing import Optional

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from ....core import auth as security
from ....core.config import settings
from ....core.auth import get_current_active_user
from ....models.base import get_db
from ....models.user import User
from ....services.two_factor_service import get_two_factor_service
from ....services.session_service import SessionService

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Pydantic Schemas
# ============================================================================

class TwoFactorSetupResponse(BaseModel):
    """2FA设置响应"""
    secret: str = Field(..., description="TOTP密钥（仅首次显示）")
    qr_code_url: str = Field(..., description="二维码图片URL")
    message: str = Field(..., description="提示信息")


class TwoFactorEnableRequest(BaseModel):
    """启用2FA请求"""
    totp_code: str = Field(..., description="TOTP验证码（6位数字）", min_length=6, max_length=6)


class TwoFactorEnableResponse(BaseModel):
    """启用2FA响应"""
    success: bool
    message: str
    backup_codes: Optional[list[str]] = Field(None, description="备用恢复码（10个）")


class TwoFactorVerifyRequest(BaseModel):
    """验证2FA请求"""
    code: str = Field(..., description="TOTP验证码或备用码")


class TwoFactorVerifyResponse(BaseModel):
    """验证2FA响应"""
    success: bool
    message: str


class TwoFactorDisableRequest(BaseModel):
    """禁用2FA请求"""
    password: str = Field(..., description="用户密码")


class TwoFactorDisableResponse(BaseModel):
    """禁用2FA响应"""
    success: bool
    message: str


class BackupCodesInfoResponse(BaseModel):
    """备用码信息响应"""
    total: int = Field(..., description="总数")
    unused: int = Field(..., description="未使用数量")
    used: int = Field(..., description="已使用数量")


class BackupCodesRegenerateRequest(BaseModel):
    """重新生成备用码请求"""
    password: str = Field(..., description="用户密码")


class BackupCodesRegenerateResponse(BaseModel):
    """重新生成备用码响应"""
    success: bool
    message: str
    backup_codes: Optional[list[str]] = Field(None, description="新备用码列表")


class TwoFactorLoginRequest(BaseModel):
    """2FA登录请求"""
    temp_token: str = Field(..., description="临时令牌")
    code: str = Field(..., description="2FA验证码")


class TwoFactorLoginResponse(BaseModel):
    """2FA登录响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/login", response_model=TwoFactorLoginResponse, summary="完成2FA登录")
async def complete_2fa_login(
    request_data: TwoFactorLoginRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    完成2FA登录（验证2FA码后返回最终token）
    
    流程：
    1. 用户在 /auth/login 登录时提供用户名密码
    2. 如果启用了2FA，返回 temp_token
    3. 用户调用此接口，提供 temp_token 和 2FA验证码
    4. 验证通过后返回最终的 access_token 和 refresh_token
    """
    # 1. 验证临时令牌
    try:
        payload = jwt.decode(
            request_data.temp_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # 检查令牌用途
        if payload.get("purpose") != "2fa_pending":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的临时令牌"
            )
        
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="临时令牌无效或已过期"
        )
    
    # 2. 查询用户
    result = db.execute(
        text("SELECT * FROM users WHERE id = :user_id LIMIT 1"),
        {"user_id": user_id}
    ).fetchone()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    user_dict = dict(result._mapping)
    
    # 3. 验证用户是否启用了2FA
    if not user_dict.get("two_factor_enabled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未启用2FA"
        )
    
    # 4. 创建User对象用于验证2FA
    user = User()
    user.id = user_dict["id"]
    user.username = user_dict["username"]
    user.two_factor_enabled = user_dict["two_factor_enabled"]
    
    # 5. 验证2FA码
    client_ip = req.client.host if req.client else None
    service = get_two_factor_service()
    success, message = service.verify_2fa_code(
        db, user, request_data.code, client_ip
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )
    
    # 6. 生成最终的Access Token和Refresh Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=7)
    
    access_token, refresh_token, access_jti, refresh_jti = security.create_token_pair(
        data={"sub": str(user_id)},
        access_expires=access_token_expires,
        refresh_expires=refresh_token_expires,
    )
    
    # 7. 创建会话记录
    try:
        user_agent = req.headers.get("User-Agent")
        SessionService.create_session(
            db=db,
            user_id=user_id,
            access_token_jti=access_jti,
            refresh_token_jti=refresh_jti,
            ip_address=client_ip,
            user_agent=user_agent,
            device_info=None,
        )
    except Exception as e:
        logger.warning(f"创建会话记录失败: {e}")
    
    logger.info(f"用户 {user.username} (ID:{user_id}) 通过2FA登录成功")
    
    return TwoFactorLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_expires_in=7 * 24 * 3600
    )

@router.post("/setup", summary="获取2FA二维码")
async def setup_two_factor(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取2FA设置信息（未启用2FA前调用）
    
    返回TOTP密钥和二维码，用户扫码后输入验证码启用2FA
    """
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA已启用，请先禁用后再重新设置"
        )
    
    # 生成TOTP密钥和二维码
    service = get_two_factor_service()
    secret, qr_code_png = service.setup_2fa_for_user(db, current_user)
    
    # 返回二维码（base64编码）
    import base64
    qr_code_base64 = base64.b64encode(qr_code_png).decode()
    qr_code_url = f"data:image/png;base64,{qr_code_base64}"
    
    return TwoFactorSetupResponse(
        secret=secret,
        qr_code_url=qr_code_url,
        message="请使用Google Authenticator或Microsoft Authenticator扫描二维码，然后输入验证码启用2FA"
    )


@router.post("/enable", response_model=TwoFactorEnableResponse, summary="启用2FA")
async def enable_two_factor(
    request: TwoFactorEnableRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    启用2FA（验证TOTP码后启用）
    
    验证成功后返回10个备用恢复码，请妥善保管
    """
    if current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA已启用"
        )
    
    # 启用2FA
    service = get_two_factor_service()
    success, message, backup_codes = service.enable_2fa_for_user(
        db, current_user, request.totp_code
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return TwoFactorEnableResponse(
        success=True,
        message=message,
        backup_codes=backup_codes
    )


@router.post("/verify", response_model=TwoFactorVerifyResponse, summary="验证2FA码")
async def verify_two_factor(
    request: TwoFactorVerifyRequest,
    req: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    验证2FA码（登录时调用）
    
    支持TOTP验证码和备用恢复码
    """
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未启用2FA"
        )
    
    # 获取客户端IP
    client_ip = req.client.host if req.client else None
    
    # 验证2FA码
    service = get_two_factor_service()
    success, message = service.verify_2fa_code(
        db, current_user, request.code, client_ip
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )
    
    return TwoFactorVerifyResponse(
        success=True,
        message=message
    )


@router.post("/disable", response_model=TwoFactorDisableResponse, summary="禁用2FA")
async def disable_two_factor(
    request: TwoFactorDisableRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    禁用2FA（需要验证密码）
    
    将删除TOTP密钥和所有备用码
    """
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未启用2FA"
        )
    
    # 禁用2FA
    service = get_two_factor_service()
    success, message = service.disable_2fa_for_user(
        db, current_user, request.password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return TwoFactorDisableResponse(
        success=True,
        message=message
    )


@router.get("/backup-codes", response_model=BackupCodesInfoResponse, summary="获取备用码信息")
async def get_backup_codes_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取备用码统计信息
    
    返回总数、已使用数量、未使用数量
    """
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未启用2FA"
        )
    
    service = get_two_factor_service()
    info = service.get_backup_codes_info(db, current_user)
    
    return BackupCodesInfoResponse(**info)


@router.post("/backup-codes/regenerate", response_model=BackupCodesRegenerateResponse, summary="重新生成备用码")
async def regenerate_backup_codes(
    request: BackupCodesRegenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    重新生成备用码（需要验证密码）
    
    将删除所有旧备用码并生成10个新备用码
    """
    if not current_user.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="未启用2FA"
        )
    
    service = get_two_factor_service()
    success, message, backup_codes = service.regenerate_backup_codes(
        db, current_user, request.password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return BackupCodesRegenerateResponse(
        success=True,
        message=message,
        backup_codes=backup_codes
    )
