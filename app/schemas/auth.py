# -*- coding: utf-8 -*-
"""
认证相关 Schema
"""

from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

from .common import BaseSchema, TimestampSchema


class Token(BaseModel):
    """令牌响应"""
    access_token: str = Field(description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(description="过期时间(秒)")


class TokenData(BaseModel):
    """令牌数据"""
    user_id: Optional[int] = None
    username: Optional[str] = None


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(min_length=3, max_length=50, description="用户名")
    password: str = Field(min_length=6, description="密码")


class UserCreate(BaseModel):
    """创建用户"""
    username: str = Field(min_length=3, max_length=50, description="用户名")
    password: str = Field(min_length=6, description="密码")
    email: Optional[EmailStr] = Field(default=None, description="邮箱")
    phone: Optional[str] = Field(default=None, max_length=20, description="手机号")
    real_name: Optional[str] = Field(default=None, max_length=50, description="真实姓名")
    employee_no: Optional[str] = Field(default=None, max_length=50, description="工号")
    department: Optional[str] = Field(default=None, max_length=100, description="部门")
    position: Optional[str] = Field(default=None, max_length=100, description="职位")
    role_ids: Optional[List[int]] = Field(default=[], description="角色ID列表")


class UserUpdate(BaseModel):
    """更新用户"""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    real_name: Optional[str] = None
    employee_no: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    avatar: Optional[str] = None
    is_active: Optional[bool] = None
    role_ids: Optional[List[int]] = None


class PasswordChange(BaseModel):
    """修改密码"""
    old_password: str = Field(min_length=6, description="原密码")
    new_password: str = Field(min_length=6, description="新密码")


class UserResponse(TimestampSchema):
    """用户响应"""
    id: int
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    real_name: Optional[str] = None
    employee_no: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    avatar: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    last_login_at: Optional[datetime] = None
    roles: List[str] = []


class RoleCreate(BaseModel):
    """创建角色"""
    role_code: str = Field(max_length=50, description="角色编码")
    role_name: str = Field(max_length=100, description="角色名称")
    description: Optional[str] = None
    data_scope: str = Field(default="OWN", description="数据权限范围")
    permission_ids: Optional[List[int]] = []


class RoleUpdate(BaseModel):
    """更新角色"""
    role_name: Optional[str] = None
    description: Optional[str] = None
    data_scope: Optional[str] = None
    is_active: Optional[bool] = None
    permission_ids: Optional[List[int]] = None


class RoleResponse(TimestampSchema):
    """角色响应"""
    id: int
    role_code: str
    role_name: str
    description: Optional[str] = None
    data_scope: str
    is_system: bool = False
    is_active: bool = True
    permissions: List[str] = []


class PermissionResponse(BaseSchema):
    """权限响应"""
    id: int
    permission_code: str
    permission_name: str
    module: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
