# -*- coding: utf-8 -*-
"""
合同审批适配器

将合同模块接入统一审批系统
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from app.models.sales.contracts import ContractApproval

import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.approval import ApprovalInstance, ApprovalTask
from app.models.sales.contracts import Contract
from app.models.user import User

from .base import ApprovalAdapter

logger = logging.getLogger(__name__)


def _read_model_attr(obj: Any, name: str, default: Any = None) -> Any:
    """Read real model attributes without creating synthetic MagicMock children."""
    if obj is None:
        return default
    if name in getattr(obj, "__dict__", {}):
        return getattr(obj, name)
    if hasattr(type(obj), name):
        return getattr(obj, name, default)
    return default


def _first_model_attr(obj: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        value = _read_model_attr(obj, name, default)
        if value is not None:
            return value
    return default


def _status_key(status: Any) -> str:
    return str(status or "").upper()


class ContractApprovalAdapter(ApprovalAdapter):
    """
    合同审批适配器

    支持的条件字段:
    - entity.contract_amount: 合同金额
    - entity.customer_name: 客户名称
    - entity.payment_terms: 付款条款类型
    """

    entity_type = "CONTRACT"

    def __init__(self, db: Session):
        self.db = db

    def get_entity(self, entity_id: int) -> Optional[Contract]:
        """获取合同实体"""
        return self.db.query(Contract).filter(Contract.id == entity_id).first()

    def get_entity_data(self, entity_id: int) -> Dict[str, Any]:
        """
        获取合同数据用于条件路由

        Returns:
            包含合同关键数据的字典
        """
        contract = self.get_entity(entity_id)
        if not contract:
            return {}

        customer = _read_model_attr(contract, "customer")
        owner = _first_model_attr(contract, "sales_owner", "owner")
        signing_date = _read_model_attr(contract, "signing_date")
        contract_amount = _read_model_attr(contract, "contract_amount")

        return {
            "contract_code": _read_model_attr(contract, "contract_code"),
            "customer_contract_no": _read_model_attr(contract, "customer_contract_no"),
            "status": _read_model_attr(contract, "status"),
            "contract_amount": float(contract_amount) if contract_amount else 0,
            "customer_id": _read_model_attr(contract, "customer_id"),
            "customer_name": _first_model_attr(customer, "name", "customer_name"),
            "project_id": _read_model_attr(contract, "project_id"),
            "signed_date": signing_date.isoformat() if signing_date else None,
            "owner_id": _first_model_attr(contract, "sales_owner_id", "owner_id"),
            "owner_name": _first_model_attr(owner, "real_name", "name", "username"),
            "payment_terms_summary": _read_model_attr(contract, "payment_terms_summary"),
        }

    def on_submit(self, entity_id: int, instance: ApprovalInstance) -> None:
        """提交审批时的回调"""
        contract = self.get_entity(entity_id)
        if contract:
            contract.status = "PENDING_APPROVAL"
            self.db.flush()

    def on_approved(self, entity_id: int, instance: ApprovalInstance) -> None:
        """审批通过时的回调"""
        contract = self.get_entity(entity_id)
        if contract:
            contract.status = "APPROVED"
            self.db.flush()

    def on_rejected(self, entity_id: int, instance: ApprovalInstance, *_args: Any) -> None:
        """审批驳回时的回调"""
        contract = self.get_entity(entity_id)
        if contract:
            contract.status = "REJECTED"
            self.db.flush()

    def on_withdrawn(self, entity_id: int, instance: ApprovalInstance) -> None:
        """撤回审批时的回调"""
        contract = self.get_entity(entity_id)
        if contract:
            contract.status = "DRAFT"
            self.db.flush()

    def on_cancelled(self, entity_id: int, instance: ApprovalInstance) -> None:
        """兼容旧调用：取消审批等同撤回到草稿。"""
        self.on_withdrawn(entity_id, instance)

    def get_title(self, entity_id: int) -> str:
        """生成审批标题"""
        contract = self.get_entity(entity_id)
        if contract:
            customer_name = contract.customer.name if contract.customer else "未知客户"
            return f"合同审批 - {contract.contract_code} ({customer_name})"
        return f"合同审批 - #{entity_id}"

    def get_summary(self, entity_id: int) -> str:
        """生成审批摘要"""
        data = self.get_entity_data(entity_id)
        if not data:
            return ""

        parts = []
        if data.get("customer_name"):
            parts.append(f"客户: {data['customer_name']}")
        if data.get("contract_amount"):
            parts.append(f"合同金额: ¥{data['contract_amount']:,.2f}")
        if data.get("signed_date"):
            parts.append(f"签订日期: {data['signed_date']}")

        return " | ".join(parts)

    def validate_submit(self, entity_id: int) -> tuple[bool, str]:
        """验证是否可以提交审批"""
        contract = self.get_entity(entity_id)
        if not contract:
            return False, "合同不存在"

        if _status_key(contract.status) not in ("DRAFT", "REJECTED"):
            return False, f"当前状态({contract.status})不允许提交审批"

        if not contract.contract_amount or contract.contract_amount <= 0:
            return False, "合同金额必须大于0"

        return True, ""

    # ========== 高级方法：使用 WorkflowEngine ========== #

    def submit_for_approval(
        self,
        contract,
        initiator_id: int,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        urgency: str = "NORMAL",
        cc_user_ids: Optional[List[int]] = None,
    ) -> ApprovalInstance:
        """
        提交合同审批到统一审批引擎

        Args:
            contract: 合同实例
            initiator_id: 发起人ID
            title: 审批标题
            summary: 审批摘要
            urgency: 紧急程度
            cc_user_ids: 抄送人ID列表

        Returns:
            创建的ApprovalInstance
        """
        # 检查是否已经提交
        if contract.approval_instance_id:
            logger.warning(f"合同 {contract.contract_code} 已经提交审批")
            return (
                self.db.query(ApprovalInstance)
                .filter(ApprovalInstance.id == contract.approval_instance_id)
                .first()
            )

        # 构建表单数据
        form_data = {
            "contract_id": contract.id,
            "contract_code": contract.contract_code,
            "contract_amount": float(contract.contract_amount) if contract.contract_amount else 0,
            "customer_id": contract.customer_id,
            "project_id": contract.project_id,
            "signed_date": contract.signing_date.isoformat() if contract.signing_date else None,
            "payment_terms": contract.payment_terms_summary,
            "acceptance_summary": contract.acceptance_summary,
        }

        # 使用统一审批引擎创建实例
        from ..engine import ApprovalEngineService

        engine = ApprovalEngineService(self.db)

        instance = engine.submit(
            template_code="SALES_CONTRACT",
            entity_type="CONTRACT",
            entity_id=contract.id,
            form_data=form_data,
            initiator_id=initiator_id,
            title=title or f"合同审批 - {contract.contract_code}",
            summary=summary or f"合同审批：{contract.contract_code}",
            urgency=urgency,
            cc_user_ids=cc_user_ids,
        )

        # 更新合同，关联审批实例
        contract.approval_instance_id = instance.id
        contract.approval_status = instance.status
        self.db.add(contract)
        self.db.commit()

        logger.info(f"合同 {contract.contract_code} 已提交审批，实例ID: {instance.id}")

        return instance

    def create_contract_approval(
        self,
        instance: ApprovalInstance,
        task: ApprovalTask,
    ) -> Optional["ContractApproval"]:
        """创建合同审批记录"""
        from app.models.sales.contracts import ContractApproval

        # 检查是否已存在
        existing = (
            self.db.query(ContractApproval)
            .filter(
                ContractApproval.contract_id == instance.entity_id,
                ContractApproval.approval_level == task.node_order,
            )
            .first()
        )

        if existing:
            return existing

        # 获取审批人
        approver = (
            self.db.query(User).filter(User.id == task.assignee_id).first()
            if task.assignee_id
            else None
        )

        # 计算到期时间
        due_date = task.due_at or (datetime.now() + timedelta(hours=48))

        # 创建新记录
        approval = ContractApproval(
            contract_id=instance.entity_id,
            approval_level=task.node_order,
            approval_role=task.node_name or "",
            approver_id=task.assignee_id,
            approver_name=approver.real_name if approver else "",
            approval_result=None,  # 待审批
            status="PENDING",
            due_date=due_date,
            is_overdue=False,
        )

        self.db.add(approval)
        return approval

    def update_contract_approval_from_action(
        self,
        task: ApprovalTask,
        action: str,
        comment: Optional[str] = None,
    ) -> Optional["ContractApproval"]:
        """更新合同审批记录"""
        approval_level = task.node_order
        approval = (
            self.db.query(ContractApproval)
            .filter(
                ContractApproval.contract_id == task.instance.entity_id,
                ContractApproval.approval_level == approval_level,
            )
            .first()
        )

        if not approval:
            logger.warning(
                f"未找到合同审批记录: entity_id={task.instance.entity_id}, level={approval_level}"
            )
            return None

        # 更新审批结果
        if action == "APPROVE":
            approval.approval_result = "APPROVED"
            approval.approval_opinion = comment
            approval.status = "APPROVED"
            approval.approved_at = datetime.now()
        elif action == "REJECT":
            approval.approval_result = "REJECTED"
            approval.approval_opinion = comment
            approval.status = "REJECTED"
            approval.approved_at = datetime.now()

        self.db.add(approval)
        self.db.commit()

        logger.info(
            f"合同审批记录已更新: entity_id={approval.contract_id}, level={approval_level}, action={action}"
        )

        return approval
