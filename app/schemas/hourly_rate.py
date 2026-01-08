# -*- coding: utf-8 -*-
"""
时薪配置管理模块 Schema
"""

from typing import Optional
from decimal import Decimal
from datetime import date
from pydantic import BaseModel, Field

from app.schemas.common import TimestampSchema


class HourlyRateConfigCreate(BaseModel):
    """创建时薪配置"""
    config_type: str = Field(..., description="配置类型：USER/ROLE/DEPT/DEFAULT")
    user_id: Optional[int] = Field(None, description="用户ID（config_type=USER时必填）")
    role_id: Optional[int] = Field(None, description="角色ID（config_type=ROLE时必填）")
    dept_id: Optional[int] = Field(None, description="部门ID（config_type=DEPT时必填）")
    hourly_rate: Decimal = Field(..., description="时薪（元/小时）")
    effective_date: Optional[date] = Field(None, description="生效日期")
    expiry_date: Optional[date] = Field(None, description="失效日期")
    remark: Optional[str] = Field(None, description="备注")


class HourlyRateConfigUpdate(BaseModel):
    """更新时薪配置"""
    hourly_rate: Optional[Decimal] = Field(None, description="时薪（元/小时）")
    effective_date: Optional[date] = Field(None, description="生效日期")
    expiry_date: Optional[date] = Field(None, description="失效日期")
    is_active: Optional[bool] = Field(None, description="是否启用")
    remark: Optional[str] = Field(None, description="备注")


class HourlyRateConfigResponse(TimestampSchema):
    """时薪配置响应"""
    id: int
    config_type: str
    user_id: Optional[int] = None
    role_id: Optional[int] = None
    dept_id: Optional[int] = None
    hourly_rate: Decimal
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    is_active: bool
    remark: Optional[str] = None
    created_by: Optional[int] = None
    
    # 关联信息
    user_name: Optional[str] = None
    role_name: Optional[str] = None
    dept_name: Optional[str] = None
    
    class Config:
        from_attributes = True






