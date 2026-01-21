# -*- coding: utf-8 -*-
"""
阶段模板 Schema 模块统一导出

模块结构:
 ├── definitions.py      # 节点和阶段定义 Schemas
 ├── instances.py        # 项目阶段和节点实例 Schemas
 ├── initialization.py   # 初始化项目阶段 Schemas
 ├── progress.py        # 进度和排序 Schemas
 ├── import_export.py    # 导入导出 Schemas
 ├── node_tasks.py      # 节点子任务 Schemas
 ├── views.py           # 视图 Schemas
 └── status.py          # 状态更新 Schemas
"""

# 节点和阶段定义
from .definitions import (
    NodeDefinitionBase,
    NodeDefinitionCreate,
    NodeDefinitionResponse,
    NodeDefinitionUpdate,
    StageDefinitionBase,
    StageDefinitionCreate,
    StageDefinitionResponse,
    StageDefinitionUpdate,
    StageDefinitionWithNodes,
    StageTemplateBase,
    StageTemplateCopy,
    StageTemplateCreate,
    StageTemplateDetail,
    StageTemplateResponse,
    StageTemplateUpdate,
    StageTemplateWithStages,
)

# 项目阶段和节点实例
from .instances import (
    ProjectNodeInstanceBase,
    ProjectNodeInstanceComplete,
    ProjectNodeInstanceResponse,
    ProjectNodeInstanceUpdate,
    ProjectStageInstanceBase,
    ProjectStageInstanceDetail,
    ProjectStageInstanceResponse,
    ProjectStageInstanceUpdate,
)

# 初始化项目阶段
from .initialization import (
    AddCustomNodeRequest,
    InitializeProjectStagesRequest,
    NodeAdjustment,
    StageAdjustment,
)

# 进度和排序
from .progress import (
    CurrentStageInfo,
    ProjectProgressResponse,
    ReorderNodesRequest,
    ReorderStagesRequest,
    SetNodeDependenciesRequest,
    StageProgress,
)

# 导入导出
from .import_export import (
    TemplateExportData,
    TemplateImportRequest,
)

# 节点子任务
from .node_tasks import (
    AssignNodeRequest,
    BatchCreateTasksRequest,
    NodeTaskBase,
    NodeTaskComplete,
    NodeTaskCreate,
    NodeTaskProgressResponse,
    NodeTaskResponse,
    NodeTaskUpdate,
    ReorderTasksRequest,
)

# 视图
from .views import (
    PipelineStatistics,
    PipelineViewResponse,
    ProjectStageOverview,
    TimelineNode,
    TimelineStage,
    TimelineViewResponse,
    TreeNode,
    TreeStage,
    TreeTask,
    TreeViewResponse,
)

# 状态更新
from .status import (
    StageReviewRequest,
    UpdateStageStatusRequest,
)

__all__ = [
    # 节点和阶段定义
    "NodeDefinitionBase",
    "NodeDefinitionCreate",
    "NodeDefinitionUpdate",
    "NodeDefinitionResponse",
    "StageDefinitionBase",
    "StageDefinitionCreate",
    "StageDefinitionUpdate",
    "StageDefinitionResponse",
    "StageDefinitionWithNodes",
    "StageTemplateBase",
    "StageTemplateCreate",
    "StageTemplateUpdate",
    "StageTemplateResponse",
    "StageTemplateWithStages",
    "StageTemplateDetail",
    "StageTemplateCopy",
    # 项目阶段和节点实例
    "ProjectStageInstanceBase",
    "ProjectStageInstanceUpdate",
    "ProjectStageInstanceResponse",
    "ProjectStageInstanceDetail",
    "ProjectNodeInstanceBase",
    "ProjectNodeInstanceUpdate",
    "ProjectNodeInstanceComplete",
    "ProjectNodeInstanceResponse",
    # 初始化项目阶段
    "StageAdjustment",
    "NodeAdjustment",
    "InitializeProjectStagesRequest",
    "AddCustomNodeRequest",
    # 进度和排序
    "StageProgress",
    "CurrentStageInfo",
    "ProjectProgressResponse",
    "ReorderStagesRequest",
    "ReorderNodesRequest",
    "SetNodeDependenciesRequest",
    # 导入导出
    "TemplateExportData",
    "TemplateImportRequest",
    # 节点子任务
    "NodeTaskBase",
    "NodeTaskCreate",
    "NodeTaskUpdate",
    "NodeTaskComplete",
    "NodeTaskResponse",
    "BatchCreateTasksRequest",
    "ReorderTasksRequest",
    "NodeTaskProgressResponse",
    "AssignNodeRequest",
    # 视图
    "ProjectStageOverview",
    "PipelineStatistics",
    "PipelineViewResponse",
    "TimelineNode",
    "TimelineStage",
    "TimelineViewResponse",
    "TreeTask",
    "TreeNode",
    "TreeStage",
    "TreeViewResponse",
    # 状态更新
    "UpdateStageStatusRequest",
    "StageReviewRequest",
]
