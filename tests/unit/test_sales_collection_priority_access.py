# -*- coding: utf-8 -*-
from pathlib import Path


def test_sales_collection_priority_endpoints_require_contract_read_permission():
    source = Path(
        "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/sales/collection_priority.py"
    ).read_text(encoding="utf-8")

    assert source.count('Depends(security.require_permission("contract:read"))') == 3


def test_sales_collection_priority_uses_finance_data_scope_by_contract_owner():
    source = Path(
        "/Users/flw/non-standard-automation-pm/app/services/sales/collection_priority_service.py"
    ).read_text(encoding="utf-8")

    assert "filter_sales_finance_data_by_scope" in source
    assert "current_user" in source
    assert "Contract" in source
    assert '"sales_owner_id"' in source
