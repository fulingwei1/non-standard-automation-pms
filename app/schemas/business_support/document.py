# -*- coding: utf-8 -*-
"""
文档归档 Schema
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from ...schemas.common import TimestampSchema


class DocumentArchiveCreate(BaseModel):
    """创建文件归档"""

    archive_no: str = Field(max_length=50, description="归档编号")
    document_type: str = Field(max_length=50, description="文件类型")
    related_type: str = Field(max_length=50, description="关联类型")
    related_id: int = Field(description="关联ID")
    document_name: str = Field(max_length=200, description="文件名称")
    file_path: str = Field(max_length=500, description="文件路径")
    file_size: Optional[int] = Field(default=None, description="文件大小(字节)")
    archive_location: Optional[str] = Field(default=None, max_length=200, description="归档位置")
    archive_date: date = Field(description="归档日期")
    remark: Optional[str] = Field(default=None, description="备注")


class DocumentArchiveUpdate(BaseModel):
    """更新文件归档"""

    document_name: Optional[str] = None
    archive_location: Optional[str] = None
    archive_date: Optional[date] = None
    status: Optional[str] = None
    remark: Optional[str] = None


class DocumentArchiveResponse(TimestampSchema):
    """文件归档响应"""

    id: int
    archive_no: str
    document_type: Optional[str] = None
    related_type: Optional[str] = None
    related_id: Optional[int] = None
    document_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    archive_location: Optional[str] = None
    archive_date: Optional[date] = None
    archiver_id: Optional[int] = None
    status: Optional[str] = None
    remark: Optional[str] = None
