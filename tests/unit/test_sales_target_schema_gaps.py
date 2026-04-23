import pytest

from app.schemas.sales_target import AutoBreakdownRequest, SalesTargetV2Create


def test_sales_target_v2_create_rejects_invalid_period():
    with pytest.raises(ValueError, match="target_period must be one of: year, quarter, month"):
        SalesTargetV2Create(target_period="week", target_year=2026, target_type="company")


def test_sales_target_v2_create_rejects_invalid_type():
    with pytest.raises(ValueError, match="target_type must be one of: company, team, personal"):
        SalesTargetV2Create(target_period="year", target_year=2026, target_type="dept")


def test_auto_breakdown_request_rejects_invalid_method():
    with pytest.raises(ValueError, match="breakdown_method must be one of: EQUAL, RATIO"):
        AutoBreakdownRequest(breakdown_method="SMART")
