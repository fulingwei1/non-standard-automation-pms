# -*- coding: utf-8 -*-
from pathlib import Path


def test_sales_payment_plan_endpoints_require_permissions():
    source = Path(
        "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/sales/payments/payment_plans.py"
    ).read_text(encoding="utf-8")

    assert source.count('Depends(security.require_permission("contract:read"))') == 2
    assert source.count('Depends(security.require_permission("contract:update"))') == 2


def test_sales_payment_plan_endpoints_scope_by_contract_owner_and_do_not_fallback_project():
    source = Path(
        "/Users/flw/non-standard-automation-pm/app/api/v1/endpoints/sales/payments/payment_plans.py"
    ).read_text(encoding="utf-8")

    assert "filter_sales_finance_data_by_scope" in source
    assert "check_sales_data_permission" in source
    assert '"sales_owner_id"' in source
    assert "fallback_project" not in source
    assert "合同未关联项目" in source
