# -*- coding: utf-8 -*-
"""
用户管理 - 请求/响应模型
"""

from typing import List, Optional

from pydantic import BaseModel

from app.schemas.auth import UserResponse
from app.schemas.common import PaginatedResponse


class SyncEmployeesRequest(BaseModel):
    """同步员工请求"""
    only_active: bool = True
    auto_activate: bool = False
    department_filter: Optional[str] = None


class BatchToggleActiveRequest(BaseModel):
    """批量激活/禁用请求"""
    user_ids: List[int]
    is_active: bool


class ToggleActiveRequest(BaseModel):
    """激活/禁用请求"""
    is_active: Optional[bool] = None


class UserListResponse(PaginatedResponse):
    """用户列表响应"""
    items: List[UserResponse]
