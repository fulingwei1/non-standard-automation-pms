# -*- coding: utf-8 -*-
"""
worker Schemas

包含worker相关的 Schema 定义
"""

"""
生产管理模块 Schema
"""
from typing import List, Optional

from pydantic import BaseModel, Field

from ..common import PaginatedResponse, TimestampSchema


# ==================== 生产人员管理 ====================

class WorkerCreate(BaseModel):
    """创建生产人员"""
    worker_code: str = Field(max_length=50, description="工人编码")
    worker_name: str = Field(max_length=100, description="工人姓名")
    user_id: Optional[int] = Field(default=None, description="关联用户ID")
    workshop_id: Optional[int] = Field(default=None, description="所属车间ID")
    worker_type: Optional[str] = Field(default=None, description="工人类型")
    phone: Optional[str] = Field(default=None, max_length=20, description="联系电话")
    status: str = Field(default="ACTIVE", description="状态：ACTIVE/LEAVE/RESIGNED")
    remark: Optional[str] = None


class WorkerUpdate(BaseModel):
    """更新生产人员"""
    worker_name: Optional[str] = None
    workshop_id: Optional[int] = None
    worker_type: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class WorkerResponse(TimestampSchema):
    """生产人员响应"""
    id: int
    worker_code: str
    worker_name: str
    user_id: Optional[int] = None
    workshop_id: Optional[int] = None
    workshop_name: Optional[str] = None
    worker_type: Optional[str] = None
    phone: Optional[str] = None
    status: str
    remark: Optional[str] = None


class WorkerListResponse(PaginatedResponse):
    """生产人员列表响应"""
    items: List[WorkerResponse]


