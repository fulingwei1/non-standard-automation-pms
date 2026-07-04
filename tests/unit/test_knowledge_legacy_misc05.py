from pathlib import Path

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints import knowledge as legacy_knowledge


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_legacy_knowledge_package_is_not_registered_by_main_api_routers():
    for path in ("app/api/v1/api.py", "app/api/v1/api_lazy.py"):
        source = _read(path)
        assert "app.api.v1.endpoints.knowledge" not in source
        assert "endpoints import knowledge" not in source
        assert 'prefix="/knowledge"' not in source
        assert "prefix='/knowledge'" not in source


def test_legacy_knowledge_router_no_longer_aggregates_broken_subrouters():
    source = _read("app/api/v1/endpoints/knowledge/__init__.py")

    assert "extraction.router" not in source
    assert "induction.router" not in source
    assert "alerts.router" not in source
    assert "search.router" not in source
    assert "legacy_knowledge_disabled" in source
    assert "501" in source


def test_legacy_knowledge_endpoint_returns_501_when_accidentally_mounted():
    with pytest.raises(HTTPException) as exc_info:
        legacy_knowledge.legacy_knowledge_disabled("search")

    assert exc_info.value.status_code == 501
    assert "/knowledge-base" in str(exc_info.value.detail)
