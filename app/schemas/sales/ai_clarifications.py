# -*- coding: utf-8 -*-
"""
AI 澄清相关 Schema
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AIClarificationBase(BaseModel):
    """AI 澄清基础模型"""
    source_type: str = Field(..., description="来源类型：LEAD/OPPORTUNITY")
    source_id: int = Field(..., description="来源ID")
    round: int = Field(1, description="澄清轮次")
    questions: str = Field(..., description="AI生成的问题(JSON Array)")


class AIClarificationCreate(AIClarificationBase):
    """创建 AI 澄清"""
    pass


class AIClarificationUpdate(BaseModel):
    """更新 AI 澄清"""
    answers: Optional[str] = Field(None, description="用户回答(JSON Array)")


class AIClarificationResponse(AIClarificationBase):
    """AI 澄清响应"""
    id: int
    answers: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
