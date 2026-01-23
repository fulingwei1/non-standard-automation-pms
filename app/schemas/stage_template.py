# -*- coding: utf-8 -*-
"""
阶段模板 Pydantic Schemas
定义 API 请求/响应的数据验证模型
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.enums import (
    CompletionMethodEnum,
    NodeTypeEnum,
    TemplateProjectTypeEnum,
)


# ==================== 节点定义 Schemas ====================


class NodeDefinitionBase(BaseModel):
    """节点定义基础模型"""

    node_code: str = Field(..., description="节点编码")
    node_name: str = Field(..., description="节点名称")
    node_type: NodeTypeEnum = Field(default=NodeTypeEnum.TASK, description="节点类型")
    sequence: int = Field(default=0, description="排序序号")
    estimated_days: Optional[int] = Field(None, description="预计工期(天)")
    completion_method: CompletionMethodEnum = Field(
        default=CompletionMethodEnum.MANUAL, description="完成方式"
    )
    dependency_node_ids: Optional[List[int]] = Field(
        default=None, description="前置依赖节点ID列表"
    )
    is_required: bool = Field(default=True, description="是否必需节点")
    required_attachments: bool = Field(default=False, description="是否需上传附件")
    approval_role_ids: Optional[List[int]] = Field(
        default=None, description="审批角色ID列表"
    )
    auto_condition: Optional[Dict[str, Any]] = Field(
        default=None, description="自动完成条件配置"
    )
    description: Optional[str] = Field(None, description="节点描述")
    owner_role_code: Optional[str] = Field(None, description="负责角色编码")
    participant_role_codes: Optional[List[str]] = Field(
        default=None, description="参与角色编码列表"
    )
    deliverables: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="交付物清单"
    )


class NodeDefinitionCreate(NodeDefinitionBase):
    """创建节点定义请求"""

    stage_definition_id: Optional[int] = Field(None, description="所属阶段ID")


class NodeDefinitionUpdate(NodeDefinitionBase):
    """更新节点定义请求"""

    pass  # 所有字段都可选


class NodeDefinitionResponse(NodeDefinitionBase):
    """节点定义响应"""

    id: int
    stage_definition_id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== 阶段定义 Schemas ====================


class StageDefinitionBase(BaseModel):
    """阶段定义基础模型"""

    stage_code: str = Field(..., description="阶段编码")
    stage_name: str = Field(..., description="阶段名称")
    sequence: int = Field(default=0, description="排序序号")
    category: str = Field(default="execution", description="阶段分类")
    estimated_days: Optional[int] = Field(None, description="预计工期(天)")
    description: Optional[str] = Field(None, description="阶段描述")
    is_required: bool = Field(default=True, description="是否必需阶段")
    is_milestone: bool = Field(default=False, description="是否关键里程碑")
    is_parallel: bool = Field(default=False, description="是否支持并行执行")


class StageDefinitionCreate(StageDefinitionBase):
    """创建阶段定义请求"""

    nodes: Optional[List[NodeDefinitionCreate]] = Field(
        default=None, description="包含的节点列表"
    )


class StageDefinitionUpdate(StageDefinitionBase):
    """更新阶段定义请求"""

    pass  # 所有字段都可选


class StageDefinitionResponse(StageDefinitionBase):
    """阶段定义响应"""

    id: int
    template_id: int
    nodes: List[NodeDefinitionResponse] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== 模板 Schemas ====================


class StageTemplateBase(BaseModel):
    """阶段模板基础模型"""

    template_code: str = Field(..., description="模板编码")
    template_name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    project_type: TemplateProjectTypeEnum = Field(
        default=TemplateProjectTypeEnum.CUSTOM, description="适用项目类型"
    )
    is_default: bool = Field(default=False, description="是否默认模板")
    is_active: bool = Field(default=True, description="是否启用")


class StageTemplateCreate(StageTemplateBase):
    """创建模板请求"""

    stages: Optional[List[StageDefinitionCreate]] = Field(
        default=None, description="包含的阶段列表"
    )


class StageTemplateUpdate(StageTemplateBase):
    """更新模板请求"""

    pass  # 所有字段都可选


class StageTemplateResponse(StageTemplateBase):
    """模板响应（列表用）"""

    id: int
    stage_count: int = Field(default=0, description="阶段数量")
    node_count: int = Field(default=0, description="节点数量")
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class StageTemplateDetail(StageTemplateBase):
    """模板详情响应"""

    id: int
    stages: List[StageDefinitionResponse] = Field(default_factory=list)
    created_by: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== 复制模板 Schema ====================


class StageTemplateCopy(BaseModel):
    """复制模板请求"""

    new_code: str = Field(..., description="新模板编码")
    new_name: str = Field(..., description="新模板名称")


# ==================== 排序 Schemas ====================


class ReorderStagesRequest(BaseModel):
    """重新排序阶段请求"""

    stage_ids: List[int] = Field(..., description="阶段ID列表，按新顺序排列")


class ReorderNodesRequest(BaseModel):
    """重新排序节点请求"""

    node_ids: List[int] = Field(..., description="节点ID列表，按新顺序排列")


class SetNodeDependenciesRequest(BaseModel):
    """设置节点依赖请求"""

    dependency_node_ids: List[int] = Field(..., description="前置依赖节点ID列表")


# ==================== 导入导出 Schemas ====================


class NodeDefinitionExport(NodeDefinitionBase):
    """节点定义导出模型"""

    id: Optional[int] = None
    stage_definition_id: Optional[int] = None


class StageDefinitionExport(StageDefinitionBase):
    """阶段定义导出模型"""

    id: Optional[int] = None
    template_id: Optional[int] = None
    nodes: Optional[List[NodeDefinitionExport]] = None


class TemplateExportData(StageTemplateBase):
    """模板导出数据"""

    id: Optional[int] = None
    stages: Optional[List[StageDefinitionExport]] = None


class TemplateImportRequest(BaseModel):
    """模板导入请求"""

    data: TemplateExportData = Field(..., description="导入的模板数据")
    override_code: Optional[str] = Field(None, description="覆盖现有模板的编码")
