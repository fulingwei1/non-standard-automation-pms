# -*- coding: utf-8 -*-
"""
技术评估相关 Schema
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from ..common import TimestampSchema


class TechnicalAssessmentApplyRequest(BaseModel):
    """申请技术评估请求"""

    evaluator_id: Optional[int] = Field(default=None, description="指定评估人ID（可选）")


class TechnicalAssessmentEvaluateRequest(BaseModel):
    """执行技术评估请求"""

    requirement_data: Dict[str, Any] = Field(description="需求数据")
    enable_ai: bool = Field(default=False, description="是否启用AI分析")


class TechnicalAssessmentResponse(TimestampSchema):
    """技术评估响应"""

    id: int
    source_type: str
    source_id: int
    evaluator_id: Optional[int] = None
    status: str
    total_score: Optional[int] = None
    dimension_scores: Optional[str] = None
    veto_triggered: bool = False
    veto_rules: Optional[str] = None
    decision: Optional[str] = None
    risks: Optional[str] = None
    similar_cases: Optional[str] = None
    ai_analysis: Optional[str] = None
    conditions: Optional[str] = None
    evaluated_at: Optional[datetime] = None
    evaluator_name: Optional[str] = None


class ScoringRuleCreate(BaseModel):
    """创建评分规则"""

    version: str = Field(max_length=20, description="版本号")
    rules_json: str = Field(description="规则配置(JSON)")
    description: Optional[str] = Field(default=None, description="描述")


class ScoringRuleResponse(TimestampSchema):
    """评分规则响应"""

    id: int
    version: str
    is_active: bool
    description: Optional[str] = None
    created_by: Optional[int] = None
    creator_name: Optional[str] = None


class FailureCaseCreate(BaseModel):
    """创建失败案例"""

    case_code: str = Field(max_length=50, description="案例编号")
    project_name: str = Field(max_length=200, description="项目名称")
    industry: str = Field(max_length=50, description="行业")
    product_types: Optional[str] = Field(default=None, description="产品类型(JSON Array)")
    processes: Optional[str] = Field(default=None, description="工序/测试类型(JSON Array)")
    takt_time_s: Optional[int] = Field(default=None, description="节拍时间(秒)")
    annual_volume: Optional[int] = Field(default=None, description="年产量")
    budget_status: Optional[str] = Field(default=None, description="预算状态")
    customer_project_status: Optional[str] = Field(default=None, description="客户项目状态")
    spec_status: Optional[str] = Field(default=None, description="规范状态")
    price_sensitivity: Optional[str] = Field(default=None, description="价格敏感度")
    delivery_months: Optional[int] = Field(default=None, description="交付周期(月)")
    failure_tags: str = Field(description="失败标签(JSON Array)")
    core_failure_reason: str = Field(description="核心失败原因")
    early_warning_signals: str = Field(description="预警信号(JSON Array)")
    final_result: Optional[str] = Field(default=None, description="最终结果")
    lesson_learned: str = Field(description="教训总结")
    keywords: str = Field(description="关键词(JSON Array)")


class FailureCaseResponse(TimestampSchema):
    """失败案例响应"""

    id: int
    case_code: str
    project_name: str
    industry: str
    product_types: Optional[str] = None
    processes: Optional[str] = None
    takt_time_s: Optional[int] = None
    annual_volume: Optional[int] = None
    budget_status: Optional[str] = None
    customer_project_status: Optional[str] = None
    spec_status: Optional[str] = None
    price_sensitivity: Optional[str] = None
    delivery_months: Optional[int] = None
    failure_tags: str
    core_failure_reason: str
    early_warning_signals: str
    final_result: Optional[str] = None
    lesson_learned: str
    keywords: str
    created_by: Optional[int] = None
    creator_name: Optional[str] = None


class OpenItemCreate(BaseModel):
    """创建未决事项"""

    item_type: str = Field(description="问题类型")
    description: str = Field(description="问题描述")
    responsible_party: str = Field(description="责任方")
    responsible_person_id: Optional[int] = Field(default=None, description="责任人ID")
    due_date: Optional[datetime] = Field(default=None, description="截止日期")
    blocks_quotation: bool = Field(default=False, description="是否阻塞报价")


class OpenItemResponse(TimestampSchema):
    """未决事项响应"""

    id: int
    source_type: str
    source_id: int
    item_code: str
    item_type: str
    description: str
    responsible_party: str
    responsible_person_id: Optional[int] = None
    due_date: Optional[datetime] = None
    status: str
    close_evidence: Optional[str] = None
    blocks_quotation: bool = False
    closed_at: Optional[datetime] = None
    responsible_person_name: Optional[str] = None
