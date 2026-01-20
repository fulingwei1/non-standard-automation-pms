# -*- coding: utf-8 -*-
"""
审批模板 Schema
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ApprovalTemplateBase(BaseModel):
    """审批模板基础字段"""
    template_code: str = Field(..., min_length=1, max_length=50, description="模板编码")
    template_name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    category: Optional[str] = Field(None, max_length=30, description="分类")
    description: Optional[str] = Field(None, description="模板描述")
    icon: Optional[str] = Field(None, max_length=100, description="图标")
    form_schema: Optional[Dict[str, Any]] = Field(None, description="表单结构定义")
    visible_scope: Optional[Dict[str, Any]] = Field(None, description="可见范围")
    entity_type: Optional[str] = Field(None, max_length=50, description="关联的业务实体类型")


class ApprovalTemplateCreate(ApprovalTemplateBase):
    """创建审批模板"""
    pass


class ApprovalTemplateUpdate(BaseModel):
    """更新审批模板"""
    template_name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = Field(None, max_length=30)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=100)
    form_schema: Optional[Dict[str, Any]] = None
    visible_scope: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ApprovalTemplateResponse(ApprovalTemplateBase):
    """审批模板响应"""
    id: int
    version: int
    is_published: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApprovalTemplateListResponse(BaseModel):
    """审批模板列表响应"""
    total: int
    page: int
    page_size: int
    items: List[ApprovalTemplateResponse]
