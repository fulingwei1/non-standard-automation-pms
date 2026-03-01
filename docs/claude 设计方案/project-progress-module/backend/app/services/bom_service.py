"""
BOM管理模块 - 业务逻辑服务层
"""
import json
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, func, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.bom_models import (
    Material, BomHeader, BomItem, BomVersion,
    get_category_name
)
from app.schemas.bom_schemas import (
    MaterialCreate, MaterialUpdate,
    BomHeaderCreate, BomHeaderUpdate,
    BomItemCreate, BomItemUpdate,
    BomVersionCreate, BomCompareItem
)


class MaterialService:
    """物料主数据服务"""

    @staticmethod
    async def create_material(
        db: AsyncSession,
        data: MaterialCreate,
        user_id: int
    ) -> Material:
        """创建物料"""
        material = Material(
            **data.model_dump(),
            created_by=user_id,
            status="启用"
        )
        db.add(material)
        await db.commit()
        await db.refresh(material)
        return material

    @staticmethod
    async def get_material(
        db: AsyncSession,
        material_id: int
    ) -> Optional[Material]:
        """获取物料详情"""
        result = await db.execute(
            select(Material).where(
                Material.material_id == material_id,
                Material.is_deleted == 0
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_material_by_code(
        db: AsyncSession,
        material_code: str
    ) -> Optional[Material]:
        """根据编码获取物料"""
        result = await db.execute(
            select(Material).where(
                Material.material_code == material_code,
                Material.is_deleted == 0
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_materials(
        db: AsyncSession,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Material], int]:
        """物料列表查询"""
        query = select(Material).where(Material.is_deleted == 0)

        if keyword:
            query = query.where(
                or_(
                    Material.material_code.contains(keyword),
                    Material.material_name.contains(keyword),
                    Material.specification.contains(keyword)
                )
            )
        if category:
            query = query.where(Material.category == category)
        if status:
            query = query.where(Material.status == status)

        # 统计总数
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        # 分页查询
        query = query.order_by(Material.created_time.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        materials = result.scalars().all()

        return list(materials), total

    @staticmethod
    async def update_material(
        db: AsyncSession,
        material_id: int,
        data: MaterialUpdate
    ) -> Optional[Material]:
        """更新物料"""
        material = await MaterialService.get_material(db, material_id)
        if not material:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(material, key, value)

        await db.commit()
        await db.refresh(material)
        return material

    @staticmethod
    async def delete_material(
        db: AsyncSession,
        material_id: int
    ) -> bool:
        """删除物料（软删除）"""
        material = await MaterialService.get_material(db, material_id)
        if not material:
            return False

        material.is_deleted = 1
        await db.commit()
        return True


class BomService:
    """BOM管理服务"""

    @staticmethod
    async def create_bom(
        db: AsyncSession,
        data: BomHeaderCreate,
        user_id: int
    ) -> BomHeader:
        """创建BOM"""
        # 创建BOM头
        bom_data = data.model_dump(exclude={"items"})
        bom = BomHeader(
            **bom_data,
            created_by=user_id,
            status="草稿",
            current_version="V1.0"
        )
        db.add(bom)
        await db.flush()

        # 创建BOM明细
        if data.items:
            total_cost = Decimal(0)
            for item_data in data.items:
                item = BomItem(
                    bom_id=bom.bom_id,
                    project_id=data.project_id,
                    **item_data.model_dump(),
                    category_name=get_category_name(item_data.category),
                    version="V1.0"
                )
                # 计算金额
                if item.unit_price and item.quantity:
                    item.amount = item.unit_price * item.quantity
                    total_cost += item.amount
                db.add(item)

            bom.total_items = len(data.items)
            bom.total_cost = total_cost

        await db.commit()
        await db.refresh(bom)
        return bom

    @staticmethod
    async def get_bom(
        db: AsyncSession,
        bom_id: int,
        include_items: bool = False
    ) -> Optional[BomHeader]:
        """获取BOM详情"""
        query = select(BomHeader).where(
            BomHeader.bom_id == bom_id,
            BomHeader.is_deleted == 0
        )
        if include_items:
            query = query.options(selectinload(BomHeader.items))

        result = await db.execute(query)
        bom = result.scalar_one_or_none()

        if bom and include_items:
            # 过滤已删除的明细
            bom.items = [item for item in bom.items if item.is_deleted == 0]

        return bom

    @staticmethod
    async def list_boms(
        db: AsyncSession,
        project_id: Optional[int] = None,
        machine_no: Optional[str] = None,
        status: Optional[str] = None,
        designer_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[BomHeader], int]:
        """BOM列表查询"""
        query = select(BomHeader).where(BomHeader.is_deleted == 0)

        if project_id:
            query = query.where(BomHeader.project_id == project_id)
        if machine_no:
            query = query.where(BomHeader.machine_no.contains(machine_no))
        if status:
            query = query.where(BomHeader.status == status)
        if designer_id:
            query = query.where(BomHeader.designer_id == designer_id)

        # 统计总数
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        # 分页查询
        query = query.order_by(BomHeader.created_time.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        boms = result.scalars().all()

        return list(boms), total

    @staticmethod
    async def update_bom(
        db: AsyncSession,
        bom_id: int,
        data: BomHeaderUpdate
    ) -> Optional[BomHeader]:
        """更新BOM头信息"""
        bom = await BomService.get_bom(db, bom_id)
        if not bom:
            return None

        # 只有草稿状态才能修改
        if bom.status != "草稿":
            raise ValueError("只有草稿状态的BOM才能修改")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(bom, key, value)

        await db.commit()
        await db.refresh(bom)
        return bom

    @staticmethod
    async def delete_bom(
        db: AsyncSession,
        bom_id: int
    ) -> bool:
        """删除BOM（软删除）"""
        bom = await BomService.get_bom(db, bom_id)
        if not bom:
            return False

        if bom.status not in ["草稿"]:
            raise ValueError("只有草稿状态的BOM才能删除")

        bom.is_deleted = 1
        await db.commit()
        return True


class BomItemService:
    """BOM明细服务"""

    @staticmethod
    async def add_item(
        db: AsyncSession,
        bom_id: int,
        data: BomItemCreate
    ) -> BomItem:
        """添加BOM明细"""
        bom = await BomService.get_bom(db, bom_id)
        if not bom:
            raise ValueError("BOM不存在")
        if bom.status != "草稿":
            raise ValueError("只有草稿状态的BOM才能添加明细")

        item = BomItem(
            bom_id=bom_id,
            project_id=bom.project_id,
            **data.model_dump(),
            category_name=get_category_name(data.category),
            version=bom.current_version
        )

        # 计算金额
        if item.unit_price and item.quantity:
            item.amount = item.unit_price * item.quantity

        db.add(item)

        # 更新BOM统计
        await BomItemService._update_bom_statistics(db, bom_id)

        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def update_item(
        db: AsyncSession,
        item_id: int,
        data: BomItemUpdate
    ) -> Optional[BomItem]:
        """更新BOM明细"""
        result = await db.execute(
            select(BomItem).where(
                BomItem.item_id == item_id,
                BomItem.is_deleted == 0
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            return None

        # 检查BOM状态
        bom = await BomService.get_bom(db, item.bom_id)
        if bom.status not in ["草稿", "已发布"]:
            raise ValueError("当前BOM状态不允许修改明细")

        update_data = data.model_dump(exclude_unset=True)

        # 如果更新了类别，同步更新类别名称
        if "category" in update_data:
            update_data["category_name"] = get_category_name(update_data["category"])

        for key, value in update_data.items():
            setattr(item, key, value)

        # 重新计算金额
        if item.unit_price and item.quantity:
            item.amount = item.unit_price * item.quantity

        # 计算缺料数量
        item.shortage_qty = max(
            Decimal(0),
            item.quantity - item.received_qty - item.stock_qty
        )

        # 更新BOM统计
        await BomItemService._update_bom_statistics(db, item.bom_id)

        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def delete_item(
        db: AsyncSession,
        item_id: int
    ) -> bool:
        """删除BOM明细（软删除）"""
        result = await db.execute(
            select(BomItem).where(
                BomItem.item_id == item_id,
                BomItem.is_deleted == 0
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            return False

        # 检查BOM状态
        bom = await BomService.get_bom(db, item.bom_id)
        if bom.status != "草稿":
            raise ValueError("只有草稿状态的BOM才能删除明细")

        item.is_deleted = 1

        # 更新BOM统计
        await BomItemService._update_bom_statistics(db, item.bom_id)

        await db.commit()
        return True

    @staticmethod
    async def batch_delete_items(
        db: AsyncSession,
        item_ids: List[int]
    ) -> int:
        """批量删除明细"""
        result = await db.execute(
            update(BomItem)
            .where(BomItem.item_id.in_(item_ids))
            .values(is_deleted=1)
        )
        await db.commit()
        return result.rowcount

    @staticmethod
    async def batch_update_procurement_status(
        db: AsyncSession,
        item_ids: List[int],
        status: str,
        ordered_qty: Optional[Decimal] = None,
        received_qty: Optional[Decimal] = None
    ) -> int:
        """批量更新采购状态"""
        values = {"procurement_status": status}
        if ordered_qty is not None:
            values["ordered_qty"] = ordered_qty
        if received_qty is not None:
            values["received_qty"] = received_qty

        result = await db.execute(
            update(BomItem)
            .where(BomItem.item_id.in_(item_ids))
            .values(**values)
        )
        await db.commit()
        return result.rowcount

    @staticmethod
    async def _update_bom_statistics(
        db: AsyncSession,
        bom_id: int
    ):
        """更新BOM统计信息"""
        # 统计物料数量和成本
        stats_result = await db.execute(
            select(
                func.count(BomItem.item_id).label("total_items"),
                func.coalesce(func.sum(BomItem.amount), 0).label("total_cost")
            ).where(
                BomItem.bom_id == bom_id,
                BomItem.is_deleted == 0
            )
        )
        stats = stats_result.one()

        # 计算齐套率
        kit_result = await db.execute(
            select(
                func.count(BomItem.item_id).label("total"),
                func.sum(
                    func.case(
                        (BomItem.shortage_qty <= 0, 1),
                        else_=0
                    )
                ).label("completed")
            ).where(
                BomItem.bom_id == bom_id,
                BomItem.is_deleted == 0
            )
        )
        kit_stats = kit_result.one()

        kit_rate = Decimal(0)
        if kit_stats.total and kit_stats.total > 0:
            kit_rate = Decimal(kit_stats.completed or 0) / Decimal(kit_stats.total) * 100

        # 更新BOM头
        await db.execute(
            update(BomHeader)
            .where(BomHeader.bom_id == bom_id)
            .values(
                total_items=stats.total_items,
                total_cost=stats.total_cost,
                kit_rate=kit_rate
            )
        )


class BomVersionService:
    """BOM版本服务"""

    @staticmethod
    async def create_version(
        db: AsyncSession,
        bom_id: int,
        data: BomVersionCreate,
        user_id: int,
        user_name: str
    ) -> BomVersion:
        """创建新版本（发布BOM）"""
        bom = await BomService.get_bom(db, bom_id, include_items=True)
        if not bom:
            raise ValueError("BOM不存在")

        # 生成新版本号
        new_version = BomVersionService._generate_version(bom.current_version)

        # 生成快照数据
        snapshot = BomVersionService._create_snapshot(bom)

        # 创建版本记录
        version = BomVersion(
            bom_id=bom_id,
            version=new_version,
            version_type=data.version_type,
            ecn_id=data.ecn_id,
            ecn_code=data.ecn_code,
            change_summary=data.change_summary,
            total_items=bom.total_items,
            total_cost=bom.total_cost,
            snapshot_data=json.dumps(snapshot, ensure_ascii=False, default=str),
            published_by=user_id,
            published_name=user_name,
            remark=data.remark
        )
        db.add(version)

        # 更新BOM头
        bom.current_version = new_version
        bom.status = "已发布"
        bom.publish_time = datetime.now()

        # 更新所有明细的版本号
        await db.execute(
            update(BomItem)
            .where(BomItem.bom_id == bom_id)
            .values(version=new_version)
        )

        await db.commit()
        await db.refresh(version)
        return version

    @staticmethod
    async def list_versions(
        db: AsyncSession,
        bom_id: int
    ) -> List[BomVersion]:
        """获取BOM版本历史"""
        result = await db.execute(
            select(BomVersion)
            .where(BomVersion.bom_id == bom_id)
            .order_by(BomVersion.published_time.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_version(
        db: AsyncSession,
        version_id: int
    ) -> Optional[BomVersion]:
        """获取版本详情"""
        result = await db.execute(
            select(BomVersion).where(BomVersion.version_id == version_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def compare_versions(
        db: AsyncSession,
        version_id_1: int,
        version_id_2: int
    ) -> Dict[str, Any]:
        """对比两个版本"""
        v1 = await BomVersionService.get_version(db, version_id_1)
        v2 = await BomVersionService.get_version(db, version_id_2)

        if not v1 or not v2:
            raise ValueError("版本不存在")

        snapshot_1 = json.loads(v1.snapshot_data) if v1.snapshot_data else {}
        snapshot_2 = json.loads(v2.snapshot_data) if v2.snapshot_data else {}

        items_1 = {item["material_code"]: item for item in snapshot_1.get("items", [])}
        items_2 = {item["material_code"]: item for item in snapshot_2.get("items", [])}

        added = []
        removed = []
        modified = []

        # 检查新增和修改
        for code, item in items_2.items():
            if code not in items_1:
                added.append(BomCompareItem(
                    material_code=code,
                    material_name=item["material_name"],
                    change_type="added",
                    old_quantity=None,
                    new_quantity=Decimal(str(item["quantity"])),
                    old_price=None,
                    new_price=Decimal(str(item.get("unit_price") or 0))
                ))
            else:
                old_item = items_1[code]
                if (str(item["quantity"]) != str(old_item["quantity"]) or
                    str(item.get("unit_price")) != str(old_item.get("unit_price"))):
                    modified.append(BomCompareItem(
                        material_code=code,
                        material_name=item["material_name"],
                        change_type="modified",
                        old_quantity=Decimal(str(old_item["quantity"])),
                        new_quantity=Decimal(str(item["quantity"])),
                        old_price=Decimal(str(old_item.get("unit_price") or 0)),
                        new_price=Decimal(str(item.get("unit_price") or 0))
                    ))

        # 检查删除
        for code, item in items_1.items():
            if code not in items_2:
                removed.append(BomCompareItem(
                    material_code=code,
                    material_name=item["material_name"],
                    change_type="removed",
                    old_quantity=Decimal(str(item["quantity"])),
                    new_quantity=None,
                    old_price=Decimal(str(item.get("unit_price") or 0)),
                    new_price=None
                ))

        return {
            "version_1": v1.version,
            "version_2": v2.version,
            "added_count": len(added),
            "removed_count": len(removed),
            "modified_count": len(modified),
            "items": added + removed + modified
        }

    @staticmethod
    def _generate_version(current_version: str) -> str:
        """生成新版本号"""
        # V1.0 -> V1.1 -> V1.2 ... -> V2.0
        if not current_version:
            return "V1.0"

        version = current_version.replace("V", "")
        parts = version.split(".")
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0

        minor += 1
        if minor >= 10:
            major += 1
            minor = 0

        return f"V{major}.{minor}"

    @staticmethod
    def _create_snapshot(bom: BomHeader) -> Dict[str, Any]:
        """创建BOM快照"""
        return {
            "bom_id": bom.bom_id,
            "project_id": bom.project_id,
            "project_code": bom.project_code,
            "machine_no": bom.machine_no,
            "machine_name": bom.machine_name,
            "bom_type": bom.bom_type,
            "total_items": bom.total_items,
            "total_cost": str(bom.total_cost),
            "items": [
                {
                    "line_no": item.line_no,
                    "material_code": item.material_code,
                    "material_name": item.material_name,
                    "specification": item.specification,
                    "brand": item.brand,
                    "category": item.category,
                    "unit": item.unit,
                    "quantity": str(item.quantity),
                    "unit_price": str(item.unit_price) if item.unit_price else None,
                    "amount": str(item.amount) if item.amount else None,
                    "supplier_name": item.supplier_name,
                    "lead_time": item.lead_time,
                    "drawing_no": item.drawing_no,
                    "position_no": item.position_no,
                    "remark": item.remark
                }
                for item in bom.items
            ]
        }


class BomStatisticsService:
    """BOM统计服务"""

    @staticmethod
    async def get_bom_statistics(
        db: AsyncSession,
        project_id: Optional[int] = None
    ) -> Dict[str, int]:
        """获取BOM统计"""
        query = select(
            BomHeader.status,
            func.count(BomHeader.bom_id).label("count")
        ).where(BomHeader.is_deleted == 0)

        if project_id:
            query = query.where(BomHeader.project_id == project_id)

        query = query.group_by(BomHeader.status)
        result = await db.execute(query)
        rows = result.all()

        stats = {
            "total_bom": 0,
            "draft_count": 0,
            "reviewing_count": 0,
            "published_count": 0,
            "frozen_count": 0
        }

        status_map = {
            "草稿": "draft_count",
            "评审中": "reviewing_count",
            "已发布": "published_count",
            "已冻结": "frozen_count"
        }

        for row in rows:
            stats["total_bom"] += row.count
            if row.status in status_map:
                stats[status_map[row.status]] = row.count

        return stats

    @staticmethod
    async def get_category_statistics(
        db: AsyncSession,
        bom_id: int
    ) -> List[Dict[str, Any]]:
        """获取物料类别统计"""
        result = await db.execute(
            select(
                BomItem.category,
                func.count(BomItem.item_id).label("count"),
                func.coalesce(func.sum(BomItem.amount), 0).label("amount")
            ).where(
                BomItem.bom_id == bom_id,
                BomItem.is_deleted == 0
            ).group_by(BomItem.category)
        )
        rows = result.all()

        return [
            {
                "category": row.category,
                "category_name": get_category_name(row.category),
                "count": row.count,
                "amount": row.amount
            }
            for row in rows
        ]

    @staticmethod
    async def get_shortage_list(
        db: AsyncSession,
        project_id: Optional[int] = None,
        bom_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取缺料清单"""
        query = (
            select(BomItem, BomHeader.machine_no)
            .join(BomHeader, BomItem.bom_id == BomHeader.bom_id)
            .where(
                BomItem.is_deleted == 0,
                BomHeader.is_deleted == 0,
                BomItem.shortage_qty > 0
            )
        )

        if project_id:
            query = query.where(BomItem.project_id == project_id)
        if bom_id:
            query = query.where(BomItem.bom_id == bom_id)

        # 统计总数
        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        # 分页查询
        query = query.order_by(BomItem.shortage_qty.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        rows = result.all()

        items = [
            {
                "item_id": row.BomItem.item_id,
                "bom_id": row.BomItem.bom_id,
                "machine_no": row.machine_no,
                "material_code": row.BomItem.material_code,
                "material_name": row.BomItem.material_name,
                "specification": row.BomItem.specification,
                "category": row.BomItem.category,
                "quantity": row.BomItem.quantity,
                "received_qty": row.BomItem.received_qty,
                "shortage_qty": row.BomItem.shortage_qty,
                "required_date": row.BomItem.required_date,
                "lead_time": row.BomItem.lead_time,
                "supplier_name": row.BomItem.supplier_name
            }
            for row in rows
        ]

        return items, total

    @staticmethod
    async def calculate_kit_rate(
        db: AsyncSession,
        bom_id: int
    ) -> Dict[str, Any]:
        """计算齐套率"""
        result = await db.execute(
            select(
                func.count(BomItem.item_id).label("total"),
                func.sum(
                    func.case(
                        (BomItem.shortage_qty <= 0, 1),
                        else_=0
                    )
                ).label("completed"),
                func.sum(
                    func.case(
                        (BomItem.shortage_qty > 0, 1),
                        else_=0
                    )
                ).label("shortage")
            ).where(
                BomItem.bom_id == bom_id,
                BomItem.is_deleted == 0
            )
        )
        stats = result.one()

        kit_rate = Decimal(0)
        if stats.total and stats.total > 0:
            kit_rate = Decimal(stats.completed or 0) / Decimal(stats.total) * 100

        bom = await BomService.get_bom(db, bom_id)

        return {
            "bom_id": bom_id,
            "machine_no": bom.machine_no if bom else "",
            "total_items": stats.total or 0,
            "completed_items": stats.completed or 0,
            "kit_rate": round(kit_rate, 2),
            "shortage_items": stats.shortage or 0
        }
