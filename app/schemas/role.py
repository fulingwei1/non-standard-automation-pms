# -*- coding: utf-8 -*-
"""
系统角色相关的 Pydantic Schema

用于角色管理 API 的请求和响应验证
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RoleBase(BaseModel):
    """角色基础字段"""
    role_code: str = Field(..., min_length=1, max_length=50, description="角色编码")
    role_name: str = Field(..., min_length=1, max_length=100, description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    data_scope: str = Field(default="OWN", description="数据权限范围: ALL/DEPARTMENT/PROJECT/OWN/CUSTOM")


class RoleCreate(RoleBase):
    """创建角色"""
    parent_id: Optional[int] = Field(default=None, description="父角色ID（继承）")
    permission_ids: Optional[List[int]] = Field(default_factory=list, description="权限ID列表")
    nav_groups: Optional[List[Dict[str, Any]]] = Field(None, description="导航组配置")
    ui_config: Optional[Dict[str, Any]] = Field(None, description="UI配置")
    sort_order: int = Field(default=0, description="排序")


class RoleUpdate(BaseModel):
    """更新角色"""
    role_code: Optional[str] = Field(None, min_length=1, max_length=50)
    role_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    data_scope: Optional[str] = None
    parent_id: Optional[int] = Field(default=None, description="父角色ID（继承）")
    permission_ids: Optional[List[int]] = Field(default=None, description="权限ID列表")
    nav_groups: Optional[List[Dict[str, Any]]] = None
    ui_config: Optional[Dict[str, Any]] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class RoleResponse(RoleBase):
    """角色响应"""
    id: int
    tenant_id: Optional[int] = None
    source_template_id: Optional[int] = None
    parent_id: Optional[int] = Field(default=None, description="父角色ID")
    parent_name: Optional[str] = Field(default=None, description="父角色名称")
    nav_groups: Optional[List[Dict[str, Any]]] = None
    ui_config: Optional[Dict[str, Any]] = None
    sort_order: int = 0
    is_system: bool = False
    is_active: bool = True
    permissions: List[str] = Field(default_factory=list, description="权限编码列表")
    permission_count: int = Field(default=0, description="直接权限数量")
    inherited_permission_count: int = Field(default=0, description="继承权限数量")
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
