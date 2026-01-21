# -*- coding: utf-8 -*-
"""
模板CRUD模块
提供模板的创建、查询、更新、删除、复制等功能
"""

from typing import List, Optional

from sqlalchemy.orm import joinedload

from app.models.enums import TemplateProjectTypeEnum
from app.models.project import Project
from app.models.stage_template import (
    NodeDefinition,
    StageDefinition,
    StageTemplate,
)


class TemplateCrudMixin:
    """模板CRUD功能混入类"""

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
