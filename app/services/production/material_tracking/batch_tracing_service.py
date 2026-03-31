# -*- coding: utf-8 -*-
"""
批次追溯子服务
"""
from typing import Any, Dict, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.material import Material
from app.models.production.material_tracking import MaterialBatch, MaterialConsumption
from app.models.production.work_order import WorkOrder
from app.models.project import Project


class BatchTracingService:
    def __init__(self, db: Session):
        self.db = db

    def trace_batch(
        self,
        batch_no: Optional[str] = None,
        batch_id: Optional[int] = None,
        barcode: Optional[str] = None,
        trace_direction: str = "forward",
    ) -> Dict[str, Any]:
        """批次追溯 - 支持正向和反向查询"""
        from fastapi import HTTPException, status

        # 查找批次
        batch = None
        if batch_id:
            batch = self.db.query(MaterialBatch).filter(MaterialBatch.id == batch_id).first()
        elif batch_no:
            batch = self.db.query(MaterialBatch).filter(MaterialBatch.batch_no == batch_no).first()
        elif barcode:
            batch = self.db.query(MaterialBatch).filter(MaterialBatch.barcode == barcode).first()

        if not batch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到批次记录")

        # 批次基本信息
        material = self.db.query(Material).filter(Material.id == batch.material_id).first()

        batch_info = {
            "batch_id": batch.id,
            "batch_no": batch.batch_no,
            "material_code": material.material_code if material else None,
            "material_name": material.material_name if material else None,
            "initial_qty": float(batch.initial_qty) if batch.initial_qty else 0,
            "current_qty": float(batch.current_qty) if batch.current_qty else 0,
            "consumed_qty": float(batch.consumed_qty) if batch.consumed_qty else 0,
            "production_date": batch.production_date.isoformat() if batch.production_date else None,
            "expire_date": batch.expire_date.isoformat() if batch.expire_date else None,
            "supplier_batch_no": batch.supplier_batch_no,
            "quality_status": batch.quality_status,
            "warehouse_location": batch.warehouse_location,
            "status": batch.status,
        }

        # 正向追溯: 查询消耗记录
        consumptions = (
            self.db.query(MaterialConsumption)
            .filter(MaterialConsumption.batch_id == batch.id)
            .order_by(desc(MaterialConsumption.consumption_date))
            .all()
        )

        consumption_trail = []
        projects_used = set()
        work_orders_used = set()

        for c in consumptions:
            # 获取关联信息
            project_info = None
            work_order_info = None

            if c.project_id:
                proj = self.db.query(Project).filter(Project.id == c.project_id).first()
                if proj:
                    project_info = {
                        "id": proj.id,
                        "project_no": proj.project_no,
                        "project_name": proj.project_name,
                    }
                    projects_used.add(proj.id)

            if c.work_order_id:
                wo = self.db.query(WorkOrder).filter(WorkOrder.id == c.work_order_id).first()
                if wo:
                    work_order_info = {
                        "id": wo.id,
                        "work_order_no": wo.work_order_no,
                    }
                    work_orders_used.add(wo.id)

            consumption_trail.append(
                {
                    "consumption_no": c.consumption_no,
                    "consumption_date": (
                        c.consumption_date.isoformat() if c.consumption_date else None
                    ),
                    "consumption_qty": float(c.consumption_qty) if c.consumption_qty else 0,
                    "consumption_type": c.consumption_type,
                    "project": project_info,
                    "work_order": work_order_info,
                    "operator_id": c.operator_id,
                }
            )

        return {
            "batch_info": batch_info,
            "consumption_trail": consumption_trail,
            "summary": {
                "total_consumptions": len(consumptions),
                "projects_count": len(projects_used),
                "work_orders_count": len(work_orders_used),
            },
        }
