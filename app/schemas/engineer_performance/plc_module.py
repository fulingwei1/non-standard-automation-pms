# -*- coding: utf-8 -*-
"""
plc_module Schemas

包含plc_module相关的 Schema 定义
"""

"""
工程师绩效评价模块 Pydantic Schemas
包含：请求/响应模型、数据验证
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ==================== PLC模块库 Schemas ====================

class PlcModuleLibraryBase(BaseModel):
    """PLC模块库基础"""
    module_name: str = Field(..., max_length=100, description="模块名称")
    category: Optional[str] = Field(None, description="分类")
    plc_brand: Optional[str] = Field(None, description="适用PLC品牌")
    description: Optional[str] = Field(None, description="描述")
    version: Optional[str] = Field(None, description="版本")
    file_path: Optional[str] = Field(None, description="文件路径")


class PlcModuleLibraryCreate(PlcModuleLibraryBase):
    """创建PLC模块"""
    pass


class PlcModuleLibraryUpdate(BaseModel):
    """更新PLC模块"""
    module_name: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    file_path: Optional[str] = None
    status: Optional[str] = None


class PlcModuleLibraryResponse(PlcModuleLibraryBase):
    """PLC模块响应"""
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


