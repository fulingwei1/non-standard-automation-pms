# -*- coding: utf-8 -*-
"""
ECN物料影响跟踪服务

提供：
- 物料影响分析
- 执行进度跟踪
- 相关人员管理
- 主动通知
- 物料处置工作流
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ecn.core import Ecn
from app.models.ecn.impact import EcnAffectedMaterial, EcnAffectedOrder, EcnBomImpact
from app.models.ecn.material_impact import (
    EcnExecutionProgress,
    EcnMaterialDisposition,
    EcnStakeholder,
)
from app.models.material import BomItem
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.services.channel_handlers.base import NotificationPriority, NotificationRequest
from app.services.unified_notification_service import NotificationService

logger = logging.getLogger(__name__)

# 角色名称映射
ROLE_NAMES = {
    "PROJECT_MANAGER": "项目经理",
    "PURCHASER": "采购员",
    "SUPPLIER_CONTACT": "供应商联系人",
    "DESIGNER": "设计人员",
    "APPROVER": "审批人",
    "OBSERVER": "观察者",
}

# 执行阶段定义
EXECUTION_PHASES = [
    ("NOTIFY_SUPPLIER", "通知供应商", 1),
    ("PURCHASE_CHANGE", "采购变更", 2),
    ("MATERIAL_DISPOSITION", "物料处理", 3),
    ("VERIFICATION", "验证确认", 4),
    ("CLOSE", "关闭", 5),
]

# 通知类型到通知系统category映射
NOTIFICATION_CATEGORY = "project"  # ECN通知归入project类


class EcnMaterialImpactService:
    """ECN物料影响跟踪服务"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 1. 物料影响分析 ====================

    def analyze_material_impact(self, ecn_id: int, current_user_id: int) -> Dict[str, Any]:
        """分析ECN变更影响的物料清单"""
        ecn = self._get_ecn_or_raise(ecn_id)

        # 获取ECN受影响物料
        affected_materials = (
            self.db.query(EcnAffectedMaterial)
            .filter(EcnAffectedMaterial.ecn_id == ecn_id)
            .all()
        )

        material_impacts = []
        status_summary: Dict[str, int] = {}
        loss_by_status: Dict[str, Decimal] = {}
        total_potential_loss = Decimal("0")

        for am in affected_materials:
            # 确定物料当前状态
            mat_status = self._determine_material_status(am)

            # 查找关联的采购订单
            po_info = self._find_purchase_order_info(am)

            # 计算潜在损失
            potential_loss = self._calculate_potential_loss(am, mat_status)

            item = {
                "material_id": am.material_id,
                "material_code": am.material_code,
                "material_name": am.material_name,
                "specification": am.specification,
                "material_status": mat_status,
                "affected_quantity": am.old_quantity or Decimal("0"),
                "unit_price": Decimal("0"),
                "potential_loss": potential_loss,
                "purchase_order_id": po_info.get("order_id"),
                "purchase_order_no": po_info.get("order_no"),
                "supplier_name": po_info.get("supplier_name"),
                "change_type": am.change_type,
            }

            if po_info.get("unit_price"):
                item["unit_price"] = po_info["unit_price"]

            material_impacts.append(item)

            # 统计
            status_summary[mat_status] = status_summary.get(mat_status, 0) + 1
            loss_by_status[mat_status] = loss_by_status.get(mat_status, Decimal("0")) + potential_loss
            total_potential_loss += potential_loss

            # 创建/更新处置记录
            self._ensure_disposition_record(ecn_id, am, mat_status, po_info)

        # 受影响采购订单
        affected_orders = self._get_affected_orders(ecn_id)

        # 项目影响
        project_impacts = self._get_project_impacts(ecn)

        self.db.commit()

        return {
            "ecn_id": ecn.id,
            "ecn_no": ecn.ecn_no,
            "analysis_time": datetime.now(),
            "affected_materials": material_impacts,
            "total_affected_count": len(material_impacts),
            "status_summary": status_summary,
            "total_potential_loss": total_potential_loss,
            "loss_by_status": {k: str(v) for k, v in loss_by_status.items()},
            "affected_orders": affected_orders,
            "project_impacts": project_impacts,
        }

    def _determine_material_status(self, am: EcnAffectedMaterial) -> str:
        """确定物料当前采购状态"""
        if not am.material_id:
            return "NOT_PURCHASED"

        # 查找相关采购订单项
        po_item = (
            self.db.query(PurchaseOrderItem)
            .filter(PurchaseOrderItem.material_id == am.material_id)
            .join(PurchaseOrder, PurchaseOrder.id == PurchaseOrderItem.order_id)
            .filter(PurchaseOrder.status.notin_(["CANCELLED", "DRAFT"]))
            .order_by(PurchaseOrderItem.created_at.desc())
            .first()
        )

        if not po_item:
            return "NOT_PURCHASED"

        # 已收货
        if po_item.received_qty and po_item.received_qty > 0:
            if po_item.received_qty >= po_item.quantity:
                return "IN_STOCK"
            return "IN_TRANSIT"

        # 有订单但未收货
        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_item.order_id).first()
        if po and po.status in ("ISSUED", "PARTIAL"):
            return "IN_TRANSIT"

        return "ORDERED"

    def _find_purchase_order_info(self, am: EcnAffectedMaterial) -> Dict[str, Any]:
        """查找物料关联的采购订单信息"""
        if not am.material_id:
            return {}

        po_item = (
            self.db.query(PurchaseOrderItem)
            .filter(PurchaseOrderItem.material_id == am.material_id)
            .join(PurchaseOrder, PurchaseOrder.id == PurchaseOrderItem.order_id)
            .filter(PurchaseOrder.status.notin_(["CANCELLED", "DRAFT"]))
            .order_by(PurchaseOrderItem.created_at.desc())
            .first()
        )

        if not po_item:
            return {}

        po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == po_item.order_id).first()
        if not po:
            return {}

        supplier_name = None
        if po.vendor:
            supplier_name = po.vendor.name if hasattr(po.vendor, "name") else str(po.vendor)

        return {
            "order_id": po.id,
            "order_no": po.order_no,
            "unit_price": po_item.unit_price or Decimal("0"),
            "supplier_id": po.supplier_id,
            "supplier_name": supplier_name,
        }

    def _calculate_potential_loss(self, am: EcnAffectedMaterial, mat_status: str) -> Decimal:
        """计算潜在损失金额"""
        # 未采购没有直接损失
        if mat_status == "NOT_PURCHASED":
            return Decimal("0")

        # 已有呆滞料分析的，直接用
        if am.obsolete_cost:
            return am.obsolete_cost

        # 用成本影响作为估算
        if am.cost_impact:
            return abs(am.cost_impact)

        return Decimal("0")

    def _ensure_disposition_record(
        self, ecn_id: int, am: EcnAffectedMaterial, mat_status: str, po_info: Dict
    ):
        """确保每个受影响物料有处置记录"""
        existing = (
            self.db.query(EcnMaterialDisposition)
            .filter(
                EcnMaterialDisposition.ecn_id == ecn_id,
                EcnMaterialDisposition.affected_material_id == am.id,
            )
            .first()
        )

        if existing:
            return

        disposition = EcnMaterialDisposition(
            ecn_id=ecn_id,
            affected_material_id=am.id,
            material_id=am.material_id,
            material_code=am.material_code,
            material_name=am.material_name,
            specification=am.specification,
            material_status=mat_status,
            purchase_order_id=po_info.get("order_id"),
            purchase_order_no=po_info.get("order_no"),
            supplier_id=po_info.get("supplier_id"),
            supplier_name=po_info.get("supplier_name"),
            affected_quantity=am.old_quantity or Decimal("0"),
            unit_price=po_info.get("unit_price", Decimal("0")),
            potential_loss=self._calculate_potential_loss(am, mat_status),
            status="PENDING",
        )
        self.db.add(disposition)

    def _get_affected_orders(self, ecn_id: int) -> List[Dict[str, Any]]:
        """获取受影响的采购订单"""
        affected = (
            self.db.query(EcnAffectedOrder)
            .filter(EcnAffectedOrder.ecn_id == ecn_id)
            .all()
        )

        orders = []
        seen_order_ids = set()
        for ao in affected:
            if ao.order_id in seen_order_ids:
                continue
            seen_order_ids.add(ao.order_id)

            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == ao.order_id).first()
            supplier_name = None
            if po and po.vendor:
                supplier_name = po.vendor.name if hasattr(po.vendor, "name") else None

            orders.append({
                "order_id": ao.order_id,
                "order_no": ao.order_no,
                "supplier_name": supplier_name,
                "total_amount": po.total_amount if po else Decimal("0"),
                "status": po.status if po else None,
                "affected_item_count": 1,
            })

        return orders

    def _get_project_impacts(self, ecn: Ecn) -> List[Dict[str, Any]]:
        """获取对项目的影响"""
        impacts = []
        if ecn.project_id and ecn.project:
            affected_count = (
                self.db.query(func.count(EcnAffectedMaterial.id))
                .filter(EcnAffectedMaterial.ecn_id == ecn.id)
                .scalar()
            ) or 0

            risk_level = "LOW"
            if ecn.schedule_impact_days and ecn.schedule_impact_days > 14:
                risk_level = "HIGH"
            elif ecn.schedule_impact_days and ecn.schedule_impact_days > 7:
                risk_level = "MEDIUM"

            project_name = (
                ecn.project.name
                if hasattr(ecn.project, "name")
                else ecn.project.project_name
                if hasattr(ecn.project, "project_name")
                else str(ecn.project)
            )

            impacts.append({
                "project_id": ecn.project_id,
                "project_name": project_name,
                "schedule_impact_days": ecn.schedule_impact_days or 0,
                "affected_material_count": affected_count,
                "risk_level": risk_level,
            })

        return impacts

    # ==================== 2. 执行进度跟踪 ====================

    def get_execution_progress(self, ecn_id: int) -> Dict[str, Any]:
        """获取ECN执行进度"""
        ecn = self._get_ecn_or_raise(ecn_id)

        # 确保执行阶段已创建
        self._ensure_execution_phases(ecn_id)

        phases = (
            self.db.query(EcnExecutionProgress)
            .filter(EcnExecutionProgress.ecn_id == ecn_id)
            .order_by(EcnExecutionProgress.phase_order)
            .all()
        )

        phase_list = []
        blocked_phases = []
        for p in phases:
            assignee_name = None
            if p.assignee:
                assignee_name = (
                    p.assignee.real_name
                    if hasattr(p.assignee, "real_name")
                    else p.assignee.username
                    if hasattr(p.assignee, "username")
                    else None
                )

            phase_data = {
                "id": p.id,
                "phase": p.phase,
                "phase_name": p.phase_name,
                "phase_order": p.phase_order,
                "status": p.status,
                "progress_pct": p.progress_pct,
                "planned_start": p.planned_start,
                "planned_end": p.planned_end,
                "actual_start": p.actual_start,
                "actual_end": p.actual_end,
                "estimated_completion": p.estimated_completion,
                "assignee_id": p.assignee_id,
                "assignee_name": assignee_name,
                "is_blocked": p.is_blocked,
                "block_reason": p.block_reason,
                "summary": p.summary,
            }
            phase_list.append(phase_data)

            if p.is_blocked:
                blocked_phases.append(phase_data)

        # 物料处置状态
        dispositions = (
            self.db.query(EcnMaterialDisposition)
            .filter(EcnMaterialDisposition.ecn_id == ecn_id)
            .all()
        )
        mat_dispositions = [
            {
                "material_code": d.material_code,
                "material_name": d.material_name,
                "disposition": d.disposition,
                "status": d.status,
                "potential_loss": d.potential_loss or Decimal("0"),
                "actual_loss": d.actual_loss or Decimal("0"),
            }
            for d in dispositions
        ]

        # 整体进度
        overall_pct = 0
        if phases:
            overall_pct = sum(p.progress_pct or 0 for p in phases) // len(phases)

        # 预计完成
        estimated = None
        for p in reversed(phases):
            if p.estimated_completion:
                estimated = p.estimated_completion
                break

        return {
            "ecn_id": ecn.id,
            "ecn_no": ecn.ecn_no,
            "ecn_status": ecn.status,
            "overall_progress_pct": overall_pct,
            "phases": phase_list,
            "material_dispositions": mat_dispositions,
            "blocked_phases": blocked_phases,
            "execution_start": ecn.execution_start,
            "estimated_completion": estimated,
        }

    def _ensure_execution_phases(self, ecn_id: int):
        """确保ECN的执行阶段记录已创建"""
        count = (
            self.db.query(func.count(EcnExecutionProgress.id))
            .filter(EcnExecutionProgress.ecn_id == ecn_id)
            .scalar()
        )

        if count and count > 0:
            return

        for phase_code, phase_name, phase_order in EXECUTION_PHASES:
            progress = EcnExecutionProgress(
                ecn_id=ecn_id,
                phase=phase_code,
                phase_name=phase_name,
                phase_order=phase_order,
                status="PENDING",
                progress_pct=0,
            )
            self.db.add(progress)

        self.db.commit()

    # ==================== 3. 相关人员管理 ====================

    def get_stakeholders(self, ecn_id: int) -> Dict[str, Any]:
        """获取ECN相关人员列表"""
        ecn = self._get_ecn_or_raise(ecn_id)

        # 自动识别相关人员
        self._auto_identify_stakeholders(ecn)

        stakeholders = (
            self.db.query(EcnStakeholder)
            .filter(EcnStakeholder.ecn_id == ecn_id)
            .all()
        )

        result = []
        by_role: Dict[str, int] = {}
        for s in stakeholders:
            user_name = None
            department = None
            if s.user:
                user_name = (
                    s.user.real_name
                    if hasattr(s.user, "real_name") and s.user.real_name
                    else s.user.username
                    if hasattr(s.user, "username")
                    else None
                )
                if hasattr(s.user, "department"):
                    department = s.user.department

            result.append({
                "id": s.id,
                "ecn_id": s.ecn_id,
                "user_id": s.user_id,
                "user_name": user_name,
                "department": department,
                "role": s.role,
                "role_name": s.role_name or ROLE_NAMES.get(s.role, s.role),
                "source": s.source,
                "source_reason": s.source_reason,
                "is_subscribed": s.is_subscribed,
                "subscription_types": s.subscription_types,
                "can_view_detail": s.can_view_detail,
                "can_view_progress": s.can_view_progress,
            })

            by_role[s.role] = by_role.get(s.role, 0) + 1

        return {
            "ecn_id": ecn.id,
            "ecn_no": ecn.ecn_no,
            "stakeholders": result,
            "total_count": len(result),
            "by_role": by_role,
        }

    def _auto_identify_stakeholders(self, ecn: Ecn):
        """自动识别并添加相关人员"""
        existing_users = set(
            row[0]
            for row in self.db.query(EcnStakeholder.user_id)
            .filter(EcnStakeholder.ecn_id == ecn.id)
            .all()
        )

        to_add = []

        # 1. 申请人 -> 设计人员
        if ecn.applicant_id and ecn.applicant_id not in existing_users:
            to_add.append((ecn.applicant_id, "DESIGNER", "ECN申请人"))
            existing_users.add(ecn.applicant_id)

        # 2. 项目经理
        if ecn.project and hasattr(ecn.project, "manager_id") and ecn.project.manager_id:
            pm_id = ecn.project.manager_id
            if pm_id not in existing_users:
                to_add.append((pm_id, "PROJECT_MANAGER", "项目经理（自动识别）"))
                existing_users.add(pm_id)

        # 3. 采购员 - 从受影响订单中识别
        affected_orders = (
            self.db.query(EcnAffectedOrder)
            .filter(EcnAffectedOrder.ecn_id == ecn.id)
            .all()
        )
        for ao in affected_orders:
            po = self.db.query(PurchaseOrder).filter(PurchaseOrder.id == ao.order_id).first()
            if po and po.created_by and po.created_by not in existing_users:
                to_add.append((po.created_by, "PURCHASER", f"采购订单{ao.order_no}创建人"))
                existing_users.add(po.created_by)

        # 4. 审批人
        from app.models.ecn.evaluation_approval import EcnApproval

        approvals = (
            self.db.query(EcnApproval)
            .filter(EcnApproval.ecn_id == ecn.id)
            .all()
        )
        for approval in approvals:
            if approval.approver_id and approval.approver_id not in existing_users:
                to_add.append(
                    (approval.approver_id, "APPROVER", f"ECN审批人（{approval.approval_role}）")
                )
                existing_users.add(approval.approver_id)

        # 批量添加
        for user_id, role, reason in to_add:
            stakeholder = EcnStakeholder(
                ecn_id=ecn.id,
                user_id=user_id,
                role=role,
                role_name=ROLE_NAMES.get(role, role),
                source="AUTO",
                source_reason=reason,
                is_subscribed=True,
                subscription_types=["STATUS_CHANGE", "DISPOSITION", "PROGRESS"],
                can_view_detail=True,
                can_view_progress=True,
            )
            self.db.add(stakeholder)

        if to_add:
            self.db.commit()

    def update_subscription(
        self, ecn_id: int, user_id: int, is_subscribed: bool,
        subscription_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """更新用户订阅状态"""
        stakeholder = (
            self.db.query(EcnStakeholder)
            .filter(
                EcnStakeholder.ecn_id == ecn_id,
                EcnStakeholder.user_id == user_id,
            )
            .first()
        )

        if not stakeholder:
            raise ValueError(f"用户{user_id}不是ECN {ecn_id}的相关人员")

        stakeholder.is_subscribed = is_subscribed
        if subscription_types is not None:
            stakeholder.subscription_types = subscription_types

        self.db.commit()
        return {"ecn_id": ecn_id, "user_id": user_id, "is_subscribed": is_subscribed}

    # ==================== 4. 主动通知 ====================

    def notify_stakeholders(
        self,
        ecn_id: int,
        notification_type: str,
        message: Optional[str] = None,
        target_roles: Optional[List[str]] = None,
        priority: str = "NORMAL",
        current_user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """通知ECN相关人员"""
        ecn = self._get_ecn_or_raise(ecn_id)

        # 获取订阅的相关人员
        query = (
            self.db.query(EcnStakeholder)
            .filter(
                EcnStakeholder.ecn_id == ecn_id,
                EcnStakeholder.is_subscribed.is_(True),
            )
        )
        if target_roles:
            query = query.filter(EcnStakeholder.role.in_(target_roles))

        stakeholders = query.all()

        # 构建通知内容
        title, content = self._build_notification_content(ecn, notification_type, message)

        notification_service = NotificationService(self.db)
        sent_count = 0
        failed_count = 0
        skipped_count = 0
        details = []

        priority_map = {
            "LOW": NotificationPriority.LOW,
            "NORMAL": NotificationPriority.NORMAL,
            "HIGH": NotificationPriority.HIGH,
            "URGENT": NotificationPriority.URGENT,
        }

        for s in stakeholders:
            # 检查订阅类型匹配
            if s.subscription_types and notification_type not in s.subscription_types:
                skipped_count += 1
                details.append({
                    "user_id": s.user_id,
                    "status": "skipped",
                    "reason": "未订阅此通知类型",
                })
                continue

            try:
                request = NotificationRequest(
                    recipient_id=s.user_id,
                    notification_type=f"ECN_{notification_type}",
                    category=NOTIFICATION_CATEGORY,
                    title=title,
                    content=content,
                    priority=priority_map.get(priority, NotificationPriority.NORMAL),
                    source_type="ecn",
                    source_id=ecn_id,
                    link_url=f"/ecn/{ecn_id}",
                    extra_data={
                        "ecn_no": ecn.ecn_no,
                        "notification_type": notification_type,
                    },
                )
                result = notification_service.send_notification(request)
                if result.get("success") or result.get("channels_sent"):
                    sent_count += 1
                    details.append({"user_id": s.user_id, "status": "sent"})
                else:
                    skipped_count += 1
                    details.append({
                        "user_id": s.user_id,
                        "status": "skipped",
                        "reason": result.get("message", ""),
                    })
            except Exception as e:
                logger.error(f"发送通知失败 user={s.user_id}: {e}")
                failed_count += 1
                details.append({
                    "user_id": s.user_id,
                    "status": "failed",
                    "reason": str(e),
                })

        return {
            "ecn_id": ecn_id,
            "notification_type": notification_type,
            "total_recipients": len(stakeholders),
            "sent_count": sent_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
            "details": details,
        }

    def _build_notification_content(
        self, ecn: Ecn, notification_type: str, custom_message: Optional[str]
    ) -> tuple:
        """构建通知标题和内容"""
        type_labels = {
            "ECN_PUBLISHED": "ECN发布",
            "STATUS_CHANGE": "ECN状态变更",
            "DISPOSITION_UPDATE": "物料处置更新",
            "PROGRESS_MILESTONE": "执行进度里程碑",
        }
        label = type_labels.get(notification_type, "ECN通知")
        title = f"[{label}] {ecn.ecn_no} - {ecn.ecn_title}"

        if custom_message:
            content = custom_message
        else:
            content_map = {
                "ECN_PUBLISHED": f"设计变更 {ecn.ecn_no} 已发布，请关注影响范围并及时处理。",
                "STATUS_CHANGE": f"设计变更 {ecn.ecn_no} 状态已变更为 {ecn.status}。",
                "DISPOSITION_UPDATE": f"设计变更 {ecn.ecn_no} 中有物料处置方案更新，请查看。",
                "PROGRESS_MILESTONE": f"设计变更 {ecn.ecn_no} 执行进度有重要更新。",
            }
            content = content_map.get(
                notification_type,
                f"设计变更 {ecn.ecn_no} 有新的更新，请关注。",
            )

        return title, content

    # ==================== 5. 物料处置工作流 ====================

    def update_material_disposition(
        self,
        ecn_id: int,
        material_id: int,
        disposition: str,
        disposition_reason: str,
        disposition_cost: Decimal = Decimal("0"),
        remark: Optional[str] = None,
        current_user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """更新物料处置决策"""
        self._get_ecn_or_raise(ecn_id)

        # 查找处置记录（优先按affected_material_id匹配，再按material_id）
        record = (
            self.db.query(EcnMaterialDisposition)
            .filter(
                EcnMaterialDisposition.ecn_id == ecn_id,
                EcnMaterialDisposition.material_id == material_id,
            )
            .first()
        )

        if not record:
            raise ValueError(f"未找到ECN {ecn_id}中物料ID {material_id}的处置记录")

        # 更新处置决策
        record.disposition = disposition
        record.disposition_reason = disposition_reason
        record.disposition_cost = disposition_cost
        record.decided_by = current_user_id
        record.decided_at = datetime.now()
        record.status = "DECIDED"
        if remark:
            record.remark = remark

        # 计算实际损失
        if disposition == "SCRAP":
            record.actual_loss = record.potential_loss or Decimal("0")
        elif disposition == "REWORK":
            record.actual_loss = disposition_cost
        elif disposition == "RETURN":
            record.actual_loss = disposition_cost  # 退货可能有运费等
        else:  # CONTINUE_USE
            record.actual_loss = Decimal("0")

        # 同步更新受影响物料的处理状态
        if record.affected_material_id:
            am = (
                self.db.query(EcnAffectedMaterial)
                .filter(EcnAffectedMaterial.id == record.affected_material_id)
                .first()
            )
            if am:
                am.status = "PROCESSING"
                am.processed_at = datetime.now()

        # 更新执行进度
        self._update_disposition_phase_progress(ecn_id)

        self.db.commit()

        # 触发通知
        try:
            self.notify_stakeholders(
                ecn_id=ecn_id,
                notification_type="DISPOSITION_UPDATE",
                message=f"物料 {record.material_code} 处置方案已确定为：{disposition}",
                priority="NORMAL",
                current_user_id=current_user_id,
            )
        except Exception as e:
            logger.warning(f"处置通知发送失败: {e}")

        return {
            "id": record.id,
            "ecn_id": record.ecn_id,
            "material_code": record.material_code,
            "material_name": record.material_name,
            "specification": record.specification,
            "material_status": record.material_status,
            "affected_quantity": record.affected_quantity,
            "potential_loss": record.potential_loss,
            "disposition": record.disposition,
            "disposition_reason": record.disposition_reason,
            "disposition_cost": record.disposition_cost,
            "actual_loss": record.actual_loss,
            "status": record.status,
            "decided_by": record.decided_by,
            "decided_at": record.decided_at,
            "completed_at": record.completed_at,
            "purchase_order_no": record.purchase_order_no,
            "supplier_name": record.supplier_name,
        }

    def _update_disposition_phase_progress(self, ecn_id: int):
        """更新物料处理阶段的进度"""
        phase = (
            self.db.query(EcnExecutionProgress)
            .filter(
                EcnExecutionProgress.ecn_id == ecn_id,
                EcnExecutionProgress.phase == "MATERIAL_DISPOSITION",
            )
            .first()
        )

        if not phase:
            return

        total = (
            self.db.query(func.count(EcnMaterialDisposition.id))
            .filter(EcnMaterialDisposition.ecn_id == ecn_id)
            .scalar()
        ) or 0

        decided = (
            self.db.query(func.count(EcnMaterialDisposition.id))
            .filter(
                EcnMaterialDisposition.ecn_id == ecn_id,
                EcnMaterialDisposition.status.in_(["DECIDED", "IN_PROGRESS", "COMPLETED"]),
            )
            .scalar()
        ) or 0

        if total > 0:
            phase.progress_pct = (decided * 100) // total
            if phase.status == "PENDING" and decided > 0:
                phase.status = "IN_PROGRESS"
                phase.actual_start = datetime.now()
            if decided == total:
                phase.status = "COMPLETED"
                phase.actual_end = datetime.now()
                phase.progress_pct = 100

    # ==================== 工具方法 ====================

    def _get_ecn_or_raise(self, ecn_id: int) -> Ecn:
        """获取ECN，不存在则抛异常"""
        ecn = self.db.query(Ecn).filter(Ecn.id == ecn_id).first()
        if not ecn:
            raise ValueError(f"ECN {ecn_id} 不存在")
        return ecn
