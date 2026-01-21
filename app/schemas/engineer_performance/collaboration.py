# -*- coding: utf-8 -*-
"""
collaboration Schemas

包含collaboration相关的 Schema 定义
"""

"""
工程师绩效评价模块 Pydantic Schemas
包含：请求/响应模型、数据验证
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ==================== 跨部门协作 Schemas ====================

class CollaborationRatingBase(BaseModel):
    """跨部门协作评价基础"""
    ratee_id: int = Field(..., description="被评价人ID")
    communication_score: int = Field(..., ge=1, le=5, description="沟通配合")
    response_score: int = Field(..., ge=1, le=5, description="响应速度")
    delivery_score: int = Field(..., ge=1, le=5, description="交付质量")
    interface_score: int = Field(..., ge=1, le=5, description="接口规范")
    comment: Optional[str] = Field(None, description="评价备注")
    project_id: Optional[int] = Field(None, description="关联项目ID")


class CollaborationRatingCreate(CollaborationRatingBase):
    """创建跨部门评价"""
    period_id: int = Field(..., description="考核周期ID")


class CollaborationRatingResponse(CollaborationRatingBase):
    """跨部门评价响应"""
    id: int
    period_id: int
    rater_id: int
    rater_name: Optional[str] = None
    ratee_name: Optional[str] = None
    rater_job_type: Optional[str] = None
    ratee_job_type: Optional[str] = None
    total_score: Optional[Decimal] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CollaborationMatrixResponse(BaseModel):
    """协作矩阵响应"""
    period_id: int
    matrix: Dict[str, Dict[str, float]] = Field(..., description="协作评分矩阵")
    details: List[Dict[str, Any]] = Field(default_factory=list, description="详细评价")


