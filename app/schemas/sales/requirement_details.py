# -*- coding: utf-8 -*-
"""
需求明细相关 Schema
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LeadRequirementDetailBase(BaseModel):
    """需求明细基础模型"""
    lead_id: int = Field(..., description="线索ID")
    requirement_items: Optional[str] = Field(None, description="需求项目(JSON)")
    technical_spec: Optional[str] = Field(None, description="技术规格(JSON)")
    delivery_requirements: Optional[str] = Field(None, description="交付要求")
    special_notes: Optional[str] = Field(None, description="特殊说明")


class LeadRequirementDetailCreate(LeadRequirementDetailBase):
    """创建需求明细"""
    pass


class LeadRequirementDetailUpdate(BaseModel):
    """更新需求明细"""
    requirement_items: Optional[str] = None
    technical_spec: Optional[str] = None
    delivery_requirements: Optional[str] = None
    special_notes: Optional[str] = None


class LeadRequirementDetailResponse(LeadRequirementDetailBase):
    """需求明细响应"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
