# -*- coding: utf-8 -*-
"""
销售团队管理 Schema
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


# ==================== 销售团队 ====================


class SalesTeamCreate(BaseModel):
    """创建销售团队请求"""
    team_code: str = Field(..., max_length=20, description="团队编码")
    team_name: str = Field(..., max_length=100, description="团队名称")
    description: Optional[str] = Field(None, description="团队描述")
    team_type: str = Field("REGION", description="团队类型：REGION/INDUSTRY/SCALE/OTHER")
    department_id: Optional[int] = Field(None, description="所属部门ID")
    leader_id: Optional[int] = Field(None, description="团队负责人ID")
    parent_team_id: Optional[int] = Field(None, description="上级团队ID")
    sort_order: int = Field(0, description="排序序号")


class SalesTeamUpdate(BaseModel):
    """更新销售团队请求"""
    team_name: Optional[str] = Field(None, max_length=100, description="团队名称")
    description: Optional[str] = Field(None, description="团队描述")
    team_type: Optional[str] = Field(None, description="团队类型")
    department_id: Optional[int] = Field(None, description="所属部门ID")
    leader_id: Optional[int] = Field(None, description="团队负责人ID")
    parent_team_id: Optional[int] = Field(None, description="上级团队ID")
    is_active: Optional[bool] = Field(None, description="是否启用")
    sort_order: Optional[int] = Field(None, description="排序序号")


class SalesTeamMemberInfo(BaseModel):
    """团队成员信息"""
    id: int
    user_id: int
    user_name: Optional[str] = None
    username: Optional[str] = None
    role: str
    is_primary: bool
    is_active: bool
    joined_at: Optional[datetime] = None
    remark: Optional[str] = None

    class Config:
        from_attributes = True


class SalesTeamResponse(BaseModel):
    """销售团队响应"""
    id: int
    team_code: str
    team_name: str
    description: Optional[str] = None
    team_type: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    leader_id: Optional[int] = None
    leader_name: Optional[str] = None
    parent_team_id: Optional[int] = None
    parent_team_name: Optional[str] = None
    is_active: bool
    sort_order: int
    member_count: int = 0
    members: List[SalesTeamMemberInfo] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SalesTeamListResponse(BaseModel):
    """销售团队列表响应（简化版）"""
    id: int
    team_code: str
    team_name: str
    team_type: str
    department_name: Optional[str] = None
    leader_name: Optional[str] = None
    is_active: bool
    member_count: int = 0
    sub_team_count: int = 0

    class Config:
        from_attributes = True


# ==================== 团队成员 ====================


class TeamMemberAddRequest(BaseModel):
    """添加团队成员请求"""
    user_id: int = Field(..., description="用户ID")
    role: str = Field("MEMBER", description="成员角色：LEADER/DEPUTY/MEMBER")
    is_primary: bool = Field(False, description="是否为主团队")
    remark: Optional[str] = Field(None, max_length=200, description="备注")


class TeamMemberUpdateRequest(BaseModel):
    """更新团队成员请求"""
    role: Optional[str] = Field(None, description="成员角色")
    is_primary: Optional[bool] = Field(None, description="是否为主团队")
    is_active: Optional[bool] = Field(None, description="是否有效")
    remark: Optional[str] = Field(None, max_length=200, description="备注")


class TeamMemberBatchAddRequest(BaseModel):
    """批量添加团队成员请求"""
    user_ids: List[int] = Field(..., description="用户ID列表")
    role: str = Field("MEMBER", description="成员角色")


# ==================== 团队业绩快照 ====================


class TeamPerformanceSnapshotResponse(BaseModel):
    """团队业绩快照响应"""
    id: int
    team_id: int
    team_name: Optional[str] = None
    period_type: str
    period_value: str
    snapshot_date: datetime
    lead_count: int = 0
    opportunity_count: int = 0
    opportunity_amount: Decimal = Decimal("0")
    contract_count: int = 0
    contract_amount: Decimal = Decimal("0")
    collection_amount: Decimal = Decimal("0")
    target_amount: Decimal = Decimal("0")
    completion_rate: Decimal = Decimal("0")
    rank_in_department: Optional[int] = None
    rank_overall: Optional[int] = None
    member_count: int = 0

    class Config:
        from_attributes = True


# ==================== 团队PK ====================


class TeamPKCreateRequest(BaseModel):
    """创建团队PK请求"""
    pk_name: str = Field(..., max_length=100, description="PK名称")
    pk_type: str = Field(..., description="PK类型：CONTRACT_AMOUNT/COLLECTION_AMOUNT/LEAD_COUNT")
    team_ids: List[int] = Field(..., min_length=2, description="参与团队ID列表")
    start_date: datetime = Field(..., description="开始时间")
    end_date: datetime = Field(..., description="结束时间")
    target_value: Optional[Decimal] = Field(None, description="PK目标值")
    reward_description: Optional[str] = Field(None, description="奖励说明")


class TeamPKUpdateRequest(BaseModel):
    """更新团队PK请求"""
    pk_name: Optional[str] = Field(None, max_length=100, description="PK名称")
    target_value: Optional[Decimal] = Field(None, description="PK目标值")
    status: Optional[str] = Field(None, description="状态：PENDING/ONGOING/COMPLETED/CANCELLED")
    winner_team_id: Optional[int] = Field(None, description="获胜团队ID")
    result_summary: Optional[str] = Field(None, description="结果汇总(JSON)")
    reward_description: Optional[str] = Field(None, description="奖励说明")


class TeamPKResponse(BaseModel):
    """团队PK响应"""
    id: int
    pk_name: str
    pk_type: str
    team_ids: List[int] = []
    teams: List[dict] = []  # 包含团队基本信息和当前业绩
    start_date: datetime
    end_date: datetime
    target_value: Optional[Decimal] = None
    status: str
    winner_team_id: Optional[int] = None
    winner_team_name: Optional[str] = None
    result_summary: Optional[dict] = None
    reward_description: Optional[str] = None
    created_by: Optional[int] = None
    creator_name: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 团队排名 ====================


class TeamRankingItem(BaseModel):
    """团队排名项"""
    rank: int
    team_id: int
    team_code: str
    team_name: str
    team_type: str
    leader_name: Optional[str] = None
    member_count: int = 0
    lead_count: int = 0
    opportunity_count: int = 0
    contract_count: int = 0
    contract_amount: Decimal = Decimal("0")
    collection_amount: Decimal = Decimal("0")
    target_amount: Decimal = Decimal("0")
    completion_rate: Decimal = Decimal("0")
    score: Decimal = Decimal("0")
    rank_change: int = 0  # 与上期相比的排名变化（正数上升，负数下降）


class TeamRankingResponse(BaseModel):
    """团队排名响应"""
    ranking_type: str
    period_type: str
    period_value: str
    rankings: List[TeamRankingItem]
    total_count: int
