# -*- coding: utf-8 -*-
"""
通用 Schema 定义
"""

from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar('T')


class ResponseModel(BaseModel, Generic[T]):
    """通用响应模型"""
    code: int = Field(default=200, description="响应代码")
    message: str = Field(default="success", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型"""
    items: List[T] = Field(default=[], description="数据列表")
    total: int = Field(default=0, description="总记录数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页条数")
    pages: int = Field(default=0, description="总页数")


class PageParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页条数")
    sort_by: Optional[str] = Field(default=None, description="排序字段")
    sort_order: Optional[str] = Field(default="desc", description="排序方向")


class IdResponse(BaseModel):
    """ID响应"""
    id: int = Field(description="记录ID")


class MessageResponse(BaseModel):
    """消息响应"""
    message: str = Field(description="消息内容")


class StatusUpdate(BaseModel):
    """状态更新"""
    status: str = Field(description="新状态")
    remark: Optional[str] = Field(default=None, description="备注")


class BaseSchema(BaseModel):
    """基础 Schema"""

    class Config:
        from_attributes = True


class TimestampSchema(BaseSchema):
    """带时间戳的 Schema"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AuditSchema(TimestampSchema):
    """带审计信息的 Schema"""
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None
