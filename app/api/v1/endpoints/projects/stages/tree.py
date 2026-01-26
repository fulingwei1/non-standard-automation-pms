# -*- coding: utf-8 -*-
"""
项目阶段视图 - 分解树视图
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.stage_instance import ProjectStageInstance
from app.models.user import User
from app.schemas.stage_template import (
    TreeNode,
    TreeStage,
    TreeTask,
    TreeViewResponse,
)

router = APIRouter()


@router.get("/views/tree", response_model=TreeViewResponse)
def get_tree_view(
    project_id: int,
    db: Session = Depends(deps.get_db),
    include_tasks: bool = Query(True, description="是否包含子任务"),
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    分解树视图 - 阶段/节点/任务分解

    返回项目的阶段-节点-任务三级分解结构，用于查看工作分解详情。
    """

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    stages = (
        db.query(ProjectStageInstance)
        .filter(ProjectStageInstance.project_id == project_id)
        .order_by(ProjectStageInstance.sequence)
        .all()
    )

    tree_stages = []
    total_stages = len(stages)
    completed_stages = 0
    total_nodes = 0
    completed_nodes = 0
    total_tasks = 0
    completed_tasks = 0

    for stage in stages:
        stage_nodes = []
        stage_completed_nodes = 0

        for node in stage.nodes or []:
            total_nodes += 1
            tasks = []
            node_completed_tasks = 0

            if include_tasks and hasattr(node, "tasks") and node.tasks:
                for task in node.tasks:
                    total_tasks += 1
                    if task.status == "COMPLETED":
                        completed_tasks += 1
                        node_completed_tasks += 1

                    # 获取执行人名称
                    assignee_name = None
                    if task.assignee:
                        assignee_name = getattr(task.assignee, "name", None) or getattr(
                            task.assignee, "username", None
                        )

                    # 计算任务进度
                    task_progress = 100 if task.status == "COMPLETED" else 0
                    if task.status == "IN_PROGRESS":
                        task_progress = 50  # 简化处理

                    tasks.append(
                        TreeTask(
                            id=task.id,
                            task_code=task.task_code,
                            task_name=task.task_name,
                            status=task.status,
                            priority=task.priority or "NORMAL",
                            assignee_name=assignee_name,
                            estimated_hours=task.estimated_hours,
                            actual_hours=task.actual_hours,
                            progress_pct=task_progress,
                        )
                    )

            if node.status == "COMPLETED":
                completed_nodes += 1
                stage_completed_nodes += 1

            # 获取负责人名称
            assignee_name = None
            if node.assignee:
                assignee_name = getattr(node.assignee, "name", None) or getattr(
                    node.assignee, "username", None
                )

            stage_nodes.append(
                TreeNode(
                    id=node.id,
                    node_code=node.node_code,
                    node_name=node.node_name,
                    node_type=node.node_type,
                    status=node.status,
                    progress=node.progress or 0,
                    assignee_name=assignee_name,
                    total_tasks=len(tasks),
                    completed_tasks=node_completed_tasks,
                    tasks=tasks,
                )
            )

        if stage.status == "COMPLETED":
            completed_stages += 1

        tree_stages.append(
            TreeStage(
                id=stage.id,
                stage_code=stage.stage_code,
                stage_name=stage.stage_name,
                category=stage.category or "execution",
                status=stage.status,
                is_milestone=stage.is_milestone or False,
                progress=stage.progress or 0,
                total_nodes=len(stage_nodes),
                completed_nodes=stage_completed_nodes,
                nodes=stage_nodes,
            )
        )

    overall_progress = (
        (completed_stages / total_stages * 100) if total_stages > 0 else 0
    )

    return TreeViewResponse(
        project_id=project.id,
        project_code=project.project_code,
        project_name=project.project_name,
        overall_progress=overall_progress,
        total_stages=total_stages,
        completed_stages=completed_stages,
        total_nodes=total_nodes,
        completed_nodes=completed_nodes,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        stages=tree_stages,
    )
