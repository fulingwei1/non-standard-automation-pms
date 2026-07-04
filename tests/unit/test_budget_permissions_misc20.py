# -*- coding: utf-8 -*-
"""MISC-20 budget write endpoint permission contracts."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


EXPECTED_PERMISSIONS = {
    "app/api/v1/endpoints/budget/budgets.py": {
        "update_budget": "budget:update",
        "submit_budget": "budget:update",
        "delete_budget": "budget:delete",
    },
    "app/api/v1/endpoints/budget/items.py": {
        "create_budget_item": "budget:update",
        "update_budget_item": "budget:update",
        "delete_budget_item": "budget:update",
    },
    "app/api/v1/endpoints/budget/allocation_rules.py": {
        "create_allocation_rule": "budget:create",
        "update_allocation_rule": "budget:update",
        "delete_allocation_rule": "budget:delete",
    },
}


def _required_permission(source_path: Path, function_name: str) -> str:
    module = ast.parse(source_path.read_text(encoding="utf-8"))
    for node in module.body:
        if not isinstance(node, ast.FunctionDef) or node.name != function_name:
            continue

        defaults_by_arg = dict(zip(node.args.kwonlyargs, node.args.kw_defaults))
        current_user_default = next(
            default
            for arg, default in defaults_by_arg.items()
            if arg.arg == "current_user"
        )
        assert isinstance(current_user_default, ast.Call)
        required_permission = current_user_default.args[0]
        assert isinstance(required_permission, ast.Call)
        assert isinstance(required_permission.func, ast.Attribute)
        assert required_permission.func.attr == "require_permission"
        return required_permission.args[0].value

    raise AssertionError(f"{function_name} current_user dependency not found")


def test_budget_write_endpoints_do_not_use_budget_read_permission():
    for relative_path, expected_by_function in EXPECTED_PERMISSIONS.items():
        source_path = ROOT / relative_path
        for function_name, expected_permission in expected_by_function.items():
            assert _required_permission(source_path, function_name) == expected_permission
