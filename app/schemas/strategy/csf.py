# -*- coding: utf-8 -*-
"""
战略管理 Schema - CSF 关键成功要素
"""

from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from ..common import TimestampSchema


class CSFCreate(BaseModel):
    """创建 CSF"""
    strategy_id: int = Field(description="关联战略ID")
    dimension: str = Field(description="BSC维度：FINANCIAL/CUSTOMER/INTERNAL/LEARNING")
    code: str = Field(max_length=50, description="CSF 编码，如 CSF-F-001")
    name: str = Field(max_length=200, description="要素名称")
    description: Optional[str] = Field(default=None, description="详细描述")
    derivation_method: Optional[str] = Field(default=None, description="导出方法")
    weight: Decimal = Field(default=0, description="权重占比（%）")
    sort_order: int = Field(default=0, description="排序")
    owner_dept_id: Optional[int] = Field(default=None, description="责任部门")
    owner_user_id: Optional[int] = Field(default=None, description="责任人")


class CSFUpdate(BaseModel):
    """更新 CSF"""
    name: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    derivation_method: Optional[str] = None
    weight: Optional[Decimal] = None
    sort_order: Optional[int] = None
    owner_dept_id: Optional[int] = None
    owner_user_id: Optional[int] = None


class CSFResponse(TimestampSchema):
    """CSF 响应"""
    id: int
    strategy_id: int
    dimension: str
    code: str
    name: str
    description: Optional[str] = None
    derivation_method: Optional[str] = None
    weight: Decimal = 0
    sort_order: int = 0
    owner_dept_id: Optional[int] = None
    owner_user_id: Optional[int] = None
    is_active: bool = True

    # 扩展字段
    owner_dept_name: Optional[str] = None
    owner_name: Optional[str] = None
    kpi_count: int = 0
    annual_work_count: int = 0


class CSFDetailResponse(CSFResponse):
    """CSF 详情响应（包含健康度）"""
    health_score: Optional[int] = None
    health_level: Optional[str] = None
    kpi_completion_rate: Optional[float] = None


class CSFByDimensionItem(BaseModel):
    """按维度分组 - 单个 CSF"""
    id: int
    code: str
    name: str
    weight: float = 0
    health_score: Optional[int] = None
    kpi_count: int = 0


class CSFByDimensionResponse(BaseModel):
    """按维度分组响应"""
    dimension: str
    dimension_name: str
    csfs: List[CSFByDimensionItem] = []
    total_weight: float = 0
    avg_health_score: Optional[float] = None

    class Config:
        from_attributes = True


class CSFBatchCreateRequest(BaseModel):
    """批量创建 CSF 请求"""
    strategy_id: int
    items: List[CSFCreate]
