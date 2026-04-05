# -*- coding: utf-8 -*-
"""
技术参数模板 Schema

用于技术参数模板的请求和响应数据验证
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import TimestampSchema


# ==================== 创建/更新 Schema ====================


class TechnicalParameterTemplateCreate(BaseModel):
    """创建技术参数模板"""

    name: str = Field(..., min_length=1, max_length=200, description="模板名称")
    code: str = Field(..., min_length=1, max_length=50, description="模板编码")
    industry: str = Field(..., description="行业分类")
    test_type: str = Field(..., description="测试类型")
    description: Optional[str] = Field(None, description="模板描述")
    parameters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="技术参数模板（JSON格式）",
        examples=[{
            "test_station_count": {"label": "测试工位数", "type": "number", "default": 4, "unit": "个"},
            "cycle_time": {"label": "节拍时间", "type": "number", "default": 30, "unit": "秒"},
        }]
    )
    cost_factors: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="成本估算因子（JSON格式）",
        examples=[{
            "base_cost": 50000,
            "factors": {
                "test_station_count": {"type": "linear", "coefficient": 8000}
            },
            "category_ratios": {
                "MECHANICAL": 0.35,
                "ELECTRICAL": 0.30,
            }
        }]
    )
    typical_labor_hours: Optional[Dict[str, int]] = Field(
        default_factory=dict,
        description="典型工时估算（JSON格式）",
        examples=[{
            "design_hours": 80,
            "assembly_hours": 120,
            "debug_hours": 60,
        }]
    )
    reference_docs: Optional[List[str]] = Field(
        default_factory=list,
        description="参考文档列表"
    )
    sample_images: Optional[List[str]] = Field(
        default_factory=list,
        description="示例图片列表"
    )


class TechnicalParameterTemplateUpdate(BaseModel):
    """更新技术参数模板"""

    name: Optional[str] = Field(None, min_length=1, max_length=200, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    parameters: Optional[Dict[str, Any]] = Field(None, description="技术参数模板")
    cost_factors: Optional[Dict[str, Any]] = Field(None, description="成本估算因子")
    typical_labor_hours: Optional[Dict[str, int]] = Field(None, description="典型工时估算")
    reference_docs: Optional[List[str]] = Field(None, description="参考文档列表")
    sample_images: Optional[List[str]] = Field(None, description="示例图片列表")
    is_active: Optional[bool] = Field(None, description="是否启用")


# ==================== 响应 Schema ====================


class TechnicalParameterTemplateResponse(TimestampSchema):
    """技术参数模板响应"""

    id: int
    name: str
    code: str
    industry: str
    test_type: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    cost_factors: Dict[str, Any] = Field(default_factory=dict)
    typical_labor_hours: Dict[str, int] = Field(default_factory=dict)
    reference_docs: List[str] = Field(default_factory=list)
    sample_images: List[str] = Field(default_factory=list)
    use_count: int = 0
    is_active: bool = True
    created_by: Optional[int] = None


class TechnicalParameterTemplateListItem(BaseModel):
    """技术参数模板列表项（简化）"""

    id: int
    name: str
    code: str
    industry: str
    test_type: str
    description: Optional[str] = None
    use_count: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None


# ==================== 成本估算 Schema ====================


class CostEstimateRequest(BaseModel):
    """成本估算请求"""

    template_id: int = Field(..., description="模板ID")
    parameters: Dict[str, Any] = Field(
        ...,
        description="技术参数值",
        examples=[{
            "test_station_count": 6,
            "cycle_time": 25,
            "accuracy": 0.005,
        }]
    )


class CostBreakdownItem(BaseModel):
    """成本分解项"""

    ratio: float = Field(..., description="占比")
    amount: float = Field(..., description="金额（元）")


class LaborHoursDetail(BaseModel):
    """工时明细"""

    detail: Dict[str, int] = Field(default_factory=dict, description="工时分类明细")
    total: int = Field(0, description="总工时")


class CostEstimateResponse(BaseModel):
    """成本估算响应"""

    template_id: int
    template_name: str
    template_code: str
    base_cost: float = Field(..., description="基础成本（元）")
    adjustment: float = Field(..., description="调整金额（元）")
    total_cost: float = Field(..., description="总成本（元）")
    cost_breakdown: Dict[str, CostBreakdownItem] = Field(
        ...,
        description="成本分类明细"
    )
    labor_hours: LaborHoursDetail = Field(..., description="工时估算")
    parameters_used: Dict[str, Any] = Field(..., description="使用的参数")
    estimated_at: str = Field(..., description="估算时间")


class BatchCostEstimateRequest(BaseModel):
    """批量成本估算请求"""

    industry: str = Field(..., description="行业")
    test_type: str = Field(..., description="测试类型")
    parameters: Dict[str, Any] = Field(..., description="技术参数值")


# ==================== 统计 Schema ====================


class IndustryStatistics(BaseModel):
    """行业统计"""

    industry: str
    template_count: int
    total_usage: int


class TestTypeStatistics(BaseModel):
    """测试类型统计"""

    test_type: str
    template_count: int
    total_usage: int


# ==================== 查询 Schema ====================


class TemplateListQuery(BaseModel):
    """模板列表查询参数"""

    industry: Optional[str] = Field(None, description="行业筛选")
    test_type: Optional[str] = Field(None, description="测试类型筛选")
    keyword: Optional[str] = Field(None, description="关键词搜索")
    is_active: Optional[bool] = Field(True, description="是否只查询启用的模板")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")


class TemplateMatchQuery(BaseModel):
    """模板匹配查询参数"""

    industry: str = Field(..., description="行业")
    test_type: str = Field(..., description="测试类型")
    top_k: int = Field(5, ge=1, le=20, description="返回数量")
