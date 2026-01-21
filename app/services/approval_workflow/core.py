# -*- coding: utf-8 -*-
"""
审批工作流服务 - 核心类
"""

from sqlalchemy.orm import Session


class ApprovalWorkflowCore:
    """审批工作流服务核心类"""

    def __init__(self, db: Session):
        self.db = db
