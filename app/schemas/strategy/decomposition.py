# -*- coding: utf-8 -*-
"""
战略管理 Schema - 目标分解
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..common import TimestampSchema


# ============================================
# DepartmentObjective - 部门目标
# ============================================

class DepartmentObjectiveCreate(BaseModel):
    """创建部门目标"""
    strategy_id: int = Field(description="关联战略")
    department_id: int = Field(description="部门ID")
    year: int = Field(description="年度")
    quarter: Optional[int] = Field(default=None, description="季度")
    objectives: Optional[Dict[str, Any]] = Field(default=None, description="部门级目标列表")
    key_results: Optional[Dict[str, Any]] = Field(default=None, description="关键成果")
    kpis_config: Optional[Dict[str, Any]] = Field(default=None, description="部门级 KPI")
    owner_user_id: Optional[int] = Field(default=None, description="部门负责人")


class DepartmentObjectiveUpdate(BaseModel):
    """更新部门目标"""
    objectives: Optional[Dict[str, Any]] = None
    key_results: Optional[Dict[str, Any]] = None
    kpis_config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    owner_user_id: Optional[int] = None


class DepartmentObjectiveResponse(TimestampSchema):
    """部门目标响应"""
    id: int
    strategy_id: int
    department_id: int
    year: int
    quarter: Optional[int] = None
    objectives: Optional[Dict[str, Any]] = None
    key_results: Optional[Dict[str, Any]] = None
    kpis_config: Optional[Dict[str, Any]] = None
    status: str = "DRAFT"
    owner_user_id: Optional[int] = None
    approved_by: Optional[int] = None
    approved_at: Optional[str] = None
    is_active: bool = True

    # 扩展字段
    department_name: Optional[str] = None
    owner_name: Optional[str] = None
    approver_name: Optional[str] = None
    personal_kpi_count: int = 0


class DepartmentObjectiveDetailResponse(DepartmentObjectiveResponse):
    """部门目标详情（含个人 KPI）"""
    personal_kpis: List["PersonalKPIResponse"] = []


# ============================================
# PersonalKPI - 个人 KPI
# ============================================

class PersonalKPICreate(BaseModel):
    """创建个人 KPI"""
    employee_id: int = Field(description="员工ID")
    year: int = Field(description="年度")
    quarter: Optional[int] = Field(default=None, description="季度")
    source_type: str = Field(description="来源类型：CSF_KPI/DEPT_OBJECTIVE/ANNUAL_WORK")
    source_id: Optional[int] = Field(default=None, description="来源 ID")
    department_objective_id: Optional[int] = Field(default=None, description="部门目标ID")
    kpi_name: str = Field(max_length=200, description="KPI 名称")
    kpi_description: Optional[str] = Field(default=None, description="KPI 描述")
    unit: Optional[str] = Field(default=None, max_length=20, description="单位")
    target_value: Optional[Decimal] = Field(default=None, description="目标值")
    weight: Decimal = Field(default=0, description="权重")


class PersonalKPIUpdate(BaseModel):
    """更新个人 KPI"""
    kpi_name: Optional[str] = Field(default=None, max_length=200)
    kpi_description: Optional[str] = None
    unit: Optional[str] = None
    target_value: Optional[Decimal] = None
    actual_value: Optional[Decimal] = None
    weight: Optional[Decimal] = None
    self_rating: Optional[int] = Field(default=None, ge=0, le=100)
    self_comment: Optional[str] = None
    manager_rating: Optional[int] = Field(default=None, ge=0, le=100)
    manager_comment: Optional[str] = None
    status: Optional[str] = None


class PersonalKPIResponse(TimestampSchema):
    """个人 KPI 响应"""
    id: int
    employee_id: int
    year: int
    quarter: Optional[int] = None
    source_type: str
    source_id: Optional[int] = None
    department_objective_id: Optional[int] = None
    kpi_name: str
    kpi_description: Optional[str] = None
    unit: Optional[str] = None
    target_value: Optional[Decimal] = None
    actual_value: Optional[Decimal] = None
    completion_rate: Optional[Decimal] = None
    weight: Decimal = 0
    self_rating: Optional[int] = None
    self_comment: Optional[str] = None
    manager_rating: Optional[int] = None
    manager_comment: Optional[str] = None
    status: str = "PENDING"
    is_active: bool = True

    # 扩展字段
    employee_name: Optional[str] = None
    department_name: Optional[str] = None
    source_name: Optional[str] = None  # 来源 KPI/工作的名称


class PersonalKPISelfRatingRequest(BaseModel):
    """个人 KPI 自评请求"""
    actual_value: Optional[Decimal] = Field(default=None, description="实际值")
    self_rating: int = Field(ge=0, le=100, description="自评分")
    self_comment: Optional[str] = Field(default=None, description="自评说明")


class PersonalKPIManagerRatingRequest(BaseModel):
    """个人 KPI 主管评分请求"""
    manager_rating: int = Field(ge=0, le=100, description="主管评分")
    manager_comment: Optional[str] = Field(default=None, description="主管评语")


class PersonalKPIBatchCreate(BaseModel):
    """批量创建个人 KPI"""
    employee_id: int
    year: int
    quarter: Optional[int] = None
    kpis: List[PersonalKPICreate]


# ============================================
# 目标分解树
# ============================================

class DecompositionTreeNode(BaseModel):
    """分解树节点"""
    id: int
    type: str  # strategy / csf / kpi / department / team / personal
    name: str
    level: int
    parent_id: Optional[int] = None
    weight: float = 0
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    completion_rate: Optional[float] = None
    health_level: Optional[str] = None
    owner_name: Optional[str] = None
    children: List["DecompositionTreeNode"] = []

    class Config:
        from_attributes = True


class DecompositionTreeResponse(BaseModel):
    """分解树响应"""
    strategy_id: int
    strategy_name: str
    year: int
    root: DecompositionTreeNode

    class Config:
        from_attributes = True


class TraceToStrategyResponse(BaseModel):
    """向上追溯到战略"""
    personal_kpi: PersonalKPIResponse
    department_objective: Optional[DepartmentObjectiveResponse] = None
    csf: Optional[Dict[str, Any]] = None
    kpi: Optional[Dict[str, Any]] = None
    strategy: Optional[Dict[str, Any]] = None
    trace_path: List[str] = []  # 追溯路径描述

    class Config:
        from_attributes = True


# 更新前向引用
DepartmentObjectiveDetailResponse.model_rebuild()
DecompositionTreeNode.model_rebuild()
