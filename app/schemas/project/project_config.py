# -*- coding: utf-8 -*-
"""
项目配置 Schema
包含项目阶段、状态、模板等配置相关的 Schema
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from ..common import BaseSchema, TimestampSchema

# ==================== 项目阶段 ====================


class ProjectStageCreate(BaseModel):
    """创建项目阶段（配置）"""

    project_id: int
    stage_code: str = Field(max_length=20)
    stage_name: str = Field(max_length=50)
    stage_order: int
    description: Optional[str] = None
    gate_conditions: Optional[str] = None
    required_deliverables: Optional[str] = None
    default_duration_days: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class ProjectStageUpdate(BaseModel):
    """更新项目阶段"""

    stage_name: Optional[str] = None
    stage_order: Optional[int] = None
    description: Optional[str] = None
    gate_conditions: Optional[str] = None
    required_deliverables: Optional[str] = None
    default_duration_days: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectStageResponse(TimestampSchema):
    """项目阶段响应"""

    id: int
    project_id: int
    stage_code: str
    stage_name: str
    stage_order: int
    description: Optional[str] = None
    gate_conditions: Optional[str] = None
    required_deliverables: Optional[str] = None
    default_duration_days: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None

    # 计划与进度
    progress_pct: int = 0
    status: str = "PENDING"
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None

    is_active: bool

    class Config:
        from_attributes = True


# ==================== 项目状态 ====================


class ProjectStatusCreate(BaseModel):
    """创建项目状态"""

    stage_id: int
    status_code: str
    status_name: str
    status_order: int
    description: Optional[str] = None
    status_type: str = "NORMAL"
    auto_next_status: Optional[str] = None


class ProjectStatusResponse(TimestampSchema):
    """项目状态响应"""

    id: int
    stage_id: int
    status_code: str
    status_name: str
    status_order: int
    description: Optional[str] = None
    status_type: str
    auto_next_status: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


# ==================== 项目模板 ====================


class ProjectTemplateCreate(BaseModel):
    """创建项目模板"""

    template_code: str = Field(max_length=50, description="模板编码")
    template_name: str = Field(max_length=200, description="模板名称")
    description: Optional[str] = None
    project_type: Optional[str] = None
    product_category: Optional[str] = None
    industry: Optional[str] = None
    default_stage: Optional[str] = Field(default="S1")
    default_status: Optional[str] = Field(default="ST01")
    default_health: Optional[str] = Field(default="H1")
    template_config: Optional[str] = None  # JSON字符串
    is_active: Optional[bool] = Field(default=True)


class ProjectTemplateUpdate(BaseModel):
    """更新项目模板"""

    template_name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[str] = None
    product_category: Optional[str] = None
    industry: Optional[str] = None
    default_stage: Optional[str] = None
    default_status: Optional[str] = None
    default_health: Optional[str] = None
    template_config: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectTemplateResponse(TimestampSchema):
    """项目模板响应"""

    id: int
    template_code: str
    template_name: str
    description: Optional[str] = None
    project_type: Optional[str] = None
    product_category: Optional[str] = None
    industry: Optional[str] = None
    default_stage: Optional[str] = None
    default_status: Optional[str] = None
    default_health: Optional[str] = None
    template_config: Optional[str] = None
    is_active: bool
    usage_count: int
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


# ==================== 项目模板版本 ====================


class ProjectTemplateVersionCreate(BaseModel):
    """创建项目模板版本"""

    version_no: str = Field(..., max_length=20, description="版本号")
    status: Optional[str] = Field(default="DRAFT", description="状态：DRAFT/ACTIVE/ARCHIVED")
    template_config: Optional[str] = Field(None, description="模板配置JSON")
    release_notes: Optional[str] = Field(None, description="版本说明")


class ProjectTemplateVersionUpdate(BaseModel):
    """更新项目模板版本"""

    version_no: Optional[str] = Field(None, max_length=20, description="版本号")
    status: Optional[str] = Field(None, description="状态：DRAFT/ACTIVE/ARCHIVED")
    template_config: Optional[str] = Field(None, description="模板配置JSON")
    release_notes: Optional[str] = Field(None, description="版本说明")


class ProjectTemplateVersionResponse(TimestampSchema):
    """项目模板版本响应"""

    id: int
    template_id: int
    version_no: str
    status: str
    template_config: Optional[str] = None
    release_notes: Optional[str] = None
    created_by: Optional[int] = None
    published_by: Optional[int] = None
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True
