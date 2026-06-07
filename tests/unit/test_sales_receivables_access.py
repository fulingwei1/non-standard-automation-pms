# -*- coding: utf-8 -*-
from pathlib import Path


def test_sales_receivable_endpoints_require_read_permission():
    source = Path(
        "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/sales/receivables.py"
    ).read_text(encoding="utf-8")

    assert source.count('Depends(security.require_permission("contract:read"))') == 4


def test_sales_receivable_scope_uses_contract_owner_not_invoice_property():
    source = Path(
        "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/sales/receivables.py"
    ).read_text(encoding="utf-8")

    assert 'Invoice, "created_by"' not in source
    assert "Contract" in source
    assert '"sales_owner_id"' in source
    assert "outerjoin(Contract, Invoice.contract_id == Contract.id)" in source
