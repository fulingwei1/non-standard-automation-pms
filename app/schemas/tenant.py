# -*- coding: utf-8 -*-
"""
租户相关的 Pydantic Schema
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


# ============================================================
# 租户 Schema
# ============================================================

class TenantBase(BaseModel):
    """租户基础字段"""
    tenant_name: str = Field(..., min_length=1, max_length=200, description="租户名称")
    plan_type: str = Field(default="FREE", description="套餐类型: FREE/STANDARD/ENTERPRISE")
    contact_name: Optional[str] = Field(None, max_length=100, description="联系人姓名")
    contact_email: Optional[str] = Field(None, description="联系邮箱")
    contact_phone: Optional[str] = Field(None, max_length=50, description="联系电话")
    settings: Optional[Dict[str, Any]] = Field(None, description="租户配置")


class TenantCreate(TenantBase):
    """创建租户"""
    tenant_code: Optional[str] = Field(None, max_length=50, description="租户编码（可选，不填则自动生成）")
    max_users: Optional[int] = Field(None, ge=1, description="最大用户数")
    max_roles: Optional[int] = Field(None, ge=1, description="最大角色数")
    expired_at: Optional[datetime] = Field(None, description="过期时间")


class TenantUpdate(BaseModel):
    """更新租户"""
    tenant_name: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[str] = Field(None, description="状态: ACTIVE/SUSPENDED/DELETED")
    plan_type: Optional[str] = Field(None, description="套餐类型")
    max_users: Optional[int] = Field(None, ge=1)
    max_roles: Optional[int] = Field(None, ge=1)
    contact_name: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    settings: Optional[Dict[str, Any]] = None
    expired_at: Optional[datetime] = None


class TenantResponse(TenantBase):
    """租户响应"""
    id: int
    tenant_code: str
    status: str
    max_users: int
    max_roles: int
    max_storage_gb: int
    expired_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # 统计信息（可选）
    user_count: Optional[int] = None
    role_count: Optional[int] = None

    class Config:
        from_attributes = True


class TenantListResponse(BaseModel):
    """租户列表响应"""
    items: list[TenantResponse]
    total: int
    page: int
    page_size: int
    pages: int


class TenantInitRequest(BaseModel):
    """租户初始化请求"""
    admin_username: str = Field(..., min_length=3, max_length=50, description="管理员用户名")
    admin_password: str = Field(..., min_length=6, max_length=100, description="管理员密码")
    admin_email: str = Field(..., description="管理员邮箱")
    admin_real_name: Optional[str] = Field(None, max_length=50, description="管理员姓名")
    copy_role_templates: bool = Field(default=True, description="是否复制角色模板")


class TenantStatsResponse(BaseModel):
    """租户统计响应"""
    tenant_id: int
    tenant_code: str
    user_count: int
    role_count: int
    project_count: int
    storage_used_mb: float
    plan_limits: Dict[str, Any]


# ============================================================
# 角色模板 Schema
# ============================================================

class RoleTemplateBase(BaseModel):
    """角色模板基础字段"""
    role_code: str = Field(..., min_length=1, max_length=50, description="角色编码")
    role_name: str = Field(..., min_length=1, max_length=100, description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    data_scope: str = Field(default="OWN", description="数据权限范围")
    nav_groups: Optional[list] = Field(None, description="导航组配置")
    ui_config: Optional[Dict[str, Any]] = Field(None, description="UI配置")
    permission_codes: Optional[list[str]] = Field(None, description="权限编码列表")
    sort_order: int = Field(default=0, description="排序")


class RoleTemplateCreate(RoleTemplateBase):
    """创建角色模板"""
    pass


class RoleTemplateUpdate(BaseModel):
    """更新角色模板"""
    role_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    data_scope: Optional[str] = None
    nav_groups: Optional[list] = None
    ui_config: Optional[Dict[str, Any]] = None
    permission_codes: Optional[list[str]] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class RoleTemplateResponse(RoleTemplateBase):
    """角色模板响应"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
