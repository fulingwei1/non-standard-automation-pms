# -*- coding: utf-8 -*-
"""MISC-14 PM involvement endpoint and data-source contracts."""

import ast
from pathlib import Path

import pytest

from app.models.presale import PresaleSolutionTemplate, PresaleSupportTicket
from app.models.project import Project
from app.services.pm_involvement_service import PMInvolvementService


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "app" / "api" / "v1" / "endpoints" / "performance" / "pm_involvement.py"
PRESALE_TICKET_CRUD_PATH = (
    ROOT / "app" / "api" / "v1" / "endpoints" / "presale" / "tickets" / "crud.py"
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


def _depends_target(default: ast.AST) -> ast.AST:
    assert isinstance(default, ast.Call)
    assert isinstance(default.func, ast.Name)
    assert default.func.id == "Depends"
    assert default.args
    return default.args[0]


def _require_permission(default: ast.AST) -> str:
    dependency = _depends_target(default)
    assert isinstance(dependency, ast.Call)
    assert isinstance(dependency.func, ast.Attribute)
    assert isinstance(dependency.func.value, ast.Name)
    assert dependency.func.value.id == "security"
    assert dependency.func.attr == "require_permission"
    return dependency.args[0].value


def _active_user_dependency(default: ast.AST) -> str:
    dependency = _depends_target(default)
    assert isinstance(dependency, ast.Attribute)
    assert isinstance(dependency.value, ast.Name)
    assert dependency.value.id == "security"
    return dependency.attr


def test_pm_involvement_post_endpoints_require_presale_manage_permission():
    for function_name in (
        "judge_pm_involvement",
        "auto_judge_from_ticket",
        "generate_notification",
    ):
        assert _require_permission(_current_user_default(function_name)) == "presale:manage"


def test_pm_involvement_read_endpoints_require_authenticated_user():
    for function_name in (
        "get_similar_projects",
        "check_standard_solution",
        "get_test_examples",
    ):
        assert _active_user_dependency(_current_user_default(function_name)) == "get_current_active_user"


def test_similar_project_count_uses_project_history(db_session):
    db_session.add_all(
        [
            Project(
                project_code="PMI-001",
                project_name="SMT success",
                project_type="SMT",
                industry="汽车电子",
                status="COMPLETED",
            ),
            Project(
                project_code="PMI-002",
                project_name="SMT failed",
                project_type="SMT",
                industry="汽车电子",
                status="FAILED",
            ),
            Project(
                project_code="PMI-003",
                project_name="SMT running",
                project_type="SMT",
                industry="汽车电子",
                status="EXECUTING",
            ),
        ]
    )
    db_session.commit()

    result = PMInvolvementService.get_similar_project_count("SMT", "汽车电子", db_session)

    assert result["总数"] == 3
    assert result["成功数"] == 1
    assert result["失败数"] == 1
    assert result["成功率"] == pytest.approx(1 / 3)


def test_standard_solution_check_uses_active_template_library(db_session):
    db_session.add(
        PresaleSolutionTemplate(
            template_no="PMI-TPL-001",
            name="SMT 标准方案",
            test_type="SMT",
            industry="汽车电子",
            is_active=True,
        )
    )
    db_session.commit()

    assert PMInvolvementService.check_has_standard_solution("SMT", "汽车电子", db_session)
    assert not PMInvolvementService.check_has_standard_solution("EOL", "汽车电子", db_session)


def test_auto_judge_from_ticket_reads_ticket_and_history(db_session):
    db_session.add_all(
        [
            PresaleSupportTicket(
                ticket_no="PMI-TICKET-001",
                title="SMT",
                ticket_type="SOLUTION",
                applicant_id=1,
            ),
            PresaleSolutionTemplate(
                template_no="PMI-TPL-002",
                name="SMT 标准方案",
                test_type="SMT",
                is_active=True,
            ),
            Project(project_code="PMI-004", project_name="SMT 1", project_type="SMT"),
            Project(project_code="PMI-005", project_name="SMT 2", project_type="SMT"),
            Project(project_code="PMI-006", project_name="SMT 3", project_type="SMT"),
        ]
    )
    db_session.commit()

    result = PMInvolvementService.auto_judge_from_ticket(1, db_session)

    assert result["建议"] == "PM签约后介入"
    assert result["风险等级"] == "低"


def test_presale_ticket_creation_no_longer_hardcodes_zero_history():
    source = PRESALE_TICKET_CRUD_PATH.read_text(encoding="utf-8")

    assert '"历史相似项目数": 0' not in source
    assert '"失败项目数": 0' not in source
    assert "PMInvolvementService.get_similar_project_count" in source
