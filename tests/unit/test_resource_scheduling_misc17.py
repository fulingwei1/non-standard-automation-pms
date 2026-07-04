from pathlib import Path

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints import resource_scheduling as legacy_resource_scheduling


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_main_api_does_not_mount_legacy_resource_scheduling_placeholder():
    source = _read("app/api/v1/api.py")

    assert "from app.api.v1.endpoints.resource_scheduling" not in source
    assert 'prefix="/resource-scheduling"' not in source
    assert "resource_scheduling_router" not in source
    assert 'prefix="/engineer-scheduling"' in source


def test_legacy_resource_scheduling_no_longer_returns_placeholder_payload():
    source = _read("app/api/v1/endpoints/resource_scheduling.py")

    assert "resource_scheduling module placeholder" not in source
    assert "from .resourcescheduling import router" not in source
    assert "legacy_resource_scheduling_disabled" in source
    assert "501" in source


def test_legacy_resource_scheduling_endpoint_returns_501_when_accidentally_mounted():
    with pytest.raises(HTTPException) as exc_info:
        legacy_resource_scheduling.legacy_resource_scheduling_disabled()

    assert exc_info.value.status_code == 501
    assert "/engineer-scheduling" in str(exc_info.value.detail)
