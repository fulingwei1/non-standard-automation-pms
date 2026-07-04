# -*- coding: utf-8 -*-
"""PRE-15: fake presale mobile AI endpoints must not be mounted."""

from pathlib import Path


def test_presale_mobile_fake_router_is_not_registered():
    api_source = Path("app/api/v1/api.py").read_text(encoding="utf-8")
    assert 'prefix="/presale-mobile"' not in api_source
    assert 'tags=["presale-mobile"]' not in api_source
