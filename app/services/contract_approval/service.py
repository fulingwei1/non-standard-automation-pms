# -*- coding: utf-8 -*-
"""
合同审批服务层

封装合同审批相关的业务逻辑，包括：
- 提交审批
- 查询待审批列表
- 执行审批操作
- 批量审批
- 查询审批状态
- 撤回审批
- 审批历史查询
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.sales.contracts import Contract
from app.models.approval import ApprovalInstance, ApprovalTask
from app.services.approval_engine import ApprovalEngineService

logger = logging.getLogger(__name__)


class ContractApprovalService:
    """合同审批服务"""

    def __init__(self, db: Session):
        self.db = db
        self.engine = ApprovalEngineService(db)

    def submit_contracts_for_approval(
        self,
        contract_ids: List[int],
        initiator_id: int,
        urgency: str = "NORMAL",
        comment: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        批量提交合同审批

        Args:
            contract_ids: 合同ID列表
            initiator_id: 提交人ID
            urgency: 紧急程度
            comment: 提交备注

        Returns:
            (成功列表, 失败列表)
        """
        results = []
        errors = []

        for contract_id in contract_ids:
            contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
            if not contract:
                errors.append({"contract_id": contract_id, "error": "合同不存在"})
                continue

            # 验证状态：只有草稿或被驳回的合同可以提交审批
            if contract.status not in ["DRAFT", "REJECTED"]:
                errors.append(
                    {
                        "contract_id": contract_id,
                        "error": f"当前状态 '{contract.status}' 不允许提交审批",
                    }
                )
                continue

            # 验证合同金额
            if not contract.contract_amount or contract.contract_amount <= 0:
                errors.append(
                    {"contract_id": contract_id, "error": "合同金额必须大于0"}
                )
                continue

            try:
                # 构建表单数据
                form_data = self._build_contract_form_data(contract)

                instance = self.engine.submit(
                    template_code="SALES_CONTRACT_APPROVAL",
                    entity_type="CONTRACT",
                    entity_id=contract_id,
                    form_data=form_data,
                    initiator_id=initiator_id,
                    urgency=urgency,
                )

                results.append(
                    {
                        "contract_id": contract_id,
                        "contract_code": contract.contract_code,
                        "contract_amount": float(contract.contract_amount) if contract.contract_amount else 0,
                        "instance_id": instance.id,
                        "status": "submitted",
                    }
                )
            except Exception as e:
                logger.exception(f"合同 {contract_id} 提交审批失败")
                errors.append({"contract_id": contract_id, "error": str(e)})

        return results, errors

    def _build_contract_form_data(self, contract: Contract) -> Dict[str, Any]:
        """构建合同表单数据"""
        return {
            "contract_id": contract.id,
            "contract_code": contract.contract_code,
            "customer_contract_no": contract.customer_contract_no,
            "contract_amount": float(contract.contract_amount) if contract.contract_amount else 0,
            "customer_id": contract.customer_id,
            "customer_name": contract.customer.name if contract.customer else None,
            "project_id": contract.project_id,
            "signed_date": contract.signing_date.isoformat() if contract.signing_date else None,
            "payment_terms_summary": contract.payment_terms_summary,
            "acceptance_summary": contract.acceptance_summary,
        }

    def get_pending_tasks(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        customer_id: Optional[int] = None,
        min_amount: Optional[float] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取用户待审批的合同任务

        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页大小
            customer_id: 客户ID筛选
            min_amount: 最小金额筛选

        Returns:
            (任务列表, 总数)
        """
        tasks = self.engine.get_pending_tasks(user_id=user_id, entity_type="CONTRACT")

        # 筛选
        filtered_tasks = []
        for task in tasks:
            contract = (
                self.db.query(Contract)
                .filter(Contract.id == task.instance.entity_id)
                .first()
            )
            if not contract:
                continue
            if customer_id and contract.customer_id != customer_id:
                continue
            if min_amount and (not contract.contract_amount or float(contract.contract_amount) < min_amount):
                continue
            filtered_tasks.append(task)

        total = len(filtered_tasks)
        offset = (page - 1) * page_size
        paginated_tasks = filtered_tasks[offset : offset + page_size]

        items = []
        for task in paginated_tasks:
            instance = task.instance
            contract = (
                self.db.query(Contract).filter(Contract.id == instance.entity_id).first()
            )

            items.append(
                {
                    "task_id": task.id,
                    "instance_id": instance.id,
                    "contract_id": instance.entity_id,
                    "contract_code": contract.contract_code if contract else None,
                    "customer_contract_no": contract.customer_contract_no if contract else None,
                    "customer_name": contract.customer.name if contract and contract.customer else None,
                    "contract_amount": float(contract.contract_amount) if contract and contract.contract_amount else 0,
                    "project_name": contract.project.project_name if contract and contract.project else None,
                    "initiator_name": instance.initiator.real_name if instance.initiator else None,
                    "submitted_at": instance.created_at.isoformat() if instance.created_at else None,
                    "urgency": instance.urgency,
                    "node_name": task.node.node_name if task.node else None,
                }
            )

        return items, total

    def approve_task(
        self,
        task_id: int,
        approver_id: int,
        comment: Optional[str] = None,
    ) -> Any:
        """
        审批通过

        Args:
            task_id: 任务ID
            approver_id: 审批人ID
            comment: 审批意见

        Returns:
            审批结果
        """
        return self.engine.approve(
            task_id=task_id,
            approver_id=approver_id,
            comment=comment,
        )

    def reject_task(
        self,
        task_id: int,
        approver_id: int,
        comment: Optional[str] = None,
    ) -> Any:
        """
        审批驳回

        Args:
            task_id: 任务ID
            approver_id: 审批人ID
            comment: 审批意见

        Returns:
            审批结果
        """
        return self.engine.reject(
            task_id=task_id,
            approver_id=approver_id,
            comment=comment,
        )

    def batch_approve_or_reject(
        self,
        task_ids: List[int],
        approver_id: int,
        action: str,
        comment: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        批量审批操作

        Args:
            task_ids: 任务ID列表
            approver_id: 审批人ID
            action: 操作类型 (approve/reject)
            comment: 审批意见

        Returns:
            (成功列表, 失败列表)
        """
        results = []
        errors = []

        for task_id in task_ids:
            try:
                if action == "approve":
                    self.engine.approve(
                        task_id=task_id,
                        approver_id=approver_id,
                        comment=comment,
                    )
                elif action == "reject":
                    self.engine.reject(
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

        return results, errors

    def get_contract_approval_status(
        self, contract_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        查询合同审批状态

        Args:
            contract_id: 合同ID

        Returns:
            审批状态信息，如果没有审批记录则返回 None
        """
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError("合同不存在")

        instance = (
            self.db.query(ApprovalInstance)
            .filter(
                ApprovalInstance.entity_type == "CONTRACT",
                ApprovalInstance.entity_id == contract_id,
            )
            .order_by(ApprovalInstance.created_at.desc())
            .first()
        )

        if not instance:
            return None

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
                    "assignee_name": task.assignee.real_name if task.assignee else None,
                    "status": task.status,
                    "action": task.action,
                    "comment": task.comment,
                    "completed_at": task.completed_at.isoformat()
                    if task.completed_at
                    else None,
                }
            )

        return {
            "contract_id": contract_id,
            "contract_code": contract.contract_code,
            "customer_contract_no": contract.customer_contract_no,
            "customer_name": contract.customer.name if contract.customer else None,
            "contract_amount": float(contract.contract_amount) if contract.contract_amount else 0,
            "contract_status": contract.status,
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
        self, contract_id: int, user_id: int, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        撤回审批

        Args:
            contract_id: 合同ID
            user_id: 撤回人ID
            reason: 撤回原因

        Returns:
            撤回结果

        Raises:
            ValueError: 合同不存在、没有进行中的审批、无权撤回
        """
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not contract:
            raise ValueError("合同不存在")

        instance = (
            self.db.query(ApprovalInstance)
            .filter(
                ApprovalInstance.entity_type == "CONTRACT",
                ApprovalInstance.entity_id == contract_id,
                ApprovalInstance.status == "PENDING",
            )
            .first()
        )

        if not instance:
            raise ValueError("没有进行中的审批流程可撤回")

        if instance.initiator_id != user_id:
            raise ValueError("只能撤回自己提交的审批")

        self.engine.withdraw(instance_id=instance.id, user_id=user_id)

        return {
            "contract_id": contract_id,
            "contract_code": contract.contract_code,
            "status": "withdrawn",
        }

    def get_approval_history(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取审批历史

        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页大小
            status_filter: 状态筛选 (APPROVED/REJECTED)

        Returns:
            (历史列表, 总数)
        """
        query = (
            self.db.query(ApprovalTask)
            .join(ApprovalInstance)
            .filter(
                ApprovalTask.assignee_id == user_id,
                ApprovalInstance.entity_type == "CONTRACT",
                ApprovalTask.status.in_(["APPROVED", "REJECTED"]),
            )
        )

        if status_filter:
            query = query.filter(ApprovalTask.status == status_filter)

        total = query.count()
        offset = (page - 1) * page_size
        tasks = (
            query.order_by(ApprovalTask.completed_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        items = []
        for task in tasks:
            instance = task.instance
            contract = (
                self.db.query(Contract)
                .filter(Contract.id == instance.entity_id)
                .first()
            )

            items.append(
                {
                    "task_id": task.id,
                    "contract_id": instance.entity_id,
                    "contract_code": contract.contract_code if contract else None,
                    "customer_name": contract.customer.name if contract and contract.customer else None,
                    "contract_amount": float(contract.contract_amount) if contract and contract.contract_amount else 0,
                    "action": task.action,
                    "status": task.status,
                    "comment": task.comment,
                    "completed_at": task.completed_at.isoformat()
                    if task.completed_at
                    else None,
                }
            )

        return items, total
