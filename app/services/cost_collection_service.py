# -*- coding: utf-8 -*-
"""
成本自动归集服务
负责从采购订单、外协订单、ECN变更等自动归集成本到项目成本
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.ecn import Ecn
from app.models.outsourcing import OutsourcingOrder
from app.models.project import Project, ProjectCost
from app.models.purchase import PurchaseOrder
from app.services.cost_alert_service import CostAlertService


class CostCollectionService:
    """成本自动归集服务"""

    @staticmethod
    def collect_from_purchase_order(
        db: Session,
        order_id: int,
        created_by: Optional[int] = None,
        cost_date: Optional[date] = None
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
        existing_cost = db.query(ProjectCost).filter(
            ProjectCost.source_module == "PURCHASE",
            ProjectCost.source_type == "PURCHASE_ORDER",
            ProjectCost.source_id == order_id
        ).first()

        if existing_cost:
            # 更新现有成本记录
            existing_cost.amount = order.total_amount or Decimal("0")
            existing_cost.tax_amount = order.tax_amount or Decimal("0")
            existing_cost.cost_date = cost_date or (order.created_at.date() if order.created_at else date.today())
            if created_by:
                existing_cost.created_by = created_by
            db.add(existing_cost)

            # 更新项目实际成本
            if order.project_id:
                project = db.query(Project).filter(Project.id == order.project_id).first()
                if project:
                    # 重新计算项目成本
                    project_costs = db.query(ProjectCost).filter(
                        ProjectCost.project_id == order.project_id
                    ).all()
                    project.actual_cost = sum([float(c.amount or 0) for c in project_costs])
                    db.add(project)

            return existing_cost

        # 如果没有关联项目，不创建成本记录
        if not order.project_id:
            return None

        # 创建新的成本记录
        cost = ProjectCost(
            project_id=order.project_id,
            cost_type="MATERIAL",  # 材料成本
            cost_category="PURCHASE",  # 采购
            source_module="PURCHASE",
            source_type="PURCHASE_ORDER",
            source_id=order_id,
            source_no=order.order_no,
            amount=order.total_amount or Decimal("0"),
            tax_amount=order.tax_amount or Decimal("0"),
            cost_date=cost_date or order.order_date or date.today(),
            description=f"采购订单：{order.order_title or order.order_no}",
            created_by=created_by
        )
        db.add(cost)

        # 更新项目实际成本
        project = db.query(Project).filter(Project.id == order.project_id).first()
        if project:
            project.actual_cost = (project.actual_cost or 0) + float(cost.amount)
            db.add(project)

        # 检查预算执行情况并生成预警
        try:
            CostAlertService.check_budget_execution(
                db, order.project_id, trigger_source="PURCHASE", source_id=order_id
            )
        except Exception as e:
            # 预警失败不影响成本归集
            logging.warning(f"成本预警检查失败：{str(e)}")

        return cost

    @staticmethod
    def collect_from_outsourcing_order(
        db: Session,
        order_id: int,
        created_by: Optional[int] = None,
        cost_date: Optional[date] = None
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
        order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == order_id).first()
        if not order:
            return None

        # 检查是否已归集过
        existing_cost = db.query(ProjectCost).filter(
            ProjectCost.source_module == "OUTSOURCING",
            ProjectCost.source_type == "OUTSOURCING_ORDER",
            ProjectCost.source_id == order_id
        ).first()

        if existing_cost:
            # 更新现有成本记录
            existing_cost.amount = order.total_amount or Decimal("0")
            existing_cost.tax_amount = order.tax_amount or Decimal("0")
            existing_cost.cost_date = cost_date or (order.created_at.date() if order.created_at else date.today())
            if created_by:
                existing_cost.created_by = created_by
            db.add(existing_cost)

            # 更新项目实际成本
            if order.project_id:
                project = db.query(Project).filter(Project.id == order.project_id).first()
                if project:
                    # 重新计算项目成本
                    project_costs = db.query(ProjectCost).filter(
                        ProjectCost.project_id == order.project_id
                    ).all()
                    project.actual_cost = sum([float(c.amount or 0) for c in project_costs])
                    db.add(project)

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
            source_module="OUTSOURCING",
            source_type="OUTSOURCING_ORDER",
            source_id=order_id,
            source_no=order.order_no,
            amount=order.total_amount or Decimal("0"),
            tax_amount=order.tax_amount or Decimal("0"),
            cost_date=cost_date or (order.created_at.date() if order.created_at else date.today()),
            description=f"外协订单：{order.order_title or order.order_no}",
            created_by=created_by
        )
        db.add(cost)

        # 更新项目实际成本
        project = db.query(Project).filter(Project.id == order.project_id).first()
        if project:
            project.actual_cost = (project.actual_cost or 0) + float(cost.amount)
            db.add(project)

        # 检查预算执行情况并生成预警
        try:
            CostAlertService.check_budget_execution(
                db, order.project_id, trigger_source="PURCHASE", source_id=order_id
            )
        except Exception as e:
            # 预警失败不影响成本归集
            logging.warning(f"成本预警检查失败：{str(e)}")

        return cost

    @staticmethod
    def collect_from_ecn(
        db: Session,
        ecn_id: int,
        created_by: Optional[int] = None,
        cost_date: Optional[date] = None
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

        # 如果没有成本影响，不创建成本记录
        cost_impact = ecn.cost_impact or Decimal("0")
        if cost_impact <= 0:
            return None

        # 检查是否已归集过
        existing_cost = db.query(ProjectCost).filter(
            ProjectCost.source_module == "ECN",
            ProjectCost.source_type == "ECN",
            ProjectCost.source_id == ecn_id
        ).first()

        if existing_cost:
            # 更新现有成本记录
            existing_cost.amount = cost_impact
            existing_cost.cost_date = cost_date or date.today()
            if created_by:
                existing_cost.created_by = created_by
            db.add(existing_cost)

            # 更新项目实际成本
            if ecn.project_id:
                project = db.query(Project).filter(Project.id == ecn.project_id).first()
                if project:
                    # 重新计算项目成本
                    project_costs = db.query(ProjectCost).filter(
                        ProjectCost.project_id == ecn.project_id
                    ).all()
                    project.actual_cost = sum([float(c.amount or 0) for c in project_costs])
                    db.add(project)

            return existing_cost

        # 如果没有关联项目，不创建成本记录
        if not ecn.project_id:
            return None

        # 创建新的成本记录（变更成本独立核算）
        cost = ProjectCost(
            project_id=ecn.project_id,
            machine_id=ecn.machine_id,
            cost_type="CHANGE",  # 变更成本
            cost_category="ECN",  # ECN变更
            source_module="ECN",
            source_type="ECN",
            source_id=ecn_id,
            source_no=ecn.ecn_no,
            amount=cost_impact,
            tax_amount=Decimal("0"),  # 变更成本通常不含税
            cost_date=cost_date or date.today(),
            description=f"ECN变更成本：{ecn.ecn_title}",
            created_by=created_by
        )
        db.add(cost)

        # 更新项目实际成本
        project = db.query(Project).filter(Project.id == ecn.project_id).first()
        if project:
            project.actual_cost = (project.actual_cost or 0) + float(cost.amount)
            db.add(project)

        # 检查预算执行情况并生成预警
        try:
            CostAlertService.check_budget_execution(
                db, ecn.project_id, trigger_source="ECN", source_id=ecn_id
            )
        except Exception as e:
            # 预警失败不影响成本归集
            logging.warning(f"成本预警检查失败：{str(e)}")

        return cost

    @staticmethod
    def remove_cost_from_source(
        db: Session,
        source_module: str,
        source_type: str,
        source_id: int
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
        cost = db.query(ProjectCost).filter(
            ProjectCost.source_module == source_module,
            ProjectCost.source_type == source_type,
            ProjectCost.source_id == source_id
        ).first()

        if not cost:
            return False

        project_id = cost.project_id
        amount = cost.amount

        # 删除成本记录
        db.delete(cost)

        # 更新项目实际成本
        if project_id:
            project = db.query(Project).filter(Project.id == project_id).first()
            if project:
                project.actual_cost = max(0, (project.actual_cost or 0) - float(amount))
                db.add(project)

        return True

    @staticmethod
    def collect_from_bom(
        db: Session,
        bom_id: int,
        created_by: Optional[int] = None,
        cost_date: Optional[date] = None
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
        existing_cost = db.query(ProjectCost).filter(
            ProjectCost.project_id == bom.project_id,
            ProjectCost.source_module == "BOM",
            ProjectCost.source_type == "BOM_COST",
            ProjectCost.source_id == bom_id
        ).first()

        # 计算BOM总成本
        bom_items = db.query(BomItem).filter(BomItem.bom_id == bom_id).all()
        total_amount = sum([float(item.amount or 0) for item in bom_items])

        if total_amount <= 0:
            # 如果BOM总成本为0，不创建成本记录
            if existing_cost:
                # 删除已存在的成本记录
                project = db.query(Project).filter(Project.id == bom.project_id).first()
                if project:
                    project.actual_cost = max(0, (project.actual_cost or 0) - float(existing_cost.amount or 0))
                    db.add(project)
                db.delete(existing_cost)
                db.commit()
            return None

        # 使用BOM的总金额（如果BOM表头有total_amount字段）
        if bom.total_amount and bom.total_amount > 0:
            total_amount = float(bom.total_amount)

        if existing_cost:
            # 更新现有成本记录
            old_amount = existing_cost.amount
            existing_cost.amount = Decimal(str(total_amount))
            existing_cost.cost_date = cost_date or date.today()
            existing_cost.description = f"BOM材料成本：{bom.bom_name}（{bom.bom_no}）"

            # 更新项目实际成本
            project = db.query(Project).filter(Project.id == bom.project_id).first()
            if project:
                project.actual_cost = (project.actual_cost or 0) - float(old_amount) + total_amount
                db.add(project)

            db.add(existing_cost)
            db.flush()
            return existing_cost
        else:
            # 创建新的成本记录
            cost = ProjectCost(
                project_id=bom.project_id,
                machine_id=bom.machine_id,
                cost_type="MATERIAL",
                cost_category="BOM",
                source_module="BOM",
                source_type="BOM_COST",
                source_id=bom_id,
                source_no=bom.bom_no,
                amount=Decimal(str(total_amount)),
                cost_date=cost_date or date.today(),
                description=f"BOM材料成本：{bom.bom_name}（{bom.bom_no}）",
                created_by=created_by
            )
            db.add(cost)

            # 更新项目实际成本
            project = db.query(Project).filter(Project.id == bom.project_id).first()
            if project:
                project.actual_cost = (project.actual_cost or 0) + total_amount
                db.add(project)

            # 检查预算执行情况并生成预警
            try:
                CostAlertService.check_budget_execution(
                    db, bom.project_id, trigger_source="BOM", source_id=bom_id
                )
            except Exception as e:
                # 预警失败不影响成本归集
                logging.warning(f"成本预警检查失败：{str(e)}")

            db.flush()
            return cost
