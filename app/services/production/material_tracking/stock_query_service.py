# -*- coding: utf-8 -*-
"""
实时库存查询子服务
"""
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.material import Material
from app.models.production.material_tracking import MaterialBatch


class StockQueryService:
    def __init__(self, db: Session):
        self.db = db

    def get_realtime_stock(
        self,
        material_id: Optional[int] = None,
        material_code: Optional[str] = None,
        category_id: Optional[int] = None,
        warehouse_location: Optional[str] = None,
        status: Optional[str] = None,
        low_stock_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """实时库存查询 - 支持多维度筛选"""
        from app.common.query_filters import apply_keyword_filter, apply_pagination

        query = self.db.query(Material).filter(Material.is_active == True)

        # 条件筛选
        if material_id:
            query = query.filter(Material.id == material_id)
        if material_code:
            query = apply_keyword_filter(query, Material, material_code, ["material_code"])
        if category_id:
            query = query.filter(Material.category_id == category_id)

        # 低库存筛选
        if low_stock_only:
            query = query.filter(Material.current_stock < Material.safety_stock)

        total = query.count()
        offset = (page - 1) * page_size
        materials = apply_pagination(query, offset, page_size).all()

        # 构建返回数据
        stock_data = []
        for mat in materials:
            # 查询批次明细
            batch_query = self.db.query(MaterialBatch).filter(
                MaterialBatch.material_id == mat.id, MaterialBatch.status == "ACTIVE"
            )

            if warehouse_location:
                batch_query = apply_keyword_filter(
                    batch_query, MaterialBatch, warehouse_location, ["warehouse_location"]
                )
            if status:
                batch_query = batch_query.filter(MaterialBatch.status == status)

            batches = batch_query.all()

            batch_list = [
                {
                    "batch_no": b.batch_no,
                    "current_qty": float(b.current_qty) if b.current_qty else 0,
                    "reserved_qty": float(b.reserved_qty) if b.reserved_qty else 0,
                    "available_qty": (
                        float(b.current_qty - b.reserved_qty)
                        if b.current_qty and b.reserved_qty
                        else 0
                    ),
                    "warehouse_location": b.warehouse_location,
                    "production_date": b.production_date.isoformat() if b.production_date else None,
                    "expire_date": b.expire_date.isoformat() if b.expire_date else None,
                    "quality_status": b.quality_status,
                }
                for b in batches
            ]

            # 计算可用库存 (总库存 - 预留)
            total_reserved = sum([float(b.reserved_qty or 0) for b in batches])
            available_stock = float(mat.current_stock or 0) - total_reserved

            stock_data.append(
                {
                    "material_id": mat.id,
                    "material_code": mat.material_code,
                    "material_name": mat.material_name,
                    "specification": mat.specification,
                    "unit": mat.unit,
                    "current_stock": float(mat.current_stock) if mat.current_stock else 0,
                    "safety_stock": float(mat.safety_stock) if mat.safety_stock else 0,
                    "available_stock": available_stock,
                    "reserved_stock": total_reserved,
                    "is_low_stock": (mat.current_stock or 0) < (mat.safety_stock or 0),
                    "batch_count": len(batches),
                    "batches": batch_list,
                }
            )

        return {
            "items": stock_data,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
