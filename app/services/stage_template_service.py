# -*- coding: utf-8 -*-
"""
阶段模板服务
提供阶段模板的 CRUD 操作、复制、导入导出等功能
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload

from app.models.enums import TemplateProjectTypeEnum
from app.models.stage_template import (
    NodeDefinition,
    StageDefinition,
    StageTemplate,
)


class StageTemplateService:
    """阶段模板服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 模板管理 ====================

    def create_template(
        self,
        template_code: str,
        template_name: str,
        description: Optional[str] = None,
        project_type: str = TemplateProjectTypeEnum.CUSTOM.value,
        is_default: bool = False,
        created_by: Optional[int] = None,
    ) -> StageTemplate:
        """
        创建阶段模板

        Args:
            template_code: 模板编码（唯一）
            template_name: 模板名称
            description: 模板描述
            project_type: 适用项目类型
            is_default: 是否设为默认模板
            created_by: 创建人ID

        Returns:
            StageTemplate: 创建的模板对象
        """
        # 检查编码唯一性
        existing = self.db.query(StageTemplate).filter(
            StageTemplate.template_code == template_code
        ).first()
        if existing:
            raise ValueError(f"模板编码 {template_code} 已存在")

        # 如果设为默认，先取消同类型的其他默认模板
        if is_default:
            self._clear_default_template(project_type)

        template = StageTemplate(
            template_code=template_code,
            template_name=template_name,
            description=description,
            project_type=project_type,
            is_default=is_default,
            is_active=True,
            created_by=created_by,
        )
        self.db.add(template)
        self.db.flush()
        return template

    def get_template(
        self,
        template_id: int,
        include_stages: bool = True,
        include_nodes: bool = True,
    ) -> Optional[StageTemplate]:
        """
        获取模板详情

        Args:
            template_id: 模板ID
            include_stages: 是否包含阶段定义
            include_nodes: 是否包含节点定义

        Returns:
            StageTemplate: 模板对象或None
        """
        query = self.db.query(StageTemplate)

        if include_stages:
            if include_nodes:
                query = query.options(
                    joinedload(StageTemplate.stages).joinedload(StageDefinition.nodes)
                )
            else:
                query = query.options(joinedload(StageTemplate.stages))

        return query.filter(StageTemplate.id == template_id).first()

    def list_templates(
        self,
        project_type: Optional[str] = None,
        is_active: Optional[bool] = True,
        include_stages: bool = False,
    ) -> List[StageTemplate]:
        """
        获取模板列表

        Args:
            project_type: 按项目类型筛选
            is_active: 按启用状态筛选
            include_stages: 是否包含阶段信息

        Returns:
            List[StageTemplate]: 模板列表
        """
        query = self.db.query(StageTemplate)

        if include_stages:
            query = query.options(joinedload(StageTemplate.stages))

        if project_type:
            query = query.filter(StageTemplate.project_type == project_type)

        if is_active is not None:
            query = query.filter(StageTemplate.is_active == is_active)

        return query.order_by(StageTemplate.project_type, StageTemplate.template_name).all()

    def update_template(
        self,
        template_id: int,
        **kwargs
    ) -> Optional[StageTemplate]:
        """
        更新模板信息

        Args:
            template_id: 模板ID
            **kwargs: 要更新的字段

        Returns:
            StageTemplate: 更新后的模板对象
        """
        template = self.db.query(StageTemplate).filter(
            StageTemplate.id == template_id
        ).first()

        if not template:
            return None

        # 处理设为默认的情况
        if kwargs.get("is_default") and not template.is_default:
            project_type = kwargs.get("project_type", template.project_type)
            self._clear_default_template(project_type)

        # 更新字段
        for key, value in kwargs.items():
            if hasattr(template, key) and key not in ["id", "created_at", "created_by"]:
                setattr(template, key, value)

        self.db.flush()
        return template

    def delete_template(self, template_id: int) -> bool:
        """
        删除模板（级联删除阶段和节点定义）

        Args:
            template_id: 模板ID

        Returns:
            bool: 是否删除成功
        """
        template = self.db.query(StageTemplate).filter(
            StageTemplate.id == template_id
        ).first()

        if not template:
            return False

        # 检查是否有项目在使用此模板
        from app.models.project import Project
        usage_count = self.db.query(Project).filter(
            Project.stage_template_id == template_id
        ).count()

        if usage_count > 0:
            raise ValueError(f"模板正在被 {usage_count} 个项目使用，无法删除")

        self.db.delete(template)
        return True

    def copy_template(
        self,
        source_template_id: int,
        new_code: str,
        new_name: str,
        created_by: Optional[int] = None,
    ) -> StageTemplate:
        """
        复制模板（包含所有阶段和节点定义）

        Args:
            source_template_id: 源模板ID
            new_code: 新模板编码
            new_name: 新模板名称
            created_by: 创建人ID

        Returns:
            StageTemplate: 新创建的模板
        """
        # 获取源模板（包含完整结构）
        source = self.get_template(source_template_id, include_stages=True, include_nodes=True)
        if not source:
            raise ValueError(f"源模板 {source_template_id} 不存在")

        # 创建新模板
        new_template = self.create_template(
            template_code=new_code,
            template_name=new_name,
            description=f"复制自: {source.template_name}",
            project_type=source.project_type,
            is_default=False,
            created_by=created_by,
        )

        # 复制阶段和节点
        stage_id_mapping = {}  # 旧ID -> 新ID 映射
        node_id_mapping = {}

        for stage in source.stages:
            new_stage = self.add_stage(
                template_id=new_template.id,
                stage_code=stage.stage_code,
                stage_name=stage.stage_name,
                sequence=stage.sequence,
                estimated_days=stage.estimated_days,
                description=stage.description,
                is_required=stage.is_required,
            )
            stage_id_mapping[stage.id] = new_stage.id

            for node in stage.nodes:
                new_node = self.add_node(
                    stage_definition_id=new_stage.id,
                    node_code=node.node_code,
                    node_name=node.node_name,
                    node_type=node.node_type,
                    sequence=node.sequence,
                    estimated_days=node.estimated_days,
                    completion_method=node.completion_method,
                    is_required=node.is_required,
                    required_attachments=node.required_attachments,
                    approval_role_ids=node.approval_role_ids,
                    auto_condition=node.auto_condition,
                    description=node.description,
                )
                node_id_mapping[node.id] = new_node.id

        # 更新节点依赖关系（使用新ID）
        for old_stage in source.stages:
            for old_node in old_stage.nodes:
                if old_node.dependency_node_ids:
                    new_node_id = node_id_mapping[old_node.id]
                    new_deps = [node_id_mapping[dep_id] for dep_id in old_node.dependency_node_ids if dep_id in node_id_mapping]
                    if new_deps:
                        self.db.query(NodeDefinition).filter(
                            NodeDefinition.id == new_node_id
                        ).update({"dependency_node_ids": new_deps})

        self.db.flush()
        return new_template

    # ==================== 阶段管理 ====================

    def add_stage(
        self,
        template_id: int,
        stage_code: str,
        stage_name: str,
        sequence: int = 0,
        estimated_days: Optional[int] = None,
        description: Optional[str] = None,
        is_required: bool = True,
    ) -> StageDefinition:
        """
        添加阶段定义

        Args:
            template_id: 模板ID
            stage_code: 阶段编码
            stage_name: 阶段名称
            sequence: 排序序号
            estimated_days: 预计工期（天）
            description: 阶段描述
            is_required: 是否必需阶段

        Returns:
            StageDefinition: 创建的阶段定义
        """
        # 检查模板存在
        template = self.db.query(StageTemplate).filter(
            StageTemplate.id == template_id
        ).first()
        if not template:
            raise ValueError(f"模板 {template_id} 不存在")

        # 检查编码在模板内唯一
        existing = self.db.query(StageDefinition).filter(
            and_(
                StageDefinition.template_id == template_id,
                StageDefinition.stage_code == stage_code
            )
        ).first()
        if existing:
            raise ValueError(f"阶段编码 {stage_code} 在该模板中已存在")

        stage = StageDefinition(
            template_id=template_id,
            stage_code=stage_code,
            stage_name=stage_name,
            sequence=sequence,
            estimated_days=estimated_days,
            description=description,
            is_required=is_required,
        )
        self.db.add(stage)
        self.db.flush()
        return stage

    def update_stage(
        self,
        stage_id: int,
        **kwargs
    ) -> Optional[StageDefinition]:
        """更新阶段定义"""
        stage = self.db.query(StageDefinition).filter(
            StageDefinition.id == stage_id
        ).first()

        if not stage:
            return None

        for key, value in kwargs.items():
            if hasattr(stage, key) and key not in ["id", "template_id", "created_at"]:
                setattr(stage, key, value)

        self.db.flush()
        return stage

    def delete_stage(self, stage_id: int) -> bool:
        """删除阶段定义（级联删除节点）"""
        stage = self.db.query(StageDefinition).filter(
            StageDefinition.id == stage_id
        ).first()

        if not stage:
            return False

        self.db.delete(stage)
        return True

    def reorder_stages(self, template_id: int, stage_ids: List[int]) -> bool:
        """重新排序阶段"""
        for index, stage_id in enumerate(stage_ids):
            self.db.query(StageDefinition).filter(
                and_(
                    StageDefinition.id == stage_id,
                    StageDefinition.template_id == template_id
                )
            ).update({"sequence": index})
        self.db.flush()
        return True

    # ==================== 节点管理 ====================

    def add_node(
        self,
        stage_definition_id: int,
        node_code: str,
        node_name: str,
        node_type: str = "TASK",
        sequence: int = 0,
        estimated_days: Optional[int] = None,
        completion_method: str = "MANUAL",
        dependency_node_ids: Optional[List[int]] = None,
        is_required: bool = True,
        required_attachments: bool = False,
        approval_role_ids: Optional[List[int]] = None,
        auto_condition: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
    ) -> NodeDefinition:
        """
        添加节点定义

        Args:
            stage_definition_id: 所属阶段定义ID
            node_code: 节点编码
            node_name: 节点名称
            node_type: 节点类型 (TASK/APPROVAL/DELIVERABLE)
            sequence: 排序序号
            estimated_days: 预计工期
            completion_method: 完成方式 (MANUAL/APPROVAL/UPLOAD/AUTO)
            dependency_node_ids: 前置依赖节点ID列表
            is_required: 是否必需节点
            required_attachments: 是否需要上传附件
            approval_role_ids: 审批角色ID列表
            auto_condition: 自动完成条件配置
            description: 节点描述

        Returns:
            NodeDefinition: 创建的节点定义
        """
        # 检查阶段存在
        stage = self.db.query(StageDefinition).filter(
            StageDefinition.id == stage_definition_id
        ).first()
        if not stage:
            raise ValueError(f"阶段定义 {stage_definition_id} 不存在")

        node = NodeDefinition(
            stage_definition_id=stage_definition_id,
            node_code=node_code,
            node_name=node_name,
            node_type=node_type,
            sequence=sequence,
            estimated_days=estimated_days,
            completion_method=completion_method,
            dependency_node_ids=dependency_node_ids,
            is_required=is_required,
            required_attachments=required_attachments,
            approval_role_ids=approval_role_ids,
            auto_condition=auto_condition,
            description=description,
        )
        self.db.add(node)
        self.db.flush()
        return node

    def update_node(
        self,
        node_id: int,
        **kwargs
    ) -> Optional[NodeDefinition]:
        """更新节点定义"""
        node = self.db.query(NodeDefinition).filter(
            NodeDefinition.id == node_id
        ).first()

        if not node:
            return None

        for key, value in kwargs.items():
            if hasattr(node, key) and key not in ["id", "stage_definition_id", "created_at"]:
                setattr(node, key, value)

        self.db.flush()
        return node

    def delete_node(self, node_id: int) -> bool:
        """删除节点定义"""
        node = self.db.query(NodeDefinition).filter(
            NodeDefinition.id == node_id
        ).first()

        if not node:
            return False

        # 清理其他节点对此节点的依赖引用
        self._remove_node_from_dependencies(node_id)

        self.db.delete(node)
        return True

    def reorder_nodes(self, stage_id: int, node_ids: List[int]) -> bool:
        """重新排序节点"""
        for index, node_id in enumerate(node_ids):
            self.db.query(NodeDefinition).filter(
                and_(
                    NodeDefinition.id == node_id,
                    NodeDefinition.stage_definition_id == stage_id
                )
            ).update({"sequence": index})
        self.db.flush()
        return True

    def set_node_dependencies(
        self,
        node_id: int,
        dependency_node_ids: List[int]
    ) -> NodeDefinition:
        """设置节点依赖关系"""
        node = self.db.query(NodeDefinition).filter(
            NodeDefinition.id == node_id
        ).first()

        if not node:
            raise ValueError(f"节点 {node_id} 不存在")

        # 验证依赖节点存在且属于同一模板
        stage = node.stage_definition
        template_id = stage.template_id

        for dep_id in dependency_node_ids:
            dep_node = self.db.query(NodeDefinition).join(StageDefinition).filter(
                and_(
                    NodeDefinition.id == dep_id,
                    StageDefinition.template_id == template_id
                )
            ).first()
            if not dep_node:
                raise ValueError(f"依赖节点 {dep_id} 不存在或不属于同一模板")

        # 检测循环依赖
        if self._has_circular_dependency(node_id, dependency_node_ids, template_id):
            raise ValueError("检测到循环依赖")

        node.dependency_node_ids = dependency_node_ids
        self.db.flush()
        return node

    # ==================== 默认模板 ====================

    def get_default_template(
        self,
        project_type: str = TemplateProjectTypeEnum.CUSTOM.value
    ) -> Optional[StageTemplate]:
        """获取指定项目类型的默认模板"""
        return self.db.query(StageTemplate).filter(
            and_(
                StageTemplate.project_type == project_type,
                StageTemplate.is_default == True,
                StageTemplate.is_active == True
            )
        ).first()

    def set_default_template(self, template_id: int) -> StageTemplate:
        """设置模板为默认"""
        template = self.db.query(StageTemplate).filter(
            StageTemplate.id == template_id
        ).first()

        if not template:
            raise ValueError(f"模板 {template_id} 不存在")

        # 取消同类型的其他默认模板
        self._clear_default_template(template.project_type)

        template.is_default = True
        self.db.flush()
        return template

    # ==================== 辅助方法 ====================

    def _clear_default_template(self, project_type: str) -> None:
        """取消指定项目类型的默认模板"""
        self.db.query(StageTemplate).filter(
            and_(
                StageTemplate.project_type == project_type,
                StageTemplate.is_default == True
            )
        ).update({"is_default": False})

    def _remove_node_from_dependencies(self, node_id: int) -> None:
        """从所有节点的依赖列表中移除指定节点"""
        # 获取引用此节点的所有节点
        nodes = self.db.query(NodeDefinition).filter(
            NodeDefinition.dependency_node_ids.isnot(None)
        ).all()

        for node in nodes:
            if node.dependency_node_ids and node_id in node.dependency_node_ids:
                new_deps = [d for d in node.dependency_node_ids if d != node_id]
                node.dependency_node_ids = new_deps if new_deps else None

    def _has_circular_dependency(
        self,
        node_id: int,
        new_dependency_ids: List[int],
        template_id: int
    ) -> bool:
        """检测是否存在循环依赖"""
        visited = set()

        def dfs(current_id: int) -> bool:
            if current_id == node_id:
                return True
            if current_id in visited:
                return False
            visited.add(current_id)

            node = self.db.query(NodeDefinition).filter(
                NodeDefinition.id == current_id
            ).first()

            if node and node.dependency_node_ids:
                for dep_id in node.dependency_node_ids:
                    if dfs(dep_id):
                        return True
            return False

        for dep_id in new_dependency_ids:
            if dfs(dep_id):
                return True
        return False

    # ==================== 导入导出 ====================

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
    ) -> StageTemplate:
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

    def _get_dependency_codes(self, node: NodeDefinition) -> List[str]:
        """获取节点依赖的节点编码列表"""
        if not node.dependency_node_ids:
            return []

        dep_nodes = self.db.query(NodeDefinition).filter(
            NodeDefinition.id.in_(node.dependency_node_ids)
        ).all()

        return [n.node_code for n in dep_nodes]
