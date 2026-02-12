# -*- coding: utf-8 -*-
"""
design_review Schemas

包含design_review相关的 Schema 定义
"""

"""
工程师绩效评价模块 Pydantic Schemas
包含：请求/响应模型、数据验证
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ==================== 设计评审 Schemas ====================

class DesignReviewBase(BaseModel):
    """设计评审基础"""
    project_id: Optional[int] = Field(None, description="项目ID")
    design_name: str = Field(..., max_length=200, description="设计名称")
    design_type: Optional[str] = Field(None, description="设计类型")
    design_code: Optional[str] = Field(None, description="设计编号")
    version: Optional[str] = Field(None, description="版本号")


class DesignReviewCreate(DesignReviewBase):
    """创建设计评审"""
    designer_id: int = Field(..., description="设计者ID")


class DesignReviewUpdate(BaseModel):
    """更新设计评审（评审结果）"""
    review_date: Optional[date] = None
    reviewer_id: Optional[int] = None
    result: Optional[str] = None
    is_first_pass: Optional[bool] = None
    issues_found: Optional[int] = None
    review_comments: Optional[str] = None


class DesignReviewResponse(DesignReviewBase):
    """设计评审响应"""
    id: int
    designer_id: int
    designer_name: Optional[str] = None
    review_date: Optional[date] = None
    reviewer_id: Optional[int] = None
    reviewer_name: Optional[str] = None
    result: Optional[str] = None
    is_first_pass: Optional[bool] = None
    issues_found: int = 0
    review_comments: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


