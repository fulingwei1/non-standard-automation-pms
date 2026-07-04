# -*- coding: utf-8 -*-
"""MISC-04 legacy best_practice endpoint guardrails."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LEGACY_SOURCE = ROOT / "app" / "api" / "v1" / "endpoints" / "best_practice.py"
API_SOURCE = ROOT / "app" / "api" / "v1" / "api.py"
PROJECTS_INIT_SOURCE = ROOT / "app" / "api" / "v1" / "endpoints" / "projects" / "__init__.py"


EXPECTED_LEGACY_PERMISSIONS = {
    "abc_classification": "material:update",
    "supplier_auto_reclassify": "supplier:update",
    "shortage_escalation": "material:update",
    "set_kitting_targets": "project:update",
}


def _current_user_default(function_name: str) -> ast.AST:
    module = ast.parse(LEGACY_SOURCE.read_text(encoding="utf-8"))
    for node in module.body:
        if not isinstance(node, ast.FunctionDef) or node.name != function_name:
            continue

        positional_args_with_defaults = node.args.args[-len(node.args.defaults) :]
        defaults_by_arg = dict(zip(positional_args_with_defaults, node.args.defaults))
        defaults_by_arg.update(zip(node.args.kwonlyargs, node.args.kw_defaults))
        for arg, default in defaults_by_arg.items():
            if arg.arg == "current_user":
                assert default is not None
                return default

    raise AssertionError(f"{function_name} current_user dependency not found")


def _require_permission(default: ast.AST) -> str:
    assert isinstance(default, ast.Call)
    assert isinstance(default.func, ast.Name)
    assert default.func.id == "Depends"
    assert default.args

    required_permission = default.args[0]
    assert isinstance(required_permission, ast.Call)
    assert isinstance(required_permission.func, ast.Attribute)
    assert isinstance(required_permission.func.value, ast.Name)
    assert required_permission.func.value.id == "security"
    assert required_permission.func.attr == "require_permission"
    return required_permission.args[0].value


def test_legacy_best_practice_write_endpoints_are_permission_guarded():
    for function_name, expected_permission in EXPECTED_LEGACY_PERMISSIONS.items():
        assert _require_permission(_current_user_default(function_name)) == expected_permission


def test_legacy_best_practice_module_is_not_mounted_in_main_router():
    api_source = API_SOURCE.read_text(encoding="utf-8")

    assert "app.api.v1.endpoints.best_practice" not in api_source
    assert "best_practice.material_router" not in api_source
    assert "best_practice.supplier_router" not in api_source
    assert "best_practice.project_router" not in api_source


def test_real_project_best_practices_route_stays_mounted():
    projects_source = PROJECTS_INIT_SOURCE.read_text(encoding="utf-8")

    assert "ext_best_practices" in projects_source
    assert "router.include_router(ext_best_practices.router" in projects_source
