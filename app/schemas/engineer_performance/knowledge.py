# -*- coding: utf-8 -*-
"""
knowledge Schemas

包含knowledge相关的 Schema 定义
"""

"""
工程师绩效评价模块 Pydantic Schemas
包含：请求/响应模型、数据验证
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ==================== 知识贡献 Schemas ====================

class KnowledgeContributionBase(BaseModel):
    """知识贡献基础"""
    contribution_type: str = Field(..., description="贡献类型")
    job_type: Optional[str] = Field(None, description="所属岗位领域")
    title: str = Field(..., max_length=200, description="标题")
    description: Optional[str] = Field(None, description="描述")
    file_path: Optional[str] = Field(None, description="文件路径")
    tags: Optional[List[str]] = Field(None, description="标签")


class KnowledgeContributionCreate(KnowledgeContributionBase):
    """创建知识贡献"""
    pass


class KnowledgeContributionUpdate(BaseModel):
    """更新知识贡献"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    file_path: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None


class KnowledgeContributionResponse(KnowledgeContributionBase):
    """知识贡献响应"""
    id: int
    contributor_id: int
    contributor_name: Optional[str] = None
    reuse_count: int = 0
    rating_score: Optional[Decimal] = None
    rating_count: int = 0
    status: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeReuseCreate(BaseModel):
    """创建知识复用记录"""
    contribution_id: int = Field(..., description="贡献ID")
    project_id: Optional[int] = Field(None, description="项目ID")
    reuse_type: Optional[str] = Field(None, description="复用类型")
    rating: Optional[int] = Field(None, ge=1, le=5, description="评分")
    feedback: Optional[str] = Field(None, description="反馈")


