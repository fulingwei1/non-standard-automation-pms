# -*- coding: utf-8 -*-
"""
客户档案管理 Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..common import TimestampSchema


class CustomerCreate(BaseModel):
    """创建客户"""

    model_config = ConfigDict(populate_by_name=True)

    customer_code: Optional[str] = Field(default=None, max_length=50, description="客户编码（留空自动生成）")
    customer_name: str = Field(max_length=200, description="客户名称")
    short_name: Optional[str] = Field(default=None, max_length=100, description="客户简称")
    customer_type: Optional[str] = Field(default="enterprise", description="客户类型：enterprise/individual")
    
    # 详细信息
    industry: Optional[str] = Field(default=None, max_length=100, description="所属行业")
    scale: Optional[str] = Field(default=None, max_length=50, description="企业规模")
    address: Optional[str] = Field(default=None, description="详细地址")
    website: Optional[str] = Field(default=None, max_length=200, description="公司网址")
    established_date: Optional[date] = Field(default=None, description="成立日期")
    
    # 财务信息
    credit_limit: Optional[Decimal] = Field(default=0, description="信用额度")
    payment_terms: Optional[str] = Field(default=None, max_length=100, description="付款条件")
    account_period: Optional[int] = Field(default=30, description="账期(天)")
    
    # 业务信息
    customer_source: Optional[str] = Field(default=None, max_length=100, description="客户来源")
    sales_owner_id: Optional[int] = Field(default=None, description="负责销售人员ID")
    status: Optional[str] = Field(default="potential", description="客户状态：potential/prospect/customer/lost")
    
    @field_validator('customer_type')
    @classmethod
    def validate_customer_type(cls, v):
        if v not in ['enterprise', 'individual']:
            raise ValueError('客户类型必须是 enterprise 或 individual')
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v not in ['potential', 'prospect', 'customer', 'lost']:
            raise ValueError('客户状态必须是 potential、prospect、customer 或 lost')
        return v


class CustomerUpdate(BaseModel):
    """更新客户"""

    model_config = ConfigDict(populate_by_name=True)

    customer_name: Optional[str] = Field(default=None, max_length=200, description="客户名称")
    short_name: Optional[str] = Field(default=None, max_length=100, description="客户简称")
    customer_type: Optional[str] = Field(default=None, description="客户类型")
    industry: Optional[str] = Field(default=None, max_length=100, description="所属行业")
    scale: Optional[str] = Field(default=None, max_length=50, description="企业规模")
    address: Optional[str] = Field(default=None, description="详细地址")
    website: Optional[str] = Field(default=None, max_length=200, description="公司网址")
    established_date: Optional[date] = Field(default=None, description="成立日期")
    credit_limit: Optional[Decimal] = Field(default=None, description="信用额度")
    payment_terms: Optional[str] = Field(default=None, max_length=100, description="付款条件")
    account_period: Optional[int] = Field(default=None, description="账期(天)")
    customer_source: Optional[str] = Field(default=None, max_length=100, description="客户来源")
    sales_owner_id: Optional[int] = Field(default=None, description="负责销售人员ID")
    status: Optional[str] = Field(default=None, description="客户状态")
    annual_revenue: Optional[Decimal] = Field(default=None, description="年成交额")
    cooperation_years: Optional[int] = Field(default=None, description="合作年限")


class CustomerResponse(TimestampSchema):
    """客户响应"""

    id: int = Field(description="客户ID")
    customer_code: str = Field(description="客户编码")
    customer_name: str = Field(description="客户名称")
    short_name: Optional[str] = Field(default=None, description="客户简称")
    customer_type: str = Field(description="客户类型")
    industry: Optional[str] = Field(default=None, description="所属行业")
    scale: Optional[str] = Field(default=None, description="企业规模")
    address: Optional[str] = Field(default=None, description="详细地址")
    website: Optional[str] = Field(default=None, description="公司网址")
    established_date: Optional[date] = Field(default=None, description="成立日期")
    customer_level: str = Field(description="客户等级")
    credit_limit: Decimal = Field(description="信用额度")
    payment_terms: Optional[str] = Field(default=None, description="付款条件")
    account_period: int = Field(description="账期(天)")
    customer_source: Optional[str] = Field(default=None, description="客户来源")
    sales_owner_id: Optional[int] = Field(default=None, description="负责销售人员ID")
    sales_owner_name: Optional[str] = Field(default=None, description="负责销售人员姓名")
    status: str = Field(description="客户状态")
    last_follow_up_at: Optional[datetime] = Field(default=None, description="最后跟进时间")
    annual_revenue: Decimal = Field(description="年成交额")
    cooperation_years: int = Field(description="合作年限")
    
    # 关联数据统计
    contacts_count: Optional[int] = Field(default=0, description="联系人数量")
    tags: Optional[List[str]] = Field(default=[], description="标签列表")


class CustomerListResponse(BaseModel):
    """客户列表响应"""

    total: int = Field(description="总数")
    items: List[CustomerResponse] = Field(description="客户列表")


class CustomerStatsResponse(BaseModel):
    """客户统计响应"""

    total_customers: int = Field(description="客户总数")
    potential_count: int = Field(description="潜在客户数")
    prospect_count: int = Field(description="意向客户数")
    customer_count: int = Field(description="成交客户数")
    lost_count: int = Field(description="流失客户数")
    
    level_a_count: int = Field(description="A级客户数")
    level_b_count: int = Field(description="B级客户数")
    level_c_count: int = Field(description="C级客户数")
    level_d_count: int = Field(description="D级客户数")
    
    total_annual_revenue: Decimal = Field(description="总年成交额")
    avg_cooperation_years: float = Field(description="平均合作年限")
