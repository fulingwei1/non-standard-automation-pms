# -*- coding: utf-8 -*-
"""旧模块名兼容。"""

from types import SimpleNamespace

from .main import check_and_create_invoice_request as _check_and_create_invoice_request


def check_and_create_invoice_request(service_or_db, acceptance_order_id: int, auto_create: bool = False):
    service = service_or_db if hasattr(service_or_db, "db") else SimpleNamespace(db=service_or_db)
    result = _check_and_create_invoice_request(service, acceptance_order_id, auto_create)
    return result if result.get("success") else False


__all__ = ["check_and_create_invoice_request"]
