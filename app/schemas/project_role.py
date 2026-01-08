# -*- coding: utf-8 -*-
"""
项目角色类型与配置 Schema

用于API请求和响应的数据验证
"""

from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field


# ===========================
# 角色类型相关 Schema
# ===========================

class ProjectRoleTypeBase(BaseModel):
    """角色类型基础字段"""
    role_code: str = Field(..., max_length=50, description="角色编码")
    role_name: str = Field(..., max_length=100, description="角色名称")
    role_category: Optional[str] = Field("GENERAL", max_length=50, description="角色分类")
    description: Optional[str] = Field(None, description="角色职责描述")
    can_have_team: bool = Field(False, description="是否可带团队")
    is_required: bool = Field(False, description="是否默认必需")
    sort_order: int = Field(0, description="排序顺序")
    is_active: bool = Field(True, description="是否启用")


class ProjectRoleTypeCreate(ProjectRoleTypeBase):
    """创建角色类型"""
    pass


class ProjectRoleTypeUpdate(BaseModel):
    """更新角色类型"""
    role_name: Optional[str] = Field(None, max_length=100, description="角色名称")
    role_category: Optional[str] = Field(None, max_length=50, description="角色分类")
    description: Optional[str] = Field(None, description="角色职责描述")
    can_have_team: Optional[bool] = Field(None, description="是否可带团队")
    is_required: Optional[bool] = Field(None, description="是否默认必需")
    sort_order: Optional[int] = Field(None, description="排序顺序")
    is_active: Optional[bool] = Field(None, description="是否启用")


class ProjectRoleTypeResponse(ProjectRoleTypeBase):
    """角色类型响应"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectRoleTypeListResponse(BaseModel):
    """角色类型列表响应"""
    items: List[ProjectRoleTypeResponse]
    total: int


# ===========================
# 项目角色配置相关 Schema
# ===========================

class ProjectRoleConfigBase(BaseModel):
    """项目角色配置基础字段"""
    role_type_id: int = Field(..., description="角色类型ID")
    is_enabled: bool = Field(True, description="是否启用该角色")
    is_required: bool = Field(False, description="是否必填")
    remark: Optional[str] = Field(None, description="配置备注")


class ProjectRoleConfigCreate(ProjectRoleConfigBase):
    """创建项目角色配置"""
    pass


class ProjectRoleConfigUpdate(BaseModel):
    """更新项目角色配置"""
    is_enabled: Optional[bool] = Field(None, description="是否启用该角色")
    is_required: Optional[bool] = Field(None, description="是否必填")
    remark: Optional[str] = Field(None, description="配置备注")


class ProjectRoleConfigBatchUpdate(BaseModel):
    """批量更新项目角色配置"""
    configs: List[ProjectRoleConfigCreate]


class ProjectRoleConfigResponse(ProjectRoleConfigBase):
    """项目角色配置响应"""
    id: int
    project_id: int
    role_type: Optional[ProjectRoleTypeResponse] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectRoleConfigListResponse(BaseModel):
    """项目角色配置列表响应"""
    items: List[ProjectRoleConfigResponse]
    total: int


# ===========================
# 项目负责人相关 Schema
# ===========================

class UserBrief(BaseModel):
    """用户简要信息"""
    id: int
    username: str
    real_name: Optional[str] = None
    department_id: Optional[int] = None
    position: Optional[str] = None
    avatar: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectLeadCreate(BaseModel):
    """指定项目负责人"""
    user_id: int = Field(..., description="用户ID")
    role_type_id: int = Field(..., description="角色类型ID")
    allocation_pct: Decimal = Field(100, ge=0, le=100, description="分配比例")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    machine_id: Optional[int] = Field(None, description="设备ID（设备级分配）")
    remark: Optional[str] = Field(None, description="备注")


class ProjectLeadUpdate(BaseModel):
    """更新项目负责人"""
    allocation_pct: Optional[Decimal] = Field(None, ge=0, le=100, description="分配比例")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    machine_id: Optional[int] = Field(None, description="设备ID")
    remark: Optional[str] = Field(None, description="备注")


class ProjectLeadResponse(BaseModel):
    """项目负责人响应"""
    id: int
    project_id: int
    user_id: int
    user: Optional[UserBrief] = None
    role_code: str
    role_type_id: Optional[int] = None
    role_type: Optional[ProjectRoleTypeResponse] = None
    is_lead: bool = True
    allocation_pct: Decimal
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    machine_id: Optional[int] = None
    remark: Optional[str] = None
    team_count: int = 0  # 团队成员数量
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectLeadListResponse(BaseModel):
    """项目负责人列表响应"""
    items: List[ProjectLeadResponse]
    total: int


# ===========================
# 团队成员相关 Schema
# ===========================

class TeamMemberCreate(BaseModel):
    """添加团队成员"""
    user_id: int = Field(..., description="用户ID")
    allocation_pct: Decimal = Field(100, ge=0, le=100, description="分配比例")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    machine_id: Optional[int] = Field(None, description="设备ID")
    remark: Optional[str] = Field(None, description="备注")


class TeamMemberResponse(BaseModel):
    """团队成员响应"""
    id: int
    project_id: int
    user_id: int
    user: Optional[UserBrief] = None
    role_code: str
    role_type_id: Optional[int] = None
    is_lead: bool = False
    lead_member_id: int
    allocation_pct: Decimal
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    machine_id: Optional[int] = None
    remark: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TeamMemberListResponse(BaseModel):
    """团队成员列表响应"""
    items: List[TeamMemberResponse]
    total: int


# ===========================
# 项目负责人完整视图（含团队）
# ===========================

class ProjectLeadWithTeamResponse(ProjectLeadResponse):
    """项目负责人（含团队成员）"""
    team_members: List[TeamMemberResponse] = []


class ProjectRoleOverviewResponse(BaseModel):
    """项目角色概览（用于项目详情页）"""
    role_type: ProjectRoleTypeResponse
    config: Optional[ProjectRoleConfigResponse] = None
    lead: Optional[ProjectLeadWithTeamResponse] = None
    is_enabled: bool = True
    is_required: bool = False
    has_lead: bool = False
