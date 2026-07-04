from pathlib import Path

from app.services.approval_engine.adapters import ADAPTER_REGISTRY


ROOT = Path(__file__).resolve().parents[2]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_project_budget_approval_adapter_and_template_are_registered():
    init_source = read_text("app/utils/init_approval_data.py")
    audit_source = read_text("tests/audit_p0/test_p0_02_approval_template_no_seed.py")

    assert "PROJECT_BUDGET" in ADAPTER_REGISTRY
    assert "ProjectBudgetApprovalAdapter" in read_text(
        "app/services/approval_engine/adapters/__init__.py"
    )
    assert 'template_code": "TPL_PROJECT_BUDGET"' in init_source
    assert 'entity_type": "PROJECT_BUDGET"' in init_source
    assert '"TPL_PROJECT_BUDGET"' in audit_source


def test_budget_submit_and_approve_routes_use_unified_approval_engine():
    source = read_text("app/api/v1/endpoints/budget/budgets.py")

    assert "PROJECT_BUDGET_APPROVAL_ENTITY_TYPE" in source
    assert "PROJECT_BUDGET_APPROVAL_TEMPLATE_CODE" in source
    assert "ApprovalEngineService" in source
    assert "engine.submit(" in source
    assert "get_active_budget_approval_instance" in source
    assert "get_pending_budget_approval_task" in source
    assert "engine.approve(" in source
    assert "engine.reject(" in source
    assert 'budget.status = "SUBMITTED"' not in source
    assert 'budget.status = "APPROVED"' not in source
    assert 'budget.status = "REJECTED"' not in source


def test_budget_total_amount_is_reconciled_from_items_before_workflow_changes():
    source = read_text("app/api/v1/endpoints/budget/budgets.py")
    adapter_source = read_text("app/services/approval_engine/adapters/budget.py")

    assert "calculate_budget_items_total" in source
    assert "sync_budget_total_from_items" in source
    assert "sync_budget_total_from_items(db, budget)" in source
    assert "_calculate_items_total" in adapter_source
    assert "budget.total_amount = self._calculate_items_total" in adapter_source
