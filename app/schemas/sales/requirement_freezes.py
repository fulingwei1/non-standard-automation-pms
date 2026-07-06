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
    freeze_type: str = Field(..., description="冻结点类型")
    version_number: str = Field(..., description="冻结版本号")
    requires_ecr: bool = Field(True, description="冻结后变更是否必须走ECR/ECN")
    description: Optional[str] = Field(None, description="冻结说明")


class RequirementFreezeCreate(RequirementFreezeBase):
    """创建需求冻结"""

    pass


class RequirementFreezeUpdate(BaseModel):
    """更新需求冻结"""

    description: Optional[str] = None


class RequirementFreezeResponse(RequirementFreezeBase):
    """需求冻结响应"""

    id: int
    freeze_time: Optional[datetime] = None
    frozen_by: Optional[int] = None
    frozen_by_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
