# -*- coding: utf-8 -*-
"""
项目阶段视图 - 时间轴视图
"""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.stage_instance import ProjectStageInstance
from app.models.user import User
from app.schemas.stage_template import (
    TimelineNode,
    TimelineStage,
    TimelineViewResponse,
)
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.get("/views/timeline", response_model=TimelineViewResponse)
def get_timeline_view(
    project_id: int,
    db: Session = Depends(deps.get_db),
    include_nodes: bool = Query(True, description="是否包含节点详情"),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    时间轴视图 - 单项目甘特图

    返回单个项目的阶段和节点时间线，用于查看项目时间规划。
    """

    project = get_or_404(db, Project, project_id, detail="项目不存在")

    stages = (
        db.query(ProjectStageInstance)
        .filter(ProjectStageInstance.project_id == project_id)
        .order_by(ProjectStageInstance.sequence)
        .all()
    )

    timeline_stages = []
    total_completed = 0

    for stage in stages:
        nodes = []
        if include_nodes and stage.nodes:
            for node in stage.nodes:
                # 获取依赖节点ID
                dependency_ids = node.dependency_node_instance_ids or []

                # 获取负责人名称
                assignee_name = None
                if node.assignee:
                    assignee_name = getattr(node.assignee, "name", None) or getattr(
                        node.assignee, "username", None
                    )

                nodes.append(
                    TimelineNode(
                        id=node.id,
                        node_code=node.node_code,
                        node_name=node.node_name,
                        node_type=node.node_type,
                        status=node.status,
                        progress=node.progress or 0,
                        planned_date=(
                            node.planned_date.isoformat() if node.planned_date else None
                        ),
                        actual_date=(
                            node.actual_date.isoformat() if node.actual_date else None
                        ),
                        assignee_name=assignee_name,
                        dependency_ids=dependency_ids,
                    )
                )

        if stage.status == "COMPLETED":
            total_completed += 1

        timeline_stages.append(
            TimelineStage(
                id=stage.id,
                stage_code=stage.stage_code,
                stage_name=stage.stage_name,
                category=stage.category or "execution",
                status=stage.status,
                is_milestone=stage.is_milestone or False,
                is_parallel=stage.is_parallel or False,
                progress=stage.progress or 0,
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
                    stage.actual_end_date.isoformat() if stage.actual_end_date else None
                ),
                nodes=nodes,
            )
        )

    total_stages = len(timeline_stages)
    overall_progress = (total_completed / total_stages * 100) if total_stages > 0 else 0

    return TimelineViewResponse(
        project_id=project.id,
        project_code=project.project_code,
        project_name=project.project_name,
        planned_start_date=(
            project.planned_start_date.isoformat()
            if hasattr(project, "planned_start_date") and project.planned_start_date
            else None
        ),
        planned_end_date=(
            project.planned_end_date.isoformat()
            if hasattr(project, "planned_end_date") and project.planned_end_date
            else None
        ),
        actual_start_date=(
            project.actual_start_date.isoformat()
            if hasattr(project, "actual_start_date") and project.actual_start_date
            else None
        ),
        overall_progress=overall_progress,
        stages=timeline_stages,
    )
