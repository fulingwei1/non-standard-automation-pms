# -*- coding: utf-8 -*-
"""
辅助方法模块
提供默认模板清理、依赖管理、循环依赖检测等辅助功能
"""

from typing import List

from sqlalchemy import and_

from app.models.stage_template import NodeDefinition, StageTemplate


class HelpersMixin:
    """辅助方法功能混入类"""

    def _clear_default_template(self, project_type: str) -> None:
        """取消指定项目类型的默认模板"""
        self.db.query(StageTemplate).filter(
            and_(
                StageTemplate.project_type == project_type,
                StageTemplate.is_default
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

    def _get_dependency_codes(self, node: NodeDefinition) -> List[str]:
        """获取节点依赖的节点编码列表"""
        if not node.dependency_node_ids:
            return []

        dep_nodes = self.db.query(NodeDefinition).filter(
            NodeDefinition.id.in_(node.dependency_node_ids)
        ).all()

        return [n.node_code for n in dep_nodes]
