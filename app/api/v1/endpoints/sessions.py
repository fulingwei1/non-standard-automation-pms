# -*- coding: utf-8 -*-
"""
会话管理 API endpoints
"""

import logging
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.auth import extract_jti_from_token
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.session import (
    RevokeSessionRequest,
    SessionListResponse,
    SessionResponse,
)
from app.services.session_service import SessionService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/sessions", response_model=SessionListResponse, status_code=status.HTTP_200_OK)
def list_sessions(
    request: Request,
    token: str = Depends(security.oauth2_scheme),
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    查看当前用户的所有活跃会话
    
    返回所有活跃会话，并标记当前会话
    """
    # 提取当前token的JTI
    current_jti = extract_jti_from_token(token)
    
    # 获取用户的所有活跃会话
    sessions = SessionService.get_user_sessions(
        db=db,
        user_id=current_user.id,
        active_only=True,
        current_jti=current_jti,
    )
    
    # 转换为响应格式
    session_responses = []
    for session in sessions:
        session_data = SessionResponse.model_validate(session)
        # 标记当前会话
        if current_jti and (
            session.access_token_jti == current_jti or
            session.refresh_token_jti == current_jti
        ):
            session_data.is_current = True
        session_responses.append(session_data)
    
    return SessionListResponse(
        sessions=session_responses,
        total=len(sessions),
        active_count=len(sessions),
    )


@router.post("/sessions/revoke", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def revoke_session(
    request: Request,
    revoke_data: RevokeSessionRequest,
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    撤销指定会话（强制下线其他设备）
    
    - **session_id**: 要撤销的会话ID
    
    注意：不能撤销当前会话，如需登出请使用logout接口
    """
    success = SessionService.revoke_session(
        db=db,
        session_id=revoke_data.session_id,
        user_id=current_user.id,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在或无权操作",
        )
    
    return ResponseModel(
        code=200,
        message="会话已撤销",
    )


@router.post("/sessions/revoke-all", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def revoke_all_sessions(
    request: Request,
    token: str = Depends(security.oauth2_scheme),
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    撤销所有其他设备的会话（保留当前会话）
    
    强制所有其他设备下线，当前设备保持登录
    """
    # 提取当前token的JTI
    current_jti = extract_jti_from_token(token)
    
    count = SessionService.revoke_all_sessions(
        db=db,
        user_id=current_user.id,
        except_jti=current_jti,
    )
    
    return ResponseModel(
        code=200,
        message=f"已撤销{count}个其他设备的会话",
    )
