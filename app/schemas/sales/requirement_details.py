# -*- coding: utf-8 -*-
"""
需求明细相关 Schema
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


def _normalize_empty_scalar(value):
    if value == "":
        return None
    return value


class LeadRequirementDetailBase(BaseModel):
    """需求明细基础模型"""

    customer_factory_location: Optional[str] = Field(None, description="客户工厂/地点")
    target_object_type: Optional[str] = Field(None, description="被测对象类型")
    application_scenario: Optional[str] = Field(None, description="应用场景")
    delivery_mode: Optional[str] = Field(None, description="计划交付模式")
    expected_delivery_date: Optional[datetime] = Field(None, description="期望交付日期")
    requirement_source: Optional[str] = Field(None, description="需求来源")
    requirement_maturity: Optional[int] = Field(None, description="需求成熟度")
    has_sow: Optional[bool] = Field(None, description="是否有客户SOW/URS")
    has_interface_doc: Optional[bool] = Field(None, description="是否有接口协议文档")
    has_drawing_doc: Optional[bool] = Field(None, description="是否有图纸/原理/IO清单")
    cycle_time_seconds: Optional[float] = Field(None, description="节拍要求(CT秒)")
    workstation_count: Optional[int] = Field(None, description="工位数/并行数")
    acceptance_method: Optional[str] = Field(None, description="验收方式")
    acceptance_basis: Optional[str] = Field(None, description="验收依据")
    requirement_items: Optional[str] = Field(None, description="需求项目(JSON)")
    technical_spec: Optional[str] = Field(None, description="技术规格(JSON)")
    delivery_requirements: Optional[str] = Field(None, description="交付要求")
    special_notes: Optional[str] = Field(None, description="特殊说明")

    @field_validator(
        "expected_delivery_date",
        "requirement_maturity",
        "cycle_time_seconds",
        "workstation_count",
        mode="before",
    )
    @classmethod
    def normalize_empty_scalar_fields(cls, value):
        """兼容前端表单把空值作为空字符串提交。"""
        return _normalize_empty_scalar(value)


class LeadRequirementDetailCreate(LeadRequirementDetailBase):
    """创建需求明细"""

    pass


class LeadRequirementDetailUpdate(BaseModel):
    """更新需求明细"""

    customer_factory_location: Optional[str] = None
    target_object_type: Optional[str] = None
    application_scenario: Optional[str] = None
    delivery_mode: Optional[str] = None
    expected_delivery_date: Optional[datetime] = None
    requirement_source: Optional[str] = None
    requirement_maturity: Optional[int] = None
    has_sow: Optional[bool] = None
    has_interface_doc: Optional[bool] = None
    has_drawing_doc: Optional[bool] = None
    cycle_time_seconds: Optional[float] = None
    workstation_count: Optional[int] = None
    acceptance_method: Optional[str] = None
    acceptance_basis: Optional[str] = None
    requirement_items: Optional[str] = None
    technical_spec: Optional[str] = None
    delivery_requirements: Optional[str] = None
    special_notes: Optional[str] = None

    @field_validator(
        "expected_delivery_date",
        "requirement_maturity",
        "cycle_time_seconds",
        "workstation_count",
        mode="before",
    )
    @classmethod
    def normalize_empty_scalar_fields(cls, value):
        """兼容前端表单把空值作为空字符串提交。"""
        return _normalize_empty_scalar(value)


class LeadRequirementDetailResponse(LeadRequirementDetailBase):
    """需求明细响应"""

    id: int
    lead_id: int
    requirement_version: Optional[str] = None
    is_frozen: Optional[bool] = None
    frozen_at: Optional[datetime] = None
    frozen_by: Optional[int] = None
    frozen_by_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
