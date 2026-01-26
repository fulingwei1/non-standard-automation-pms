# -*- coding: utf-8 -*-
"""
节点管理模块
提供节点定义的CRUD、排序和依赖管理功能
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import and_

from app.models.stage_template import NodeDefinition, StageDefinition


class NodeManagementMixin:
    """节点管理功能混入类"""

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
        owner_role_code: Optional[str] = None,
        participant_role_codes: Optional[List[str]] = None,
        deliverables: Optional[List[str]] = None,
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
            owner_role_code: 负责角色编码
            participant_role_codes: 参与角色编码列表
            deliverables: 交付物清单

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
            owner_role_code=owner_role_code,
            participant_role_codes=participant_role_codes,
            deliverables=deliverables,
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
