# -*- coding: utf-8 -*-
"""
工单管理 - 工具函数

保留此文件以保持向后兼容，实际逻辑已迁移到 WorkOrderService。
"""
from sqlalchemy.orm import Session

from app.models.production import WorkOrder
from app.schemas.production import WorkOrderResponse
from app.services.production.work_order_service import WorkOrderService


def get_work_order_response(db: Session, order: WorkOrder) -> WorkOrderResponse:
    """构建工单响应对象的辅助函数（委托给 WorkOrderService）"""
    service = WorkOrderService(db)
    return service.build_response(order)
