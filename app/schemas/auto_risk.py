# -*- coding: utf-8 -*-
"""
自动风险识别 Schemas
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class AutoRiskType(str, Enum):
    """自动识别的风险子类型"""

    # 进度风险
    MILESTONE_OVERDUE = "MILESTONE_OVERDUE"
    STAGE_DELAY_TREND = "STAGE_DELAY_TREND"
    CRITICAL_PATH_DELAY = "CRITICAL_PATH_DELAY"

    # 成本风险
    BUDGET_OVERRUN = "BUDGET_OVERRUN"
    COST_GROWTH_ABNORMAL = "COST_GROWTH_ABNORMAL"
    PURCHASE_OVER_BUDGET = "PURCHASE_OVER_BUDGET"

    # 资源风险
    KEY_PERSON_OVERLOAD = "KEY_PERSON_OVERLOAD"
    RESOURCE_CONFLICT_UNRESOLVED = "RESOURCE_CONFLICT_UNRESOLVED"
    SINGLE_SKILL_DEPENDENCY = "SINGLE_SKILL_DEPENDENCY"

    # 质量风险
    DEFECT_RATE_RISING = "DEFECT_RATE_RISING"
    REWORK_COUNT_INCREASE = "REWORK_COUNT_INCREASE"
    ACCEPTANCE_PASS_RATE_DROP = "ACCEPTANCE_PASS_RATE_DROP"


class AutoRiskItem(BaseModel):
    """单条自动识别风险"""

    risk_type: AutoRiskType = Field(..., description="风险子类型")
    risk_category: str = Field(..., description="风险大类: SCHEDULE/COST/RESOURCE/QUALITY")
    risk_level: str = Field(..., description="风险等级: LOW/MEDIUM/HIGH/CRITICAL")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度 0-1")
    risk_name: str = Field(..., description="风险名称")
    evidence: str = Field(..., description="证据描述")
    suggestion: str = Field(..., description="建议措施")
    # 用于自动创建 ProjectRisk 的评估参数
    probability: int = Field(..., ge=1, le=5, description="概率评估 1-5")
    impact: int = Field(..., ge=1, le=5, description="影响评估 1-5")
    related_entity_type: Optional[str] = Field(None, description="关联实体类型")
    related_entity_id: Optional[int] = Field(None, description="关联实体ID")


class AutoRiskScanRequest(BaseModel):
    """扫描请求"""

    categories: Optional[List[str]] = Field(
        None,
        description="要扫描的风险类别, 默认全部. 可选: SCHEDULE/COST/RESOURCE/QUALITY",
    )
    auto_create: bool = Field(
        True, description="是否自动创建风险记录"
    )
    min_confidence: float = Field(
        0.6, ge=0.0, le=1.0, description="最低置信度阈值"
    )


class AutoRiskScanResult(BaseModel):
    """扫描结果"""

    project_id: int
    scanned_at: datetime
    total_risks_found: int
    auto_risks: List[AutoRiskItem]
    created_risk_ids: List[int] = Field(default_factory=list, description="自动创建的风险记录ID")
    summary: dict = Field(default_factory=dict, description="按类别汇总")
