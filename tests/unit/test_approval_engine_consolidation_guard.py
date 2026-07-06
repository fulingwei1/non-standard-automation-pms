import sqlite3
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_runtime_code_creates_approval_action_logs_only_inside_approval_engine():
    """Only the unified approval engine may write approval action history."""
    allowed_prefix = "app/services/approval_engine/"
    violations = []

    for source_path in (PROJECT_ROOT / "app").rglob("*.py"):
        source_lines = source_path.read_text(errors="ignore").splitlines()
        writes_action_log = any(
            "ApprovalActionLog(" in line and not line.lstrip().startswith("class ")
            for line in source_lines
        )
        if not writes_action_log:
            continue

        relative_path = source_path.relative_to(PROJECT_ROOT).as_posix()
        if not relative_path.startswith(allowed_prefix):
            violations.append(relative_path)

    assert violations == []


def test_runtime_code_does_not_record_business_status_changes_as_approval_actions():
    """Business status history belongs in state/domain logs, not approval actions."""
    forbidden_action = re.compile(
        r"\baction\s*=\s*['\"](STATUS_CHANGE|STATE_CHANGE|UPDATE_STATUS|TRANSITION)['\"]"
    )
    violations = []

    for source_path in (PROJECT_ROOT / "app").rglob("*.py"):
        source = source_path.read_text(errors="ignore")
        if not (
            "ApprovalActionLog" in source
            or "_log_action(" in source
            or "record_action_log(" in source
        ):
            continue

        for match in forbidden_action.finditer(source):
            line_no = source.count("\n", 0, match.start()) + 1
            relative_path = source_path.relative_to(PROJECT_ROOT).as_posix()
            violations.append(f"{relative_path}:{line_no}:{match.group(1)}")

    assert violations == []


def test_sales_router_does_not_mount_legacy_approval_workflow_routes():
    sales_router_source = (PROJECT_ROOT / "app/api/v1/endpoints/sales/__init__.py").read_text()

    assert "router.include_router(workflows.router" not in sales_router_source
    assert not (PROJECT_ROOT / "app/api/v1/endpoints/sales/workflows.py").exists()


def test_invoice_approval_does_not_mount_global_approvals_router_under_sales_invoice():
    invoice_router_source = (
        PROJECT_ROOT / "app/api/v1/endpoints/sales/invoices/__init__.py"
    ).read_text()

    assert "from ...approvals import router as approvals_router" not in invoice_router_source
    assert "router.include_router(approvals_router)" not in invoice_router_source


def test_invoice_approval_uses_canonical_template_code():
    sources = [
        PROJECT_ROOT / "app/services/approval_workflow_service.py",
        PROJECT_ROOT / "app/services/approval_engine/adapters/invoice.py",
        PROJECT_ROOT / "app/utils/init_approval_data.py",
    ]

    for source_path in sources:
        source = source_path.read_text()
        assert "TPL_INVOICE" in source, f"{source_path.name} misses canonical invoice template"
        assert "SALES_INVOICE" not in source, f"{source_path.name} still uses legacy invoice template"


def test_runtime_code_does_not_import_deprecated_approval_workflow_engine():
    deprecated_import = "approval_engine.workflow_engine"

    for source_path in (PROJECT_ROOT / "app").rglob("*.py"):
        if source_path.name == "workflow_engine.py":
            continue
        source = source_path.read_text(errors="ignore")
        assert deprecated_import not in source, (
            f"{source_path.relative_to(PROJECT_ROOT)} imports deprecated approval workflow engine"
        )


def test_sales_approval_adapters_do_not_expose_legacy_table_sync_methods():
    from app.services.approval_engine.adapters.contract import ContractApprovalAdapter
    from app.services.approval_engine.adapters.invoice import InvoiceApprovalAdapter
    from app.services.approval_engine.adapters.quote import QuoteApprovalAdapter

    legacy_methods = {
        QuoteApprovalAdapter: (
            "create_quote_approval",
            "update_quote_approval_from_action",
        ),
        InvoiceApprovalAdapter: (
            "create_invoice_approval",
            "update_invoice_approval_from_action",
        ),
        ContractApprovalAdapter: (
            "create_contract_approval",
            "update_contract_approval_from_action",
        ),
    }

    for adapter_cls, method_names in legacy_methods.items():
        for method_name in method_names:
            assert not hasattr(adapter_cls, method_name), (
                f"{adapter_cls.__name__}.{method_name} still writes legacy approval tables"
            )


def test_sales_approval_services_do_not_query_retired_workflow_models():
    legacy_sources = [
        PROJECT_ROOT / "app/services/approval_workflow_service.py",
        PROJECT_ROOT / "app/services/sales_reminder/sales_flow_reminders.py",
    ]

    forbidden_tokens = (
        "app.models.sales.workflow",
        "ApprovalRecord",
        "ApprovalWorkflowStep",
        "ApprovalRecordStatusEnum",
    )

    for source_path in legacy_sources:
        source = source_path.read_text()
        for token in forbidden_tokens:
            assert token not in source, f"{source_path.name} still depends on {token}"


def test_legacy_approval_tables_are_archived_then_dropped_on_temp_database():
    from scripts.consolidate_legacy_approval_tables import (
        LEGACY_APPROVAL_TABLES,
        consolidate_legacy_approval_tables,
    )

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE quote_approvals (
            id INTEGER PRIMARY KEY,
            quote_id INTEGER,
            approval_level INTEGER,
            approval_role TEXT,
            approver_id INTEGER,
            approval_result TEXT,
            status TEXT,
            created_at TEXT,
            updated_at TEXT,
            tenant_id INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE invoice_approvals (
            id INTEGER PRIMARY KEY,
            invoice_id INTEGER,
            approval_level INTEGER,
            approval_role TEXT,
            approver_id INTEGER,
            approval_result TEXT,
            status TEXT,
            created_at TEXT,
            updated_at TEXT,
            tenant_id INTEGER
        )
        """
    )
    conn.execute(
        """
        INSERT INTO quote_approvals (
            id, quote_id, approval_level, approval_role, approver_id,
            approval_result, status, created_at, updated_at, tenant_id
        )
        VALUES (1, 101, 2, 'SALES_MANAGER', 9, 'APPROVED', 'APPROVED',
                '2026-01-01T10:00:00', '2026-01-01T10:30:00', 7)
        """
    )
    conn.execute(
        """
        INSERT INTO invoice_approvals (
            id, invoice_id, approval_level, approval_role, approver_id,
            approval_result, status, created_at, updated_at, tenant_id
        )
        VALUES (2, 202, 1, 'FINANCE', 8, NULL, 'PENDING',
                '2026-01-02T10:00:00', '2026-01-02T10:00:00', 7)
        """
    )
    conn.commit()

    assert "quote_approvals" in LEGACY_APPROVAL_TABLES
    assert "invoice_approvals" in LEGACY_APPROVAL_TABLES

    report = consolidate_legacy_approval_tables(conn, drop_legacy_tables=True)

    assert report["archived_rows"] == 2
    assert report["dropped_tables"] == ["invoice_approvals", "quote_approvals"]

    rows = conn.execute(
        """
        SELECT source_table, source_id, entity_type, entity_id, status, approver_id
        FROM legacy_approval_archives
        ORDER BY source_table, source_id
        """
    ).fetchall()
    assert [dict(row) for row in rows] == [
        {
            "source_table": "invoice_approvals",
            "source_id": 2,
            "entity_type": "INVOICE",
            "entity_id": 202,
            "status": "PENDING",
            "approver_id": 8,
        },
        {
            "source_table": "quote_approvals",
            "source_id": 1,
            "entity_type": "QUOTE",
            "entity_id": 101,
            "status": "APPROVED",
            "approver_id": 9,
        },
    ]

    remaining_tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    assert "quote_approvals" not in remaining_tables
    assert "invoice_approvals" not in remaining_tables
    assert "legacy_approval_archives" in remaining_tables

    second_report = consolidate_legacy_approval_tables(conn, drop_legacy_tables=True)
    assert second_report["archived_rows"] == 0
    assert second_report["dropped_tables"] == []


def test_retired_approval_tables_are_not_registered_in_model_metadata():
    import app.models  # noqa: F401
    from app.models.base import Base
    from scripts.consolidate_legacy_approval_tables import LEGACY_APPROVAL_TABLES

    assert set(LEGACY_APPROVAL_TABLES).isdisjoint(Base.metadata.tables)
