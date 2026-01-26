# -*- coding: utf-8 -*-
"""
发票自动服务模块

聚合所有发票自动相关的服务，保持向后兼容
"""
from .base import InvoiceAutoService
from .main import check_and_create_invoice_request

__all__ = ["InvoiceAutoService"]

# 将方法添加到类中，保持向后兼容
def _patch_methods():
    """将模块函数作为方法添加到类中"""
    InvoiceAutoService.check_and_create_invoice_request = lambda self, acceptance_order_id, auto_create=False: check_and_create_invoice_request(self, acceptance_order_id, auto_create)

_patch_methods()
