# -*- coding: utf-8 -*-
"""
认证相关 Schema
"""
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from .common import TimestampSchema

# 从 role.py 导入角色相关 Schema（保持向后兼容）
from .role import RoleCreate, RoleUpdate, RoleResponse


def validate_password_strength(password: str) -> str:
    """
    验证密码强度

    要求：
    - 最少 8 位
    - 至少包含一个大写字母
    - 至少包含一个小写字母
    - 至少包含一个数字
    """
    if len(password) < 8:
        raise ValueError("密码长度至少8位")
    if not re.search(r"[A-Z]", password):
        raise ValueError("密码必须包含至少一个大写字母")
    if not re.search(r"[a-z]", password):
        raise ValueError("密码必须包含至少一个小写字母")
    if not re.search(r"\d", password):
        raise ValueError("密码必须包含至少一个数字")
    return password


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
    employee_no: Optional[str] = Field(default=None, max_length=50, description="工号（将同步为员工编码）")
    employee_id: Optional[int] = Field(default=None, description="绑定员工ID")
    department: Optional[str] = Field(default=None, max_length=100, description="部门")
    position: Optional[str] = Field(default=None, max_length=100, description="职位")
    role_ids: Optional[List[int]] = Field(default_factory=list, description="角色ID列表")


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
    employee_id: Optional[int] = None
    role_ids: Optional[List[int]] = None


class PasswordChange(BaseModel):
    """修改密码"""
    old_password: str = Field(min_length=6, description="原密码")
    new_password: str = Field(min_length=8, description="新密码（至少8位，包含大小写字母和数字）")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return validate_password_strength(v)


class UserResponse(TimestampSchema):
    """用户响应"""
    id: int
    username: str
    employee_id: Optional[int] = None
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
    roles: List[Any] = Field(default_factory=list, description="角色列表")
    role_ids: List[int] = Field(default_factory=list, description="角色ID列表")
    permissions: List[str] = Field(default_factory=list)


class PermissionResponse(TimestampSchema):
    """权限响应"""
    id: int
    permission_code: str
    permission_name: str
    module: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = True  # 兼容旧表结构，可能不存在


class UserRoleAssign(BaseModel):
    """用户角色分配"""
    role_ids: List[int] = Field(default_factory=list, description="角色ID列表")


# ============================================================
# 角色模板 Schemas
# ============================================================

class RoleTemplateCreate(BaseModel):
    """创建角色模板"""
    template_code: str = Field(max_length=50, description="模板编码")
    template_name: str = Field(max_length=100, description="模板名称")
    description: Optional[str] = None
    data_scope: str = Field(default="OWN", description="数据权限范围")
    permission_ids: Optional[List[int]] = Field(default_factory=list, description="权限ID列表")
    sort_order: int = Field(default=0, description="排序")


class RoleTemplateUpdate(BaseModel):
    """更新角色模板"""
    template_name: Optional[str] = None
    description: Optional[str] = None
    data_scope: Optional[str] = None
    permission_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class RoleTemplateResponse(TimestampSchema):
    """角色模板响应"""
    id: int
    template_code: str
    template_name: str
    description: Optional[str] = None
    data_scope: str
    permission_ids: List[int] = Field(default_factory=list)
    is_active: bool = True
    sort_order: int = 0


# ============================================================
# 角色对比 Schemas
# ============================================================

class RoleComparisonRequest(BaseModel):
    """角色对比请求"""
    role_ids: List[int] = Field(min_length=2, max_length=5, description="要对比的角色ID列表（2-5个）")


class RoleComparisonItem(BaseModel):
    """角色对比项"""
    role_id: int
    role_code: str
    role_name: str
    data_scope: str
    permissions: List[str] = Field(default_factory=list)
    permission_ids: List[int] = Field(default_factory=list)


class RoleComparisonResponse(BaseModel):
    """角色对比响应"""
    roles: List[RoleComparisonItem]
    common_permissions: List[str] = Field(default_factory=list, description="共同拥有的权限")
    diff_permissions: Dict[str, List[str]] = Field(default_factory=dict, description="差异权限（角色ID -> 独有权限列表）")


# ============================================================
# 数据权限规则 Schemas
# ============================================================

class DataScopeRuleCreate(BaseModel):
    """创建数据权限规则"""
    role_id: int = Field(description="角色ID")
    rule_type: str = Field(description="规则类型：INCLUDE/EXCLUDE")
    target_type: str = Field(description="目标类型：DEPARTMENT/PROJECT/USER")
    target_id: int = Field(description="目标ID")


class DataScopeRuleResponse(TimestampSchema):
    """数据权限规则响应"""
    id: int
    role_id: int
    rule_type: str
    target_type: str
    target_id: int
    target_name: Optional[str] = Field(default=None, description="目标名称（冗余）")
    is_active: bool = True


class RoleWithFullPermissions(BaseModel):
    """完整权限的角色响应（用于角色详情）"""
    id: int
    role_code: str
    role_name: str
    description: Optional[str] = None
    data_scope: str
    parent_id: Optional[int] = None
    parent_name: Optional[str] = None
    is_system: bool = False
    is_active: bool = True
    sort_order: int = 0

    # 权限详情
    direct_permissions: List[PermissionResponse] = Field(default_factory=list, description="直接分配的权限")
    inherited_permissions: List[PermissionResponse] = Field(default_factory=list, description="继承的权限")

    # 数据权限规则
    data_scope_rules: List[DataScopeRuleResponse] = Field(default_factory=list, description="自定义数据权限规则")

    # 前端配置
    nav_groups: Optional[List[str]] = None
    ui_config: Optional[Dict[str, Any]] = None

