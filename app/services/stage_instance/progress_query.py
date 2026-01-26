# -*- coding: utf-8 -*-
"""
进度查询模块
提供项目阶段进度查询功能
"""

from typing import Any, Dict

from sqlalchemy.orm import joinedload

from app.models.enums import StageStatusEnum
from app.models.stage_instance import (
    ProjectNodeInstance,
    ProjectStageInstance,
)


class ProgressQueryMixin:
    """进度查询功能混入类"""

    def get_project_progress(self, project_id: int) -> Dict[str, Any]:
        """
        获取项目阶段进度

        Returns:
            Dict: {
                "total_stages": 总阶段数,
                "completed_stages": 已完成阶段数,
                "current_stage": 当前阶段信息,
                "total_nodes": 总节点数,
                "completed_nodes": 已完成节点数,
                "progress_pct": 整体进度百分比,
                "stages": [阶段列表]
            }
        """
        stages = self.db.query(ProjectStageInstance).filter(
            ProjectStageInstance.project_id == project_id
        ).options(
            joinedload(ProjectStageInstance.nodes)
        ).order_by(ProjectStageInstance.sequence).all()

        total_stages = len(stages)
        completed_stages = sum(1 for s in stages if s.status == StageStatusEnum.COMPLETED.value)

        total_nodes = 0
        completed_nodes = 0
        current_stage = None

        stage_list = []
        for stage in stages:
            nodes = list(stage.nodes)
            stage_total = len(nodes)
            stage_completed = sum(1 for n in nodes if n.status == StageStatusEnum.COMPLETED.value)

            total_nodes += stage_total
            completed_nodes += stage_completed

            if stage.status == StageStatusEnum.IN_PROGRESS.value:
                current_stage = {
                    "id": stage.id,
                    "stage_code": stage.stage_code,
                    "stage_name": stage.stage_name,
                    "progress_pct": round(stage_completed / stage_total * 100, 1) if stage_total > 0 else 0,
                }

            stage_list.append({
                "id": stage.id,
                "stage_code": stage.stage_code,
                "stage_name": stage.stage_name,
                "status": stage.status,
                "sequence": stage.sequence,
                "total_nodes": stage_total,
                "completed_nodes": stage_completed,
                "progress_pct": round(stage_completed / stage_total * 100, 1) if stage_total > 0 else 0,
                "planned_start_date": stage.planned_start_date.isoformat() if stage.planned_start_date else None,
                "planned_end_date": stage.planned_end_date.isoformat() if stage.planned_end_date else None,
                "actual_start_date": stage.actual_start_date.isoformat() if stage.actual_start_date else None,
                "actual_end_date": stage.actual_end_date.isoformat() if stage.actual_end_date else None,
            })

        return {
            "total_stages": total_stages,
            "completed_stages": completed_stages,
            "current_stage": current_stage,
            "total_nodes": total_nodes,
            "completed_nodes": completed_nodes,
            "progress_pct": round(completed_nodes / total_nodes * 100, 1) if total_nodes > 0 else 0,
            "stages": stage_list,
        }

    def get_stage_detail(self, stage_instance_id: int) -> Dict[str, Any]:
        """获取阶段详情（包含所有节点）"""
        stage = self.db.query(ProjectStageInstance).options(
            joinedload(ProjectStageInstance.nodes)
        ).filter(ProjectStageInstance.id == stage_instance_id).first()

        if not stage:
            return None

        nodes = []
        for node in sorted(stage.nodes, key=lambda n: n.sequence):
            nodes.append({
                "id": node.id,
                "node_code": node.node_code,
                "node_name": node.node_name,
                "node_type": node.node_type,
                "status": node.status,
                "sequence": node.sequence,
                "completion_method": node.completion_method,
                "is_required": node.is_required,
                "planned_date": node.planned_date.isoformat() if node.planned_date else None,
                "actual_date": node.actual_date.isoformat() if node.actual_date else None,
                "completed_by": node.completed_by,
                "completed_at": node.completed_at.isoformat() if node.completed_at else None,
                "attachments": node.attachments,
                "dependency_node_instance_ids": node.dependency_node_instance_ids,
                "can_start": self._check_node_dependencies(node) if node.status == StageStatusEnum.PENDING.value else False,
            })

        return {
            "id": stage.id,
            "project_id": stage.project_id,
            "stage_code": stage.stage_code,
            "stage_name": stage.stage_name,
            "status": stage.status,
            "sequence": stage.sequence,
            "planned_start_date": stage.planned_start_date.isoformat() if stage.planned_start_date else None,
            "planned_end_date": stage.planned_end_date.isoformat() if stage.planned_end_date else None,
            "actual_start_date": stage.actual_start_date.isoformat() if stage.actual_start_date else None,
            "actual_end_date": stage.actual_end_date.isoformat() if stage.actual_end_date else None,
            "is_modified": stage.is_modified,
            "remark": stage.remark,
            "nodes": nodes,
        }
