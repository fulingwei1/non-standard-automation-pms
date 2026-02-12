# -*- coding: utf-8 -*-
"""
项目评价模块 Schema 定义
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.schemas.common import PageParams, PaginatedResponse

# ==================== 项目评价 ====================

class ProjectEvaluationBase(BaseModel):
    """项目评价基础模型"""
    project_id: Optional[int] = Field(None, description="项目ID（可选，通常从路径中获取）")
    novelty_score: Decimal = Field(..., ge=1, le=10, description="项目新旧得分（1-10分）")
    new_tech_score: Decimal = Field(..., ge=1, le=10, description="新技术得分（1-10分）")
    difficulty_score: Decimal = Field(..., ge=1, le=10, description="项目难度得分（1-10分）")
    workload_score: Decimal = Field(..., ge=1, le=10, description="项目工作量得分（1-10分）")
    amount_score: Decimal = Field(..., ge=1, le=10, description="项目金额得分（1-10分）")
    weights: Optional[Dict[str, Decimal]] = Field(None, description="权重配置")
    evaluation_detail: Optional[Dict[str, Any]] = Field(None, description="评价详情")
    evaluation_note: Optional[str] = Field(None, description="评价说明")


class ProjectEvaluationCreate(ProjectEvaluationBase):
    """创建项目评价"""
    pass


class ProjectEvaluationUpdate(BaseModel):
    """更新项目评价"""
    novelty_score: Optional[Decimal] = Field(None, ge=1, le=10)
    new_tech_score: Optional[Decimal] = Field(None, ge=1, le=10)
    difficulty_score: Optional[Decimal] = Field(None, ge=1, le=10)
    workload_score: Optional[Decimal] = Field(None, ge=1, le=10)
    amount_score: Optional[Decimal] = Field(None, ge=1, le=10)
    weights: Optional[Dict[str, Decimal]] = None
    evaluation_detail: Optional[Dict[str, Any]] = None
    evaluation_note: Optional[str] = None
    status: Optional[str] = None


class ProjectEvaluationResponse(ProjectEvaluationBase):
    """项目评价响应"""
    id: int
    evaluation_code: str
    total_score: Decimal
    evaluation_level: str
    evaluator_id: int
    evaluator_name: Optional[str] = None
    evaluation_date: date
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectEvaluationQuery(PageParams):
    """项目评价查询"""
    project_id: Optional[int] = None
    evaluation_level: Optional[str] = None
    evaluator_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None


# ==================== 自动评价请求 ====================

class AutoEvaluationRequest(BaseModel):
    """自动评价请求"""
    project_id: int = Field(..., description="项目ID")
    auto_calculate_novelty: bool = Field(True, description="是否自动计算项目新旧得分")
    auto_calculate_amount: bool = Field(True, description="是否自动计算项目金额得分")
    manual_scores: Optional[Dict[str, Decimal]] = Field(None, description="手动评分（覆盖自动计算）")
    # 例如：{"novelty_score": 3.0, "new_tech_score": 2.0}


# ==================== 评价维度配置 ====================

class ProjectEvaluationDimensionBase(BaseModel):
    """评价维度基础模型"""
    dimension_code: str = Field(..., description="维度编码")
    dimension_name: str = Field(..., description="维度名称")
    dimension_type: str = Field(..., description="维度类型")
    scoring_rules: Optional[Dict[str, Any]] = Field(None, description="评分规则")
    default_weight: Decimal = Field(..., description="默认权重(%)")
    calculation_method: str = Field("MANUAL", description="计算方式")
    auto_calculation_rule: Optional[Dict[str, Any]] = Field(None, description="自动计算规则")
    is_active: bool = Field(True, description="是否启用")
    sort_order: int = Field(0, description="排序")


class ProjectEvaluationDimensionCreate(ProjectEvaluationDimensionBase):
    """创建评价维度"""
    pass


class ProjectEvaluationDimensionUpdate(BaseModel):
    """更新评价维度"""
    dimension_code: Optional[str] = Field(None, description="维度编码")
    dimension_name: Optional[str] = Field(None, description="维度名称")
    dimension_type: Optional[str] = Field(None, description="维度类型")
    scoring_rules: Optional[Dict[str, Any]] = Field(None, description="评分规则")
    default_weight: Optional[Decimal] = Field(None, description="默认权重(%)")
    calculation_method: Optional[str] = Field(None, description="计算方式")
    auto_calculation_rule: Optional[Dict[str, Any]] = Field(None, description="自动计算规则")
    is_active: Optional[bool] = Field(None, description="是否启用")
    sort_order: Optional[int] = Field(None, description="排序")


class ProjectEvaluationDimensionResponse(ProjectEvaluationDimensionBase):
    """评价维度响应"""
    id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# ==================== 项目评价统计 ====================

class ProjectEvaluationStatisticsResponse(BaseModel):
    """项目评价统计响应"""
    total_evaluations: int = Field(..., description="总评价数")
    by_level: Dict[str, int] = Field(default={}, description="按等级统计")
    avg_total_score: Decimal = Field(..., description="平均综合得分")
    avg_novelty_score: Decimal = Field(..., description="平均项目新旧得分")
    avg_new_tech_score: Decimal = Field(..., description="平均新技术得分")
    avg_difficulty_score: Decimal = Field(..., description="平均难度得分")
    avg_workload_score: Decimal = Field(..., description="平均工作量得分")
    avg_amount_score: Decimal = Field(..., description="平均金额得分")


# ==================== 响应类型 ====================

ProjectEvaluationListResponse = PaginatedResponse[ProjectEvaluationResponse]
ProjectEvaluationDimensionListResponse = PaginatedResponse[ProjectEvaluationDimensionResponse]

