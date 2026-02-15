# -*- coding: utf-8 -*-
"""
项目风险管理 Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class ProjectRiskBase(BaseModel):
    """风险基础Schema"""
    risk_name: str = Field(..., min_length=1, max_length=200, description="风险名称")
    description: Optional[str] = Field(None, description="风险描述")
    risk_type: str = Field(..., description="风险类型：TECHNICAL/COST/SCHEDULE/QUALITY")
    probability: int = Field(..., ge=1, le=5, description="发生概率（1-5）")
    impact: int = Field(..., ge=1, le=5, description="影响程度（1-5）")
    mitigation_plan: Optional[str] = Field(None, description="应对措施")
    contingency_plan: Optional[str] = Field(None, description="应急计划")
    owner_id: Optional[int] = Field(None, description="负责人ID")
    target_closure_date: Optional[datetime] = Field(None, description="计划关闭日期")

    @validator('risk_type')
    def validate_risk_type(cls, v):
        allowed = ['TECHNICAL', 'COST', 'SCHEDULE', 'QUALITY']
        if v not in allowed:
            raise ValueError(f'风险类型必须是以下之一: {", ".join(allowed)}')
        return v


class ProjectRiskCreate(ProjectRiskBase):
    """创建风险Schema"""
    pass


class ProjectRiskUpdate(BaseModel):
    """更新风险Schema"""
    risk_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    risk_type: Optional[str] = None
    probability: Optional[int] = Field(None, ge=1, le=5)
    impact: Optional[int] = Field(None, ge=1, le=5)
    mitigation_plan: Optional[str] = None
    contingency_plan: Optional[str] = None
    owner_id: Optional[int] = None
    status: Optional[str] = None
    target_closure_date: Optional[datetime] = None
    is_occurred: Optional[bool] = None
    occurrence_date: Optional[datetime] = None
    actual_impact: Optional[str] = None
    actual_closure_date: Optional[datetime] = None

    @validator('risk_type')
    def validate_risk_type(cls, v):
        if v is not None:
            allowed = ['TECHNICAL', 'COST', 'SCHEDULE', 'QUALITY']
            if v not in allowed:
                raise ValueError(f'风险类型必须是以下之一: {", ".join(allowed)}')
        return v

    @validator('status')
    def validate_status(cls, v):
        if v is not None:
            allowed = ['IDENTIFIED', 'ANALYZING', 'PLANNING', 'MONITORING', 'MITIGATED', 'OCCURRED', 'CLOSED']
            if v not in allowed:
                raise ValueError(f'状态必须是以下之一: {", ".join(allowed)}')
        return v


class ProjectRiskResponse(BaseModel):
    """风险响应Schema"""
    id: int
    risk_code: str
    project_id: int
    risk_name: str
    description: Optional[str]
    risk_type: str
    probability: int
    impact: int
    risk_score: int
    risk_level: str
    mitigation_plan: Optional[str]
    contingency_plan: Optional[str]
    owner_id: Optional[int]
    owner_name: Optional[str]
    status: str
    identified_date: Optional[datetime]
    target_closure_date: Optional[datetime]
    actual_closure_date: Optional[datetime]
    is_occurred: bool
    occurrence_date: Optional[datetime]
    actual_impact: Optional[str]
    created_by_id: Optional[int]
    created_by_name: Optional[str]
    updated_by_id: Optional[int]
    updated_by_name: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class RiskMatrixItem(BaseModel):
    """风险矩阵项"""
    probability: int
    impact: int
    count: int
    risks: list[dict]


class RiskMatrixResponse(BaseModel):
    """风险矩阵响应"""
    matrix: list[RiskMatrixItem]
    summary: dict


class RiskSummaryResponse(BaseModel):
    """风险汇总统计响应"""
    total_risks: int
    by_type: dict[str, int]
    by_level: dict[str, int]
    by_status: dict[str, int]
    occurred_count: int
    closed_count: int
    high_priority_count: int  # HIGH + CRITICAL
    avg_risk_score: float
