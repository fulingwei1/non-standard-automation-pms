# -*- coding: utf-8 -*-
"""
ECN 状态枚举
定义 ECN 的所有可能状态及其流转规则
"""

from enum import Enum


class EcnStatus(str, Enum):
    """ECN 状态枚举"""

    # === 草稿状态 ===
    DRAFT = "DRAFT"  # 草稿

    # === 待提交状态 ===
    READY_TO_SUBMIT = "READY_TO_SUBMIT"  # 准备提交

    # === 审批流程状态 ===
    SUBMITTED = "SUBMITTED"  # 已提交（待审批）
    EVALUATION_PENDING = "EVALUATION_PENDING"  # 评估待处理
    EVALUATION_IN_PROGRESS = "EVALUATION_IN_PROGRESS"  # 评估进行中
    APPROVAL_PENDING = "APPROVAL_PENDING"  # 待审批（评估完成后）

    # === 审批结果 ===
    APPROVED = "APPROVED"  # 已批准
    REJECTED = "REJECTED"  # 已拒绝

    # === 执行状态 ===
    READY_TO_EXECUTE = "READY_TO_EXECUTE"  # 准备执行
    IN_PROGRESS = "IN_PROGRESS"  # 执行中
    EXECUTION_PAUSED = "EXECUTION_PAUSED"  # 执行暂停
    EXECUTION_COMPLETED = "EXECUTION_COMPLETED"  # 执行完成

    # === 完成状态 ===
    READY_TO_CLOSE = "READY_TO_CLOSE"  # 准备关闭
    CLOSED = "CLOSED"  # 已关闭

    # === 终止状态 ===
    CANCELLED = "CANCELLED"  # 已取消

    # === 获取状态描述 ===
    def description(self) -> str:
        """获取状态描述"""
        descriptions = {
            "DRAFT": "草稿",
            "READY_TO_SUBMIT": "准备提交",
            "SUBMITTED": "已提交",
            "EVALUATION_PENDING": "待评估",
            "EVALUATION_IN_PROGRESS": "评估中",
            "APPROVAL_PENDING": "待审批",
            "APPROVED": "已批准",
            "REJECTED": "已拒绝",
            "READY_TO_EXECUTE": "准备执行",
            "IN_PROGRESS": "执行中",
            "EXECUTION_PAUSED": "执行暂停",
            "EXECUTION_COMPLETED": "执行完成",
            "READY_TO_CLOSE": "准备关闭",
            "CLOSED": "已关闭",
            "CANCELLED": "已取消",
        }
        return descriptions.get(self.value, "未知状态")

    # === 获取显示名称 ===
    def display_name(self) -> str:
        """获取显示名称（中英文对照）"""
        display_names = {
            "DRAFT": "草稿",
            "READY_TO_SUBMIT": "准备提交",
            "SUBMITTED": "已提交",
            "EVALUATION_PENDING": "待评估",
            "EVALUATION_IN_PROGRESS": "评估中",
            "APPROVAL_PENDING": "待审批",
            "APPROVED": "已批准",
            "REJECTED": "已拒绝",
            "READY_TO_EXECUTE": "准备执行",
            "IN_PROGRESS": "执行中",
            "EXECUTION_PAUSED": "执行暂停",
            "EXECUTION_COMPLETED": "执行完成",
            "READY_TO_CLOSE": "准备关闭",
            "CLOSED": "已关闭",
            "CANCELLED": "已取消",
        }
        return display_names.get(self.value, "未知状态")

    # === 状态分组 ===
    @property
    def category(self) -> str:
        """获取状态所属类别"""
        categories = {
            "DRAFT": "draft",  # 草稿
            "READY_TO_SUBMIT": "draft",
            "SUBMITTED": "submitted",
            "EVALUATION_PENDING": "approval",
            "EVALUATION_IN_PROGRESS": "approval",
            "APPROVAL_PENDING": "approval",
            "APPROVED": "execution",
            "REJECTED": "terminated",
            "READY_TO_EXECUTE": "execution",
            "IN_PROGRESS": "execution",
            "EXECUTION_PAUSED": "execution",
            "EXECUTION_COMPLETED": "execution",
            "READY_TO_CLOSE": "closed",
            "CLOSED": "closed",
            "CANCELLED": "terminated",
        }
        return categories.get(self.value, "draft")

    # === 是否可编辑 ===
    @property
    def is_editable(self) -> bool:
        """状态是否可编辑"""
        editable_statuses = ["DRAFT", "READY_TO_SUBMIT"]
        return self.value in editable_statuses

    # === 是否可提交 ===
    @property
    def is_submittable(self) -> bool:
        """状态是否可提交审批"""
        submittable_statuses = ["READY_TO_SUBMIT"]
        return self.value in submittable_statuses

    # === 是否可撤销提交 ===
    @property
    def is_withdrawable(self) -> bool:
        """状态是否可撤销提交（在审批通过前）"""
        withdrawable_statuses = ["SUBMITTED", "EVALUATION_PENDING", "APPROVAL_PENDING"]
        return self.value in withdrawable_statuses

    # === 是否可取消 ===
    @property
    def is_cancellable(self) -> bool:
        """状态是否可取消"""
        cancellable_statuses = [
            "DRAFT",
            "SUBMITTED",
            "EVALUATION_PENDING",
            "APPROVAL_PENDING",
            "IN_PROGRESS",
            "EXECUTION_PAUSED",
        ]
        return self.value in cancellable_statuses
