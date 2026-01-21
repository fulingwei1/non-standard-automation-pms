# -*- coding: utf-8 -*-
"""
节点和阶段定义 Schemas

包含节点定义、阶段定义、模板定义的 Schema
"""

"""
阶段模板 Schema 定义
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field



# ==================== 节点定义 Schemas ====================

class NodeDefinitionBase(BaseModel):
    """节点定义基础"""
    node_code: str = Field(..., max_length=20, description="节点编码")
    node_name: str = Field(..., max_length=100, description="节点名称")
    node_type: str = Field(default="TASK", description="节点类型: TASK/APPROVAL/DELIVERABLE")
    sequence: int = Field(default=0, ge=0, description="排序序号")
    estimated_days: Optional[int] = Field(default=None, ge=0, description="预计工期(天)")
    completion_method: str = Field(default="MANUAL", description="完成方式: MANUAL/APPROVAL/UPLOAD/AUTO")
    is_required: bool = Field(default=True, description="是否必需节点")
    required_attachments: bool = Field(default=False, description="是否需要上传附件")
    approval_role_ids: Optional[List[int]] = Field(default=None, description="审批角色ID列表")
    auto_condition: Optional[Dict[str, Any]] = Field(default=None, description="自动完成条件配置")
    description: Optional[str] = Field(default=None, description="节点描述")
    # 责任分配与交付物
    owner_role_code: Optional[str] = Field(default=None, max_length=50, description="负责角色编码")
    participant_role_codes: Optional[List[str]] = Field(default=None, description="参与角色编码列表")
    deliverables: Optional[List[str]] = Field(default=None, description="交付物清单")


class NodeDefinitionCreate(NodeDefinitionBase):
    """创建节点定义"""
    stage_definition_id: int = Field(..., description="所属阶段定义ID")
    dependency_node_ids: Optional[List[int]] = Field(default=None, description="前置依赖节点ID列表")


class NodeDefinitionUpdate(BaseModel):
    """更新节点定义"""
    node_name: Optional[str] = Field(default=None, max_length=100, description="节点名称")
    node_type: Optional[str] = Field(default=None, description="节点类型")
    sequence: Optional[int] = Field(default=None, ge=0, description="排序序号")
    estimated_days: Optional[int] = Field(default=None, ge=0, description="预计工期")
    completion_method: Optional[str] = Field(default=None, description="完成方式")
    is_required: Optional[bool] = Field(default=None, description="是否必需")
    required_attachments: Optional[bool] = Field(default=None, description="是否需要附件")
    approval_role_ids: Optional[List[int]] = Field(default=None, description="审批角色ID列表")
    auto_condition: Optional[Dict[str, Any]] = Field(default=None, description="自动完成条件")
    description: Optional[str] = Field(default=None, description="描述")
    dependency_node_ids: Optional[List[int]] = Field(default=None, description="前置依赖节点ID")
    # 责任分配与交付物
    owner_role_code: Optional[str] = Field(default=None, max_length=50, description="负责角色编码")
    participant_role_codes: Optional[List[str]] = Field(default=None, description="参与角色编码列表")
    deliverables: Optional[List[str]] = Field(default=None, description="交付物清单")


class NodeDefinitionResponse(NodeDefinitionBase):
    """节点定义响应"""
    id: int
    stage_definition_id: int
    dependency_node_ids: Optional[List[int]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 阶段定义 Schemas ====================

class StageDefinitionBase(BaseModel):
    """阶段定义基础"""
    stage_code: str = Field(..., max_length=20, description="阶段编码")
    stage_name: str = Field(..., max_length=100, description="阶段名称")
    sequence: int = Field(default=0, ge=0, description="排序序号")
    category: str = Field(default="execution", description="阶段分类: sales/presales/execution/closure")
    estimated_days: Optional[int] = Field(default=None, ge=0, description="预计工期(天)")
    description: Optional[str] = Field(default=None, description="阶段描述")
    is_required: bool = Field(default=True, description="是否必需阶段")
    is_milestone: bool = Field(default=False, description="是否关键里程碑")
    is_parallel: bool = Field(default=False, description="是否支持并行执行")


class StageDefinitionCreate(StageDefinitionBase):
    """创建阶段定义"""
    template_id: int = Field(..., description="所属模板ID")


class StageDefinitionUpdate(BaseModel):
    """更新阶段定义"""
    stage_name: Optional[str] = Field(default=None, max_length=100, description="阶段名称")
    sequence: Optional[int] = Field(default=None, ge=0, description="排序序号")
    category: Optional[str] = Field(default=None, description="阶段分类")
    estimated_days: Optional[int] = Field(default=None, ge=0, description="预计工期")
    description: Optional[str] = Field(default=None, description="描述")
    is_required: Optional[bool] = Field(default=None, description="是否必需")
    is_milestone: Optional[bool] = Field(default=None, description="是否关键里程碑")
    is_parallel: Optional[bool] = Field(default=None, description="是否支持并行执行")


class StageDefinitionResponse(StageDefinitionBase):
    """阶段定义响应"""
    id: int
    template_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StageDefinitionWithNodes(StageDefinitionResponse):
    """阶段定义响应(含节点)"""
    nodes: List[NodeDefinitionResponse] = []


# ==================== 模板 Schemas ====================

class StageTemplateBase(BaseModel):
    """阶段模板基础"""
    template_code: str = Field(..., max_length=50, description="模板编码")
    template_name: str = Field(..., max_length=100, description="模板名称")
    description: Optional[str] = Field(default=None, description="模板描述")
    project_type: str = Field(default="CUSTOM", description="适用项目类型: NEW/REPEAT/SIMPLE/CUSTOM")


class StageTemplateCreate(StageTemplateBase):
    """创建阶段模板"""
    is_default: bool = Field(default=False, description="是否默认模板")


class StageTemplateUpdate(BaseModel):
    """更新阶段模板"""
    template_name: Optional[str] = Field(default=None, max_length=100, description="模板名称")
    description: Optional[str] = Field(default=None, description="描述")
    project_type: Optional[str] = Field(default=None, description="项目类型")
    is_default: Optional[bool] = Field(default=None, description="是否默认")
    is_active: Optional[bool] = Field(default=None, description="是否启用")


class StageTemplateResponse(StageTemplateBase):
    """阶段模板响应"""
    id: int
    is_default: bool = False
    is_active: bool = True
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StageTemplateWithStages(StageTemplateResponse):
    """阶段模板响应(含阶段)"""
    stages: List[StageDefinitionResponse] = []


class StageTemplateDetail(StageTemplateResponse):
    """阶段模板详情(含阶段和节点)"""
    stages: List[StageDefinitionWithNodes] = []


class StageTemplateCopy(BaseModel):
    """复制模板请求"""
    new_code: str = Field(..., max_length=50, description="新模板编码")
    new_name: str = Field(..., max_length=100, description="新模板名称")

