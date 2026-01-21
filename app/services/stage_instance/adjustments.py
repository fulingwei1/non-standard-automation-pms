# -*- coding: utf-8 -*-
"""
调整操作模块
处理阶段/节点的动态调整
"""

from datetime import date
from typing import Optional

from sqlalchemy import and_

from app.models.enums import CompletionMethodEnum, NodeTypeEnum, StageStatusEnum
from app.models.stage_instance import (
    ProjectNodeInstance,
    ProjectStageInstance,
)


class AdjustmentsMixin:
    """调整操作功能混入类"""

    def add_custom_node(
        self,
        stage_instance_id: int,
        node_code: str,
        node_name: str,
        node_type: str = NodeTypeEnum.TASK.value,
        completion_method: str = CompletionMethodEnum.MANUAL.value,
        is_required: bool = False,
        planned_date: Optional[date] = None,
        insert_after_node_id: Optional[int] = None,
    ) -> ProjectNodeInstance:
        """
        在阶段中添加自定义节点

        Args:
            stage_instance_id: 阶段实例ID
            node_code: 节点编码
            node_name: 节点名称
            node_type: 节点类型
            completion_method: 完成方式
            is_required: 是否必需
            planned_date: 计划日期
            insert_after_node_id: 插入位置（在此节点之后）

        Returns:
            ProjectNodeInstance: 创建的节点实例
        """
        stage = self.db.query(ProjectStageInstance).filter(
            ProjectStageInstance.id == stage_instance_id
        ).first()

        if not stage:
            raise ValueError(f"阶段实例 {stage_instance_id} 不存在")

        # 确定序号
        if insert_after_node_id:
            after_node = self.db.query(ProjectNodeInstance).filter(
                ProjectNodeInstance.id == insert_after_node_id
            ).first()
            sequence = after_node.sequence + 1 if after_node else 0

            # 后移其他节点
            self.db.query(ProjectNodeInstance).filter(
                and_(
                    ProjectNodeInstance.stage_instance_id == stage_instance_id,
                    ProjectNodeInstance.sequence >= sequence
                )
            ).update({"sequence": ProjectNodeInstance.sequence + 1})
        else:
            # 添加到末尾
            max_seq = self.db.query(ProjectNodeInstance).filter(
                ProjectNodeInstance.stage_instance_id == stage_instance_id
            ).count()
            sequence = max_seq

        node = ProjectNodeInstance(
            project_id=stage.project_id,
            stage_instance_id=stage_instance_id,
            node_code=node_code,
            node_name=node_name,
            node_type=node_type,
            sequence=sequence,
            status=StageStatusEnum.PENDING.value,
            completion_method=completion_method,
            is_required=is_required,
            planned_date=planned_date,
        )
        self.db.add(node)

        # 标记阶段已修改
        stage.is_modified = True

        self.db.flush()
        return node

    def update_node_planned_date(
        self,
        node_instance_id: int,
        planned_date: date,
    ) -> ProjectNodeInstance:
        """更新节点计划日期"""
        node = self.db.query(ProjectNodeInstance).filter(
            ProjectNodeInstance.id == node_instance_id
        ).first()

        if not node:
            raise ValueError(f"节点实例 {node_instance_id} 不存在")

        node.planned_date = planned_date
        self.db.flush()
        return node
