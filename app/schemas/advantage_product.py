# -*- coding: utf-8 -*-
"""
优势产品数据模式
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

# ==================== 产品类别 ====================

class AdvantageProductCategoryBase(BaseModel):
    """产品类别基础"""
    code: str = Field(..., max_length=50, description="类别编码")
    name: str = Field(..., max_length=100, description="类别名称")
    description: Optional[str] = Field(None, description="类别描述")
    sort_order: int = Field(0, description="排序序号")
    is_active: bool = Field(True, description="是否启用")


class AdvantageProductCategoryCreate(AdvantageProductCategoryBase):
    """创建产品类别"""
    pass


class AdvantageProductCategoryUpdate(BaseModel):
    """更新产品类别"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class AdvantageProductCategoryResponse(AdvantageProductCategoryBase):
    """产品类别响应"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    product_count: int = Field(0, description="产品数量")

    class Config:
        from_attributes = True


# ==================== 优势产品 ====================

class AdvantageProductBase(BaseModel):
    """优势产品基础"""
    product_code: str = Field(..., max_length=50, description="产品编码")
    product_name: str = Field(..., max_length=200, description="产品名称")
    category_id: Optional[int] = Field(None, description="所属类别ID")
    series_code: Optional[str] = Field(None, max_length=50, description="产品系列编码")
    description: Optional[str] = Field(None, description="产品描述")
    is_active: bool = Field(True, description="是否启用")


class AdvantageProductCreate(AdvantageProductBase):
    """创建优势产品"""
    pass


class AdvantageProductUpdate(BaseModel):
    """更新优势产品"""
    product_name: Optional[str] = Field(None, max_length=200)
    category_id: Optional[int] = None
    series_code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class AdvantageProductResponse(AdvantageProductBase):
    """优势产品响应"""
    id: int
    category_name: Optional[str] = Field(None, description="类别名称")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdvantageProductSimple(BaseModel):
    """优势产品简略（用于下拉选择）"""
    id: int
    product_code: str
    product_name: str
    category_id: Optional[int] = None
    category_name: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== 产品列表（按类别分组） ====================

class AdvantageProductGrouped(BaseModel):
    """按类别分组的产品列表"""
    category: AdvantageProductCategoryResponse
    products: List[AdvantageProductResponse] = Field(default_factory=list)


# ==================== Excel 导入 ====================

class AdvantageProductImportRequest(BaseModel):
    """Excel 导入请求"""
    clear_existing: bool = Field(True, description="是否先清空现有数据")


class AdvantageProductImportResult(BaseModel):
    """Excel 导入结果"""
    success: bool
    categories_created: int = Field(0, description="创建的类别数")
    products_created: int = Field(0, description="创建的产品数")
    products_updated: int = Field(0, description="更新的产品数")
    products_skipped: int = Field(0, description="跳过的产品数")
    errors: List[str] = Field(default_factory=list, description="错误信息")
    message: str = ""


# ==================== 产品匹配检查 ====================

class ProductMatchCheckRequest(BaseModel):
    """产品匹配检查请求"""
    product_name: str = Field(..., description="产品名称")


class ProductMatchCheckResponse(BaseModel):
    """产品匹配检查响应"""
    match_type: str = Field(..., description="匹配类型: ADVANTAGE/NEW/UNKNOWN")
    matched_product: Optional[AdvantageProductSimple] = Field(None, description="匹配到的优势产品")
    suggestions: List[AdvantageProductSimple] = Field(default_factory=list, description="相似产品建议")
