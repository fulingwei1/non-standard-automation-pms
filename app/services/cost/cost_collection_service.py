# -*- coding: utf-8 -*-
"""
成本自动归集服务
负责从采购订单、外协订单、ECN变更等自动归集成本到项目成本
"""

import logging
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ecn import Ecn
from app.models.outsourcing import OutsourcingOrder, OutsourcingOrderItem
from app.models.project import Project, ProjectCost
from app.models.purchase import GoodsReceipt, PurchaseOrder
from app.services.cost.cost_basis import (
    COST_BASIS_ACTUAL as PROJECT_COST_BASIS_ACTUAL,
    COST_BASIS_PLAN as PROJECT_COST_BASIS_PLAN,
    actual_project_cost_filter,
)
from app.services.budget_alert_service import BudgetAlertService
from app.services.cost.cost_alert_service import CostAlertService  # noqa: F401 - legacy patch target
from app.utils.db_helpers import delete_obj


class CostCollectionService:
    """成本自动归集服务"""

    COST_BASIS_PLAN = PROJECT_COST_BASIS_PLAN
    COST_BASIS_ACTUAL = PROJECT_COST_BASIS_ACTUAL
    PURCHASE_COLLECTIBLE_STATUSES = (
        "RECEIVING",
        "PARTIAL_RECEIVED",
        "PARTIALLY_RECEIVED",
        "RECEIVED",
        "COMPLETED",
        "SHIPPED",
    )
    WORK_ORDER_COLLECTIBLE_STATUSES = ("COMPLETED", "DONE")
    TIMESHEET_COLLECTIBLE_STATUSES = ("APPROVED",)
    PURCHASE_CANCELLED_STATUSES = ("CANCELLED", "VOID", "DELETED", "REJECTED")
    COST_SOURCE_DEFAULTS = {
        "PURCHASE_ORDER": ("PURCHASE", "MATERIAL", "PURCHASE", PROJECT_COST_BASIS_ACTUAL),
        "OUTSOURCING_ORDER": (
            "OUTSOURCING",
            "OUTSOURCING",
            "OUTSOURCING",
            PROJECT_COST_BASIS_ACTUAL,
        ),
        "ECN": ("ECN", "CHANGE", "ECN", PROJECT_COST_BASIS_ACTUAL),
        "BOM_COST": ("BOM", "MATERIAL", "BOM", PROJECT_COST_BASIS_PLAN),
        "WORK_ORDER": ("PRODUCTION", "LABOR", "PRODUCTION", PROJECT_COST_BASIS_ACTUAL),
        "LABOR_COST": ("TIMESHEET", "LABOR", "LABOR", PROJECT_COST_BASIS_ACTUAL),
    }

    @staticmethod
    def _as_decimal(value: Any) -> Decimal:
        try:
            return Decimal(str(value or 0))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal("0")

    @staticmethod
    def _find_source_cost(
        db: Session,
        source_type: str,
        source_id: int,
        project_id: Optional[int] = None,
    ) -> Optional[ProjectCost]:
        """按来源类型和业务ID查找已归集成本，兼容旧接口的小写来源字段。"""
        conditions = [
            func.upper(ProjectCost.source_type) == source_type.upper(),
            ProjectCost.source_id == source_id,
        ]
        if project_id is not None:
            conditions.append(ProjectCost.project_id == project_id)
        return db.query(ProjectCost).filter(*conditions).first()

    @staticmethod
    def _purchase_order_status(order: PurchaseOrder) -> str:
        status = getattr(order, "status", None)
        return status.upper() if isinstance(status, str) else ""

    @staticmethod
    def _purchase_received_amount(order: PurchaseOrder) -> Decimal:
        received_amount = CostCollectionService._as_decimal(
            getattr(order, "received_amount", None)
        )
        if received_amount > 0:
            return received_amount
        status = CostCollectionService._purchase_order_status(order)
        if status in ("RECEIVING", "PARTIAL_RECEIVED", "PARTIALLY_RECEIVED"):
            return Decimal("0")
        return CostCollectionService._as_decimal(order.total_amount)

    @staticmethod
    def _purchase_tax_amount(order: PurchaseOrder, amount: Decimal) -> Decimal:
        tax_amount = CostCollectionService._as_decimal(order.tax_amount)
        total_amount = CostCollectionService._as_decimal(order.total_amount)
        if total_amount > 0 and amount > 0 and amount != total_amount:
            return (tax_amount * amount / total_amount).quantize(Decimal("0.01"))
        return tax_amount

    @staticmethod
    def _purchase_cost_date(
        db: Session, order: PurchaseOrder, explicit_cost_date: Optional[date]
    ) -> date:
        if explicit_cost_date:
            return explicit_cost_date
        latest_receipt_date = (
            db.query(func.max(GoodsReceipt.receipt_date))
            .filter(
                GoodsReceipt.order_id == order.id,
                GoodsReceipt.status.notin_(["CANCELLED", "VOID", "DELETED"]),
            )
            .scalar()
        )
        return latest_receipt_date or order.order_date or date.today()

    @staticmethod
    def _outsourcing_qualified_cost_basis(
        db: Session, order: OutsourcingOrder
    ) -> Optional[Dict[str, Decimal]]:
        """Return accepted outsourcing cost based on qualified inspection quantity.

        Returns None when item rows cannot be loaded, which keeps legacy mock-based tests
        and degraded callers on the previous order-total fallback.
        """
        if not isinstance(order, OutsourcingOrder):
            return None

        try:
            items = (
                db.query(OutsourcingOrderItem)
                .filter(OutsourcingOrderItem.order_id == order.id)
                .all()
            )
        except Exception:
            return None
        if not isinstance(items, list):
            return None

        total_order_qty = Decimal("0")
        total_qualified_qty = Decimal("0")
        accepted_amount = Decimal("0")

        for item in items:
            order_qty = CostCollectionService._as_decimal(item.quantity)
            qualified_qty = CostCollectionService._as_decimal(item.qualified_quantity)
            if order_qty > 0:
                qualified_qty = min(qualified_qty, order_qty)
            unit_price = CostCollectionService._as_decimal(item.unit_price)
            if unit_price <= 0 and order_qty > 0:
                unit_price = CostCollectionService._as_decimal(item.amount) / order_qty

            total_order_qty += order_qty
            total_qualified_qty += qualified_qty
            accepted_amount += qualified_qty * unit_price

        accepted_amount = accepted_amount.quantize(Decimal("0.01"))
        order_amount = CostCollectionService._as_decimal(order.total_amount)
        order_tax = CostCollectionService._as_decimal(order.tax_amount)
        if order_amount > 0 and accepted_amount > 0:
            tax_amount = (order_tax * accepted_amount / order_amount).quantize(Decimal("0.01"))
        else:
            tax_amount = Decimal("0.00")

        return {
            "amount": accepted_amount,
            "tax_amount": tax_amount,
            "qualified_quantity": total_qualified_qty,
            "order_quantity": total_order_qty,
        }

    @staticmethod
    def _work_order_hourly_rate(
        db: Session, work_order: Any, explicit_hourly_rate: Optional[Decimal]
    ) -> Optional[Decimal]:
        if explicit_hourly_rate is not None:
            return CostCollectionService._as_decimal(explicit_hourly_rate)
        if not getattr(work_order, "assigned_to", None):
            return None
        from app.models.production.worker import Worker

        worker_rate = (
            db.query(Worker.hourly_rate).filter(Worker.id == work_order.assigned_to).scalar()
        )
        rate = CostCollectionService._as_decimal(worker_rate)
        return rate if rate > 0 else None

    @staticmethod
    def _recalculate_project_actual_cost(db: Session, project_id: int) -> None:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return

        total = (
            db.query(func.coalesce(func.sum(ProjectCost.amount), Decimal("0")))
            .filter(
                ProjectCost.project_id == project_id,
                actual_project_cost_filter(),
            )
            .scalar()
        )
        try:
            project.actual_cost = Decimal(str(total or 0))
        except (InvalidOperation, TypeError, ValueError):
            costs = (
                db.query(ProjectCost)
                .filter(
                    ProjectCost.project_id == project_id, actual_project_cost_filter()
                )
                .all()
            )
            try:
                project.actual_cost = sum(
                    CostCollectionService._as_decimal(cost.amount) for cost in costs
                )
            except (InvalidOperation, TypeError, ValueError):
                return
        db.add(project)

    @staticmethod
    def _cost_item(cost: ProjectCost) -> Dict[str, Any]:
        return {
            "source": f"{cost.source_type}#{cost.source_no or cost.source_id}",
            "source_module": cost.source_module,
            "source_type": cost.source_type,
            "source_id": cost.source_id,
            "source_no": cost.source_no,
            "cost_basis": cost.cost_basis or CostCollectionService.COST_BASIS_ACTUAL,
            "project_id": cost.project_id,
            "amount": float(cost.amount or 0),
            "type": cost.cost_type,
        }

    @staticmethod
    def _check_budget_alert(
        db: Session, project_id: int, trigger_source: str, source_id: int
    ) -> None:
        try:
            BudgetAlertService(db).check_and_alert(
                project_id=project_id,
                trigger_source=trigger_source,
                source_id=source_id,
            )
        except Exception as e:
            logging.warning(f"成本预警检查失败：{str(e)}")

    @staticmethod
    def _delete_cost_and_recalculate(
        db: Session, cost: ProjectCost, fallback_project_id: Optional[int] = None
    ) -> None:
        project_id = cost.project_id or fallback_project_id
        db.delete(cost)
        db.flush()
        if project_id:
            CostCollectionService._recalculate_project_actual_cost(db, project_id)

    @staticmethod
    def normalize_project_cost_records(
        db: Session, project_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        修复历史 project_costs 空口径字段，并按 ACTUAL/PLAN 口径重算项目实际成本。
        """
        query = db.query(ProjectCost)
        if project_id:
            query = query.filter(ProjectCost.project_id == project_id)

        updated = 0
        affected_project_ids: set[int] = set()
        for cost in query.all():
            source_type = str(cost.source_type or "").upper()
            defaults = CostCollectionService.COST_SOURCE_DEFAULTS.get(source_type)
            if not defaults:
                continue

            source_module, cost_type, cost_category, cost_basis = defaults
            changed = False
            if not cost.source_module:
                cost.source_module = source_module
                changed = True
            if not cost.cost_type:
                cost.cost_type = cost_type
                changed = True
            if not cost.cost_category:
                cost.cost_category = cost_category
                changed = True
            if not cost.cost_basis or (
                source_type == "BOM_COST" and cost.cost_basis != cost_basis
            ):
                cost.cost_basis = cost_basis
                changed = True

            if changed:
                db.add(cost)
                updated += 1
                if cost.project_id:
                    affected_project_ids.add(cost.project_id)

        if updated:
            db.flush()
            for affected_project_id in affected_project_ids:
                CostCollectionService._recalculate_project_actual_cost(
                    db, affected_project_id
                )

        return {
            "scanned": query.count(),
            "updated": updated,
            "affected_projects": len(affected_project_ids),
        }

    @staticmethod
    def collect_from_purchase_order(
        db: Session,
        order_id: int,
        created_by: Optional[int] = None,
        cost_date: Optional[date] = None,
    ) -> Optional[ProjectCost]:
        """
        从采购订单归集成本

        Args:
            db: 数据库会话
            order_id: 采购订单ID
            created_by: 创建人ID
            cost_date: 成本发生日期（默认使用订单日期）

        Returns:
            创建的项目成本记录，如果订单没有关联项目则返回None
        """
        order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
        if not order:
            return None

        # 检查是否已归集过
        existing_cost = CostCollectionService._find_source_cost(
            db, "PURCHASE_ORDER", order_id, order.project_id
        )
        order_status = CostCollectionService._purchase_order_status(order)
        if (
            order_status
            and order_status not in CostCollectionService.PURCHASE_COLLECTIBLE_STATUSES
        ):
            if existing_cost:
                CostCollectionService._delete_cost_and_recalculate(
                    db, existing_cost, order.project_id
                )
            return None

        amount = CostCollectionService._purchase_received_amount(order)
        if amount <= 0:
            if existing_cost:
                CostCollectionService._delete_cost_and_recalculate(
                    db, existing_cost, order.project_id
                )
            return None

        tax_amount = CostCollectionService._purchase_tax_amount(order, amount)
        effective_cost_date = CostCollectionService._purchase_cost_date(
            db, order, cost_date
        )

        if existing_cost:
            # 更新现有成本记录
            existing_cost.project_id = order.project_id or existing_cost.project_id
            existing_cost.cost_type = "MATERIAL"
            existing_cost.cost_category = "PURCHASE"
            existing_cost.cost_basis = CostCollectionService.COST_BASIS_ACTUAL
            existing_cost.source_module = "PURCHASE"
            existing_cost.source_type = "PURCHASE_ORDER"
            existing_cost.source_no = order.order_no
            existing_cost.amount = amount
            existing_cost.tax_amount = tax_amount
            existing_cost.cost_date = effective_cost_date
            existing_cost.description = (
                f"采购订单：{order.order_title or order.order_no}"
            )
            if created_by is not None:
                existing_cost.created_by = created_by
            db.add(existing_cost)
            if order.project_id:
                db.flush()
                CostCollectionService._recalculate_project_actual_cost(
                    db, order.project_id
                )

            return existing_cost

        # 如果没有关联项目，不创建成本记录
        if not order.project_id:
            return None

        # 创建新的成本记录
        cost = ProjectCost(
            project_id=order.project_id,
            cost_type="MATERIAL",  # 材料成本
            cost_category="PURCHASE",  # 采购
            cost_basis=CostCollectionService.COST_BASIS_ACTUAL,
            source_module="PURCHASE",
            source_type="PURCHASE_ORDER",
            source_id=order_id,
            source_no=order.order_no,
            amount=amount,
            tax_amount=tax_amount,
            cost_date=effective_cost_date,
            description=f"采购订单：{order.order_title or order.order_no}",
            created_by=created_by,
        )
        db.add(cost)
        db.flush()
        CostCollectionService._recalculate_project_actual_cost(db, order.project_id)

        # 检查预算执行情况并生成预警
        CostCollectionService._check_budget_alert(
            db, order.project_id, trigger_source="PURCHASE", source_id=order_id
        )

        return cost

    @staticmethod
    def collect_from_outsourcing_order(
        db: Session,
        order_id: int,
        created_by: Optional[int] = None,
        cost_date: Optional[date] = None,
    ) -> Optional[ProjectCost]:
        """
        从外协订单归集成本

        Args:
            db: 数据库会话
            order_id: 外协订单ID
            created_by: 创建人ID
            cost_date: 成本发生日期（默认使用订单日期）

        Returns:
            创建的项目成本记录，如果订单没有关联项目则返回None
        """
        order = (
            db.query(OutsourcingOrder).filter(OutsourcingOrder.id == order_id).first()
        )
        if not order:
            return None

        qualified_basis = CostCollectionService._outsourcing_qualified_cost_basis(db, order)
        if qualified_basis is None:
            cost_amount = CostCollectionService._as_decimal(order.total_amount)
            tax_amount = CostCollectionService._as_decimal(order.tax_amount)
            qualified_note = ""
        else:
            cost_amount = qualified_basis["amount"]
            tax_amount = qualified_basis["tax_amount"]
            qualified_note = (
                f"（合格数量：{qualified_basis['qualified_quantity']}/"
                f"{qualified_basis['order_quantity']}）"
            )

        # 检查是否已归集过
        existing_cost = (
            db.query(ProjectCost)
            .filter(
                ProjectCost.source_module == "OUTSOURCING",
                ProjectCost.source_type == "OUTSOURCING_ORDER",
                ProjectCost.source_id == order_id,
            )
            .first()
        )

        if qualified_basis is not None and cost_amount <= 0:
            if existing_cost:
                CostCollectionService._delete_cost_and_recalculate(
                    db, existing_cost, order.project_id
                )
            return None

        if existing_cost:
            # 更新现有成本记录
            existing_cost.amount = cost_amount
            existing_cost.tax_amount = tax_amount
            existing_cost.cost_basis = CostCollectionService.COST_BASIS_ACTUAL
            existing_cost.cost_date = cost_date or (
                order.created_at.date() if order.created_at else date.today()
            )
            existing_cost.description = (
                f"外协订单：{order.order_title or order.order_no}{qualified_note}"
            )
            if created_by:
                existing_cost.created_by = created_by
            db.add(existing_cost)
            if order.project_id:
                db.flush()
                CostCollectionService._recalculate_project_actual_cost(
                    db, order.project_id
                )

            return existing_cost

        # 如果没有关联项目，不创建成本记录
        if not order.project_id:
            return None

        # 创建新的成本记录
        cost = ProjectCost(
            project_id=order.project_id,
            machine_id=order.machine_id,
            cost_type="OUTSOURCING",  # 外协成本
            cost_category="OUTSOURCING",  # 外协
            cost_basis=CostCollectionService.COST_BASIS_ACTUAL,
            source_module="OUTSOURCING",
            source_type="OUTSOURCING_ORDER",
            source_id=order_id,
            source_no=order.order_no,
            amount=cost_amount,
            tax_amount=tax_amount,
            cost_date=cost_date
            or (order.created_at.date() if order.created_at else date.today()),
            description=f"外协订单：{order.order_title or order.order_no}{qualified_note}",
            created_by=created_by,
        )
        db.add(cost)
        db.flush()
        CostCollectionService._recalculate_project_actual_cost(db, order.project_id)

        # 检查预算执行情况并生成预警
        CostCollectionService._check_budget_alert(
            db, order.project_id, trigger_source="OUTSOURCING", source_id=order_id
        )

        return cost

    @staticmethod
    def collect_from_ecn(
        db: Session,
        ecn_id: int,
        created_by: Optional[int] = None,
        cost_date: Optional[date] = None,
    ) -> Optional[ProjectCost]:
        """
        从ECN变更归集成本（变更成本独立核算）

        Args:
            db: 数据库会话
            ecn_id: ECN ID
            created_by: 创建人ID
            cost_date: 成本发生日期（默认使用当前日期）

        Returns:
            创建的项目成本记录，如果ECN没有成本影响或没有关联项目则返回None
        """
        ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
        if not ecn:
            return None

        # 检查是否已归集过
        existing_cost = (
            db.query(ProjectCost)
            .filter(
                ProjectCost.source_module == "ECN",
                ProjectCost.source_type == "ECN",
                ProjectCost.source_id == ecn_id,
            )
            .first()
        )
        cost_impact = CostCollectionService._as_decimal(ecn.cost_impact)

        # 如果没有成本影响，不保留历史成本记录
        if cost_impact == 0:
            if existing_cost:
                CostCollectionService._delete_cost_and_recalculate(
                    db, existing_cost, ecn.project_id
                )
            return None

        # 如果没有关联项目，不创建成本记录；已有脏记录也一并清掉。
        if not ecn.project_id:
            if existing_cost:
                CostCollectionService._delete_cost_and_recalculate(
                    db, existing_cost, None
                )
            return None

        if existing_cost:
            # 更新现有成本记录
            existing_cost.project_id = ecn.project_id
            existing_cost.amount = cost_impact
            existing_cost.cost_basis = CostCollectionService.COST_BASIS_ACTUAL
            existing_cost.cost_date = cost_date or date.today()
            if created_by:
                existing_cost.created_by = created_by
            db.add(existing_cost)
            if ecn.project_id:
                db.flush()
                CostCollectionService._recalculate_project_actual_cost(
                    db, ecn.project_id
                )

            return existing_cost

        # 创建新的成本记录（变更成本独立核算）
        cost = ProjectCost(
            project_id=ecn.project_id,
            machine_id=ecn.machine_id,
            cost_type="CHANGE",  # 变更成本
            cost_category="ECN",  # ECN变更
            cost_basis=CostCollectionService.COST_BASIS_ACTUAL,
            source_module="ECN",
            source_type="ECN",
            source_id=ecn_id,
            source_no=ecn.ecn_no,
            amount=cost_impact,
            tax_amount=Decimal("0"),  # 变更成本通常不含税
            cost_date=cost_date or date.today(),
            description=f"ECN变更成本：{ecn.ecn_title}",
            created_by=created_by,
        )
        db.add(cost)
        db.flush()
        CostCollectionService._recalculate_project_actual_cost(db, ecn.project_id)

        # 成本增加才需要预算超支预警；负向变更是冲减。
        if cost_impact > 0:
            CostCollectionService._check_budget_alert(
                db, ecn.project_id, trigger_source="ECN", source_id=ecn_id
            )

        return cost

    @staticmethod
    def remove_cost_from_source(
        db: Session, source_module: str, source_type: str, source_id: int
    ) -> bool:
        """
        删除指定来源的成本记录（用于订单取消等情况）

        Args:
            db: 数据库会话
            source_module: 来源模块
            source_type: 来源类型
            source_id: 来源ID

        Returns:
            是否成功删除
        """
        cost = (
            db.query(ProjectCost)
            .filter(
                ProjectCost.source_module == source_module,
                ProjectCost.source_type == source_type,
                ProjectCost.source_id == source_id,
            )
            .first()
        )

        if not cost:
            return False

        project_id = cost.project_id

        # 删除成本记录
        db.delete(cost)
        db.flush()

        # 删除 PLAN 成本也不应该影响项目实际成本，统一按 ACTUAL 口径重算。
        if project_id:
            CostCollectionService._recalculate_project_actual_cost(db, project_id)

        return True

    @staticmethod
    def collect_from_bom(
        db: Session,
        bom_id: int,
        created_by: Optional[int] = None,
        cost_date: Optional[date] = None,
    ) -> Optional[ProjectCost]:
        """
        从BOM归集材料成本

        Args:
            db: 数据库会话
            bom_id: BOM ID
            created_by: 创建人ID
            cost_date: 成本日期（默认今天）

        Returns:
            创建或更新的项目成本记录
        """
        from app.models.material import BomHeader, BomItem

        bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
        if not bom:
            raise ValueError("BOM不存在")

        if not bom.project_id:
            raise ValueError("BOM未关联项目，无法归集成本")

        # 只归集已发布的BOM
        if bom.status != "RELEASED":
            raise ValueError("只有已发布的BOM才能归集成本")

        # 检查是否已存在该BOM的成本记录
        existing_cost = CostCollectionService._find_source_cost(
            db, "BOM_COST", bom_id, bom.project_id
        )

        # 计算BOM总成本
        bom_items = db.query(BomItem).filter(BomItem.bom_id == bom_id).all()
        total_amount = sum([float(item.amount or 0) for item in bom_items])

        if total_amount <= 0:
            # 如果BOM总成本为0，不创建成本记录
            if existing_cost:
                # 删除已存在的成本记录
                delete_obj(db, existing_cost)
                db.flush()
                CostCollectionService._recalculate_project_actual_cost(
                    db, bom.project_id
                )
            return None

        # 使用BOM的总金额（如果BOM表头有total_amount字段）
        if bom.total_amount and bom.total_amount > 0:
            total_amount = float(bom.total_amount)

        if existing_cost:
            # 更新现有成本记录
            existing_cost.project_id = bom.project_id
            existing_cost.machine_id = bom.machine_id
            existing_cost.cost_type = "MATERIAL"
            existing_cost.cost_category = "BOM"
            existing_cost.cost_basis = CostCollectionService.COST_BASIS_PLAN
            existing_cost.source_module = "BOM"
            existing_cost.source_type = "BOM_COST"
            existing_cost.source_no = bom.bom_no
            existing_cost.amount = Decimal(str(total_amount))
            existing_cost.cost_date = cost_date or date.today()
            existing_cost.description = f"BOM材料成本：{bom.bom_name}（{bom.bom_no}）"
            if created_by is not None:
                existing_cost.created_by = created_by

            db.add(existing_cost)
            db.flush()
            CostCollectionService._recalculate_project_actual_cost(db, bom.project_id)
            return existing_cost
        else:
            # 创建新的成本记录
            cost = ProjectCost(
                project_id=bom.project_id,
                machine_id=bom.machine_id,
                cost_type="MATERIAL",
                cost_category="BOM",
                cost_basis=CostCollectionService.COST_BASIS_PLAN,
                source_module="BOM",
                source_type="BOM_COST",
                source_id=bom_id,
                source_no=bom.bom_no,
                amount=Decimal(str(total_amount)),
                cost_date=cost_date or date.today(),
                description=f"BOM材料成本：{bom.bom_name}（{bom.bom_no}）",
                created_by=created_by,
            )
            db.add(cost)

            # BOM 是计划/估算成本，不计入项目实际成本。
            db.flush()
            CostCollectionService._recalculate_project_actual_cost(db, bom.project_id)

            # 检查预算执行情况并推送预警
            CostCollectionService._check_budget_alert(
                db, bom.project_id, trigger_source="BOM", source_id=bom_id
            )

            return cost

    @staticmethod
    def collect_from_work_order(
        db: Session,
        work_order_id: int,
        created_by: Optional[int] = None,
        cost_date: Optional[date] = None,
        hourly_rate: Optional[Decimal] = None,
    ) -> Optional[ProjectCost]:
        """
        从生产工单归集人工/加工成本。

        工单没有直接金额字段，按实际工时优先、标准工时兜底，并使用默认加工时薪估算。
        """
        from app.models.production.work_order import WorkOrder

        work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
        if not work_order or not work_order.project_id:
            return None

        existing_cost = CostCollectionService._find_source_cost(
            db, "WORK_ORDER", work_order_id, work_order.project_id
        )
        if work_order.status not in CostCollectionService.WORK_ORDER_COLLECTIBLE_STATUSES:
            if existing_cost:
                db.delete(existing_cost)
                db.flush()
                CostCollectionService._recalculate_project_actual_cost(
                    db, work_order.project_id
                )
            return None

        hours = CostCollectionService._as_decimal(
            work_order.actual_hours or work_order.standard_hours or 0
        )

        if hours <= 0:
            if existing_cost:
                db.delete(existing_cost)
                db.flush()
                CostCollectionService._recalculate_project_actual_cost(
                    db, work_order.project_id
                )
            return None

        rate = CostCollectionService._work_order_hourly_rate(db, work_order, hourly_rate)
        if not rate:
            if existing_cost:
                db.delete(existing_cost)
                db.flush()
                CostCollectionService._recalculate_project_actual_cost(
                    db, work_order.project_id
                )
            return None

        amount = (hours * rate).quantize(Decimal("0.01"))
        task_type = work_order.task_type or "PRODUCTION"
        cost_type = (
            "OUTSOURCING" if task_type in ("OUTSOURCE", "SUBCONTRACT") else "LABOR"
        )
        effective_date = (
            cost_date
            or (
                work_order.actual_end_time.date()
                if work_order.actual_end_time
                else None
            )
            or work_order.plan_end_date
            or date.today()
        )

        if existing_cost:
            cost = existing_cost
            cost.project_id = work_order.project_id
            cost.machine_id = work_order.machine_id
            cost.cost_type = cost_type
            cost.cost_category = task_type
            cost.cost_basis = CostCollectionService.COST_BASIS_ACTUAL
            cost.source_module = "PRODUCTION"
            cost.source_type = "WORK_ORDER"
            cost.source_id = work_order_id
            cost.source_no = work_order.work_order_no
            cost.amount = amount
            cost.tax_amount = Decimal("0")
            cost.cost_date = effective_date
            cost.description = (
                f"生产工单：{work_order.task_name or work_order.work_order_no}，"
                f"工时：{hours}小时"
            )
            if created_by is not None:
                cost.created_by = created_by
        else:
            cost = ProjectCost(
                project_id=work_order.project_id,
                machine_id=work_order.machine_id,
                cost_type=cost_type,
                cost_category=task_type,
                cost_basis=CostCollectionService.COST_BASIS_ACTUAL,
                source_module="PRODUCTION",
                source_type="WORK_ORDER",
                source_id=work_order_id,
                source_no=work_order.work_order_no,
                amount=amount,
                tax_amount=Decimal("0"),
                cost_date=effective_date,
                description=(
                    f"生产工单：{work_order.task_name or work_order.work_order_no}，"
                    f"工时：{hours}小时"
                ),
                created_by=created_by,
            )

        db.add(cost)
        db.flush()
        CostCollectionService._recalculate_project_actual_cost(
            db, work_order.project_id
        )
        CostCollectionService._check_budget_alert(
            db,
            work_order.project_id,
            trigger_source="WORK_ORDER",
            source_id=work_order_id,
        )
        return cost

    @staticmethod
    def collect_from_timesheets(
        db: Session,
        project_id: int,
        created_by: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        recalculate: bool = False,
    ) -> Dict[str, Any]:
        """从已审批工时按项目+人员汇总人工成本。"""
        from app.models.timesheet import Timesheet
        from app.services.hourly_rate_service import HourlyRateService

        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {
                "costs": [],
                "total_amount": Decimal("0"),
                "total_hours": Decimal("0"),
            }

        if recalculate:
            existing_costs = (
                db.query(ProjectCost)
                .filter(
                    ProjectCost.project_id == project_id,
                    func.upper(ProjectCost.source_type) == "LABOR_COST",
                )
                .all()
            )
            for cost in existing_costs:
                db.delete(cost)
            db.flush()

        query = db.query(Timesheet).filter(
            Timesheet.project_id == project_id,
            Timesheet.status.in_(CostCollectionService.TIMESHEET_COLLECTIBLE_STATUSES),
        )
        if start_date:
            query = query.filter(Timesheet.work_date >= start_date)
        if end_date:
            query = query.filter(Timesheet.work_date <= end_date)

        grouped: Dict[int, Dict[str, Any]] = {}
        for timesheet in query.all():
            hours = CostCollectionService._as_decimal(timesheet.hours)
            if hours <= 0:
                continue
            user_data = grouped.setdefault(
                timesheet.user_id,
                {
                    "user_id": timesheet.user_id,
                    "user_name": timesheet.user_name,
                    "hours": Decimal("0"),
                    "latest_date": timesheet.work_date,
                },
            )
            user_data["hours"] += hours
            if timesheet.work_date and (
                not user_data["latest_date"]
                or timesheet.work_date > user_data["latest_date"]
            ):
                user_data["latest_date"] = timesheet.work_date

        costs: List[ProjectCost] = []
        total_amount = Decimal("0")
        total_hours = Decimal("0")

        for user_id, user_data in grouped.items():
            work_date = end_date or user_data["latest_date"] or date.today()
            hourly_rate = HourlyRateService.get_user_hourly_rate(db, user_id, work_date)
            amount = (user_data["hours"] * hourly_rate).quantize(Decimal("0.01"))
            total_amount += amount
            total_hours += user_data["hours"]

            existing_cost = None
            if not recalculate:
                existing_cost = CostCollectionService._find_source_cost(
                    db, "LABOR_COST", user_id, project_id
                )

            if existing_cost:
                cost = existing_cost
                cost.project_id = project_id
                cost.cost_type = "LABOR"
                cost.cost_category = "LABOR"
                cost.cost_basis = CostCollectionService.COST_BASIS_ACTUAL
                cost.source_module = "TIMESHEET"
                cost.source_type = "LABOR_COST"
                cost.source_id = user_id
                cost.source_no = f"LABOR-{user_id}"
                cost.amount = amount
                cost.tax_amount = Decimal("0")
                cost.cost_date = work_date
                cost.description = (
                    f"人工成本：{user_data['user_name'] or user_id}，"
                    f"工时：{user_data['hours']}小时"
                )
                if created_by is not None:
                    cost.created_by = created_by
            else:
                cost = ProjectCost(
                    project_id=project_id,
                    cost_type="LABOR",
                    cost_category="LABOR",
                    cost_basis=CostCollectionService.COST_BASIS_ACTUAL,
                    source_module="TIMESHEET",
                    source_type="LABOR_COST",
                    source_id=user_id,
                    source_no=f"LABOR-{user_id}",
                    amount=amount,
                    tax_amount=Decimal("0"),
                    cost_date=work_date,
                    description=(
                        f"人工成本：{user_data['user_name'] or user_id}，"
                        f"工时：{user_data['hours']}小时"
                    ),
                    created_by=created_by,
                )

            db.add(cost)
            costs.append(cost)
            CostCollectionService._check_budget_alert(
                db, project_id, trigger_source="TIMESHEET", source_id=user_id
            )

        if costs or recalculate:
            db.flush()
            CostCollectionService._recalculate_project_actual_cost(db, project_id)

        return {
            "costs": costs,
            "total_amount": total_amount,
            "total_hours": total_hours,
        }

    @staticmethod
    def collect_project_costs(
        db: Session,
        project_id: Optional[int] = None,
        created_by: Optional[int] = None,
    ) -> Dict[str, Any]:
        """批量扫描业务单据并归集到 project_costs。"""
        from app.models.material import BomHeader
        from app.models.production.work_order import WorkOrder
        from app.models.timesheet import Timesheet

        results: List[Dict[str, Any]] = []
        collected_costs: List[ProjectCost] = []
        normalization = CostCollectionService.normalize_project_cost_records(
            db, project_id=project_id
        )

        purchase_query = db.query(PurchaseOrder).filter(
            PurchaseOrder.project_id.isnot(None),
            PurchaseOrder.status.in_(
                CostCollectionService.PURCHASE_COLLECTIBLE_STATUSES
            ),
            PurchaseOrder.total_amount > 0,
        )
        if project_id:
            purchase_query = purchase_query.filter(
                PurchaseOrder.project_id == project_id
            )

        purchase_costs = []
        for order in purchase_query.all():
            cost = CostCollectionService.collect_from_purchase_order(
                db, order.id, created_by=created_by
            )
            if cost:
                purchase_costs.append(cost)
        results.append(
            {
                "source": "purchase_orders",
                "collected": len(purchase_costs),
                "items": [
                    CostCollectionService._cost_item(cost) for cost in purchase_costs
                ],
            }
        )
        collected_costs.extend(purchase_costs)

        bom_query = db.query(BomHeader).filter(
            BomHeader.project_id.isnot(None),
            BomHeader.status == "RELEASED",
        )
        if project_id:
            bom_query = bom_query.filter(BomHeader.project_id == project_id)

        bom_costs = []
        for bom in bom_query.all():
            cost = CostCollectionService.collect_from_bom(
                db, bom.id, created_by=created_by
            )
            if cost:
                bom_costs.append(cost)
        results.append(
            {
                "source": "bom_headers",
                "collected": len(bom_costs),
                "items": [CostCollectionService._cost_item(cost) for cost in bom_costs],
            }
        )
        collected_costs.extend(bom_costs)

        work_order_query = db.query(WorkOrder).filter(
            WorkOrder.project_id.isnot(None),
            WorkOrder.status.in_(CostCollectionService.WORK_ORDER_COLLECTIBLE_STATUSES),
        )
        if project_id:
            work_order_query = work_order_query.filter(
                WorkOrder.project_id == project_id
            )

        work_order_costs = []
        for work_order in work_order_query.all():
            cost = CostCollectionService.collect_from_work_order(
                db, work_order.id, created_by=created_by
            )
            if cost:
                work_order_costs.append(cost)
        results.append(
            {
                "source": "work_orders",
                "collected": len(work_order_costs),
                "items": [
                    CostCollectionService._cost_item(cost) for cost in work_order_costs
                ],
            }
        )
        collected_costs.extend(work_order_costs)

        timesheet_projects_query = (
            db.query(Timesheet.project_id)
            .filter(
                Timesheet.project_id.isnot(None),
                Timesheet.status.in_(
                    CostCollectionService.TIMESHEET_COLLECTIBLE_STATUSES
                ),
            )
            .distinct()
        )
        if project_id:
            timesheet_projects_query = timesheet_projects_query.filter(
                Timesheet.project_id == project_id
            )

        timesheet_costs = []
        for (ts_project_id,) in timesheet_projects_query.all():
            labor_result = CostCollectionService.collect_from_timesheets(
                db, ts_project_id, created_by=created_by
            )
            timesheet_costs.extend(labor_result["costs"])
        results.append(
            {
                "source": "timesheets",
                "collected": len(timesheet_costs),
                "items": [
                    CostCollectionService._cost_item(cost) for cost in timesheet_costs
                ],
            }
        )
        collected_costs.extend(timesheet_costs)

        db.flush()
        affected_project_ids = {
            cost.project_id for cost in collected_costs if cost.project_id
        }
        for affected_project_id in affected_project_ids:
            CostCollectionService._recalculate_project_actual_cost(
                db, affected_project_id
            )

        total_amount = sum(float(cost.amount or 0) for cost in collected_costs)
        actual_amount = sum(
            float(cost.amount or 0)
            for cost in collected_costs
            if (cost.cost_basis or CostCollectionService.COST_BASIS_ACTUAL)
            == CostCollectionService.COST_BASIS_ACTUAL
        )
        plan_amount = total_amount - actual_amount
        return {
            "message": (
                f"成本归集完成：{len(collected_costs)}条记录，合计¥{total_amount:,.2f}"
            ),
            "total_collected": len(collected_costs),
            "total_amount": round(total_amount, 2),
            "actual_amount": round(actual_amount, 2),
            "plan_amount": round(plan_amount, 2),
            "normalized_cost_records": normalization,
            "details": results,
        }
