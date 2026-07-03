# -*- coding: utf-8 -*-
"""Progress compatibility route contracts."""


def test_progress_auto_preview_route_is_registered():
    from app.api.v1.endpoints.progress_compat import router

    paths = {route.path for route in router.routes}

    assert "/projects/{project_id}/auto-preview" in paths
