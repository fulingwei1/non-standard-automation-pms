# -*- coding: utf-8 -*-
"""
资源计划相关的 Pydantic Schema
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

# ==================== 基础 Schema ====================


class ResourcePlanBase(BaseModel):
    """资源计划基础字段"""

    stage_code: str = Field(..., description="阶段编码 S1-S9", pattern="^S[1-9]$")
    role_code: str = Field(..., description="角色编码")
    role_name: Optional[str] = Field(None, description="角色名称")
    headcount: int = Field(1, ge=1, description="需求人数")
    allocation_pct: Decimal = Field(Decimal("100"), ge=0, le=100, description="分配比例%")
    planned_start: Optional[date] = Field(None, description="计划开始日期")
    planned_end: Optional[date] = Field(None, description="计划结束日期")
    remark: Optional[str] = Field(None, description="备注")


class ResourcePlanCreate(ResourcePlanBase):
    """创建资源计划"""

    role_code: Optional[str] = Field(None, description="角色编码（兼容老请求，可仅传 role_name）")
    staffing_need_id: Optional[int] = Field(None, description="关联人员需求ID")

    @model_validator(mode="after")
    def ensure_role_code(self):
        if self.role_code:
            return self

        if self.role_name:
            normalized = "".join(ch if ch.isalnum() else "_" for ch in self.role_name.upper())
            normalized = "_".join(filter(None, normalized.split("_")))
            self.role_code = normalized[:50] or f"ROLE_{self.stage_code}"
        else:
            self.role_code = f"ROLE_{self.stage_code}"
        return self


class ResourcePlanUpdate(BaseModel):
    """更新资源计划"""

    role_name: Optional[str] = None
    headcount: Optional[int] = Field(None, ge=1)
    allocation_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    remark: Optional[str] = None


# ==================== 分配相关 ====================


class ResourceAssignment(BaseModel):
    """人员分配请求"""

    employee_id: int = Field(..., description="员工ID")
    force: bool = Field(False, description="是否强制分配（忽略冲突警告）")


class EmployeeBrief(BaseModel):
    """员工简要信息"""

    id: int
    name: str
    department: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def normalize_user_like_object(cls, value):
        if isinstance(value, dict) or value is None:
            return value

        if hasattr(value, "id"):
            return {
                "id": getattr(value, "id"),
                "name": getattr(value, "name", None)
                or getattr(value, "real_name", None)
                or getattr(value, "display_name", None)
                or getattr(value, "username", None),
                "department": getattr(value, "department", None),
            }
        return value


# ==================== 响应 Schema ====================


class ResourcePlanResponse(ResourcePlanBase):
    """资源计划响应"""

    id: int
    project_id: int
    staffing_need_id: Optional[int] = None
    assigned_employee_id: Optional[int] = None
    assignment_status: str
    assigned_employee: Optional[EmployeeBrief] = None

    model_config = ConfigDict(from_attributes=True)


class StageResourceSummary(BaseModel):
    """阶段资源汇总"""

    stage_code: str
    stage_name: str
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    requirements: List[ResourcePlanResponse]
    total_headcount: int
    filled_count: int
    fill_rate: float = Field(..., description="填充率 0-100")


class ProjectResourcePlanSummary(BaseModel):
    """项目资源计���汇总"""

    project_id: int
    project_name: str
    stages: List[StageResourceSummary]
    overall_fill_rate: float


# ==================== 冲突相关 ====================


class ConflictProject(BaseModel):
    """冲突项目信息"""

    project_id: int
    project_name: str
    stage_code: str
    stage_name: Optional[str] = None
    allocation_pct: Decimal
    period: str  # "2026-03-01 ~ 2026-03-31"


class ResourceConflict(BaseModel):
    """资源冲突"""

    id: Optional[int] = None
    employee: EmployeeBrief
    this_project: ConflictProject
    conflict_with: ConflictProject
    overlap_period: str
    total_allocation: Decimal
    over_allocation: Decimal
    severity: str = Field(..., description="严重度: HIGH/MEDIUM/LOW")
    resolved: bool = False


class ProjectConflictSummary(BaseModel):
    """项目冲突汇总"""

    project_id: int
    conflicts: List[ResourceConflict]
    conflict_count: int
    affected_employees: int


# ==================== 候选人相关 ====================


class CandidateAvailability(BaseModel):
    """候选人可用性"""

    current_allocation: Decimal
    available_pct: Decimal
    available_hours: Decimal
    current_projects: List[dict]


class ResourceCandidate(BaseModel):
    """资源候选人"""

    employee: EmployeeBrief
    skill_match: dict  # {skill_code: {score, level}}
    availability: CandidateAvailability
    match_score: float
    recommendation: str = Field(..., description="STRONG/RECOMMENDED/ACCEPTABLE/WEAK")
    potential_conflict: Optional[ResourceConflict] = None
