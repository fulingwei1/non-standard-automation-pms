# -*- coding: utf-8 -*-
"""MISC-09 cost collection endpoint permission contracts."""

import ast
from pathlib import Path


SOURCE_PATH = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "api"
    / "v1"
    / "endpoints"
    / "cost_endpoints"
    / "collection.py"
)


def _current_user_default(function_name: str) -> ast.AST:
    module = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            defaults_by_arg = dict(zip(node.args.kwonlyargs, node.args.kw_defaults))
            for arg, default in defaults_by_arg.items():
                if arg.arg == "current_user":
                    assert default is not None
                    return default
    raise AssertionError(f"{function_name} current_user dependency not found")


def test_cost_collection_collect_requires_cost_manage_permission():
    dependency = _current_user_default("run_cost_collection")

    assert isinstance(dependency, ast.Call)
    assert isinstance(dependency.func, ast.Name)
    assert dependency.func.id == "Depends"
    assert dependency.args

    required_permission = dependency.args[0]
    assert isinstance(required_permission, ast.Call)
    assert isinstance(required_permission.func, ast.Attribute)
    assert isinstance(required_permission.func.value, ast.Name)
    assert required_permission.func.value.id == "security"
    assert required_permission.func.attr == "require_permission"
    assert required_permission.args[0].value == "cost:manage"
