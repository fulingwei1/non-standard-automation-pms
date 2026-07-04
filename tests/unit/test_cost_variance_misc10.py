# -*- coding: utf-8 -*-
"""MISC-10 cost variance route permission and 404 contracts."""

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.cost_endpoints import variance_analysis


SOURCE_PATH = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "api"
    / "v1"
    / "endpoints"
    / "cost_endpoints"
    / "variance_analysis.py"
)


def _current_user_default(function_name: str) -> ast.AST:
    module = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    for node in module.body:
        if not isinstance(node, ast.FunctionDef) or node.name != function_name:
            continue

        defaults_by_arg = dict(zip(node.args.kwonlyargs, node.args.kw_defaults))
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


def test_cost_variance_routes_require_project_read_permission():
    for function_name in ("variance_summary", "variance_patterns", "variance_detail"):
        assert _require_permission(_current_user_default(function_name)) == "project:read"


class _NoProjectResult:
    def fetchone(self):
        return None


class _NoProjectDb:
    def execute(self, *args, **kwargs):
        return _NoProjectResult()


class _RowsResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _SummaryDb:
    def __init__(self):
        self.execute_count = 0
        self._results = [
            _RowsResult(
                [
                    SimpleNamespace(
                        id=1,
                        project_name="项目A",
                        project_code="PA",
                        product_category="ICT",
                        contract_amount=1000,
                        budget_amount=800,
                        actual_cost=900,
                    ),
                    SimpleNamespace(
                        id=2,
                        project_name="项目B",
                        project_code="PB",
                        product_category="FCT",
                        contract_amount=2000,
                        budget_amount=1000,
                        actual_cost=950,
                    ),
                ]
            ),
            _RowsResult(
                [
                    SimpleNamespace(project_id=1, cost_type="material", total=600),
                    SimpleNamespace(project_id=1, cost_type="labor", total=300),
                    SimpleNamespace(project_id=2, cost_type="material", total=950),
                ]
            ),
        ]

    def execute(self, *args, **kwargs):
        result = self._results[self.execute_count]
        self.execute_count += 1
        return result


def test_variance_detail_returns_404_for_missing_project():
    with pytest.raises(HTTPException) as exc:
        variance_analysis.variance_detail(
            db=_NoProjectDb(),
            current_user=SimpleNamespace(id=1),
            project_id=999999,
        )

    assert exc.value.status_code == 404
    assert "项目不存在" in exc.value.detail


def test_variance_summary_loads_cost_breakdowns_in_one_grouped_query():
    db = _SummaryDb()

    result = variance_analysis.variance_summary(db=db, current_user=SimpleNamespace(id=1))

    assert db.execute_count == 2
    assert result["projects"][0]["cost_breakdown"] == {"material": 600.0, "labor": 300.0}
    assert result["projects"][1]["cost_breakdown"] == {"material": 950.0}
