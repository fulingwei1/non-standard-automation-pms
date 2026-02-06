# -*- coding: utf-8 -*-
"""
ApprovalEngine 工作流引擎
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from .models import (
    LegacyApprovalFlow as ApprovalFlow,
    LegacyApprovalInstance as ApprovalInstance,
    LegacyApprovalNode as ApprovalNode,
    LegacyApprovalRecord as ApprovalRecord,
    ApprovalStatus,
    ApprovalDecision,
    ApprovalNodeRole,
)

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """工作流引擎 - 负责审批流程的执行和状态管理"""

    def __init__(self, db: Session):
        self.db = db

    def create_instance(
        self,
        flow_code: str,
        business_type: str,
        business_id: int,
        business_title: str,
        submitted_by: int,
        config: Optional[Dict[str, Any]] = None,
    ) -> ApprovalInstance:
        """
        创建审批实例
        """
        flow = (
            self.db.query(ApprovalFlow)
            .filter(ApprovalFlow.flow_code == flow_code, ApprovalFlow.is_active == True)
            .first()
        )

        if not flow:
            raise ValueError(f"审批流程 {flow_code} 不存在或未启用")

        # 创建审批实例
        instance = ApprovalInstance(
            flow_id=flow.id,
            flow_code=flow.flow_code,
            business_type=business_type,
            business_id=business_id,
            business_title=business_title,
            submitted_by=submitted_by,
            submitted_at=datetime.now(),
            current_status=ApprovalStatus.PENDING.value,
            total_nodes=len(flow.nodes),
            completed_nodes=0,
            due_date=datetime.now()
            + timedelta(hours=self._get_first_node_timeout(flow)),
        )

        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)

        return instance

    def get_current_node(self, instance: ApprovalInstance) -> Optional[ApprovalNode]:
        """
        获取当前待审批节点
        """
        if instance.current_status not in [
            ApprovalStatus.PENDING.value,
            ApprovalStatus.IN_PROGRESS.value,
        ]:
            return None

        if not instance.current_node_id:
            # 查找第一个节点
            node = (
                self.db.query(ApprovalNode)
                .filter(ApprovalNode.flow_id == instance.flow_id)
                .order_by(ApprovalNode.sequence)
                .first()
            )
        else:
            # 查找当前节点后的下一个节点
            current_node = (
                self.db.query(ApprovalNode)
                .filter(ApprovalNode.id == instance.current_node_id)
                .first()
            )
            if current_node:
                node = (
                    self.db.query(ApprovalNode)
                    .filter(
                        ApprovalNode.flow_id == instance.flow_id,
                        ApprovalNode.sequence > current_node.sequence,
                    )
                    .order_by(ApprovalNode.sequence)
                    .first()
                )

        return node

    def evaluate_node_conditions(
        self, node: ApprovalNode, instance: ApprovalInstance
    ) -> bool:
        """
        评估节点条件是否满足

        使用 ConditionEvaluator 解析和评估条件表达式，
        支持 Jinja2 模板、简单 JSON 条件、SQL-like 表达式三种语法。

        Args:
            node: 审批节点
            instance: 审批实例

        Returns:
            条件是否满足
        """
        if not node.condition_expression:
            return True

        try:
            from .condition_parser import ConditionEvaluator, ConditionParseError

            # 构建评估上下文
            context = self._build_condition_context(instance)

            # 使用条件评估器
            evaluator = ConditionEvaluator()
            result = evaluator.evaluate(node.condition_expression, context)

            # 确保返回布尔值
            if isinstance(result, bool):
                return result
            elif isinstance(result, (int, float)):
                return result > 0
            elif isinstance(result, str):
                return result.lower() in ('true', '1', 'yes')
            else:
                return bool(result)

        except ConditionParseError as e:
            logger.warning(f"条件表达式解析失败: {e}, node_id={node.id}")
            return True  # 解析失败时默认允许
        except Exception as e:
            logger.error(f"评估节点条件失败: {e}, node_id={node.id}")
            return True  # 条件评估失败时默认允许审批

    def _build_condition_context(self, instance: ApprovalInstance) -> dict:
        """
        构建条件评估上下文

        包含业务实体数据、表单数据、发起人信息等
        """
        from app.models.user import User

        context = {
            # 实例信息
            "instance": {
                "id": instance.id,
                "flow_code": instance.flow_code,
                "business_type": instance.business_type,
                "business_id": instance.business_id,
                "status": instance.current_status,
                "submitted_at": instance.submitted_at,
            },
            # 表单数据 (从业务数据中提取)
            "form": {},
            # 业务实体
            "entity": {},
            # 发起人
            "initiator": {},
        }

        # 获取发起人信息
        if instance.submitted_by:
            submitter = self.db.query(User).filter(User.id == instance.submitted_by).first()
            if submitter:
                context["initiator"] = {
                    "id": submitter.id,
                    "username": submitter.username,
                    "real_name": submitter.real_name,
                    "department": submitter.department,
                }
                context["user"] = context["initiator"]

        # 获取业务实体数据
        entity_data = self._get_business_entity_data(
            instance.business_type,
            instance.business_id
        )
        if entity_data:
            context["entity"] = entity_data
            context["form"] = entity_data  # 兼容表单字段访问

        return context

    def _get_business_entity_data(self, business_type: str, business_id: int) -> dict:
        """
        获取业务实体数据

        根据业务类型查询对应的业务数据
        """
        try:
            if business_type == "ECN":
                from app.models.ecn import Ecn
                ecn = self.db.query(Ecn).filter(Ecn.id == business_id).first()
                if ecn:
                    return {
                        "id": ecn.id,
                        "ecn_no": ecn.ecn_no,
                        "ecn_type": ecn.ecn_type,
                        "status": ecn.status,
                        "priority": getattr(ecn, 'priority', None),
                        "change_reason": ecn.change_reason,
                        "estimated_cost": getattr(ecn, 'estimated_cost', 0),
                    }

            elif business_type == "SALES_QUOTE":
                from app.models.sales import SalesQuote
                quote = self.db.query(SalesQuote).filter(SalesQuote.id == business_id).first()
                if quote:
                    return {
                        "id": quote.id,
                        "quote_no": quote.quote_no,
                        "status": quote.status,
                        "total_amount": float(quote.total_amount) if quote.total_amount else 0,
                        "gross_margin": float(quote.gross_margin) if hasattr(quote, 'gross_margin') and quote.gross_margin else 0,
                        "customer_id": quote.customer_id,
                    }

            elif business_type == "SALES_INVOICE":
                from app.models.sales import SalesInvoice
                invoice = self.db.query(SalesInvoice).filter(SalesInvoice.id == business_id).first()
                if invoice:
                    return {
                        "id": invoice.id,
                        "invoice_no": getattr(invoice, 'invoice_no', None),
                        "status": invoice.status,
                        "amount": float(invoice.amount) if invoice.amount else 0,
                    }

            elif business_type == "PURCHASE_ORDER":
                from app.models.purchase import PurchaseOrder
                po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == business_id).first()
                if po:
                    return {
                        "id": po.id,
                        "order_no": po.order_no,
                        "status": po.status,
                        "total_amount": float(po.total_amount) if po.total_amount else 0,
                        "supplier_id": po.supplier_id,
                    }

            elif business_type == "ACCEPTANCE":
                from app.models.acceptance import AcceptanceOrder
                order = self.db.query(AcceptanceOrder).filter(AcceptanceOrder.id == business_id).first()
                if order:
                    return {
                        "id": order.id,
                        "order_no": order.order_no,
                        "acceptance_type": order.acceptance_type,
                        "status": order.status,
                        "project_id": order.project_id,
                    }

            elif business_type == "OUTSOURCING":
                from app.models.outsourcing import OutsourcingOrder
                order = self.db.query(OutsourcingOrder).filter(OutsourcingOrder.id == business_id).first()
                if order:
                    return {
                        "id": order.id,
                        "order_no": order.order_no,
                        "status": order.status,
                        "total_amount": float(order.total_amount) if order.total_amount else 0,
                        "vendor_id": order.vendor_id,
                    }

            # 默认返回空字典
            return {}

        except Exception as e:
            logger.error(f"获取业务实体数据失败: {e}, type={business_type}, id={business_id}")
            return {}

    def submit_approval(
        self,
        instance: ApprovalInstance,
        approver_id: int,
        decision: str,
        comment: Optional[str] = None,
    ) -> ApprovalRecord:
        """
        提交审批决策
        """
        node = self.get_current_node(instance)
        if not node:
            raise ValueError("没有可审批的节点")

        # 验证条件
        if not self.evaluate_node_conditions(node, instance):
            raise ValueError("不满足审批条件")

        # 创建审批记录
        record = ApprovalRecord(
            instance_id=instance.id,
            node_id=node.id,
            approver_id=approver_id,
            approver_name=self._get_approver_name(approver_id),
            approver_role=self._get_approver_role(node),
            decision=decision,
            comment=comment,
            approved_at=datetime.now(),
        )

        self.db.add(record)
        self.db.commit()

        # 更新实例状态
        self._update_instance_status(instance, record)

        return record

    def _get_approver_name(self, approver_id: int) -> str:
        """获取审批人姓名"""
        from app.models.user import User

        user = self.db.query(User).filter(User.id == approver_id).first()
        if user:
            return user.real_name or user.username
        return f"User_{approver_id}"

    def _get_approver_role(self, node: ApprovalNode) -> str:
        """获取审批人角色"""
        if node.role_type == ApprovalNodeRole.USER.value:
            return "用户"
        elif node.role_type == ApprovalNodeRole.ROLE.value:
            return "角色"
        elif node.role_type == ApprovalNodeRole.DEPARTMENT.value:
            return "部门"
        elif node.role.role_type == ApprovalNodeRole.SUPERVISOR.value:
            return "上级"
        return node.role_type

    def _update_instance_status(
        self,
        instance: ApprovalInstance,
        record: ApprovalRecord,
    ) -> None:
        """
        更新实例状态
        """
        flow = instance.flow

        if record.decision == ApprovalDecision.APPROVED:
            # 审批通过，进入下一节点或完成
            next_node = self._find_next_node(instance, record.node)
            if next_node:
                instance.current_node_id = next_node.id
                instance.current_status = ApprovalStatus.IN_PROGRESS.value
                instance.completed_nodes += 1
            else:
                instance.current_status = ApprovalStatus.APPROVED.value
                instance.current_node_id = None
                instance.completed_nodes = flow.total_nodes

        elif record.decision == ApprovalDecision.REJECTED:
            # 驳回
            prev_node = self._find_previous_node(instance, record.node)
            if prev_node:
                instance.current_node_id = prev_node.id
                instance.current_status = ApprovalStatus.PENDING.value
            else:
                instance.current_status = ApprovalStatus.REJECTED.value
                instance.current_node_id = None

        elif record.decision == ApprovalDecision.RETURNED:
            # 退回上一级
            prev_node = self._find_previous_node(instance, record.node)
            if prev_node:
                instance.current_node_id = prev_node.id
                instance.current_status = ApprovalStatus.PENDING.value
            else:
                raise ValueError("已经是第一个节点，无法退回")

        self.db.add(instance)
        self.db.commit()

        # 检查是否完成
        if instance.current_status == ApprovalStatus.APPROVED.value:
            instance.completed_nodes = flow.total_nodes
            instance.current_node_id = None

    def _find_next_node(
        self, instance: ApprovalInstance, current_node: ApprovalNode
    ) -> Optional[ApprovalNode]:
        """查找下一个审批节点"""
        return (
            self.db.query(ApprovalNode)
            .filter(
                ApprovalNode.flow_id == instance.flow_id,
                ApprovalNode.sequence > current_node.sequence,
            )
            .order_by(ApprovalNode.sequence)
            .first()
        )

    def _find_previous_node(
        self, instance: ApprovalInstance, current_node: ApprovalNode
    ) -> Optional[ApprovalNode]:
        """查找上一个审批节点"""
        return (
            self.db.query(ApprovalNode)
            .filter(
                ApprovalNode.flow_id == instance.flow_id,
                ApprovalNode.sequence < current_node.sequence,
            )
            .order_by(ApprovalNode.sequence.desc())
            .first()
        )

    def _get_first_node_timeout(self, flow: ApprovalFlow) -> int:
        """获取第一个节点的超时时间（小时）"""
        # 从配置中读取，默认48小时
        return 48

    def is_expired(self, instance: ApprovalInstance) -> bool:
        """检查实例是否超时"""
        if not instance.due_date:
            return False
        return datetime.now() > instance.due_date


class ApprovalRouter:
    """审批路由器 - 根据业务类型和配置决定审批流程"""

    def __init__(self, db: Session):
        self.db = db

    def get_approval_flow(
        self, business_type: str, config: Optional[Dict[str, Any]] = None
    ) -> Optional[ApprovalFlow]:
        """
        根据业务类型获取审批流程

        Args:
            business_type: 业务类型（对应 module_name 字段）
            config: 可选的配置参数

        Returns:
            匹配的审批流程，如果未找到则返回 None
        """
        flow = (
            self.db.query(ApprovalFlow)
            .filter(
                ApprovalFlow.module_name == business_type,
                ApprovalFlow.is_active == True,
            )
            .first()
        )

        return flow

    def determine_approval_flow(
        self, business_type: str, business_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        根据业务数据和配置决定使用哪个审批流程
        """
        # ECN：根据金额和类型决定流程
        if business_type == "ECN":
            return "ECN_STANDARD"  # 标准ECN审批流程

        # Sales Invoice：根据金额决定单级或多级
        elif business_type == "SALES_INVOICE":
            amount = business_data.get("amount", 0)
            if amount < 50000:
                return "SALES_INVOICE_SINGLE"
            else:
                return "SALES_INVOICE_MULTI"

        # Sales Quote：默认单级
        elif business_type == "SALES_QUOTE":
            return "SALES_QUOTE_SINGLE"

        return None

    def create_approval_instance(
        self,
        business_type: str,
        business_data: Dict[str, Any],
        submitted_by: int,
    ) -> ApprovalInstance:
        """
        创建审批实例（简化版，用于快速集成）
        """
        flow_code = self.determine_approval_flow(business_type, business_data)
        if not flow_code:
            raise ValueError(f"未找到业务类型 {business_type} 的审批流程")

        instance = self.create_instance(
            flow_code=flow_code,
            business_type=business_type,
            business_id=business_data.get("business_id"),
            business_title=business_data.get("business_title", ""),
            submitted_by=submitted_by,
            config=business_data.get("config"),
        )

        return instance
