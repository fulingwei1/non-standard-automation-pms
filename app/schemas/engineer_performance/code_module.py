# -*- coding: utf-8 -*-
"""
code_module Schemas

包含code_module相关的 Schema 定义
"""

"""
工程师绩效评价模块 Pydantic Schemas
包含：请求/响应模型、数据验证
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ==================== 代码模块 Schemas ====================

class CodeModuleBase(BaseModel):
    """代码模块基础"""
    module_name: str = Field(..., max_length=100, description="模块名称")
    category: Optional[str] = Field(None, description="分类")
    language: Optional[str] = Field(None, description="编程语言")
    description: Optional[str] = Field(None, description="描述")
    version: Optional[str] = Field(None, description="版本")
    repository_url: Optional[str] = Field(None, description="仓库地址")


class CodeModuleCreate(CodeModuleBase):
    """创建代码模块"""
    pass


class CodeModuleUpdate(BaseModel):
    """更新代码模块"""
    module_name: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    repository_url: Optional[str] = None
    status: Optional[str] = None


class CodeModuleResponse(CodeModuleBase):
    """代码模块响应"""
    id: int
    module_code: Optional[str] = None
    contributor_id: int
    contributor_name: Optional[str] = None
    reuse_count: int = 0
    rating_score: Optional[Decimal] = None
    rating_count: int = 0
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


