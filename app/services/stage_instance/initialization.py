# -*- coding: utf-8 -*-
"""
阶段实例初始化模块
处理项目阶段/节点的实例化
"""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import joinedload

from app.models.enums import StageStatusEnum
from app.models.project import Project
from app.models.stage_instance import (
    ProjectNodeInstance,
    ProjectStageInstance,
)
from app.models.stage_template import (
    NodeDefinition,
    StageDefinition,
    StageTemplate,
)


class InitializationMixin:
    """项目实例化功能混入类"""

    def initialize_project_stages(
        self,
        project_id: int,
        template_id: int,
        start_date: Optional[date] = None,
        adjustments: Optional[Dict[str, Any]] = None,
    ) -> List[ProjectStageInstance]:
        """
        根据模板初始化项目的阶段和节点

        Args:
            project_id: 项目ID
            template_id: 模板ID
            start_date: 项目开始日期（用于计算计划日期）
            adjustments: 调整配置（可跳过某些阶段/节点）
                {
                    "skip_stages": ["STAGE_CODE1", "STAGE_CODE2"],
                    "skip_nodes": ["NODE_CODE1", "NODE_CODE2"],
                    "stage_overrides": {
                        "STAGE_CODE": {"estimated_days": 10, "stage_name": "新名称"}
                    },
                    "node_overrides": {
                        "NODE_CODE": {"estimated_days": 5, "is_required": False}
                    }
                }

        Returns:
            List[ProjectStageInstance]: 创建的阶段实例列表
        """
        # 验证项目存在
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")

        # 获取模板（包含完整结构）
        template = self.db.query(StageTemplate).options(
            joinedload(StageTemplate.stages).joinedload(StageDefinition.nodes)
        ).filter(StageTemplate.id == template_id).first()

        if not template:
            raise ValueError(f"模板 {template_id} 不存在")

        # 检查项目是否已有阶段实例
        existing_count = self.db.query(ProjectStageInstance).filter(
            ProjectStageInstance.project_id == project_id
        ).count()

        if existing_count > 0:
            raise ValueError(f"项目 {project_id} 已有阶段实例，请先清除")

        adjustments = adjustments or {}
        skip_stages = set(adjustments.get("skip_stages", []))
        skip_nodes = set(adjustments.get("skip_nodes", []))
        stage_overrides = adjustments.get("stage_overrides", {})
        node_overrides = adjustments.get("node_overrides", {})

        # 计算日期
        current_date = start_date or date.today()
        created_stages = []
        node_def_to_instance = {}  # 节点定义ID -> 实例ID 映射（用于依赖转换）

        # 按顺序创建阶段实例
        for stage_def in sorted(template.stages, key=lambda s: s.sequence):
            if stage_def.stage_code in skip_stages:
                continue

            # 应用阶段覆盖
            stage_override = stage_overrides.get(stage_def.stage_code, {})
            estimated_days = stage_override.get("estimated_days", stage_def.estimated_days) or 0

            stage_instance = ProjectStageInstance(
                project_id=project_id,
                stage_definition_id=stage_def.id,
                stage_code=stage_def.stage_code,
                stage_name=stage_override.get("stage_name", stage_def.stage_name),
                sequence=stage_def.sequence,
                status=StageStatusEnum.PENDING.value,
                planned_start_date=current_date,
                planned_end_date=current_date + timedelta(days=estimated_days) if estimated_days else None,
                is_modified=bool(stage_override),
            )
            self.db.add(stage_instance)
            self.db.flush()

            # 创建节点实例
            node_start_date = current_date
            for node_def in sorted(stage_def.nodes, key=lambda n: n.sequence):
                if node_def.node_code in skip_nodes:
                    continue

                # 应用节点覆盖
                node_override = node_overrides.get(node_def.node_code, {})
                node_estimated_days = node_override.get("estimated_days", node_def.estimated_days) or 0

                node_instance = ProjectNodeInstance(
                    project_id=project_id,
                    stage_instance_id=stage_instance.id,
                    node_definition_id=node_def.id,
                    node_code=node_def.node_code,
                    node_name=node_override.get("node_name", node_def.node_name),
                    node_type=node_def.node_type,
                    sequence=node_def.sequence,
                    status=StageStatusEnum.PENDING.value,
                    completion_method=node_def.completion_method,
                    is_required=node_override.get("is_required", node_def.is_required),
                    planned_date=node_start_date + timedelta(days=node_estimated_days) if node_estimated_days else None,
                    # 复制责任分配与交付物字段
                    owner_role_code=node_def.owner_role_code,
                    participant_role_codes=node_def.participant_role_codes,
                    deliverables=node_def.deliverables,
                )
                self.db.add(node_instance)
                self.db.flush()

                node_def_to_instance[node_def.id] = node_instance.id

                # 累加节点工期
                if node_estimated_days:
                    node_start_date = node_start_date + timedelta(days=node_estimated_days)

            # 更新下一阶段的开始日期
            if estimated_days:
                current_date = current_date + timedelta(days=estimated_days)

            created_stages.append(stage_instance)

        # 第二遍：转换节点依赖关系（定义ID -> 实例ID）
        for stage_instance in created_stages:
            for node_instance in stage_instance.nodes:
                if node_instance.node_definition_id:
                    node_def = self.db.query(NodeDefinition).filter(
                        NodeDefinition.id == node_instance.node_definition_id
                    ).first()
                    if node_def and node_def.dependency_node_ids:
                        instance_deps = [
                            node_def_to_instance[def_id]
                            for def_id in node_def.dependency_node_ids
                            if def_id in node_def_to_instance
                        ]
                        if instance_deps:
                            node_instance.dependency_node_instance_ids = instance_deps

        # 更新项目关联
        project.stage_template_id = template_id
        if created_stages:
            project.current_stage_instance_id = created_stages[0].id
            first_stage_nodes = list(created_stages[0].nodes)
            if first_stage_nodes:
                project.current_node_instance_id = first_stage_nodes[0].id

        self.db.flush()
        return created_stages

    def clear_project_stages(self, project_id: int) -> int:
        """
        清除项目的所有阶段实例

        Args:
            project_id: 项目ID

        Returns:
            int: 删除的阶段实例数量
        """
        # 先清除项目的当前阶段引用
        self.db.query(Project).filter(Project.id == project_id).update({
            "stage_template_id": None,
            "current_stage_instance_id": None,
            "current_node_instance_id": None,
        })

        # 删除节点实例（会由 cascade 自动删除，但显式删除更清晰）
        self.db.query(ProjectNodeInstance).filter(
            ProjectNodeInstance.project_id == project_id
        ).delete()

        # 删除阶段实例
        count = self.db.query(ProjectStageInstance).filter(
            ProjectStageInstance.project_id == project_id
        ).delete()

        return count
