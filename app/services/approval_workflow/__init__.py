# -*- coding: utf-8 -*-
"""
审批工作流服务统一导出

通过多重继承组合所有功能模块
"""

from sqlalchemy.orm import Session

from .approval_actions import ApprovalActionsMixin
from .core import ApprovalWorkflowCore
from .helpers import ApprovalHelpersMixin
from .queries import ApprovalQueriesMixin
from .workflow_start import WorkflowStartMixin


class ApprovalWorkflowService(
    ApprovalWorkflowCore,
    WorkflowStartMixin,
    ApprovalActionsMixin,
    ApprovalQueriesMixin,
    ApprovalHelpersMixin,
):
    """审批工作流服务（组合所有功能模块）"""

    def __init__(self, db: Session):
        ApprovalWorkflowCore.__init__(self, db)


__all__ = ["ApprovalWorkflowService"]
