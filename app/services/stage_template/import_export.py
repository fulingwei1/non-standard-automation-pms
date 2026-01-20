# -*- coding: utf-8 -*-
"""
导入导出模块
提供模板的导入导出功能
"""

from typing import Any, Dict, List, Optional

from app.models.enums import TemplateProjectTypeEnum
from app.models.stage_template import NodeDefinition


class ImportExportMixin:
    """导入导出功能混入类"""

    def export_template(self, template_id: int) -> Dict[str, Any]:
        """
        导出模板为字典格式（用于JSON导出）

        Args:
            template_id: 模板ID

        Returns:
            Dict: 模板完整结构
        """
        template = self.get_template(template_id, include_stages=True, include_nodes=True)
        if not template:
            raise ValueError(f"模板 {template_id} 不存在")

        return {
            "template_code": template.template_code,
            "template_name": template.template_name,
            "description": template.description,
            "project_type": template.project_type,
            "stages": [
                {
                    "stage_code": stage.stage_code,
                    "stage_name": stage.stage_name,
                    "sequence": stage.sequence,
                    "estimated_days": stage.estimated_days,
                    "description": stage.description,
                    "is_required": stage.is_required,
                    "nodes": [
                        {
                            "node_code": node.node_code,
                            "node_name": node.node_name,
                            "node_type": node.node_type,
                            "sequence": node.sequence,
                            "estimated_days": node.estimated_days,
                            "completion_method": node.completion_method,
                            "is_required": node.is_required,
                            "required_attachments": node.required_attachments,
                            "approval_role_ids": node.approval_role_ids,
                            "auto_condition": node.auto_condition,
                            "description": node.description,
                            "dependency_node_codes": self._get_dependency_codes(node),
                        }
                        for node in sorted(stage.nodes, key=lambda n: n.sequence)
                    ]
                }
                for stage in sorted(template.stages, key=lambda s: s.sequence)
            ]
        }

    def import_template(
        self,
        data: Dict[str, Any],
        created_by: Optional[int] = None,
        override_code: Optional[str] = None,
        override_name: Optional[str] = None,
    ) -> Any:
        """
        从字典格式导入模板

        Args:
            data: 模板数据
            created_by: 创建人ID
            override_code: 覆盖模板编码
            override_name: 覆盖模板名称

        Returns:
            StageTemplate: 创建的模板
        """
        from app.models.stage_template import StageTemplate

        template = self.create_template(
            template_code=override_code or data["template_code"],
            template_name=override_name or data["template_name"],
            description=data.get("description"),
            project_type=data.get("project_type", TemplateProjectTypeEnum.CUSTOM.value),
            is_default=False,
            created_by=created_by,
        )

        # 第一遍：创建所有阶段和节点（不处理依赖）
        node_code_to_id = {}  # node_code -> node_id 映射

        for stage_data in data.get("stages", []):
            stage = self.add_stage(
                template_id=template.id,
                stage_code=stage_data["stage_code"],
                stage_name=stage_data["stage_name"],
                sequence=stage_data.get("sequence", 0),
                estimated_days=stage_data.get("estimated_days"),
                description=stage_data.get("description"),
                is_required=stage_data.get("is_required", True),
            )

            for node_data in stage_data.get("nodes", []):
                node = self.add_node(
                    stage_definition_id=stage.id,
                    node_code=node_data["node_code"],
                    node_name=node_data["node_name"],
                    node_type=node_data.get("node_type", "TASK"),
                    sequence=node_data.get("sequence", 0),
                    estimated_days=node_data.get("estimated_days"),
                    completion_method=node_data.get("completion_method", "MANUAL"),
                    is_required=node_data.get("is_required", True),
                    required_attachments=node_data.get("required_attachments", False),
                    approval_role_ids=node_data.get("approval_role_ids"),
                    auto_condition=node_data.get("auto_condition"),
                    description=node_data.get("description"),
                )
                node_code_to_id[node_data["node_code"]] = node.id

        # 第二遍：处理节点依赖关系
        for stage_data in data.get("stages", []):
            for node_data in stage_data.get("nodes", []):
                dep_codes = node_data.get("dependency_node_codes", [])
                if dep_codes:
                    node_id = node_code_to_id[node_data["node_code"]]
                    dep_ids = [node_code_to_id[code] for code in dep_codes if code in node_code_to_id]
                    if dep_ids:
                        self.db.query(NodeDefinition).filter(
                            NodeDefinition.id == node_id
                        ).update({"dependency_node_ids": dep_ids})

        self.db.flush()
        return template
