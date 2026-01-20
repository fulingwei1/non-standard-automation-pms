# -*- coding: utf-8 -*-
"""
战略管理 Schema - Strategy CRUD
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from ..common import TimestampSchema


# ============================================
# Strategy - 战略主表
# ============================================

class StrategyCreate(BaseModel):
    """创建战略"""
    code: str = Field(max_length=50, description="战略编码，如 STR-2026")
    name: str = Field(max_length=200, description="战略名称")
    vision: Optional[str] = Field(default=None, description="愿景描述")
    mission: Optional[str] = Field(default=None, description="使命描述")
    slogan: Optional[str] = Field(default=None, max_length=200, description="战略口号")
    year: int = Field(description="战略年度")
    start_date: Optional[date] = Field(default=None, description="战略周期开始")
    end_date: Optional[date] = Field(default=None, description="战略周期结束")


class StrategyUpdate(BaseModel):
    """更新战略"""
    name: Optional[str] = Field(default=None, max_length=200)
    vision: Optional[str] = None
    mission: Optional[str] = None
    slogan: Optional[str] = Field(default=None, max_length=200)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = Field(default=None, description="状态：DRAFT/ACTIVE/ARCHIVED")


class StrategyResponse(TimestampSchema):
    """战略响应"""
    id: int
    code: str
    name: str
    vision: Optional[str] = None
    mission: Optional[str] = None
    slogan: Optional[str] = None
    year: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str
    created_by: Optional[int] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    is_active: bool = True

    # ��展字段（可选加载）
    creator_name: Optional[str] = None
    approver_name: Optional[str] = None


class StrategyDetailResponse(StrategyResponse):
    """战略详情响应（包含统计信息）"""
    csf_count: int = 0
    kpi_count: int = 0
    annual_work_count: int = 0
    health_score: Optional[int] = None


class StrategyPublishRequest(BaseModel):
    """发布战略请求"""
    remark: Optional[str] = Field(default=None, description="发布备注")


class StrategyMapCSF(BaseModel):
    """战略地图 - CSF 项"""
    id: int
    code: str
    name: str
    weight: float = 0
    health_score: Optional[int] = None
    health_level: Optional[str] = None
    kpi_count: int = 0
    kpi_completion_rate: Optional[float] = None


class StrategyMapDimension(BaseModel):
    """战略地图 - 维度数据"""
    dimension: str
    dimension_name: str
    csfs: List[StrategyMapCSF] = []
    health_score: Optional[int] = None
    total_weight: float = 0


class StrategyMapResponse(BaseModel):
    """战略地图响应"""
    strategy_id: int
    strategy_code: str
    strategy_name: str
    vision: Optional[str] = None
    slogan: Optional[str] = None
    year: int
    overall_health_score: Optional[int] = None
    dimensions: List[StrategyMapDimension] = []

    class Config:
        from_attributes = True
