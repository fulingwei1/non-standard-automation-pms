# -*- coding: utf-8 -*-
"""
BOM服务 - 实施BOM审核通过后自动创建采购订单功能
创建日期：2026-01-25
"""

from typing import Dict, Any
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.material import Material, BomHeader, BomItem
from app.models.purchase import PurchaseOrder
from app.models.vendor import Vendor
from app.models.project import Project


class BOMService:
    """BOM服务类 - 实施BOM审核通过后自动创建采购订单功能"""

    @staticmethod
    async def approve_bom_and_create_purchase_orders(
        db: AsyncSession, bom_id: int, approved_by: int
    ) -> Dict[str, Any]:
        """
        BOM审核通过，自动创建采购订单

        功能说明：
        1. 查询BOM和项目信息
        2. 查询BOM明细
        3. 按供应商分组物料
        4. 为每个供应商创建采购订单
        5. 采购金额 = 物料数量 * 标准价格 * 1.1（安全库存系数）

        Args:
            db: 数据库会话
            bom_id: BOM ID
            approved_by: 审核人ID

        Returns:
            包含采购订单数量、采购订单ID列表等信息的字典

        Raises:
            ValueError: 如果BOM不存在或状态不正确
        """

        # 1. 查询BOM
        result = await db.execute(
            select(BomHeader, Project)
            .options(selectinload(Project))
            .where(BomHeader.id == bom_id)
        )
        bom_data = result.first()

        if not bom_data:
            raise ValueError(f"BOM不存在: {bom_id}")

        bom = bom_data[0]
        project = bom_data[1]

        # 2. 检查BOM状态
        if bom.status != "APPROVED":
            raise ValueError(f"BOM状态不是已审核: {bom.status}")

        # 3. 查询BOM明细
        items_result = await db.execute(
            select(BomItem, Material)
            .options(selectinload(Material))
            .where(BomItem.bom_id == bom_id)
            .order_by(BomItem.id)
        )
        items = items_result.scalars().all()

        if not items:
            return {
                "success": False,
                "message": f"BOM {bom.bom_name}没有明细，无法创建采购订单",
                "bom_id": bom_id,
            }

        # 4. 按供应商分组物料
        supplier_groups = defaultdict(list)
        for item in items:
            # 获取物料供应商（优先使用primary_supplier_id）
            supplier_id = (
                item.material.primary_supplier_id or item.material.default_supplier_id
            )

            if supplier_id:
                supplier_groups[supplier_id].append(item)

        # 5. 为每个供应商创建采购订单
        created_orders = []
        for supplier_id, items in supplier_groups.items():
            # 跳过无供应商的物料
            if not supplier_id:
                continue

            # 查询供应商信息
            vendor_result = await db.execute(
                select(Vendor).where(Vendor.id == supplier_id)
            )
            vendor = vendor_result.scalar_one_or_none()

            if not vendor:
                # 记录警告，继续处理
                continue

            # 计算采购金额（物料数量 * 标准价格 * 1.1安全系数）
            total_amount = 0
            for item in items:
                quantity = item.quantity or 1
                standard_price = item.material.standard_price or 0

                # 安全库存系数：增加10%
                safety_factor = 1.1

                amount = quantity * standard_price * safety_factor
                total_amount += amount

            # 创建采购订单
            purchase_order = PurchaseOrder(
                project_id=project.id,
                supplier_id=vendor.id,
                bom_id=bom.id,
                source_type="AUTO_BOM",  # BOM自动创建
                order_type="STANDARD",  # 标准件采购
                total_amount=total_amount,
                status="DRAFT",
            )

            db.add(purchase_order)
            await db.flush()
            created_orders.append(purchase_order.id)

            # 添加采购订单明细
            for item in items:
                po_item = PurchaseOrderItem(
                    purchase_order_id=purchase_order.id,
                    bom_item_id=item.id,
                    material_id=item.material_id,
                    quantity=item.quantity * 1.1,  # 增加10%安全库存
                    unit_price=item.material.standard_price or 0,
                    amount=item.quantity * item.material.standard_price or 0 * 1.1,
                )

                db.add(po_item)

        # 6. 更新BOM状态
        bom.status = "APPROVED"
        bom.approved_by = approved_by
        bom.approved_at = datetime.now()

        await db.commit()

        return {
            "success": True,
            "message": f"BOM审核通过，已创建 {len(created_orders)}个采购订单",
            "bom_id": bom_id,
            "purchase_orders_count": len(created_orders),
            "purchase_order_ids": created_orders,
        }


class PurchaseOrderItem(Base):
    """采购订单明细模型（临时，用于BOM服务）"""

    __tablename__ = "purchase_order_items"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    purchase_order_id = Column(
        Integer, nullable=False, index=True, comment="采购订单ID"
    )
    bom_item_id = Column(Integer, nullable=True, comment="BOM明细ID")
    material_id = Column(Integer, nullable=False, comment="物料ID")
    quantity = Column(Numeric(10, 4), default=0, comment="数量")
    unit_price = Column(Numeric(12, 4), default=0, comment="单价")
    amount = Column(Numeric(14, 2), default=0, comment="金额")
