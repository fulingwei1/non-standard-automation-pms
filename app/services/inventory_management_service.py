# -*- coding: utf-8 -*-
"""
库存管理服务 — 向后兼容入口
原始单体文件已拆分至 app/services/inventory/ 包。
此文件保留以确保现有 import 路径不变。
"""
from app.services.inventory.stock_update_service import InsufficientStockError  # noqa: F401
from app.services.inventory.inventory_management_facade import InventoryManagementService  # noqa: F401

__all__ = ["InventoryManagementService", "InsufficientStockError"]
