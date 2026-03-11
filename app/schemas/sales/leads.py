# -*- coding: utf-8 -*-
"""
销售线索管理 Schema
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
        default=None, description="选择的优势产品ID列表"
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
    selected_advantage_products: Optional[List[int]] = Field(
        default=None, description="选择的优势产品ID列表"
    )
    owner_name: Optional[str] = Field(default=None, description="负责人姓名")


class LeadFollowUpCreate(BaseModel):
    """创建线索跟进

    兼容两套字段命名：
    - 新版（前后端当前使用）：follow_up_type / content
    - 旧版（历史调用）：action_type / action_summary
    """

    model_config = ConfigDict(populate_by_name=True)

    lead_id: Optional[int] = Field(default=None, description="线索ID（由路径参数决定，可选）")

    # 新版字段
    follow_up_type: Optional[str] = Field(default=None, description="跟进类型")
    content: Optional[str] = Field(default=None, description="跟进内容")

    # 旧版兼容字段
    action_type: Optional[str] = Field(default=None, description="行动类型（旧字段）")
    action_summary: Optional[str] = Field(default=None, description="行动摘要（旧字段）")

    next_action: Optional[str] = Field(default=None, description="下一步行动")
    next_action_at: Optional[datetime] = Field(default=None, description="下次行动时间")
    attachments: Optional[str] = Field(default=None, description="附件JSON")

    @model_validator(mode="after")
    def normalize_legacy_fields(self):
        # 旧字段 -> 新字段 归一化
        if not self.follow_up_type and self.action_type:
            self.follow_up_type = self.action_type
        if not self.content and self.action_summary:
            self.content = self.action_summary

        if not self.follow_up_type:
            raise ValueError("follow_up_type/action_type 至少提供一个")
        if not self.content:
            raise ValueError("content/action_summary 至少提供一个")
        return self


class LeadFollowUpResponse(TimestampSchema):
    """线索跟进响应"""

    id: int = Field(description="跟进ID")
    lead_id: int = Field(description="线索ID")
    follow_up_type: str = Field(description="跟进类型")
    content: str = Field(description="跟进内容")
    next_action: Optional[str] = Field(default=None, description="下一步行动")
    next_action_at: Optional[datetime] = Field(default=None, description="下次行动时间")
    created_by: Optional[int] = Field(default=None, description="创建人ID")
    attachments: Optional[str] = Field(default=None, description="附件JSON")
    creator_name: Optional[str] = Field(default=None, description="创建人姓名")

    # 兼容旧前端/旧接口字段（只读别名）
    action_type: Optional[str] = Field(default=None, description="行动类型（兼容）")
    action_summary: Optional[str] = Field(default=None, description="行动摘要（兼容）")
    created_by_name: Optional[str] = Field(default=None, description="创建人姓名（兼容）")

    @model_validator(mode="after")
    def fill_compat_fields(self):
        if not self.action_type:
            self.action_type = self.follow_up_type
        if not self.action_summary:
            self.action_summary = self.content
        if not self.created_by_name:
            self.created_by_name = self.creator_name
        return self
