# -*- coding: utf-8 -*-
"""
销售线索管理 Schema
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ..common import TimestampSchema


class LeadCreate(BaseModel):
    """创建线索"""

    model_config = ConfigDict(populate_by_name=True)

    lead_code: Optional[str] = Field(default=None, max_length=20, description="线索编码")
    source: Optional[str] = Field(default=None, max_length=50, description="来源")
    customer_name: Optional[str] = Field(default=None, max_length=100, description="客户名称")
    industry: Optional[str] = Field(default=None, max_length=50, description="行业")
    contact_name: Optional[str] = Field(default=None, max_length=50, description="联系人")
    contact_phone: Optional[str] = Field(default=None, max_length=20, description="联系电话")
    demand_summary: Optional[str] = Field(default=None, description="需求摘要")
    owner_id: Optional[int] = Field(default=None, description="负责人ID")
    status: Optional[str] = Field(default="NEW", description="状态")
    next_action_at: Optional[datetime] = Field(default=None, description="下次行动时间")
    selected_advantage_products: Optional[List[int]] = Field(
        default=None,
        description="选择的优势产品ID列表"
    )


class LeadUpdate(BaseModel):
    """更新线索"""

    source: Optional[str] = None
    customer_name: Optional[str] = None
    industry: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    demand_summary: Optional[str] = None
    owner_id: Optional[int] = None
    status: Optional[str] = None
    next_action_at: Optional[datetime] = None
    selected_advantage_products: Optional[List[int]] = None


class LeadResponse(TimestampSchema):
    """线索响应"""

    id: int = Field(description="线索ID")
    lead_code: str = Field(description="线索编码")
    source: Optional[str] = Field(default=None, description="来源")
    customer_name: Optional[str] = Field(default=None, description="客户名称")
    industry: Optional[str] = Field(default=None, description="行业")
    contact_name: Optional[str] = Field(default=None, description="联系人")
    contact_phone: Optional[str] = Field(default=None, description="联系电话")
    demand_summary: Optional[str] = Field(default=None, description="需求摘要")
    owner_id: Optional[int] = Field(default=None, description="负责人ID")
    status: str = Field(description="状态")
    next_action_at: Optional[datetime] = Field(default=None, description="下次行动时间")
    selected_advantage_products: Optional[List[int]] = Field(default=None, description="选择的优势产品ID列表")
    owner_name: Optional[str] = Field(default=None, description="负责人姓名")


class LeadFollowUpCreate(BaseModel):
    """创建线索跟进"""

    model_config = ConfigDict(populate_by_name=True)

    lead_id: int = Field(description="线索ID")
    action_type: str = Field(description="行动类型")
    action_summary: Optional[str] = Field(default=None, description="行动摘要")
    next_action: Optional[str] = Field(default=None, description="下一步行动")
    next_action_at: Optional[datetime] = Field(default=None, description="下次行动时间")


class LeadFollowUpResponse(TimestampSchema):
    """线索跟进响应"""

    id: int = Field(description="跟进ID")
    lead_id: int = Field(description="线索ID")
    action_type: str = Field(description="行动类型")
    action_summary: Optional[str] = Field(default=None, description="行动摘要")
    next_action: Optional[str] = Field(default=None, description="下一步行动")
    next_action_at: Optional[datetime] = Field(default=None, description="下次行动时间")
    created_by_name: Optional[str] = Field(default=None, description="创建人姓名")
