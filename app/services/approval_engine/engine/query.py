# -*- coding: utf-8 -*-
"""
审批查询功能
"""

from datetime import datetime
from typing import Any, Dict, Optional

from app.common.pagination import get_pagination_params
from app.common.query_filters import apply_pagination
from app.models.approval import ApprovalCarbonCopy, ApprovalInstance, ApprovalTask

from .core import ApprovalEngineCore


class ApprovalQueryMixin:
    """审批查询功能混入类

    可独立实例化使用（传入 core 对象），也可作为 mixin 与 ApprovalEngineCore 混合使用。
    """

    def __init__(self, core: ApprovalEngineCore):
        """初始化查询混入类

        Args:
            core: 审批引擎核心实例，提供 db 会话和内部方法
        """
        self.db = core.db
        self._core = core
        # 代理核心类的内部方法，确保独立实例化时 _log_action 等方法可用
        self._log_action = core._log_action

    def get_pending_tasks(
        self: ApprovalEngineCore,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取用户待审批的任务"""
        query = (
            self.db.query(ApprovalTask)
            .filter(
                ApprovalTask.assignee_id == user_id,
                ApprovalTask.status == "PENDING",
            )
            .order_by(ApprovalTask.created_at.desc())
        )

        pagination = get_pagination_params(page=page, page_size=page_size)
        total = query.count()
        query = apply_pagination(query, pagination.offset, pagination.limit)
        tasks = query.all()

        return {
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "items": tasks,
        }

    def get_initiated_instances(
        self: ApprovalEngineCore,
        user_id: int,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取用户发起的审批"""
        query = self.db.query(ApprovalInstance).filter(
            ApprovalInstance.initiator_id == user_id,
        )

        if status:
            query = query.filter(ApprovalInstance.status == status)

        query = query.order_by(ApprovalInstance.created_at.desc())

        pagination = get_pagination_params(page=page, page_size=page_size)
        total = query.count()
        query = apply_pagination(query, pagination.offset, pagination.limit)
        instances = query.all()

        return {
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "items": instances,
        }

    def get_cc_records(
        self: ApprovalEngineCore,
        user_id: int,
        is_read: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """获取抄送给用户的记录"""
        query = self.db.query(ApprovalCarbonCopy).filter(
            ApprovalCarbonCopy.cc_user_id == user_id,
        )

        if is_read is not None:
            query = query.filter(ApprovalCarbonCopy.is_read == is_read)

        query = query.order_by(ApprovalCarbonCopy.created_at.desc())

        pagination = get_pagination_params(page=page, page_size=page_size)
        total = query.count()
        query = apply_pagination(query, pagination.offset, pagination.limit)
        records = query.all()

        return {
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "items": records,
        }

    def mark_cc_as_read(self: ApprovalEngineCore, cc_id: int, user_id: int) -> bool:
        """标记抄送为已读"""
        cc = (
            self.db.query(ApprovalCarbonCopy)
            .filter(
                ApprovalCarbonCopy.id == cc_id,
                ApprovalCarbonCopy.cc_user_id == user_id,
            )
            .first()
        )

        if cc:
            cc.is_read = True
            cc.read_at = datetime.now()

            self._log_action(
                instance_id=cc.instance_id,
                operator_id=user_id,
                action="READ_CC",
            )

            self.db.commit()
            return True

        return False
