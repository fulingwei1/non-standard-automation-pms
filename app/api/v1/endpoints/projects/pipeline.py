# -*- coding: utf-8 -*-
"""
项目阶段视图 - 流水线视图
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.stage_instance import ProjectStageInstance
from app.models.stage_template import StageDefinition, StageTemplate
from app.models.user import User
from app.common.query_filters import apply_pagination
from app.common.pagination import PaginationParams, get_pagination_query
from app.schemas.stage_template import (
    PipelineStatistics,
    PipelineViewResponse,
    ProjectStageOverview,
    StageDefinitionResponse,
    StageProgress,
    TemplateGroup,
)

router = APIRouter()


@router.get("/views/pipeline", response_model=PipelineViewResponse)
def get_pipeline_view(
    db: Session = Depends(deps.get_db),
    category: Optional[str] = Query(None, description="阶段分类筛选"),
    health_status: Optional[str] = Query(None, description="健康状态筛选"),
    template_id: Optional[int] = Query(None, description="模板ID筛选"),
    group_by_template: bool = Query(False, description="是否按模板分组"),
    pagination: PaginationParams = Depends(get_pagination_query),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    流水线视图 - 多项目阶段全景

    返回所有项目的阶段进度概览，支持按分类、健康状态和模板筛选。
    可选按模板分组显示，用于 PM 总监查看整体项目进展情况。
    """

    # 获取所有可用模板（用于筛选下拉框）
    all_templates = db.query(StageTemplate).filter(StageTemplate.is_active).all()
    available_templates = [
        {"id": t.id, "code": t.template_code, "name": t.template_name}
        for t in all_templates
    ]

    # 查询所有活跃项目
    projects_query = db.query(Project).filter(Project.is_active)

    # 按健康状态筛选
    if health_status:
        projects_query = projects_query.filter(Project.health == health_status)

    # 按模板筛选
    if template_id:
        projects_query = projects_query.filter(Project.stage_template_id == template_id)

    projects = apply_pagination(projects_query, pagination.offset, pagination.limit).all()

    # 构建统计数据
    total_count = projects_query.count()
    stats = PipelineStatistics(
        total_projects=total_count,
        in_progress_count=0,
        completed_count=0,
        delayed_count=0,
        blocked_count=0,
        by_category={},
        by_current_stage={},
    )

    project_overviews = []
    for project in projects:
        # 获取项目的阶段实例
        stages = (
            db.query(ProjectStageInstance)
            .filter(ProjectStageInstance.project_id == project.id)
            .order_by(ProjectStageInstance.sequence)
            .all()
        )

        # 构建阶段进度列表
        stage_progress_list = []
        current_stage = None
        has_delayed = False
        has_blocked = False
        completed_stages = 0

        for stage in stages:
            # 按分类筛选
            if category and stage.category != category:
                continue

            # 计算节点完成数
            total_nodes = len(stage.nodes) if stage.nodes else 0
            completed_nodes = sum(
                1 for n in (stage.nodes or []) if n.status == "COMPLETED"
            )
            progress_pct = (
                (completed_nodes / total_nodes * 100) if total_nodes > 0 else 0
            )

            stage_progress = StageProgress(
                id=stage.id,
                stage_code=stage.stage_code,
                stage_name=stage.stage_name,
                status=stage.status,
                sequence=stage.sequence,
                category=stage.category or "execution",
                is_milestone=stage.is_milestone or False,
                is_parallel=stage.is_parallel or False,
                total_nodes=total_nodes,
                completed_nodes=completed_nodes,
                progress_pct=progress_pct,
                planned_start_date=(
                    stage.planned_start_date.isoformat()
                    if stage.planned_start_date
                    else None
                ),
                planned_end_date=(
                    stage.planned_end_date.isoformat()
                    if stage.planned_end_date
                    else None
                ),
                actual_start_date=(
                    stage.actual_start_date.isoformat()
                    if stage.actual_start_date
                    else None
                ),
                actual_end_date=(
                    stage.actual_end_date.isoformat()
                    if stage.actual_end_date
                    else None
                ),
            )
            stage_progress_list.append(stage_progress)

            # 统计
            if stage.status == "IN_PROGRESS":
                current_stage = stage
            elif stage.status == "COMPLETED":
                completed_stages += 1
            elif stage.status == "DELAYED":
                has_delayed = True
            elif stage.status == "BLOCKED":
                has_blocked = True

            # 按分类统计
            cat = stage.category or "execution"
            stats.by_category[cat] = stats.by_category.get(cat, 0) + 1

        # 计算整体进度
        total_stages = len(stage_progress_list)
        overall_progress = (
            (completed_stages / total_stages * 100) if total_stages > 0 else 0
        )

        # 更新统计
        if has_blocked:
            stats.blocked_count += 1
        elif has_delayed:
            stats.delayed_count += 1
        elif completed_stages == total_stages and total_stages > 0:
            stats.completed_count += 1
        else:
            stats.in_progress_count += 1

        if current_stage:
            stats.by_current_stage[current_stage.stage_code] = (
                stats.by_current_stage.get(current_stage.stage_code, 0) + 1
            )

        # 获取项目的模板信息
        project_template = None
        if hasattr(project, "stage_template_id") and project.stage_template_id:
            project_template = db.query(StageTemplate).filter(
                StageTemplate.id == project.stage_template_id
            ).first()

        project_overviews.append(
            ProjectStageOverview(
                project_id=project.id,
                project_code=project.project_code,
                project_name=project.project_name,
                customer_name=getattr(project, "customer_name", None),
                template_id=project.stage_template_id if hasattr(project, "stage_template_id") else None,
                template_code=project_template.template_code if project_template else None,
                template_name=project_template.template_name if project_template else None,
                current_stage_code=(
                    current_stage.stage_code if current_stage else None
                ),
                current_stage_name=(
                    current_stage.stage_name if current_stage else None
                ),
                progress_pct=overall_progress,
                health_status=project.health or "H1",
                stages=stage_progress_list,
            )
        )

    # 获取阶段定义（用于表头）
    default_template = (
        db.query(StageTemplate).filter(StageTemplate.is_default).first()
    )
    stage_definitions = []
    if default_template:
        definitions = (
            db.query(StageDefinition)
            .filter(StageDefinition.template_id == default_template.id)
            .order_by(StageDefinition.sequence)
            .all()
        )
        stage_definitions = [StageDefinitionResponse.model_validate(d) for d in definitions]

    # 按模板分组（如果请求分组）
    template_groups = []
    if group_by_template:
        # 按模板ID分组项目
        groups_map = {}
        for proj in project_overviews:
            tid = proj.template_id or 0
            if tid not in groups_map:
                # 获取模板的阶段定义
                if tid > 0:
                    template = db.query(StageTemplate).filter(StageTemplate.id == tid).first()
                    template_defs = (
                        db.query(StageDefinition)
                        .filter(StageDefinition.template_id == tid)
                        .order_by(StageDefinition.sequence)
                        .all()
                    )
                    groups_map[tid] = {
                        "template_id": tid,
                        "template_code": template.template_code if template else "UNKNOWN",
                        "template_name": template.template_name if template else "未知模板",
                        "stage_definitions": [StageDefinitionResponse.model_validate(d) for d in template_defs],
                        "projects": [],
                    }
                else:
                    groups_map[tid] = {
                        "template_id": 0,
                        "template_code": "NO_TEMPLATE",
                        "template_name": "无模板（旧项目）",
                        "stage_definitions": stage_definitions,  # 使用默认模板的阶段定义
                        "projects": [],
                    }
            groups_map[tid]["projects"].append(proj)

        # 转换为列表并添加项目数量
        for tid, group_data in groups_map.items():
            template_groups.append(TemplateGroup(
                template_id=group_data["template_id"],
                template_code=group_data["template_code"],
                template_name=group_data["template_name"],
                project_count=len(group_data["projects"]),
                stage_definitions=group_data["stage_definitions"],
                projects=group_data["projects"],
            ))

    return PipelineViewResponse(
        statistics=stats,
        projects=project_overviews,
        stage_definitions=stage_definitions,
        template_groups=template_groups,
        available_templates=available_templates,
    )
