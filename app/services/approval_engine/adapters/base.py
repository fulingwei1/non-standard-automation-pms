# -*- coding: utf-8 -*-
"""
审批适配器基类

定义业务实体接入审批系统的标准接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.approval import (
    ApprovalInstance,
    ApprovalNodeDefinition,
)


class ApprovalAdapter(ABC):
    """
    审批适配器基类

    每个业务模块需要实现自己的适配器，用于：
    1. 提供业务实体数据供审批条件判断
    2. 在审批状态变更时更新业务实体状态
    3. 动态解析审批人
    4. 生成审批摘要信息
    """

    # 适配器标识
    entity_type: str = ""

    def __init__(self, db: Session):
        self.db = db

    @abstractmethod
    def get_entity(self, entity_id: int) -> Any:
        """
        获取业务实体

        Args:
            entity_id: 业务实体ID

        Returns:
            业务实体对象
        """
        pass

    @abstractmethod
    def get_entity_data(self, entity_id: int) -> Dict[str, Any]:
        """
        获取业务实体数据（用于条件路由）

        Args:
            entity_id: 业务实体ID

        Returns:
            实体数据字典，用于审批条件判断
        """
        pass

    @abstractmethod
    def on_submit(self, entity_id: int, instance: ApprovalInstance):
        """
        审批提交时的回调

        Args:
            entity_id: 业务实体ID
            instance: 审批实例
        """
        pass

    @abstractmethod
    def on_approved(self, entity_id: int, instance: ApprovalInstance):
        """
        审批通过时的回调

        Args:
            entity_id: 业务实体ID
            instance: 审批实例
        """
        pass

    @abstractmethod
    def on_rejected(self, entity_id: int, instance: ApprovalInstance):
        """
        审批驳回时的回调

        Args:
            entity_id: 业务实体ID
            instance: 审批实例
        """
        pass

    def on_withdrawn(self, entity_id: int, instance: ApprovalInstance):
        """
        审批撤回时的回调

        Args:
            entity_id: 业务实体ID
            instance: 审批实例
        """
        pass

    def on_terminated(self, entity_id: int, instance: ApprovalInstance):
        """
        审批终止时的回调

        Args:
            entity_id: 业务实体ID
            instance: 审批实例
        """
        pass

    def resolve_approvers(
        self,
        node: ApprovalNodeDefinition,
        context: Dict[str, Any],
    ) -> List[int]:
        """
        动态解析审批人（可选实现）

        当节点的 approver_type 为 DYNAMIC 时调用

        Args:
            node: 节点定义
            context: 上下文数据

        Returns:
            审批人ID列表
        """
        return []

    def generate_title(self, entity_id: int) -> str:
        """
        生成审批标题

        Args:
            entity_id: 业务实体ID

        Returns:
            审批标题
        """
        return f"{self.entity_type}审批 - {entity_id}"

    def generate_summary(self, entity_id: int) -> str:
        """
        生成审批摘要

        Args:
            entity_id: 业务实体ID

        Returns:
            审批摘要
        """
        return ""

    def get_form_data(self, entity_id: int) -> Dict[str, Any]:
        """
        获取表单数据

        可以将业务实体数据转换为表单数据

        Args:
            entity_id: 业务实体ID

        Returns:
            表单数据
        """
        return self.get_entity_data(entity_id)

    def validate_submit(self, entity_id: int) -> tuple[bool, Optional[str]]:
        """
        验证是否可以提交审批

        Args:
            entity_id: 业务实体ID

        Returns:
            (是否可以提交, 错误信息)
        """
        return True, None

    def get_cc_user_ids(self, entity_id: int) -> List[int]:
        """
        获取默认抄送人列表

        Args:
            entity_id: 业务实体ID

        Returns:
            抄送人ID列表
        """
        return []
