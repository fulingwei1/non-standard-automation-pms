# -*- coding: utf-8 -*-
"""
战略管理 Schema - 年度重点工作
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from ..common import TimestampSchema


class AnnualKeyWorkCreate(BaseModel):
    """创建年度重点工作"""
    csf_id: int = Field(description="关联 CSF")
    code: str = Field(max_length=50, description="工作编码")
    name: str = Field(max_length=200, description="工作名称")
    description: Optional[str] = Field(default=None, description="工作描述")
    voc_source: Optional[str] = Field(default=None, description="声音来源")
    pain_point: Optional[str] = Field(default=None, description="痛点/短板")
    solution: Optional[str] = Field(default=None, description="解决方案")
    target: Optional[str] = Field(default=None, description="目标描述")
    year: int = Field(description="年度")
    start_date: Optional[date] = Field(default=None, description="计划开始")
    end_date: Optional[date] = Field(default=None, description="计划结束")
    owner_dept_id: Optional[int] = Field(default=None, description="责任部门")
    owner_user_id: Optional[int] = Field(default=None, description="责任人")
    priority: str = Field(default="MEDIUM", description="优先级")
    budget: Optional[Decimal] = Field(default=None, description="预算金额")


class AnnualKeyWorkUpdate(BaseModel):
    """更新年度重点工作"""
    name: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    voc_source: Optional[str] = None
    pain_point: Optional[str] = None
    solution: Optional[str] = None
    target: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    owner_dept_id: Optional[int] = None
    owner_user_id: Optional[int] = None
    status: Optional[str] = None
    progress_percent: Optional[int] = None
    priority: Optional[str] = None
    budget: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    risk_description: Optional[str] = None
    remark: Optional[str] = None


class AnnualKeyWorkResponse(TimestampSchema):
    """年度重点工作响应"""
    id: int
    csf_id: int
    code: str
    name: str
    description: Optional[str] = None
    voc_source: Optional[str] = None
    pain_point: Optional[str] = None
    solution: Optional[str] = None
    target: Optional[str] = None
    year: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    owner_dept_id: Optional[int] = None
    owner_user_id: Optional[int] = None
    status: str = "NOT_STARTED"
    progress_percent: int = 0
    priority: str = "MEDIUM"
    budget: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    risk_description: Optional[str] = None
    remark: Optional[str] = None
    is_active: bool = True

    # 扩展字段
    owner_dept_name: Optional[str] = None
    owner_name: Optional[str] = None
    csf_name: Optional[str] = None
    csf_dimension: Optional[str] = None
    linked_project_count: int = 0


class AnnualKeyWorkDetailResponse(AnnualKeyWorkResponse):
    """年度重点工作详情（含关联项目）"""
    linked_projects: List["ProjectLinkItem"] = []


class ProjectLinkItem(BaseModel):
    """关联项目项"""
    id: int
    project_id: int
    project_code: str
    project_name: str
    link_type: str
    contribution_weight: float = 100
    project_status: Optional[str] = None
    project_progress: Optional[float] = None

    class Config:
        from_attributes = True


class AnnualKeyWorkProgressUpdate(BaseModel):
    """更新工作进度"""
    progress_percent: int = Field(ge=0, le=100, description="完成进度（%）")
    status: Optional[str] = Field(default=None, description="状态")
    remark: Optional[str] = Field(default=None, description="备注")


class LinkProjectRequest(BaseModel):
    """关联项目请求"""
    project_id: int = Field(description="项目ID")
    link_type: str = Field(default="SUPPORT", description="关联类型：MAIN/SUPPORT/RELATED")
    contribution_weight: Decimal = Field(default=100, description="贡献权重（%）")
    remark: Optional[str] = Field(default=None, description="备注")


class UnlinkProjectRequest(BaseModel):
    """取消关联项目请求"""
    project_id: int = Field(description="项目ID")


# 更新前向引用
AnnualKeyWorkDetailResponse.model_rebuild()
