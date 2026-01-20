# -*- coding: utf-8 -*-
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

class StageAdjustment(BaseModel):
    """阶段调整配置"""
    estimated_days: Optional[int] = Field(default=None, description="调整后的预计工期")
    stage_name: Optional[str] = Field(default=None, description="调整后的阶段名称")


class NodeAdjustment(BaseModel):
    """节点调整配置"""
    estimated_days: Optional[int] = Field(default=None, description="调整后的预计工期")
    node_name: Optional[str] = Field(default=None, description="调整后的节点名称")
    is_required: Optional[bool] = Field(default=None, description="是否必需")


class InitializeProjectStagesRequest(BaseModel):
    """初始化项目阶段请求"""
    template_id: int = Field(..., description="模板ID")
    start_date: Optional[date] = Field(default=None, description="项目开始日期")
    skip_stages: Optional[List[str]] = Field(default=None, description="跳过的阶段编码列表")
    skip_nodes: Optional[List[str]] = Field(default=None, description="跳过的节点编码列表")
    stage_overrides: Optional[Dict[str, StageAdjustment]] = Field(default=None, description="阶段调整配置")
    node_overrides: Optional[Dict[str, NodeAdjustment]] = Field(default=None, description="节点调整配置")


class AddCustomNodeRequest(BaseModel):
    """添加自定义节点请求"""
    stage_instance_id: int = Field(..., description="阶段实例ID")
    node_code: str = Field(..., max_length=20, description="节点编码")
    node_name: str = Field(..., max_length=100, description="节点名称")
    node_type: str = Field(default="TASK", description="节点类型")
    completion_method: str = Field(default="MANUAL", description="完成方式")
    is_required: bool = Field(default=False, description="是否必需")
    planned_date: Optional[date] = Field(default=None, description="计划日期")
    insert_after_node_id: Optional[int] = Field(default=None, description="插入位置(在此节点之后)")


# ==================== 进度 Schemas ====================

class StageProgress(BaseModel):
    """阶段进度信息"""
    id: int
    stage_code: str
    stage_name: str
    status: str
    sequence: int
    category: str = Field(default="execution", description="阶段分类")
    is_milestone: bool = Field(default=False, description="是否关键里程碑")
    is_parallel: bool = Field(default=False, description="是否支持并行执行")
    total_nodes: int
    completed_nodes: int
    progress_pct: float
    planned_start_date: Optional[str] = None
    planned_end_date: Optional[str] = None
    actual_start_date: Optional[str] = None
    actual_end_date: Optional[str] = None


class CurrentStageInfo(BaseModel):
    """当前阶段信息"""
    id: int
    stage_code: str
    stage_name: str
    progress_pct: float


class ProjectProgressResponse(BaseModel):
    """项目进度响应"""
    total_stages: int = Field(description="总阶段数")
    completed_stages: int = Field(description="已完成阶段数")
    current_stage: Optional[CurrentStageInfo] = Field(default=None, description="当前阶段")
    total_nodes: int = Field(description="总节点数")
    completed_nodes: int = Field(description="已完成节点数")
    progress_pct: float = Field(description="整体进度百分比")
    stages: List[StageProgress] = Field(default=[], description="阶段列表")


# ==================== 排序 Schemas ====================

class ReorderStagesRequest(BaseModel):
    """重排阶段顺序请求"""
    stage_ids: List[int] = Field(..., description="按新顺序排列的阶段ID列表")


class ReorderNodesRequest(BaseModel):
    """重排节点顺序请求"""
    node_ids: List[int] = Field(..., description="按新顺序排列的节点ID列表")


class SetNodeDependenciesRequest(BaseModel):
    """设置节点依赖请求"""
    dependency_node_ids: List[int] = Field(default=[], description="依赖节点ID列表")


# ==================== 导入导出 Schemas ====================

class TemplateExportData(BaseModel):
    """模板导出数据"""
    template_code: str
    template_name: str
    description: Optional[str] = None
    project_type: str
    stages: List[Dict[str, Any]]


class TemplateImportRequest(BaseModel):
    """模板导入请求"""
    data: Dict[str, Any] = Field(..., description="模板数据")
    override_code: Optional[str] = Field(default=None, description="覆盖模板编码")
    override_name: Optional[str] = Field(default=None, description="覆盖模板名称")


# ==================== 节点子任务 Schemas ====================

class NodeTaskBase(BaseModel):
    """节点子任务基础"""
    task_name: str = Field(..., max_length=200, description="任务名称")
    description: Optional[str] = Field(default=None, description="任务描述")
    estimated_hours: Optional[int] = Field(default=None, ge=0, description="预计工时(小时)")
    planned_start_date: Optional[date] = Field(default=None, description="计划开始日期")
    planned_end_date: Optional[date] = Field(default=None, description="计划结束日期")
    priority: str = Field(default="NORMAL", description="优先级: LOW/NORMAL/HIGH/URGENT")
    tags: Optional[str] = Field(default=None, max_length=200, description="标签(逗号分隔)")


class NodeTaskCreate(NodeTaskBase):
    """创建节点子任务"""
    node_instance_id: int = Field(..., description="所属节点实例ID")
    task_code: Optional[str] = Field(default=None, max_length=30, description="任务编码(不传则自动生成)")
    assignee_id: Optional[int] = Field(default=None, description="执行人ID")


class NodeTaskUpdate(BaseModel):
    """更新节点子任务"""
    task_name: Optional[str] = Field(default=None, max_length=200, description="任务名称")
    description: Optional[str] = Field(default=None, description="任务描述")
    estimated_hours: Optional[int] = Field(default=None, ge=0, description="预计工时")
    planned_start_date: Optional[date] = Field(default=None, description="计划开始日期")
    planned_end_date: Optional[date] = Field(default=None, description="计划结束日期")
    priority: Optional[str] = Field(default=None, description="优先级")
    tags: Optional[str] = Field(default=None, description="标签")
    assignee_id: Optional[int] = Field(default=None, description="执行人ID")
    remark: Optional[str] = Field(default=None, description="备注")


class NodeTaskComplete(BaseModel):
    """完成节点子任务请求"""
    actual_hours: Optional[int] = Field(default=None, ge=0, description="实际工时")
    attachments: Optional[List[Dict[str, Any]]] = Field(default=None, description="附件列表")
    remark: Optional[str] = Field(default=None, description="备注")


class NodeTaskResponse(NodeTaskBase):
    """节点子任务响应"""
    id: int
    node_instance_id: int
    task_code: str
    sequence: int
    status: str
    actual_hours: Optional[int] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    assignee_id: Optional[int] = None
    completed_by: Optional[int] = None
    completed_at: Optional[datetime] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    remark: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BatchCreateTasksRequest(BaseModel):
    """批量创建任务请求"""
    tasks: List[NodeTaskBase] = Field(..., description="任务列表")


class ReorderTasksRequest(BaseModel):
    """重排任务顺序请求"""
    task_ids: List[int] = Field(..., description="按新顺序排列的任务ID列表")


class NodeTaskProgressResponse(BaseModel):
    """节点任务进度响应"""
    total: int = Field(description="总任务数")
    completed: int = Field(description="已完成数")
    in_progress: int = Field(description="进行中数")
    pending: int = Field(description="待开始数")
    skipped: int = Field(description="已跳过数")
    progress_pct: float = Field(description="完成百分比")
    total_estimated_hours: int = Field(description="总预计工时")
    total_actual_hours: int = Field(description="总实际工时")


class AssignNodeRequest(BaseModel):
    """分配节点负责人请求"""
    assignee_id: int = Field(..., description="负责人ID")
    auto_complete_on_tasks: bool = Field(default=True, description="子任务全部完成时是否自动完成节点")


# ==================== 流水线视图 Schemas ====================

class ProjectStageOverview(BaseModel):
    """项目阶段概览（流水线视图用）"""
    project_id: int
    project_code: str
    project_name: str
    customer_name: Optional[str] = None
    current_stage_code: Optional[str] = None
    current_stage_name: Optional[str] = None
    progress_pct: float = Field(default=0, description="整体进度百分比")
    health_status: str = Field(default="H1", description="健康状态")
    stages: List[StageProgress] = Field(default=[], description="阶段列表")


class PipelineStatistics(BaseModel):
    """流水线统计数据"""
    total_projects: int = Field(default=0, description="总项目数")
    in_progress_count: int = Field(default=0, description="进行中项目数")
    completed_count: int = Field(default=0, description="已完成项目数")
    delayed_count: int = Field(default=0, description="延期项目数")
    blocked_count: int = Field(default=0, description="受阻项目数")
    # 按阶段分类统计
    by_category: Dict[str, int] = Field(default={}, description="按阶段分类统计")
    # 按当前阶段统计
    by_current_stage: Dict[str, int] = Field(default={}, description="按当前阶段统计")


class PipelineViewResponse(BaseModel):
    """流水线视图响应"""
    statistics: PipelineStatistics
    projects: List[ProjectStageOverview]
    stage_definitions: List[StageDefinitionResponse] = Field(
        default=[], description="阶段定义列表（用于表头）"
    )


# ==================== 时间轴视图 Schemas ====================

class TimelineNode(BaseModel):
    """时间轴节点"""
    id: int
    node_code: str
    node_name: str
    node_type: str
    status: str
    progress: int = 0
    planned_date: Optional[str] = None
    actual_date: Optional[str] = None
    assignee_name: Optional[str] = None
    dependency_ids: List[int] = Field(default=[], description="依赖节点ID")


class TimelineStage(BaseModel):
    """时间轴阶段"""
    id: int
    stage_code: str
    stage_name: str
    category: str
    status: str
    is_milestone: bool = False
    is_parallel: bool = False
    progress: int = 0
    planned_start_date: Optional[str] = None
    planned_end_date: Optional[str] = None
    actual_start_date: Optional[str] = None
    actual_end_date: Optional[str] = None
    nodes: List[TimelineNode] = Field(default=[], description="节点列表")


class TimelineViewResponse(BaseModel):
    """时间轴视图响应"""
    project_id: int
    project_code: str
    project_name: str
    planned_start_date: Optional[str] = None
    planned_end_date: Optional[str] = None
    actual_start_date: Optional[str] = None
    overall_progress: float = 0
    stages: List[TimelineStage] = Field(default=[], description="阶段列表")


# ==================== 分解树视图 Schemas ====================

class TreeTask(BaseModel):
    """分解树任务节点"""
    id: int
    task_code: str
    task_name: str
    status: str
    priority: str = "NORMAL"
    assignee_name: Optional[str] = None
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None
    progress_pct: float = 0


class TreeNode(BaseModel):
    """分解树节点"""
    id: int
    node_code: str
    node_name: str
    node_type: str
    status: str
    progress: int = 0
    assignee_name: Optional[str] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    tasks: List[TreeTask] = Field(default=[], description="子任务列表")


class TreeStage(BaseModel):
    """分解树阶段"""
    id: int
    stage_code: str
    stage_name: str
    category: str
    status: str
    is_milestone: bool = False
    progress: int = 0
    total_nodes: int = 0
    completed_nodes: int = 0
    nodes: List[TreeNode] = Field(default=[], description="节点列表")


class TreeViewResponse(BaseModel):
    """分解树视图响应"""
    project_id: int
    project_code: str
    project_name: str
    overall_progress: float = 0
    total_stages: int = 0
    completed_stages: int = 0
    total_nodes: int = 0
    completed_nodes: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    stages: List[TreeStage] = Field(default=[], description="阶段列表")


# ==================== 状态更新 Schemas ====================

class UpdateStageStatusRequest(BaseModel):
    """更新阶段状态请求"""
    status: str = Field(..., description="新状态: PENDING/IN_PROGRESS/COMPLETED/DELAYED/BLOCKED/SKIPPED")
    remark: Optional[str] = Field(default=None, description="备注说明")


class StageReviewRequest(BaseModel):
    """阶段评审请求"""
    review_result: str = Field(..., description="评审结果: PASSED/CONDITIONAL/FAILED")
    review_notes: Optional[str] = Field(default=None, description="评审记录")

