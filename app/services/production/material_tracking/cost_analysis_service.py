# -*- coding: utf-8 -*-
"""
物料成本与周转分析子服务
"""
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.material import Material
from app.models.production.material_tracking import MaterialConsumption


class CostAnalysisService:
    def __init__(self, db: Session):
        self.db = db

    def get_cost_analysis(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        project_id: Optional[int] = None,
        category_id: Optional[int] = None,
        top_n: int = 10,
    ) -> Dict[str, Any]:
        """物料成本分析"""
        query = self.db.query(MaterialConsumption)

        if start_date:
            query = query.filter(MaterialConsumption.consumption_date >= start_date)
        if end_date:
            query = query.filter(MaterialConsumption.consumption_date <= end_date)
        if project_id:
            query = query.filter(MaterialConsumption.project_id == project_id)

        consumptions = query.all()

        # 按物料聚合
        material_costs = {}
        for c in consumptions:
            if c.material_id not in material_costs:
                material_costs[c.material_id] = {
                    "material_id": c.material_id,
                    "material_code": c.material_code,
                    "material_name": c.material_name,
                    "total_qty": 0,
                    "total_cost": 0,
                }
            material_costs[c.material_id]["total_qty"] += float(c.consumption_qty or 0)
            material_costs[c.material_id]["total_cost"] += float(c.total_cost or 0)

        # 排序获取 Top N
        sorted_materials = sorted(
            material_costs.values(), key=lambda x: x["total_cost"], reverse=True
        )[:top_n]

        total_cost = sum([m["total_cost"] for m in material_costs.values()])

        return {
            "total_cost": total_cost,
            "material_count": len(material_costs),
            "top_materials": sorted_materials,
        }

    def get_turnover_analysis(
        self,
        material_id: Optional[int] = None,
        category_id: Optional[int] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """库存周转率分析"""
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=days)

        query = self.db.query(Material).filter(Material.is_active == True)

        if material_id:
            query = query.filter(Material.id == material_id)
        if category_id:
            query = query.filter(Material.category_id == category_id)

        materials = query.all()

        turnover_data = []
        for mat in materials:
            # 查询期间内消耗
            consumptions = (
                self.db.query(MaterialConsumption)
                .filter(
                    MaterialConsumption.material_id == mat.id,
                    MaterialConsumption.consumption_date >= start_dt,
                    MaterialConsumption.consumption_date <= end_dt,
                )
                .all()
            )

            total_consumption = sum([float(c.consumption_qty or 0) for c in consumptions])

            # 平均库存 (简化: 使用当前库存)
            avg_stock = float(mat.current_stock or 0)

            # 周转率和周转天数
            turnover_rate = (total_consumption / avg_stock) if avg_stock > 0 else 0
            turnover_days = (days / turnover_rate) if turnover_rate > 0 else 0

            turnover_data.append(
                {
                    "material_id": mat.id,
                    "material_code": mat.material_code,
                    "material_name": mat.material_name,
                    "current_stock": avg_stock,
                    "consumption_qty": total_consumption,
                    "turnover_rate": round(turnover_rate, 2),
                    "turnover_days": round(turnover_days, 1),
                }
            )

        # 按周转率排序
        turnover_data.sort(key=lambda x: x["turnover_rate"], reverse=True)

        return {
            "period_days": days,
            "materials": turnover_data,
        }

    def calculate_avg_daily_consumption(self, material_id: int, days: int = 30) -> float:
        """计算平均日消耗"""
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=days)

        consumptions = (
            self.db.query(MaterialConsumption)
            .filter(
                MaterialConsumption.material_id == material_id,
                MaterialConsumption.consumption_date >= start_dt,
                MaterialConsumption.consumption_date <= end_dt,
            )
            .all()
        )

        total_consumption = sum([float(c.consumption_qty or 0) for c in consumptions])

        return total_consumption / days if days > 0 else 0
