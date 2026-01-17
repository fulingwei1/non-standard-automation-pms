# -*- coding: utf-8 -*-
"""
销售机会管理 Schema
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from ..common import BaseSchema, TimestampSchema


class OpportunityRequirementCreate(BaseModel):
    """创建机会需求"""

    model_config = ConfigDict(populate_by_name=True)

    opportunity_id: Optional[int] = Field(default=None, description="机会ID")
    requirement_type: str = Field(description="需求类型")
    requirement_desc: str = Field(description="需求描述")
    specification: Optional[str] = Field(default=None, description="规格要求")
    quantity: Optional[int] = Field(default=None, description="数量")
    priority: Optional[str] = Field(default="MEDIUM", description="优先级")
    expected_delivery_date: Optional[date] = Field(default=None, description="期望交付日期")
    budget: Optional[Decimal] = Field(default=None, description="预算")


class OpportunityRequirementResponse(TimestampSchema):
    """机会需求响应 - 与数据库模型字段匹配"""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: int = Field(description="需求ID")
    opportunity_id: int = Field(description="机会ID")
    # 兼容模型字段名
    product_object: Optional[str] = Field(default=None, description="产品对象")
    ct_seconds: Optional[int] = Field(default=None, description="节拍(秒)")
    interface_desc: Optional[str] = Field(default=None, description="接口/通信协议")
    site_constraints: Optional[str] = Field(default=None, description="现场约束")
    acceptance_criteria: Optional[str] = Field(default=None, description="验收依据")
    safety_requirement: Optional[str] = Field(default=None, description="安全要求")
    attachments: Optional[str] = Field(default=None, description="需求附件")
    extra_json: Optional[str] = Field(default=None, description="其他补充(JSON)")


class OpportunityCreate(BaseModel):
    """创建销售机会"""

    model_config = ConfigDict(populate_by_name=True)

    opp_code: Optional[str] = Field(
        default=None,
        max_length=20,
        description="机会编码",
        validation_alias=AliasChoices("opp_code", "opportunity_code"),
    )
    lead_id: Optional[int] = Field(default=None, description="线索ID")
    customer_id: int = Field(description="客户ID")
    opp_name: str = Field(
        max_length=200,
        description="机会名称",
        validation_alias=AliasChoices("opp_name", "opportunity_name"),
    )
    stage: Optional[str] = Field(default=None, description="阶段")
    probability: Optional[int] = Field(default=None, ge=0, le=100, description="成交概率(0-100)")
    project_type: Optional[str] = Field(default=None, description="项目类型")
    equipment_type: Optional[str] = Field(default=None, description="设备类型")
    est_amount: Optional[Decimal] = Field(
        default=None,
        description="预估金额",
        validation_alias=AliasChoices("est_amount", "expected_amount"),
    )
    est_margin: Optional[Decimal] = Field(default=None, description="预估毛利率")
    expected_close_date: Optional[date] = Field(default=None, description="预计成交日期")
    budget_range: Optional[str] = Field(default=None, description="预算范围")
    decision_chain: Optional[str] = Field(default=None, description="决策链")
    delivery_window: Optional[str] = Field(default=None, description="交付窗口")
    acceptance_basis: Optional[str] = Field(default=None, description="验收依据")
    owner_id: Optional[int] = Field(default=None, description="负责人ID")
    requirement: Optional["OpportunityRequirementCreate"] = Field(default=None, description="需求详情")


class OpportunityUpdate(BaseModel):
    """更新销售机会"""

    model_config = ConfigDict(populate_by_name=True)

    opp_name: Optional[str] = Field(default=None, description="机会名称")
    project_type: Optional[str] = Field(default=None, description="项目类型")
    equipment_type: Optional[str] = Field(default=None, description="设备类型")
    stage: Optional[str] = Field(default=None, description="阶段")
    probability: Optional[int] = Field(default=None, ge=0, le=100, description="成交概率(0-100)")
    est_amount: Optional[Decimal] = Field(default=None, description="预估金额")
    est_margin: Optional[Decimal] = Field(default=None, description="预估毛利率")
    expected_close_date: Optional[date] = Field(default=None, description="预计成交日期")
    budget_range: Optional[str] = Field(default=None, description="预算范围")
    decision_chain: Optional[str] = Field(default=None, description="决策链")
    delivery_window: Optional[str] = Field(default=None, description="交付窗口")
    acceptance_basis: Optional[str] = Field(default=None, description="验收依据")
    score: Optional[int] = Field(default=None, description="评分")
    risk_level: Optional[str] = Field(default=None, description="风险等级")
    owner_id: Optional[int] = Field(default=None, description="负责人ID")
    requirement_maturity: Optional[int] = Field(default=None, description="需求成熟度(1-5)")


class OpportunityResponse(TimestampSchema):
    """销售机会响应 - 字段与数据库模型对齐"""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: int = Field(description="机会ID")
    # 使用 validation_alias 接受 opp_code 或 opportunity_code
    opp_code: str = Field(description="机会编码", validation_alias=AliasChoices("opp_code", "opportunity_code"))
    lead_id: Optional[int] = Field(default=None, description="线索ID")
    customer_id: Optional[int] = Field(default=None, description="客户ID")
    # 使用 validation_alias 接受 opp_name 或 opportunity_name
    opp_name: str = Field(description="机会名称", validation_alias=AliasChoices("opp_name", "opportunity_name"))
    project_type: Optional[str] = Field(default=None, description="项目类型")
    equipment_type: Optional[str] = Field(default=None, description="设备类型")
    # 使用 validation_alias 接受 stage 或 status
    stage: Optional[str] = Field(default=None, description="阶段", validation_alias=AliasChoices("stage", "status"))
    probability: Optional[int] = Field(default=None, description="成交概率(0-100)")
    est_amount: Optional[Decimal] = Field(default=None, description="预估金额")
    est_margin: Optional[Decimal] = Field(default=None, description="预估毛利率")
    expected_close_date: Optional[date] = Field(default=None, description="预计成交日期")
    budget_range: Optional[str] = Field(default=None, description="预算范围")
    decision_chain: Optional[str] = Field(default=None, description="决策链")
    delivery_window: Optional[str] = Field(default=None, description="交付窗口")
    acceptance_basis: Optional[str] = Field(default=None, description="验收依据")
    score: Optional[int] = Field(default=None, description="评分")
    risk_level: Optional[str] = Field(default=None, description="风险等级")
    owner_id: Optional[int] = Field(default=None, description="负责人ID")
    gate_status: Optional[str] = Field(default=None, description="阶段门状态")
    gate_passed_at: Optional[datetime] = Field(default=None, description="阶段门通过时间")
    assessment_id: Optional[int] = Field(default=None, description="技术评估ID")
    requirement_maturity: Optional[int] = Field(default=None, description="需求成熟度(1-5)")
    assessment_status: Optional[str] = Field(default=None, description="技术评估状态")
    priority_score: Optional[int] = Field(default=0, description="优先级得分")

    # 关联数据 (从 endpoint 手动添加)
    customer_name: Optional[str] = Field(default=None, description="客户名称")
    owner_name: Optional[str] = Field(default=None, description="负责人姓名")
    requirement: Optional[OpportunityRequirementResponse] = Field(default=None, description="需求详情")


class GateSubmitRequest(BaseModel):
    """阶段门提交请求"""

    model_config = ConfigDict(populate_by_name=True)

    gate_type: str = Field(default="G2", description="阶段门类型")
    comments: Optional[str] = Field(default=None, description="提交说明")
    attachments: Optional[List[str]] = Field(default=None, description="附件列表")
