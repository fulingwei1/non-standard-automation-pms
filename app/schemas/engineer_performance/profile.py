# -*- coding: utf-8 -*-
"""
profile Schemas

包含profile相关的 Schema 定义
"""

"""
工程师绩效评价模块 Pydantic Schemas
包含：请求/响应模型、数据验证
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ==================== 基础 Schemas ====================

class EngineerProfileBase(BaseModel):
    """工程师档案基础"""
    job_type: str = Field(..., description="岗位类型")
    job_level: Optional[str] = Field('junior', description="职级")
    skills: Optional[List[str]] = Field(None, description="技能标签")
    certifications: Optional[List[str]] = Field(None, description="资质证书")
    job_start_date: Optional[date] = Field(None, description="岗位开始日期")
    level_start_date: Optional[date] = Field(None, description="级别开始日期")


class EngineerProfileCreate(EngineerProfileBase):
    """创建工程师档案"""
    user_id: int = Field(..., description="用户ID")


class EngineerProfileUpdate(BaseModel):
    """更新工程师档案"""
    job_type: Optional[str] = None
    job_level: Optional[str] = None
    skills: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    job_start_date: Optional[date] = None
    level_start_date: Optional[date] = None


class EngineerProfileResponse(EngineerProfileBase):
    """工程师档案响应"""
    id: int
    user_id: int
    user_name: Optional[str] = None
    department_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


