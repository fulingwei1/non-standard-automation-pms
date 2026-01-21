# -*- coding: utf-8 -*-
"""
节点操作模块
处理节点的开始、完成、跳过等操作
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from app.models.enums import CompletionMethodEnum, StageStatusEnum
from app.models.project import Project
from app.models.stage_instance import ProjectNodeInstance


class NodeOperationsMixin:
    """节点操作功能混入类"""

    def start_node(
        self,
        node_instance_id: int,
    ) -> ProjectNodeInstance:
        """开始节点"""
        node = self.db.query(ProjectNodeInstance).filter(
            ProjectNodeInstance.id == node_instance_id
        ).first()

        if not node:
            raise ValueError(f"节点实例 {node_instance_id} 不存在")

        if node.status != StageStatusEnum.PENDING.value:
            raise ValueError(f"节点当前状态为 {node.status}，无法开始")

        # 检查依赖是否满足
        if not self._check_node_dependencies(node):
            raise ValueError("前置依赖节点未完成")

        node.status = StageStatusEnum.IN_PROGRESS.value

        # 更新项目的当前节点
        self.db.query(Project).filter(
            Project.id == node.project_id
        ).update({"current_node_instance_id": node_instance_id})

        # 如果所属阶段还未开始，自动开始阶段
        stage = node.stage_instance
        if stage.status == StageStatusEnum.PENDING.value:
            self.start_stage(stage.id)

        self.db.flush()
        return node

    def complete_node(
        self,
        node_instance_id: int,
        completed_by: Optional[int] = None,
        actual_date: Optional[date] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        approval_record_id: Optional[int] = None,
        remark: Optional[str] = None,
    ) -> ProjectNodeInstance:
        """
        完成节点

        Args:
            node_instance_id: 节点实例ID
            completed_by: 完成人ID
            actual_date: 实际完成日期
            attachments: 附件列表
            approval_record_id: 审批记录ID（审批类节点）
            remark: 备注

        Returns:
            ProjectNodeInstance: 更新后的节点实例
        """
        node = self.db.query(ProjectNodeInstance).filter(
            ProjectNodeInstance.id == node_instance_id
        ).first()

        if not node:
            raise ValueError(f"节点实例 {node_instance_id} 不存在")

        if node.status not in [StageStatusEnum.PENDING.value, StageStatusEnum.IN_PROGRESS.value]:
            raise ValueError(f"节点当前状态为 {node.status}，无法完成")

        # 验证完成条件
        self._validate_node_completion(node, attachments, approval_record_id)

        node.status = StageStatusEnum.COMPLETED.value
        node.completed_by = completed_by
        node.completed_at = datetime.now()
        node.actual_date = actual_date or date.today()

        if attachments:
            node.attachments = attachments
        if approval_record_id:
            node.approval_record_id = approval_record_id
        if remark:
            node.remark = remark

        # 检查是否可以自动完成下一个节点
        self._try_auto_complete_next_nodes(node)

        # 检查阶段是否可以自动完成
        self._check_stage_completion(node.stage_instance_id)

        self.db.flush()
        return node

    def skip_node(
        self,
        node_instance_id: int,
        reason: Optional[str] = None,
    ) -> ProjectNodeInstance:
        """跳过节点"""
        node = self.db.query(ProjectNodeInstance).filter(
            ProjectNodeInstance.id == node_instance_id
        ).first()

        if not node:
            raise ValueError(f"节点实例 {node_instance_id} 不存在")

        if node.status not in [StageStatusEnum.PENDING.value, StageStatusEnum.IN_PROGRESS.value]:
            raise ValueError(f"节点当前状态为 {node.status}，无法跳过")

        node.status = StageStatusEnum.SKIPPED.value
        node.remark = reason or node.remark

        self.db.flush()
        return node
