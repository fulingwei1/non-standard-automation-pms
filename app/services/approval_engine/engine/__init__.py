# -*- coding: utf-8 -*-
"""
审批引擎服务统一导出

通过多重继承组合所有功能模块
"""

from sqlalchemy.orm import Session

from .actions import ApprovalActionsMixin
from .approve import ApprovalProcessMixin
from .core import ApprovalEngineCore
from .query import ApprovalQueryMixin
from .submit import ApprovalSubmitMixin


class ApprovalEngineService(
    ApprovalEngineCore,
    ApprovalSubmitMixin,
    ApprovalProcessMixin,
    ApprovalActionsMixin,
    ApprovalQueryMixin,
):
    """审批引擎核心服务（组合所有功能模块）"""

    def __init__(self, db: Session):
        ApprovalEngineCore.__init__(self, db)


__all__ = ["ApprovalEngineService"]
