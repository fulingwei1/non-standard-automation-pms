# -*- coding: utf-8 -*-
"""
技术规格管理 Schema
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .common import PaginatedResponse, TimestampSchema

# ==================== 技术规格要求 ====================

class TechnicalSpecRequirementCreate(BaseModel):
    """创建技术规格要求"""
    project_id: int = Field(description="项目ID")
    document_id: Optional[int] = Field(default=None, description="关联技术规格书文档ID")
    material_code: Optional[str] = Field(default=None, max_length=50, description="物料编码")
    material_name: str = Field(max_length=200, description="物料名称")
    specification: str = Field(max_length=500, description="规格型号要求")
    brand: Optional[str] = Field(default=None, max_length=100, description="品牌要求")
    model: Optional[str] = Field(default=None, max_length=100, description="型号要求")
    key_parameters: Optional[Dict[str, Any]] = Field(default=None, description="关键参数（JSON）")
    requirement_level: str = Field(default="REQUIRED", description="要求级别：REQUIRED/OPTIONAL/STRICT")
    remark: Optional[str] = Field(default=None, description="备注说明")


class TechnicalSpecRequirementUpdate(BaseModel):
    """更新技术规格要求"""
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    specification: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    key_parameters: Optional[Dict[str, Any]] = None
    requirement_level: Optional[str] = None
    remark: Optional[str] = None


class TechnicalSpecRequirementResponse(TimestampSchema):
    """技术规格要求响应"""
    id: int
    project_id: int
    document_id: Optional[int] = None
    material_code: Optional[str] = None
    material_name: str
    specification: str
    brand: Optional[str] = None
    model: Optional[str] = None
    key_parameters: Optional[Dict[str, Any]] = None
    requirement_level: str = "REQUIRED"
    remark: Optional[str] = None
    extracted_by: Optional[int] = None
    extracted_by_name: Optional[str] = None


class TechnicalSpecRequirementListResponse(PaginatedResponse[TechnicalSpecRequirementResponse]):
    """技术规格要求列表响应"""
    pass


# ==================== 规格匹配记录 ====================

class SpecMatchRecordResponse(TimestampSchema):
    """规格匹配记录响应"""
    id: int
    project_id: int
    spec_requirement_id: Optional[int] = None
    match_type: str
    match_target_id: int
    match_status: str
    match_score: Optional[Decimal] = None
    differences: Optional[Dict[str, Any]] = None
    alert_id: Optional[int] = None

    # 关联信息
    spec_requirement: Optional[TechnicalSpecRequirementResponse] = None
    match_target_name: Optional[str] = None


class SpecMatchRecordListResponse(PaginatedResponse[SpecMatchRecordResponse]):
    """规格匹配记录列表响应"""
    pass


# ==================== 规格匹配检查 ====================

class SpecMatchCheckRequest(BaseModel):
    """规格匹配检查请求"""
    project_id: int = Field(description="项目ID")
    match_type: str = Field(description="匹配类型：BOM/PURCHASE_ORDER")
    match_target_id: Optional[int] = Field(default=None, description="匹配对象ID，为空则检查所有")


class SpecMatchResult(BaseModel):
    """规格匹配结果"""
    spec_requirement_id: int
    material_name: str
    match_status: str
    match_score: Optional[Decimal] = None
    differences: Optional[Dict[str, Any]] = None
    alert_id: Optional[int] = None


class SpecMatchCheckResponse(BaseModel):
    """规格匹配检查响应"""
    total_checked: int = Field(description="检查总数")
    matched_count: int = Field(description="匹配数量")
    mismatched_count: int = Field(description="不匹配数量")
    unknown_count: int = Field(description="未知数量")
    results: List[SpecMatchResult] = Field(default=[], description="匹配结果列表")


# ==================== 规格提取 ====================

class SpecExtractRequest(BaseModel):
    """规格提取请求"""
    document_id: int = Field(description="文档ID")
    project_id: int = Field(description="项目ID")
    auto_extract: bool = Field(default=False, description="是否自动提取")


class SpecExtractResponse(BaseModel):
    """规格提取响应"""
    extracted_count: int = Field(description="提取数量")
    requirements: List[TechnicalSpecRequirementResponse] = Field(default=[], description="提取的规格要求")




