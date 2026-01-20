# -*- coding: utf-8 -*-
"""
需求冻结相关 Schema
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RequirementFreezeBase(BaseModel):
    """需求冻结基础模型"""
    source_type: str = Field(..., description="来源类型：LEAD/OPPORTUNITY")
    source_id: int = Field(..., description="来源ID")
    freeze_version: str = Field(..., description="冻结版本号")
    frozen_content: Optional[str] = Field(None, description="冻结内容(JSON)")
    frozen_by: Optional[int] = Field(None, description="冻结人ID")
    freeze_reason: Optional[str] = Field(None, description="冻结原因")


class RequirementFreezeCreate(RequirementFreezeBase):
    """创建需求冻结"""
    pass


class RequirementFreezeUpdate(BaseModel):
    """更新需求冻结"""
    freeze_reason: Optional[str] = None


class RequirementFreezeResponse(RequirementFreezeBase):
    """需求冻结响应"""
    id: int
    frozen_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
