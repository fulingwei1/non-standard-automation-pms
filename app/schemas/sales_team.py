# -*- coding: utf-8 -*-
"""
销售团队管理 Schemas
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ============= 销售团队 =============

class SalesTeamBase(BaseModel):
    """销售团队基础Schema"""
    team_code: str = Field(..., max_length=20, description="团队编码")
    team_name: str = Field(..., max_length=100, description="团队名称")
    description: Optional[str] = Field(None, description="团队描述")
    team_type: str = Field(default="REGION", description="团队类型")
    department_id: Optional[int] = Field(None, description="所属部门ID")
    leader_id: Optional[int] = Field(None, description="团队负责人ID")
    parent_team_id: Optional[int] = Field(None, description="上级团队ID")
    is_active: bool = Field(default=True, description="是否启用")
    sort_order: int = Field(default=0, description="排序序号")


class SalesTeamCreate(SalesTeamBase):
    """创建销售团队Schema"""
    pass


class SalesTeamUpdate(BaseModel):
    """更新销售团队Schema"""
    team_name: Optional[str] = Field(None, max_length=100, description="团队名称")
    description: Optional[str] = Field(None, description="团队描述")
    team_type: Optional[str] = Field(None, description="团队类型")
    department_id: Optional[int] = Field(None, description="所属部门ID")
    leader_id: Optional[int] = Field(None, description="团队负责人ID")
    parent_team_id: Optional[int] = Field(None, description="上级团队ID")
    is_active: Optional[bool] = Field(None, description="是否启用")
    sort_order: Optional[int] = Field(None, description="排序序号")


class SalesTeamResponse(SalesTeamBase):
    """销售团队响应Schema"""
    id: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    # 关联数据
    leader_name: Optional[str] = None
    department_name: Optional[str] = None
    member_count: int = 0
    
    class Config:
        from_attributes = True


class SalesTeamTreeNode(SalesTeamResponse):
    """销售团队树节点Schema"""
    sub_teams: List['SalesTeamTreeNode'] = []


# ============= 团队成员 =============

class SalesTeamMemberBase(BaseModel):
    """团队成员基础Schema"""
    team_id: int = Field(..., description="团队ID")
    user_id: int = Field(..., description="用户ID")
    role: str = Field(default="MEMBER", description="成员角色")
    is_primary: bool = Field(default=False, description="是否为主团队")
    is_active: bool = Field(default=True, description="是否有效")
    remark: Optional[str] = Field(None, max_length=200, description="备注")


class SalesTeamMemberCreate(SalesTeamMemberBase):
    """添加团队成员Schema"""
    pass


class SalesTeamMemberUpdate(BaseModel):
    """更新团队成员Schema"""
    role: Optional[str] = Field(None, description="成员角色")
    is_primary: Optional[bool] = Field(None, description="是否为主团队")
    is_active: Optional[bool] = Field(None, description="是否有效")
    remark: Optional[str] = Field(None, max_length=200, description="备注")


class SalesTeamMemberResponse(SalesTeamMemberBase):
    """团队成员响应Schema"""
    id: int
    joined_at: datetime
    created_at: datetime
    updated_at: datetime
    
    # 关联数据
    user_name: Optional[str] = None
    team_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============= 销售区域 =============

class SalesRegionBase(BaseModel):
    """销售区域基础Schema"""
    region_code: str = Field(..., max_length=50, description="区域编码")
    region_name: str = Field(..., max_length=100, description="区域名称")
    parent_region_id: Optional[int] = Field(None, description="上级区域ID")
    level: int = Field(default=1, description="区域层级")
    provinces: Optional[List[str]] = Field(None, description="包含的省份")
    cities: Optional[List[str]] = Field(None, description="包含的城市")
    team_id: Optional[int] = Field(None, description="负责团队ID")
    leader_id: Optional[int] = Field(None, description="负责人ID")
    description: Optional[str] = Field(None, description="区域描述")
    is_active: bool = Field(default=True, description="是否启用")
    sort_order: int = Field(default=0, description="排序序号")


class SalesRegionCreate(SalesRegionBase):
    """创建销售区域Schema"""
    pass


class SalesRegionUpdate(BaseModel):
    """更新销售区域Schema"""
    region_name: Optional[str] = Field(None, max_length=100, description="区域名称")
    parent_region_id: Optional[int] = Field(None, description="上级区域ID")
    level: Optional[int] = Field(None, description="区域层级")
    provinces: Optional[List[str]] = Field(None, description="包含的省份")
    cities: Optional[List[str]] = Field(None, description="包含的城市")
    team_id: Optional[int] = Field(None, description="负责团队ID")
    leader_id: Optional[int] = Field(None, description="负责人ID")
    description: Optional[str] = Field(None, description="区域描述")
    is_active: Optional[bool] = Field(None, description="是否启用")
    sort_order: Optional[int] = Field(None, description="排序序号")


class SalesRegionResponse(SalesRegionBase):
    """销售区域响应Schema"""
    id: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    # 关联数据
    team_name: Optional[str] = None
    leader_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class SalesRegionAssignTeam(BaseModel):
    """分配团队Schema"""
    team_id: int = Field(..., description="团队ID")
    leader_id: Optional[int] = Field(None, description="负责人ID")


# 防止循环引用
SalesTeamTreeNode.model_rebuild()
