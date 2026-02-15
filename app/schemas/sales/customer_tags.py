# -*- coding: utf-8 -*-
"""
客户标签 Schema
"""

from typing import List

from pydantic import BaseModel, Field

from ..common import TimestampSchema


class CustomerTagCreate(BaseModel):
    """创建客户标签"""

    customer_id: int = Field(description="客户ID")
    tag_name: str = Field(max_length=50, description="标签名称")


class CustomerTagBatchCreate(BaseModel):
    """批量创建客户标签"""

    customer_id: int = Field(description="客户ID")
    tag_names: List[str] = Field(description="标签名称列表")


class CustomerTagResponse(TimestampSchema):
    """客户标签响应"""

    id: int = Field(description="标签ID")
    customer_id: int = Field(description="客户ID")
    tag_name: str = Field(description="标签名称")


class PredefinedTagsResponse(BaseModel):
    """预定义标签列表响应"""

    tags: List[str] = Field(description="预定义标签列表")
