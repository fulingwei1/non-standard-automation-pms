# -*- coding: utf-8 -*-
"""
报价审批服务

处理报价审批相关的业务逻辑，包括提交审批、审批操作、查询状态等。
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance, ApprovalTask
from app.models.sales.quotes import Quote, QuoteVersion
from app.services.approval_engine import ApprovalEngineService

logger = logging.getLogger(__name__)


class QuoteApprovalService:
    """报价审批服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.approval_engine = ApprovalEngineService(db)

    def submit_quotes_for_approval(
        self,
        quote_ids: List[int],
        initiator_id: int,
        version_ids: Optional[List[int]] = None,
        urgency: str = "NORMAL",
        comment: Optional[str] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        批量提交报价审批

        Args:
            quote_ids: 报价ID列表
            initiator_id: 发起人ID
            version_ids: 版本ID列表（可选）
            urgency: 紧急程度
            comment: 提交备注

        Returns:
            包含成功和失败记录的字典
        """
        results = []
        errors = []

        for i, quote_id in enumerate(quote_ids):
            quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
            if not quote:
                errors.append({"quote_id": quote_id, "error": "报价不存在"})
                continue

            # 验证状态
            if quote.status not in ["DRAFT", "REJECTED"]:
                errors.append(
                    {
                        "quote_id": quote_id,
                        "error": f"当前状态 '{quote.status}' 不允许提交审批",
                    }
                )
                continue

            # 获取版本信息
            version = self._get_quote_version(quote, version_ids, i)
            if not version:
                errors.append({"quote_id": quote_id, "error": "报价没有版本，无法提交审批"})
                continue

            try:
                # 构建表单数据
                form_data = self._build_form_data(quote, version)

                # 提交审批
                instance = self.approval_engine.submit(
                    template_code="SALES_QUOTE_APPROVAL",
                    entity_type="QUOTE",
                    entity_id=quote_id,
                    form_data=form_data,
                    initiator_id=initiator_id,
                    urgency=urgency,
                )

                results.append(
                    {
                        "quote_id": quote_id,
                        "quote_code": quote.quote_code,
                        "version_no": version.version_no,
                        "instance_id": instance.id,
                        "status": "submitted",
                    }
                )
            except Exception as e:
                logger.exception(f"报价 {quote_id} 提交审批失败")
                errors.append({"quote_id": quote_id, "error": str(e)})

        return {"success": results, "errors": errors}

    def get_pending_tasks(
        self,
        user_id: int,
        customer_id: Optional[int] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        获取待审批的报价列表

        Args:
            user_id: 用户ID
            customer_id: 客户ID筛选（可选）
            offset: 分页偏移
            limit: 每页数量

        Returns:
            包含任务列表和总数的字典
        """
        tasks = self.approval_engine.get_pending_tasks(
            user_id=user_id, entity_type="QUOTE"
        )

        # 客户筛选
        if customer_id:
            filtered_tasks = []
            for task in tasks:
                quote = (
                    self.db.query(Quote)
                    .filter(Quote.id == task.instance.entity_id)
                    .first()
                )
                if quote and quote.customer_id == customer_id:
                    filtered_tasks.append(task)
            tasks = filtered_tasks

        total = len(tasks)
        paginated_tasks = tasks[offset : offset + limit]

        items = []
        for task in paginated_tasks:
            instance = task.instance
            quote = self.db.query(Quote).filter(Quote.id == instance.entity_id).first()

            # 获取版本信息
            version = self._get_current_version(quote)

            items.append(
                {
                    "task_id": task.id,
                    "instance_id": instance.id,
                    "quote_id": instance.entity_id,
                    "quote_code": quote.quote_code if quote else None,
                    "customer_name": quote.customer.name
                    if quote and quote.customer
                    else None,
                    "version_no": version.version_no if version else None,
                    "total_price": float(version.total_price)
                    if version and version.total_price
                    else 0,
                    "gross_margin": float(version.gross_margin)
                    if version and version.gross_margin
                    else 0,
                    "lead_time_days": version.lead_time_days if version else None,
                    "initiator_name": instance.initiator.real_name
                    if instance.initiator
                    else None,
                    "submitted_at": instance.created_at.isoformat()
                    if instance.created_at
                    else None,
                    "urgency": instance.urgency,
                    "node_name": task.node.node_name if task.node else None,
                }
            )

        return {"items": items, "total": total}

    def perform_action(
        self,
        task_id: int,
        action: str,
        approver_id: int,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        执行审批操作

        Args:
            task_id: 审批任务ID
            action: 操作类型 (approve/reject)
            approver_id: 审批人ID
            comment: 审批意见

        Returns:
            操作结果

        Raises:
            ValueError: 不支持的操作类型
        """
        if action == "approve":
            result = self.approval_engine.approve(
                task_id=task_id,
                approver_id=approver_id,
                comment=comment,
            )
        elif action == "reject":
            result = self.approval_engine.reject(
                task_id=task_id,
                approver_id=approver_id,
                comment=comment,
            )
        else:
            raise ValueError(f"不支持的操作类型: {action}")

        return {
            "task_id": task_id,
            "action": action,
            "instance_status": result.status if hasattr(result, "status") else None,
        }

    def perform_batch_actions(
        self,
        task_ids: List[int],
        action: str,
        approver_id: int,
        comment: Optional[str] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        批量执行审批操作

        Args:
            task_ids: 审批任务ID列表
            action: 操作类型 (approve/reject)
            approver_id: 审批人ID
            comment: 审批意见

        Returns:
            包含成功和失败记录的字典
        """
        results = []
        errors = []

        for task_id in task_ids:
            try:
                if action == "approve":
                    self.approval_engine.approve(
                        task_id=task_id,
                        approver_id=approver_id,
                        comment=comment,
                    )
                elif action == "reject":
                    self.approval_engine.reject(
                        task_id=task_id,
                        approver_id=approver_id,
                        comment=comment,
                    )
                else:
                    errors.append(
                        {"task_id": task_id, "error": f"不支持的操作: {action}"}
                    )
                    continue

                results.append({"task_id": task_id, "status": "success"})
            except Exception as e:
                errors.append({"task_id": task_id, "error": str(e)})

        return {"success": results, "errors": errors}

    def get_quote_approval_status(self, quote_id: int) -> Optional[Dict[str, Any]]:
        """
        查询报价审批状态

        Args:
            quote_id: 报价ID

        Returns:
            审批状态信息，如果报价不存在则返回 None
        """
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            return None

        instance = (
            self.db.query(ApprovalInstance)
            .filter(
                ApprovalInstance.entity_type == "QUOTE",
                ApprovalInstance.entity_id == quote_id,
            )
            .order_by(ApprovalInstance.created_at.desc())
            .first()
        )

        if not instance:
            return {
                "quote_id": quote_id,
                "quote_code": quote.quote_code,
                "status": quote.status,
                "approval_instance": None,
            }

        # 获取任务历史
        tasks = (
            self.db.query(ApprovalTask)
            .filter(ApprovalTask.instance_id == instance.id)
            .order_by(ApprovalTask.created_at)
            .all()
        )

        task_history = []
        for task in tasks:
            task_history.append(
                {
                    "task_id": task.id,
                    "node_name": task.node.node_name if task.node else None,
                    "assignee_name": task.assignee.real_name
                    if task.assignee
                    else None,
                    "status": task.status,
                    "action": task.action,
                    "comment": task.comment,
                    "completed_at": task.completed_at.isoformat()
                    if task.completed_at
                    else None,
                }
            )

        # 获取版本信息
        version = quote.current_version
        version_info = None
        if version:
            version_info = {
                "version_no": version.version_no,
                "total_price": float(version.total_price)
                if version.total_price
                else 0,
                "gross_margin": float(version.gross_margin)
                if version.gross_margin
                else 0,
            }

        return {
            "quote_id": quote_id,
            "quote_code": quote.quote_code,
            "customer_name": quote.customer.name if quote.customer else None,
            "quote_status": quote.status,
            "version_info": version_info,
            "instance_id": instance.id,
            "instance_status": instance.status,
            "urgency": instance.urgency,
            "submitted_at": instance.created_at.isoformat()
            if instance.created_at
            else None,
            "completed_at": instance.completed_at.isoformat()
            if instance.completed_at
            else None,
            "task_history": task_history,
        }

    def withdraw_approval(
        self, quote_id: int, user_id: int, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        撤回审批

        Args:
            quote_id: 报价ID
            user_id: 用户ID
            reason: 撤回原因

        Returns:
            撤回结果

        Raises:
            ValueError: 报价不存在、没有进行中的审批或权限不足
        """
        quote = self.db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise ValueError("报价不存在")

        instance = (
            self.db.query(ApprovalInstance)
            .filter(
                ApprovalInstance.entity_type == "QUOTE",
                ApprovalInstance.entity_id == quote_id,
                ApprovalInstance.status == "PENDING",
            )
            .first()
        )

        if not instance:
            raise ValueError("没有进行中的审批流程可撤回")

        if instance.initiator_id != user_id:
            raise ValueError("只能撤回自己提交的审批")

        self.approval_engine.withdraw(instance_id=instance.id, user_id=user_id)

        return {
            "quote_id": quote_id,
            "quote_code": quote.quote_code,
            "status": "withdrawn",
        }

    def get_approval_history(
        self,
        user_id: int,
        status_filter: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        获取审批历史

        Args:
            user_id: 用户ID
            status_filter: 状态筛选 (APPROVED/REJECTED)
            offset: 分页偏移
            limit: 每页数量

        Returns:
            包含审批历史列表和总数的字典
        """
        query = (
            self.db.query(ApprovalTask)
            .join(ApprovalInstance)
            .filter(
                ApprovalTask.assignee_id == user_id,
                ApprovalInstance.entity_type == "QUOTE",
                ApprovalTask.status.in_(["APPROVED", "REJECTED"]),
            )
        )

        if status_filter:
            query = query.filter(ApprovalTask.status == status_filter)

        total = query.count()
        tasks = (
            query.order_by(ApprovalTask.completed_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        items = []
        for task in tasks:
            instance = task.instance
            quote = self.db.query(Quote).filter(Quote.id == instance.entity_id).first()

            items.append(
                {
                    "task_id": task.id,
                    "quote_id": instance.entity_id,
                    "quote_code": quote.quote_code if quote else None,
                    "customer_name": quote.customer.name
                    if quote and quote.customer
                    else None,
                    "action": task.action,
                    "status": task.status,
                    "comment": task.comment,
                    "completed_at": task.completed_at.isoformat()
                    if task.completed_at
                    else None,
                }
            )

        return {"items": items, "total": total}

    # ==================== 私有辅助方法 ====================

    def _get_quote_version(
        self, quote: Quote, version_ids: Optional[List[int]], index: int
    ) -> Optional[QuoteVersion]:
        """获取报价版本"""
        version = None

        # 尝试从指定的版本ID列表获取
        if version_ids and index < len(version_ids):
            version = (
                self.db.query(QuoteVersion)
                .filter(
                    QuoteVersion.id == version_ids[index],
                    QuoteVersion.quote_id == quote.id,
                )
                .first()
            )

        # 如果没有找到，尝试获取当前版本
        if not version:
            version = quote.current_version

        # 如果还是没有，获取最新版本
        if not version:
            version = (
                self.db.query(QuoteVersion)
                .filter(QuoteVersion.quote_id == quote.id)
                .order_by(QuoteVersion.id.desc())
                .first()
            )

        return version

    def _get_current_version(self, quote: Optional[Quote]) -> Optional[QuoteVersion]:
        """获取报价当前版本"""
        if not quote:
            return None

        version = quote.current_version
        if not version:
            version = (
                self.db.query(QuoteVersion)
                .filter(QuoteVersion.quote_id == quote.id)
                .order_by(QuoteVersion.id.desc())
                .first()
            )
        return version

    def _build_form_data(self, quote: Quote, version: QuoteVersion) -> Dict[str, Any]:
        """构建审批表单数据"""
        return {
            "quote_id": quote.id,
            "quote_code": quote.quote_code,
            "version_id": version.id,
            "version_no": version.version_no,
            "total_price": float(version.total_price) if version.total_price else 0,
            "cost_total": float(version.cost_total) if version.cost_total else 0,
            "gross_margin": float(version.gross_margin) if version.gross_margin else 0,
            "customer_id": quote.customer_id,
            "customer_name": quote.customer.name if quote.customer else None,
            "lead_time_days": version.lead_time_days,
        }
