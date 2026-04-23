# -*- coding: utf-8 -*-
"""角色路由兼容层测试。"""

from unittest.mock import MagicMock
import sys

import pytest
from fastapi import HTTPException

# Mock optional dependencies pulled in by route imports
sys.modules.setdefault("app.services.permission_audit_service", MagicMock())
sys.modules.setdefault("app.services.notification_handlers", MagicMock())
sys.modules.setdefault("app.services.notification_handlers.email_handler", MagicMock())


class TestRolesEndpointCompatibility:
    def test_router_metadata_and_routes(self):
        from app.api.v1.endpoints import roles

        assert roles.router.prefix == "/roles"
        assert roles.router.routes[0].tags == ["roles"]
        assert roles.__all__ == ["router"]

        route_names = [route.name for route in roles.router.routes]
        assert route_names == [
            "read_root",
            "list_permissions",
            "create_role",
            "role_templates",
            "get_role",
            "update_role",
            "delete_role",
        ]

    @pytest.mark.parametrize(
        ("route_name", "args"),
        [("update_role", (1, {"role_name": "ops"})), ("delete_role", (1,))],
    )
    def test_fallback_routes_raise_not_implemented(self, route_name, args):
        from app.api.v1.endpoints.roles import router

        route = next(route for route in router.routes if route.name == route_name)
        with pytest.raises(HTTPException, match="Roles API not implemented") as exc_info:
            route.endpoint(*args)

        assert exc_info.value.status_code == 404

    def test_templates_route_precedes_dynamic_role_route(self):
        from app.api.v1.endpoints.roles import router

        paths = [route.path for route in router.routes]
        assert paths.index("/roles/templates") < paths.index("/roles/{role_id}")
