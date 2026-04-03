# -*- coding: utf-8 -*-
"""
物料跟踪系统 - 业务服务层 (Facade)

Delegates to focused sub-services while preserving the original public API.
"""
from datetime import date
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.material import Material
from .alert_service import AlertService
from .batch_tracing_service import BatchTracingService
from .consumption_service import ConsumptionService
from .cost_analysis_service import CostAnalysisService
from .stock_query_service import StockQueryService


class MaterialTrackingService:
    def __init__(self, db: Session):
        self.db = db
        self._stock = StockQueryService(db)
        self._consumption = ConsumptionService(db)
        self._batch = BatchTracingService(db)
        self._alert = AlertService(db)
        self._cost = CostAnalysisService(db)

    # ================== 1. 实时库存查询 ==================
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
        return self._stock.get_realtime_stock(
            material_id=material_id,
            material_code=material_code,
            category_id=category_id,
            warehouse_location=warehouse_location,
            status=status,
            low_stock_only=low_stock_only,
            page=page,
            page_size=page_size,
        )

    # ================== 2. 记录物料消耗 ==================
    def create_consumption(
        self,
        consumption_data: Dict[str, Any],
        current_user_id: int,
    ) -> Dict[str, Any]:
        """记录物料消耗"""
        return self._consumption.create_consumption(
            consumption_data=consumption_data,
            current_user_id=current_user_id,
            alert_callback=self.check_and_create_alerts,
        )

    # ================== 3. 消耗分析 ==================
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
        return self._consumption.get_consumption_analysis(
            material_id=material_id,
            project_id=project_id,
            work_order_id=work_order_id,
            consumption_type=consumption_type,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by,
        )

    # ================== 4. 缺料预警列表 ==================
    def list_alerts(
        self,
        alert_type: Optional[str] = None,
        alert_level: Optional[str] = None,
        status: str = "ACTIVE",
        material_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """物料预警列表"""
        return self._alert.list_alerts(
            alert_type=alert_type,
            alert_level=alert_level,
            status=status,
            material_id=material_id,
            page=page,
            page_size=page_size,
        )

    # ================== 5. 配置预警规则 ==================
    def create_alert_rule(
        self,
        rule_data: Dict[str, Any],
        current_user_id: int,
    ) -> Dict[str, Any]:
        """配置物料预警规则"""
        return self._alert.create_alert_rule(
            rule_data=rule_data,
            current_user_id=current_user_id,
        )

    # ================== 6. 物料浪费追溯 ==================
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
        return self._consumption.get_waste_records(
            material_id=material_id,
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
            min_variance_rate=min_variance_rate,
            page=page,
            page_size=page_size,
        )

    # ================== 7. 批次追溯 ==================
    def trace_batch(
        self,
        batch_no: Optional[str] = None,
        batch_id: Optional[int] = None,
        barcode: Optional[str] = None,
        trace_direction: str = "forward",
    ) -> Dict[str, Any]:
        """批次追溯 - 支持正向和反向查询"""
        return self._batch.trace_batch(
            batch_no=batch_no,
            batch_id=batch_id,
            barcode=barcode,
            trace_direction=trace_direction,
        )

    # ================== 8. 物料成本分析 ==================
    def get_cost_analysis(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        project_id: Optional[int] = None,
        category_id: Optional[int] = None,
        top_n: int = 10,
    ) -> Dict[str, Any]:
        """物料成本分析"""
        return self._cost.get_cost_analysis(
            start_date=start_date,
            end_date=end_date,
            project_id=project_id,
            category_id=category_id,
            top_n=top_n,
        )

    # ================== 9. 库存周转率 ==================
    def get_turnover_analysis(
        self,
        material_id: Optional[int] = None,
        category_id: Optional[int] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """库存周转率分析"""
        return self._cost.get_turnover_analysis(
            material_id=material_id,
            category_id=category_id,
            days=days,
        )

    # ================== 辅助方法 ==================
    def check_and_create_alerts(self, material: Material):
        """检查并创建物料预警"""
        return self._alert.check_and_create_alerts(material)

    def calculate_avg_daily_consumption(self, material_id: int, days: int = 30) -> float:
        """计算平均日消耗"""
        return self._cost.calculate_avg_daily_consumption(material_id=material_id, days=days)
