# -*- coding: utf-8 -*-
"""MISC-11 solution credit internal endpoint permission contracts."""

import ast
from pathlib import Path


SOURCE_PATH = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "api"
    / "v1"
    / "endpoints"
    / "solution_credits"
    / "internal.py"
)


def _current_user_default(function_name: str) -> ast.AST:
    module = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    for node in module.body:
        if not isinstance(node, ast.AsyncFunctionDef) or node.name != function_name:
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


def test_internal_refund_requires_solution_credit_manage_permission():
    assert (
        _require_permission(_current_user_default("internal_refund_credits"))
        == "solution_credit:manage"
    )
