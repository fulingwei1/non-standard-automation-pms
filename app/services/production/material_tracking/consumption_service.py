# -*- coding: utf-8 -*-
"""
物料消耗子服务
"""
from datetime import date, datetime
from typing import Any, Dict, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.material import Material
from app.models.production.material_tracking import MaterialBatch, MaterialConsumption
from app.models.production.work_order import WorkOrder
from app.models.project import Project
from app.utils.db_helpers import get_or_404


class ConsumptionService:
    def __init__(self, db: Session):
        self.db = db

    def create_consumption(
        self,
        consumption_data: Dict[str, Any],
        current_user_id: int,
        alert_callback=None,
    ) -> Dict[str, Any]:
        """记录物料消耗"""
        from fastapi import HTTPException, status

        material_id = consumption_data.get("material_id")
        consumption_qty = consumption_data.get("consumption_qty")
        consumption_type = consumption_data.get("consumption_type", "PRODUCTION")

        if not material_id or not consumption_qty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="material_id 和 consumption_qty 为必填项",
            )

        # 查询物料
        material = get_or_404(self.db, Material, material_id)

        # 条码/二维码扫描支持
        barcode = consumption_data.get("barcode")
        batch_id = consumption_data.get("batch_id")

        if barcode and not batch_id:
            # 通过条码查找批次
            batch = (
                self.db.query(MaterialBatch)
                .filter(MaterialBatch.barcode == barcode, MaterialBatch.material_id == material_id)
                .first()
            )
            if batch:
                batch_id = batch.id

        # 生成消耗单号
        consumption_no = f"CONS-{datetime.now().strftime('%Y%m%d%H%M%S')}-{material.material_code}"

        # 计算差异 (浪费识别)
        standard_qty = consumption_data.get("standard_qty")
        variance_qty = 0
        variance_rate = 0
        is_waste = False

        if standard_qty:
            variance_qty = float(consumption_qty) - float(standard_qty)
            if standard_qty > 0:
                variance_rate = (variance_qty / float(standard_qty)) * 100
                # 差异超过10%视为异常浪费
                is_waste = abs(variance_rate) > 10

        # 计算成本
        unit_price = consumption_data.get("unit_price") or material.standard_price or 0
        total_cost = float(consumption_qty) * float(unit_price)

        # 创建消耗记录
        consumption = MaterialConsumption(
            consumption_no=consumption_no,
            material_id=material_id,
            batch_id=batch_id,
            material_code=material.material_code,
            material_name=material.material_name,
            consumption_date=consumption_data.get("consumption_date", datetime.now()),
            consumption_qty=consumption_qty,
            unit=consumption_data.get("unit", material.unit),
            work_order_id=consumption_data.get("work_order_id"),
            project_id=consumption_data.get("project_id"),
            requisition_id=consumption_data.get("requisition_id"),
            consumption_type=consumption_type,
            standard_qty=standard_qty,
            variance_qty=variance_qty,
            variance_rate=variance_rate,
            is_waste=is_waste,
            operator_id=consumption_data.get("operator_id", current_user_id),
            workshop_id=consumption_data.get("workshop_id"),
            unit_price=unit_price,
            total_cost=total_cost,
            remark=consumption_data.get("remark"),
        )

        self.db.add(consumption)

        # 更新批次库存
        if batch_id:
            batch = self.db.query(MaterialBatch).filter(MaterialBatch.id == batch_id).first()
            if batch:
                batch.current_qty = (batch.current_qty or 0) - consumption_qty
                batch.consumed_qty = (batch.consumed_qty or 0) + consumption_qty
                if batch.current_qty <= 0:
                    batch.status = "DEPLETED"

        # 更新物料总库存
        material.current_stock = (material.current_stock or 0) - consumption_qty

        self.db.commit()
        self.db.refresh(consumption)

        # 检查是否需要触发预警
        if alert_callback:
            alert_callback(material)

        return {
            "id": consumption.id,
            "consumption_no": consumption.consumption_no,
            "material_code": consumption.material_code,
            "material_name": consumption.material_name,
            "consumption_qty": float(consumption.consumption_qty),
            "is_waste": consumption.is_waste,
            "variance_rate": float(consumption.variance_rate) if consumption.variance_rate else 0,
        }

    def get_consumption_analysis(
        self,
        material_id: Optional[int] = None,
        project_id: Optional[int] = None,
        work_order_id: Optional[int] = None,
        consumption_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        group_by: str = "day",
    ) -> Dict[str, Any]:
        """物料消耗分析"""
        query = self.db.query(MaterialConsumption)

        # 筛选条件
        if material_id:
            query = query.filter(MaterialConsumption.material_id == material_id)
        if project_id:
            query = query.filter(MaterialConsumption.project_id == project_id)
        if work_order_id:
            query = query.filter(MaterialConsumption.work_order_id == work_order_id)
        if consumption_type:
            query = query.filter(MaterialConsumption.consumption_type == consumption_type)
        if start_date:
            query = query.filter(MaterialConsumption.consumption_date >= start_date)
        if end_date:
            query = query.filter(MaterialConsumption.consumption_date <= end_date)

        consumptions = query.all()

        # 统计数据
        total_consumption = sum([float(c.consumption_qty or 0) for c in consumptions])
        total_cost = sum([float(c.total_cost or 0) for c in consumptions])
        total_standard = sum([float(c.standard_qty or 0) for c in consumptions if c.standard_qty])
        waste_count = len([c for c in consumptions if c.is_waste])

        # 分组统计
        grouped_data = {}
        if group_by == "material":
            for c in consumptions:
                key = f"{c.material_code}-{c.material_name}"
                if key not in grouped_data:
                    grouped_data[key] = {
                        "material_code": c.material_code,
                        "material_name": c.material_name,
                        "total_qty": 0,
                        "total_cost": 0,
                        "waste_qty": 0,
                    }
                grouped_data[key]["total_qty"] += float(c.consumption_qty or 0)
                grouped_data[key]["total_cost"] += float(c.total_cost or 0)
                if c.is_waste:
                    grouped_data[key]["waste_qty"] += float(c.consumption_qty or 0)

        elif group_by in ["day", "week", "month"]:
            for c in consumptions:
                if group_by == "day":
                    key = c.consumption_date.strftime("%Y-%m-%d")
                elif group_by == "week":
                    key = c.consumption_date.strftime("%Y-W%U")
                else:  # month
                    key = c.consumption_date.strftime("%Y-%m")

                if key not in grouped_data:
                    grouped_data[key] = {
                        "period": key,
                        "total_qty": 0,
                        "total_cost": 0,
                        "record_count": 0,
                    }
                grouped_data[key]["total_qty"] += float(c.consumption_qty or 0)
                grouped_data[key]["total_cost"] += float(c.total_cost or 0)
                grouped_data[key]["record_count"] += 1

        return {
            "summary": {
                "total_records": len(consumptions),
                "total_consumption": total_consumption,
                "total_cost": total_cost,
                "total_standard": total_standard,
                "waste_count": waste_count,
                "waste_rate": (waste_count / len(consumptions) * 100) if consumptions else 0,
            },
            "grouped_data": list(grouped_data.values()),
        }

    def get_waste_records(
        self,
        material_id: Optional[int] = None,
        project_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        min_variance_rate: float = 10,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """物料浪费追溯"""
        from app.common.query_filters import apply_pagination

        query = self.db.query(MaterialConsumption).filter(
            MaterialConsumption.is_waste == True,
            MaterialConsumption.variance_rate >= min_variance_rate,
        )

        if material_id:
            query = query.filter(MaterialConsumption.material_id == material_id)
        if project_id:
            query = query.filter(MaterialConsumption.project_id == project_id)
        if start_date:
            query = query.filter(MaterialConsumption.consumption_date >= start_date)
        if end_date:
            query = query.filter(MaterialConsumption.consumption_date <= end_date)

        query = query.order_by(desc(MaterialConsumption.variance_rate))

        total = query.count()
        offset = (page - 1) * page_size
        wastes = apply_pagination(query, offset, page_size).all()

        waste_data = []
        for w in wastes:
            # 获取关联信息
            project_name = None
            work_order_no = None

            if w.project_id:
                proj = self.db.query(Project).filter(Project.id == w.project_id).first()
                if proj:
                    project_name = proj.project_name

            if w.work_order_id:
                wo = self.db.query(WorkOrder).filter(WorkOrder.id == w.work_order_id).first()
                if wo:
                    work_order_no = wo.work_order_no

            waste_data.append(
                {
                    "id": w.id,
                    "consumption_no": w.consumption_no,
                    "material_code": w.material_code,
                    "material_name": w.material_name,
                    "consumption_date": (
                        w.consumption_date.isoformat() if w.consumption_date else None
                    ),
                    "actual_qty": float(w.consumption_qty) if w.consumption_qty else 0,
                    "standard_qty": float(w.standard_qty) if w.standard_qty else 0,
                    "variance_qty": float(w.variance_qty) if w.variance_qty else 0,
                    "variance_rate": float(w.variance_rate) if w.variance_rate else 0,
                    "consumption_type": w.consumption_type,
                    "project_name": project_name,
                    "work_order_no": work_order_no,
                    "total_cost": float(w.total_cost) if w.total_cost else 0,
                    "remark": w.remark,
                }
            )

        # 统计汇总
        total_waste_qty = sum([float(w.variance_qty or 0) for w in wastes])
        total_waste_cost = sum(
            [float(w.variance_qty or 0) * float(w.unit_price or 0) for w in wastes]
        )

        return {
            "items": waste_data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "summary": {
                "total_waste_qty": total_waste_qty,
                "total_waste_cost": total_waste_cost,
            },
        }
