# -*- coding: utf-8 -*-
"""
物料调拨服务
处理项目间物料调拨、库存查询、库存更新
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

# from app.models.inventory_tracking import MaterialStock, MaterialTransaction, MaterialReservation  # FIXME: Classes do not exist
# Use correct class names:
from app.models.inventory_tracking import MaterialStock, MaterialTransaction, MaterialReservation
from app.models.material import Material, ProjectMaterial
from app.models.project import Project
from app.models.shortage import MaterialTransfer

logger = logging.getLogger(__name__)


class MaterialTransferService:
    """物料调拨服务"""

    @staticmethod
    def get_project_material_stock(
        db: Session,
        project_id: int,
        material_id: int
    ) -> Dict[str, Any]:
        """
        获取项目指定物料的库存数量

        Args:
            db: 数据库会话
            project_id: 项目ID
            material_id: 物料ID

        Returns:
            库存信息字典
        """
        result = {
            "available_qty": Decimal("0"),
            "reserved_qty": Decimal("0"),
            "total_qty": Decimal("0"),
            "source": "未设置"
        }

        # 1. 首先尝试从项目物料表查询
        project_material = db.query(ProjectMaterial).filter(
            ProjectMaterial.project_id == project_id,
            ProjectMaterial.material_id == material_id
        ).first()

        if project_material:
            result.update({
                "available_qty": project_material.available_qty or Decimal("0"),
                "reserved_qty": project_material.reserved_qty or Decimal("0"),
                "total_qty": project_material.total_qty or Decimal("0"),
                "source": "项目物料表"
            })
            return result

        # 2. 尝试从库存表查询
        inventory = db.query(MaterialReservation).filter(
            MaterialReservation.project_id == project_id,
            MaterialReservation.material_id == material_id
        ).first()

        if inventory:
            result.update({
                "available_qty": inventory.available_qty or Decimal("0"),
                "reserved_qty": inventory.reserved_qty or Decimal("0"),
                "total_qty": inventory.total_qty or Decimal("0"),
                "source": "库存表"
            })
            return result

        # 3. 使用物料档案的通用库存
        material = db.query(Material).filter(Material.id == material_id).first()
        if material:
            result.update({
                "available_qty": material.current_stock or Decimal("0"),
                "reserved_qty": Decimal("0"),
                "total_qty": material.current_stock or Decimal("0"),
                "source": "物料档案"
            })

        return result

    @staticmethod
    def check_transfer_available(
        db: Session,
        from_project_id: int,
        material_id: int,
        transfer_qty: Decimal
    ) -> Dict[str, Any]:
        """
        检查调出项目的物料是否足够

        Args:
            db: 数据库会话
            from_project_id: 调出项目ID
            material_id: 物料ID
            transfer_qty: 调拨数量

        Returns:
            检查结果
        """
        stock_info = MaterialTransferService.get_project_material_stock(
            db, from_project_id, material_id
        )

        available = stock_info["available_qty"]
        is_sufficient = available >= transfer_qty

        return {
            "is_sufficient": is_sufficient,
            "available_qty": float(available),
            "transfer_qty": float(transfer_qty),
            "shortage_qty": float(transfer_qty - available) if not is_sufficient else 0,
            "stock_source": stock_info["source"]
        }

    @staticmethod
    def execute_stock_update(
        db: Session,
        transfer: MaterialTransfer,
        actual_qty: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        执行库存更新（调出项目减少，调入项目增加）

        Args:
            db: 数据库会话
            transfer: 调拨单
            actual_qty: 实际调拨数量（不传则使用transfer_qty）

        Returns:
            更新结果
        """
        qty = actual_qty or transfer.transfer_qty

        updates = {
            "from_project": {"before": 0, "after": 0, "success": False},
            "to_project": {"before": 0, "after": 0, "success": False}
        }

        # 1. 更新调出项目库存
        if transfer.from_project_id:
            from_stock = MaterialTransferService._update_project_stock(
                db,
                transfer.from_project_id,
                transfer.material_id,
                -qty,  # 减少库存
                "TRANSFER_OUT",
                f"调拨至项目 {transfer.to_project_id}",
            )
            updates["from_project"] = from_stock

        # 2. 更新调入项目库存
        to_stock = MaterialTransferService._update_project_stock(
            db,
            transfer.to_project_id,
            transfer.material_id,
            qty,  # 增加库存
            "TRANSFER_IN",
            f"从项目 {transfer.from_project_id} 调入",
        )
        updates["to_project"] = to_stock

        # 3. 更新物料档案的总库存（如果有）
        material = db.query(Material).filter(Material.id == transfer.material_id).first()
        if material and material.current_stock is not None:
            # 如果是从项目调拨，总库存不变
            # 如果是从仓库调拨（from_project_id为空），总库存减少
            if not transfer.from_project_id:
                material.current_stock = max(Decimal("0"), material.current_stock - qty)
                db.add(material)

        db.commit()

        return updates

    @staticmethod
    def _update_project_stock(
        db: Session,
        project_id: int,
        material_id: int,
        qty_change: Decimal,
        transaction_type: str,
        remark: str
    ) -> Dict[str, Any]:
        """
        更新项目物料库存（内部方法）

        Args:
            db: 数据库会话
            project_id: 项目ID
            material_id: 物料ID
            qty_change: 数量变化（正数为增加，负数为减少）
            transaction_type: 交易类型
            remark: 备注

        Returns:
            更新结果
        """
        result = {"before": 0, "after": 0, "success": False}

        # 1. 尝试更新项目物料表
        project_material = db.query(ProjectMaterial).filter(
            ProjectMaterial.project_id == project_id,
            ProjectMaterial.material_id == material_id
        ).first()

        if project_material:
            result["before"] = float(project_material.available_qty or 0)
            project_material.available_qty = max(
                Decimal("0"),
                (project_material.available_qty or Decimal("0")) + qty_change
            )
            project_material.total_qty = max(
                Decimal("0"),
                (project_material.total_qty or Decimal("0")) + qty_change
            )
            result["after"] = float(project_material.available_qty)
            result["success"] = True
            db.add(project_material)

            # 记录交易日志
            MaterialTransferService._record_transaction(
                db, project_id, material_id, qty_change, transaction_type, remark
            )

            return result

        # 2. 如果项目物料表没有记录，尝试更新库存表
        inventory = db.query(MaterialReservation).filter(
            MaterialReservation.project_id == project_id,
            MaterialReservation.material_id == material_id
        ).first()

        if inventory:
            result["before"] = float(inventory.available_qty or 0)
            inventory.available_qty = max(
                Decimal("0"),
                (inventory.available_qty or Decimal("0")) + qty_change
            )
            inventory.total_qty = max(
                Decimal("0"),
                (inventory.total_qty or Decimal("0")) + qty_change
            )
            result["after"] = float(inventory.available_qty)
            result["success"] = True
            db.add(inventory)

            # 记录交易日志
            MaterialTransferService._record_transaction(
                db, project_id, material_id, qty_change, transaction_type, remark
            )

            return result

        # 3. 如果都不存在，创建新的项目物料记录
        if qty_change > 0:  # 只允许增加时创建新记录
            new_project_material = ProjectMaterial(
                project_id=project_id,
                material_id=material_id,
                available_qty=qty_change,
                reserved_qty=Decimal("0"),
                total_qty=qty_change
            )
            db.add(new_project_material)
            db.flush()  # 获取ID

            result["before"] = 0
            result["after"] = float(qty_change)
            result["success"] = True

            # 记录交易日志
            MaterialTransferService._record_transaction(
                db, project_id, material_id, qty_change, transaction_type, remark
            )

            return result

        # 4. 如果是减少操作但记录不存在，报错
        result["error"] = "项目物料库存不存在，无法减少"

        return result

    @staticmethod
    def _record_transaction(
        db: Session,
        project_id: int,
        material_id: int,
        qty_change: Decimal,
        transaction_type: str,
        remark: str
    ):
        """记录库存交易日志"""
        try:
            # 获取物料信息
            material = db.query(Material).filter(Material.id == material_id).first()

            transaction = MaterialTransaction(
                project_id=project_id,
                material_id=material_id,
                material_code=material.material_code if material else None,
                material_name=material.material_name if material else None,
                transaction_type=transaction_type,
                quantity=qty_change,
                before_qty=Decimal("0"),  # 已在调用前记录
                after_qty=Decimal("0"),   # 已在调用前记录
                transaction_time=datetime.now(),
                reference_type="MATERIAL_TRANSFER",
                remark=remark
            )
            db.add(transaction)
        except Exception:
            # 交易日志记录失败不影响主流程
            logger.warning("库存交易日志记录失败，不影响主流程", exc_info=True)

    @staticmethod
    def suggest_transfer_sources(
        db: Session,
        to_project_id: int,
        material_id: int,
        required_qty: Decimal
    ) -> List[Dict[str, Any]]:
        """
        推荐物料调拨来源

        Args:
            db: 数据库会话
            to_project_id: 调入项目ID
            material_id: 物料ID
            required_qty: 需要的数量

        Returns:
            推荐的调拨来源列表
        """
        suggestions = []

        # 1. 查找有该物料库存的其他项目
        project_materials = db.query(ProjectMaterial).filter(
            ProjectMaterial.material_id == material_id,
            ProjectMaterial.available_qty > 0
        ).order_by(ProjectMaterial.available_qty.desc()).all()

        for pm in project_materials:
            if pm.project_id == to_project_id:
                continue  # 跳过当前项目

            project = db.query(Project).filter(Project.id == pm.project_id).first()
            if not project:
                continue

            available = pm.available_qty or Decimal("0")
            can_fully_supply = available >= required_qty

            suggestions.append({
                "project_id": pm.project_id,
                "project_name": project.project_name,
                "project_code": project.project_code if hasattr(project, 'project_code') else "",
                "available_qty": float(available),
                "can_fully_supply": can_fully_supply,
                "supply_ratio": float(available / required_qty) if required_qty > 0 else 0,
                "priority": "HIGH" if can_fully_supply else "MEDIUM"
            })

        # 2. 检查中心仓库库存
        inventory = db.query(MaterialStock).filter(
            MaterialStock.material_id == material_id
        ).first()

        if inventory and inventory.available_qty > 0:
            available = inventory.available_qty or Decimal("0")
            can_fully_supply = available >= required_qty

            suggestions.append({
                "project_id": None,
                "project_name": "中心仓库",
                "project_code": "WAREHOUSE",
                "available_qty": float(available),
                "can_fully_supply": can_fully_supply,
                "supply_ratio": float(available / required_qty) if required_qty > 0 else 0,
                "priority": "HIGH" if can_fully_supply else "LOW"
            })

        # 按优先级排序
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        suggestions.sort(key=lambda x: priority_order.get(x["priority"], 3))

        return suggestions

    @staticmethod
    def validate_transfer_before_execute(
        db: Session,
        transfer: MaterialTransfer
    ) -> Dict[str, Any]:
        """
        执行调拨前的最终校验

        Args:
            db: 数据库会话
            transfer: 调拨单

        Returns:
            校验结果
        """
        errors = []
        warnings = []

        # 1. 检查调入项目是否存在
        to_project = db.query(Project).filter(Project.id == transfer.to_project_id).first()
        if not to_project:
            errors.append("调入项目不存在")
        elif to_project.is_active is False:
            warnings.append("调入项目已归档")

        # 2. 检查调出项目是否存在
        if transfer.from_project_id:
            from_project = db.query(Project).filter(Project.id == transfer.from_project_id).first()
            if not from_project:
                errors.append("调出项目不存在")
            elif from_project.is_active is False:
                warnings.append("调出项目已归档")

        # 3. 检查物料是否存在
        material = db.query(Material).filter(Material.id == transfer.material_id).first()
        if not material:
            errors.append("物料不存在")

        # 4. 检查调出数量是否足够
        if transfer.from_project_id:
            check_result = MaterialTransferService.check_transfer_available(
                db,
                transfer.from_project_id,
                transfer.material_id,
                transfer.transfer_qty
            )
            if not check_result["is_sufficient"]:
                errors.append(
                    f"调出项目库存不足，可用: {check_result['available_qty']}，"
                    f"需要: {check_result['transfer_qty']}，"
                    f"缺口: {check_result['shortage_qty']}"
                )

        # 5. 检查状态
        if transfer.status != "APPROVED":
            errors.append(f"调拨单状态不正确，当前状态: {transfer.status}，需要: APPROVED")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }


# 创建单例
material_transfer_service = MaterialTransferService()
