# -*- coding: utf-8 -*-
"""
项目阶段和节点实例 Schemas

包含项目阶段实例和节点实例的 Schema
"""

"""
阶段模板 Schema 定义
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field



# ==================== 项目阶段实例 Schemas ====================

class ProjectStageInstanceBase(BaseModel):
    """项目阶段实例基础"""
    stage_code: str = Field(..., max_length=20, description="阶段编码")
    stage_name: str = Field(..., max_length=100, description="阶段名称")
    sequence: int = Field(default=0, description="排序序号")
    status: str = Field(default="PENDING", description="状态")
    category: str = Field(default="execution", description="阶段分类")
    is_milestone: bool = Field(default=False, description="是否关键里程碑")
    is_parallel: bool = Field(default=False, description="是否支持并行执行")
    progress: int = Field(default=0, ge=0, le=100, description="阶段进度百分比")
    planned_start_date: Optional[date] = Field(default=None, description="计划开始日期")
    planned_end_date: Optional[date] = Field(default=None, description="计划结束日期")
    remark: Optional[str] = Field(default=None, description="备注")


class ProjectStageInstanceUpdate(BaseModel):
    """更新项目阶段实例"""
    planned_start_date: Optional[date] = Field(default=None, description="计划开始日期")
    planned_end_date: Optional[date] = Field(default=None, description="计划结束日期")
    remark: Optional[str] = Field(default=None, description="备注")


class ProjectStageInstanceResponse(ProjectStageInstanceBase):
    """项目阶段实例响应"""
    id: int
    project_id: int
    stage_definition_id: Optional[int] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    is_modified: bool = False
    # 门控检查
    entry_criteria: Optional[str] = Field(default=None, description="入口条件")
    exit_criteria: Optional[str] = Field(default=None, description="出口条件")
    entry_check_result: Optional[str] = Field(default=None, description="入口检查结果")
    exit_check_result: Optional[str] = Field(default=None, description="出口检查结果")
    # 阶段评审
    review_required: bool = Field(default=False, description="是否需要评审")
    review_result: Optional[str] = Field(default=None, description="评审结果")
    review_date: Optional[datetime] = Field(default=None, description="评审日期")
    review_notes: Optional[str] = Field(default=None, description="评审记录")
    # 时间戳
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 项目节点实例 Schemas ====================

class ProjectNodeInstanceBase(BaseModel):
    """项目节点实例基础"""
    node_code: str = Field(..., max_length=20, description="节点编码")
    node_name: str = Field(..., max_length=100, description="节点名称")
    node_type: str = Field(default="TASK", description="节点类型")
    sequence: int = Field(default=0, description="排序序号")
    status: str = Field(default="PENDING", description="状态")
    progress: int = Field(default=0, ge=0, le=100, description="节点进度百分比")
    completion_method: str = Field(default="MANUAL", description="完成方式")
    is_required: bool = Field(default=True, description="是否必需")
    planned_date: Optional[date] = Field(default=None, description="计划完成日期")
    remark: Optional[str] = Field(default=None, description="备注")
    # 责任分配与交付物
    owner_role_code: Optional[str] = Field(default=None, description="负责角色编码")
    participant_role_codes: Optional[List[str]] = Field(default=None, description="参与角色编码列表")
    deliverables: Optional[List[str]] = Field(default=None, description="交付物清单")


class ProjectNodeInstanceUpdate(BaseModel):
    """更新项目节点实例"""
    planned_date: Optional[date] = Field(default=None, description="计划完成日期")
    remark: Optional[str] = Field(default=None, description="备注")
    # 责任分配与交付物（可在项目中调整）
    owner_role_code: Optional[str] = Field(default=None, description="负责角色编码")
    participant_role_codes: Optional[List[str]] = Field(default=None, description="参与角色编码列表")
    deliverables: Optional[List[str]] = Field(default=None, description="交付物清单")
    owner_id: Optional[int] = Field(default=None, description="实际负责人ID")
    participant_ids: Optional[List[int]] = Field(default=None, description="实际参与人ID列表")


class ProjectNodeInstanceComplete(BaseModel):
    """完成节点请求"""
    attachments: Optional[List[Dict[str, Any]]] = Field(default=None, description="附件列表")
    approval_record_id: Optional[int] = Field(default=None, description="审批记录ID")
    remark: Optional[str] = Field(default=None, description="备注")


class ProjectNodeInstanceResponse(ProjectNodeInstanceBase):
    """项目节点实例响应"""
    id: int
    project_id: int
    stage_instance_id: int
    node_definition_id: Optional[int] = None
    dependency_node_instance_ids: Optional[List[int]] = None
    actual_date: Optional[date] = None
    completed_by: Optional[int] = None
    completed_at: Optional[datetime] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    approval_record_id: Optional[int] = None
    can_start: bool = Field(default=False, description="是否可以开始")
    # 任务分解相关
    assignee_id: Optional[int] = Field(default=None, description="负责人ID")
    auto_complete_on_tasks: bool = Field(default=True, description="子任务全部完成时自动完成节点")
    # 实际指派的人员
    owner_id: Optional[int] = None
    participant_ids: Optional[List[int]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectStageInstanceDetail(ProjectStageInstanceResponse):
    """项目阶段实例详情(含节点)"""
    nodes: List[ProjectNodeInstanceResponse] = []


# ==================== 初始化项目阶段 Schemas ====================
