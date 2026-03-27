# -*- coding: utf-8 -*-
"""
物料采购管理 P3 增强 Schema
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class ShortageWasteCalculationRequest(BaseModel):
    """缺料等待浪费计算请求"""

    project_id: Optional[int] = Field(default=None, description="项目ID")
    material_id: Optional[int] = Field(default=None, description="物料ID")
    material_code: Optional[str] = Field(default=None, description="物料编码")
    shortage_reason: Optional[str] = Field(default=None, description="缺料原因")

    waiting_workers: int = Field(default=0, ge=0, description="等待人数")
    labor_hourly_rate: Decimal = Field(default=Decimal("80"), ge=0, description="工时单价")
    waiting_hours: Decimal = Field(default=Decimal("0"), ge=0, description="等待小时")

    idle_machines: int = Field(default=0, ge=0, description="设备台数")
    machine_hourly_rate: Decimal = Field(default=Decimal("120"), ge=0, description="台时费率")

    contract_amount: Decimal = Field(default=Decimal("0"), ge=0, description="合同金额")
    delay_days: int = Field(default=0, ge=0, description="延期天数")
    daily_penalty_rate: Decimal = Field(default=Decimal("0.001"), ge=0, description="日罚款率")
    daily_output_value: Decimal = Field(default=Decimal("0"), ge=0, description="日均产值")

    include_management_buffer: bool = Field(default=False, description="是否计入管理缓冲系数")
    management_buffer_rate: Decimal = Field(
        default=Decimal("0.1"), ge=0, description="管理缓冲系数"
    )


class DuplicatePurchaseCheckRequest(BaseModel):
    """重复采购检查请求"""

    project_id: Optional[int] = Field(default=None, description="项目ID")
    material_id: Optional[int] = Field(default=None, description="物料ID")
    material_code: Optional[str] = Field(default=None, description="物料编码")
    material_name: Optional[str] = Field(default=None, description="物料名称")
    specification: Optional[str] = Field(default=None, description="规格型号")
    requested_quantity: Decimal = Field(default=Decimal("0"), ge=0, description="申请数量")
    requested_bom_version: Optional[str] = Field(default=None, description="申请依据BOM版本")
    check_open_purchase_requests: bool = Field(default=True, description="是否检查开放采购申请")
    check_open_purchase_orders: bool = Field(default=True, description="是否检查开放采购订单")
    check_bom_consistency: bool = Field(default=True, description="是否检查BOM版本一致性")
