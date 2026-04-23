# -*- coding: utf-8 -*-
"""旧模块名兼容。"""

from .notifications import log_auto_invoice as _log_auto_invoice


def log_auto_invoice(service_or_db, order=None, created_items=None, auto_create: bool = False, **kwargs):
    if hasattr(service_or_db, "db") and order is not None:
        return _log_auto_invoice(service_or_db, order, created_items or [], auto_create)
    return None


__all__ = ["log_auto_invoice"]
