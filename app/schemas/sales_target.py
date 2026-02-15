# -*- coding: utf-8 -*-
"""
销售目标管理 Schemas
"""

from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


# ============= 销售目标 V2 =============

class SalesTargetV2Base(BaseModel):
    """销售目标基础Schema"""
    target_period: str = Field(..., description="目标期间(year/quarter/month)")
    target_year: int = Field(..., description="目标年份")
    target_month: Optional[int] = Field(None, ge=1, le=12, description="目标月份")
    target_quarter: Optional[int] = Field(None, ge=1, le=4, description="目标季度")
    target_type: str = Field(..., description="目标类型(company/team/personal)")
    team_id: Optional[int] = Field(None, description="团队ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    
    # 目标指标
    sales_target: Decimal = Field(default=Decimal('0'), description="销售额目标")
    payment_target: Decimal = Field(default=Decimal('0'), description="回款目标")
    new_customer_target: int = Field(default=0, description="新客户数目标")
    lead_target: int = Field(default=0, description="线索数目标")
    opportunity_target: int = Field(default=0, description="商机数目标")
    deal_target: int = Field(default=0, description="签单数目标")
    
    description: Optional[str] = Field(None, description="目标描述")
    remark: Optional[str] = Field(None, description="备注")
    
    @field_validator('target_period')
    @classmethod
    def validate_period(cls, v):
        if v not in ['year', 'quarter', 'month']:
            raise ValueError('target_period must be one of: year, quarter, month')
        return v
    
    @field_validator('target_type')
    @classmethod
    def validate_type(cls, v):
        if v not in ['company', 'team', 'personal']:
            raise ValueError('target_type must be one of: company, team, personal')
        return v


class SalesTargetV2Create(SalesTargetV2Base):
    """创建销售目标Schema"""
    pass


class SalesTargetV2Update(BaseModel):
    """更新销售目标Schema"""
    target_period: Optional[str] = Field(None, description="目标期间")
    target_year: Optional[int] = Field(None, description="目标年份")
    target_month: Optional[int] = Field(None, ge=1, le=12, description="目标月份")
    target_quarter: Optional[int] = Field(None, ge=1, le=4, description="目标季度")
    
    sales_target: Optional[Decimal] = Field(None, description="销售额目标")
    payment_target: Optional[Decimal] = Field(None, description="回款目标")
    new_customer_target: Optional[int] = Field(None, description="新客户数目标")
    lead_target: Optional[int] = Field(None, description="线索数目标")
    opportunity_target: Optional[int] = Field(None, description="商机数目标")
    deal_target: Optional[int] = Field(None, description="签单数目标")
    
    actual_sales: Optional[Decimal] = Field(None, description="实际销售额")
    actual_payment: Optional[Decimal] = Field(None, description="实际回款")
    actual_new_customers: Optional[int] = Field(None, description="实际新客户数")
    actual_leads: Optional[int] = Field(None, description="实际线索数")
    actual_opportunities: Optional[int] = Field(None, description="实际商机数")
    actual_deals: Optional[int] = Field(None, description="实际签单数")
    
    description: Optional[str] = Field(None, description="目标描述")
    remark: Optional[str] = Field(None, description="备注")


class SalesTargetV2Response(SalesTargetV2Base):
    """销售目标响应Schema"""
    id: int
    
    # 实际完成值
    actual_sales: Decimal
    actual_payment: Decimal
    actual_new_customers: int
    actual_leads: int
    actual_opportunities: int
    actual_deals: int
    
    # 完成率
    completion_rate: Decimal
    
    # 上级目标
    parent_target_id: Optional[int]
    
    # 时间戳
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    # 关联数据
    team_name: Optional[str] = None
    user_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class SalesTargetV2WithSubTargets(SalesTargetV2Response):
    """包含子目标的销售目标Schema"""
    sub_targets: List['SalesTargetV2WithSubTargets'] = []


# ============= 目标分解 =============

class TargetBreakdownItem(BaseModel):
    """目标分解项"""
    target_type: str = Field(..., description="目标类型(team/personal)")
    team_id: Optional[int] = Field(None, description="团队ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    
    sales_target: Decimal = Field(default=Decimal('0'), description="销售额目标")
    payment_target: Decimal = Field(default=Decimal('0'), description="回款目标")
    new_customer_target: int = Field(default=0, description="新客户数目标")
    lead_target: int = Field(default=0, description="线索数目标")
    opportunity_target: int = Field(default=0, description="商机数目标")
    deal_target: int = Field(default=0, description="签单数目标")


class TargetBreakdownRequest(BaseModel):
    """目标分解请求Schema"""
    breakdown_items: List[TargetBreakdownItem] = Field(..., description="分解项列表")


class AutoBreakdownRequest(BaseModel):
    """自动分解请求Schema"""
    breakdown_method: str = Field(
        default="EQUAL",
        description="分解方法(EQUAL:平均分配/RATIO:按比例)"
    )
    target_ids: Optional[List[int]] = Field(None, description="目标ID列表(团队或个人)")
    
    @field_validator('breakdown_method')
    @classmethod
    def validate_method(cls, v):
        if v not in ['EQUAL', 'RATIO']:
            raise ValueError('breakdown_method must be one of: EQUAL, RATIO')
        return v


class TargetBreakdownResponse(BaseModel):
    """目标分解响应Schema"""
    parent_target_id: int
    breakdown_count: int
    created_targets: List[SalesTargetV2Response]


# ============= 目标统计 =============

class TargetStatsItem(BaseModel):
    """目标统计项"""
    id: int
    name: str
    target_type: str
    
    # 目标值
    sales_target: Decimal
    payment_target: Decimal
    new_customer_target: int
    lead_target: int
    opportunity_target: int
    deal_target: int
    
    # 实际值
    actual_sales: Decimal
    actual_payment: Decimal
    actual_new_customers: int
    actual_leads: int
    actual_opportunities: int
    actual_deals: int
    
    # 完成率
    completion_rate: Decimal
    
    # 排名
    rank: Optional[int] = None


class TeamRankingResponse(BaseModel):
    """团队排名响应Schema"""
    period: str
    rankings: List[TargetStatsItem]


class PersonalRankingResponse(BaseModel):
    """个人排名响应Schema"""
    period: str
    rankings: List[TargetStatsItem]


class CompletionTrendPoint(BaseModel):
    """完成趋势数据点"""
    date: str
    completion_rate: Decimal
    actual_sales: Decimal
    target_sales: Decimal


class CompletionTrendResponse(BaseModel):
    """完成趋势响应Schema"""
    target_id: int
    trend_data: List[CompletionTrendPoint]


class CompletionDistributionBucket(BaseModel):
    """完成率分布桶"""
    range_label: str  # 如 "0-20%", "20-40%"
    count: int


class CompletionDistributionResponse(BaseModel):
    """完成率分布响应Schema"""
    period: str
    distribution: List[CompletionDistributionBucket]


# 防止循环引用
SalesTargetV2WithSubTargets.model_rebuild()
