# -*- coding: utf-8 -*-
"""
辅助方法模块
提供节点依赖检查、完成条件验证等辅助功能
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_

from app.models.enums import CompletionMethodEnum, StageStatusEnum
from app.models.stage_instance import ProjectNodeInstance


class HelpersMixin:
    """辅助方法功能混入类"""

    def _check_node_dependencies(self, node: ProjectNodeInstance) -> bool:
        """检查节点依赖是否满足"""
        if not node.dependency_node_instance_ids:
            return True

        # 检查所有依赖节点是否已完成
        incomplete = self.db.query(ProjectNodeInstance).filter(
            and_(
                ProjectNodeInstance.id.in_(node.dependency_node_instance_ids),
                ProjectNodeInstance.status.notin_([
                    StageStatusEnum.COMPLETED.value,
                    StageStatusEnum.SKIPPED.value
                ])
            )
        ).count()

        return incomplete == 0

    def _validate_node_completion(
        self,
        node: ProjectNodeInstance,
        attachments: Optional[List[Dict[str, Any]]],
        approval_record_id: Optional[int],
    ) -> None:
        """验证节点完成条件"""
        # 检查依赖
        if not self._check_node_dependencies(node):
            raise ValueError("前置依赖节点未完成")

        # 检查附件要求
        node_def = node.node_definition
        if node_def and node_def.required_attachments:
            if not attachments and not node.attachments:
                raise ValueError("该节点要求上传附件")

        # 检查审批要求
        if node.completion_method == CompletionMethodEnum.APPROVAL.value:
            if not approval_record_id:
                raise ValueError("审批类节点需要关联审批记录")

    def _try_auto_complete_next_nodes(self, completed_node: ProjectNodeInstance) -> None:
        """尝试自动完成依赖于当前节点的自动节点"""
        # 查找依赖于当前节点的自动完成节点
        dependent_nodes = self.db.query(ProjectNodeInstance).filter(
            and_(
                ProjectNodeInstance.stage_instance_id == completed_node.stage_instance_id,
                ProjectNodeInstance.completion_method == CompletionMethodEnum.AUTO.value,
                ProjectNodeInstance.status == StageStatusEnum.PENDING.value
            )
        ).all()

        for node in dependent_nodes:
            if node.dependency_node_instance_ids and completed_node.id in node.dependency_node_instance_ids:
                if self._check_node_dependencies(node):
                    # 检查自动完成条件
                    if self._check_auto_condition(node):
                        node.status = StageStatusEnum.COMPLETED.value
                        node.completed_at = datetime.now()
                        node.actual_date = date.today()

    def _check_auto_condition(self, node: ProjectNodeInstance) -> bool:
        """检查自动完成条件"""
        node_def = node.node_definition
        if not node_def or not node_def.auto_condition:
            # 无条件配置，依赖满足即可完成
            return True

        # TODO: 实现自动条件检查逻辑
        # auto_condition 可能包含：
        # - "all_dependencies": 所有依赖完成即完成
        # - "percentage": 依赖完成百分比达到阈值
        # - "custom": 自定义条件
        return True

    def _check_stage_completion(self, stage_instance_id: int) -> None:
        """检查阶段是否可以自动完成"""
        # 检查所有必需节点是否完成
        incomplete = self.db.query(ProjectNodeInstance).filter(
            and_(
                ProjectNodeInstance.stage_instance_id == stage_instance_id,
                ProjectNodeInstance.is_required == True,
                ProjectNodeInstance.status.notin_([
                    StageStatusEnum.COMPLETED.value,
                    StageStatusEnum.SKIPPED.value
                ])
            )
        ).count()

        # 如果所有必需节点完成，可以提示用户完成阶段（但不自动完成）
        # 自动完成阶段可能不符合业务需求，保留手动确认
        pass
