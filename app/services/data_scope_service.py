# -*- coding: utf-8 -*-
"""
数据权限服务 - 向后兼容入口

原始实现已整合到 data_scope_service_enhanced.py (#43)。
DataScopeService 现在是 DataScopeServiceEnhanced 的别名。
"""

from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced  # noqa: F401

# 向后兼容别名
DataScopeService = DataScopeServiceEnhanced

__all__ = ["DataScopeService", "DataScopeServiceEnhanced"]
