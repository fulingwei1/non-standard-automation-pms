# -*- coding: utf-8 -*-
"""
物料进度可视化 Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


# ==================== 1. 项目物料进度总览 ====================

class KeyMaterialItem(BaseModel):
    """关键物料"""
    material_id: int
    material_code: str
    material_name: str
    specification: Optional[str] = None
    required_qty: Decimal
    received_qty: Decimal
    shortage_qty: Decimal
    kitting_status: str
    expected_arrival_date: Optional[date] = None
    impact_description: Optional[str] = None


class KittingTrendPoint(BaseModel):
    """齐套率趋势数据点"""
    date: date
    kitting_rate: Decimal = Field(description="齐套率(%)")


class MaterialProgressOverview(BaseModel):
    """项目物料进度总览"""
    project_id: int
    project_code: str
    project_name: str
    # 整体进度
    total_bom_items: int = Field(description="BOM 物料总行数")
    kitted_items: int = Field(description="已齐套行数")
    in_progress_items: int = Field(description="进行中行数")
    shortage_items: int = Field(description="缺料行数")
    kitting_rate: Decimal = Field(description="齐套率(%)")
    material_status: Optional[str] = Field(None, description="物料状态")
    # 关键物料
    key_materials: List[KeyMaterialItem] = Field(default_factory=list)
    # 趋势
    kitting_trend: List[KittingTrendPoint] = Field(default_factory=list)
    # 预计齐套日期
    estimated_kitting_date: Optional[date] = None


# ==================== 2. BOM 物料明细进度 ====================

class BomItemProgress(BaseModel):
    """单个 BOM 物料行的进度"""
    bom_item_id: int
    item_no: int
    material_id: Optional[int] = None
    material_code: str
    material_name: str
    specification: Optional[str] = None
    unit: str = "件"
    # 数量进度
    required_qty: Decimal
    purchased_qty: Decimal = Decimal("0")
    in_transit_qty: Decimal = Field(Decimal("0"), description="在途数量(已采购-已到货)")
    received_qty: Decimal = Decimal("0")
    shortage_qty: Decimal = Field(Decimal("0"), description="缺料数量")
    # 状态
    kitting_status: str = "PENDING"
    is_key_item: bool = False
    # 供应商交货
    supplier_name: Optional[str] = None
    promised_date: Optional[date] = None
    expected_arrival_date: Optional[date] = None
    actual_arrival_date: Optional[date] = None


class BomProgress(BaseModel):
    """单个 BOM 的齐套进度"""
    bom_id: int
    bom_no: str
    bom_name: str
    machine_name: Optional[str] = None
    status: str
    total_items: int
    kitted_items: int
    kitting_rate: Decimal
    items: List[BomItemProgress] = Field(default_factory=list)


class BomProgressResponse(BaseModel):
    """BOM 物料明细进度响应"""
    project_id: int
    boms: List[BomProgress] = Field(default_factory=list)
    total_boms: int = 0


# ==================== 3. 缺料跟踪看板 ====================

class ShortageItem(BaseModel):
    """缺料项"""
    shortage_id: int
    material_id: int
    material_code: str
    material_name: str
    specification: Optional[str] = None
    shortage_qty: Decimal
    required_date: Optional[date] = None
    alert_level: str = "WARNING"
    # 处理进度
    status: str = "OPEN"
    handler_name: Optional[str] = None
    assigned_to_name: Optional[str] = None
    solution: Optional[str] = None
    resolution_method: Optional[str] = None
    # 供应商反馈
    supplier_name: Optional[str] = None
    supplier_promised_date: Optional[date] = None
    expected_arrival_date: Optional[date] = None
    # 影响
    impact_days: Optional[int] = Field(None, description="影响交付天数")
    machine_name: Optional[str] = None


class ShortageTrackerResponse(BaseModel):
    """缺料跟踪看板响应"""
    project_id: int
    total_shortages: int = 0
    open_count: int = 0
    in_progress_count: int = 0
    resolved_count: int = 0
    critical_count: int = 0
    total_impact_days: int = 0
    items: List[ShortageItem] = Field(default_factory=list)


# ==================== 4. 物料进度通知订阅 ====================

class MaterialProgressSubscribeRequest(BaseModel):
    """订阅请求"""
    notify_kitting_change: bool = Field(True, description="齐套率变化通知")
    notify_key_material_arrival: bool = Field(True, description="关键物料到货通知")
    notify_shortage_alert: bool = Field(True, description="缺料预警通知")
    kitting_change_threshold: Decimal = Field(
        Decimal("5"), description="齐套率变化阈值(%), 变化超过此值时通知"
    )


class MaterialProgressSubscription(BaseModel):
    """订阅信息"""
    id: int
    project_id: int
    user_id: int
    notify_kitting_change: bool = True
    notify_key_material_arrival: bool = True
    notify_shortage_alert: bool = True
    kitting_change_threshold: Decimal = Decimal("5")
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
