from pathlib import Path

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints import change_impact as legacy_change_impact
from app.api.v1.endpoints.projects import change_impact as project_change_impact


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_main_api_mounts_real_project_change_impact_not_legacy_placeholder():
    source = _read("app/api/v1/api.py")

    assert (
        "from app.api.v1.endpoints.projects.change_impact import "
        "router as project_change_impact_router"
    ) in source
    assert (
        'api_router.include_router(project_change_impact_router, prefix="", '
        'tags=["project-change-impact"])'
    ) in source
    assert (
        "from app.api.v1.endpoints.change_impact import router as "
        "change_impact_router"
    ) not in source
    assert 'prefix="/change-impact"' not in source


def test_real_project_change_impact_router_exposes_contract_paths():
    paths = {route.path for route in project_change_impact.router.routes}

    assert "/project-change-impacts/assess" in paths
    assert "/project-change-impacts/execute-linkage" in paths
    assert "/project-change-impacts/by-project/{project_id}/summary" in paths


def test_legacy_change_impact_router_no_longer_returns_placeholder_payload():
    source = _read("app/api/v1/endpoints/change_impact.py")

    assert "change_impact module placeholder" not in source
    assert "from .changeimpact import router" not in source
    assert "legacy_change_impact_disabled" in source
    assert "501" in source


def test_legacy_change_impact_endpoint_returns_501_when_accidentally_mounted():
    with pytest.raises(HTTPException) as exc_info:
        legacy_change_impact.legacy_change_impact_disabled()

    assert exc_info.value.status_code == 501
    assert "/project-change-impacts" in str(exc_info.value.detail)
