import sqlite3


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
        is not None
    )


def test_retire_unused_tables_archives_rows_before_drop(tmp_path):
    from scripts.retire_unused_tables_20260705 import retire_unused_tables

    db_path = tmp_path / "app.db"
    archive_path = tmp_path / "retired_archive.db"

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE currency_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            currency TEXT NOT NULL UNIQUE,
            rate REAL NOT NULL
        );
        INSERT INTO currency_rates(currency, rate) VALUES ('USD', 7.2);

        CREATE TABLE investors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            investor_name TEXT NOT NULL
        );
        INSERT INTO investors(investor_name) VALUES ('Demo Capital');

        CREATE TABLE funding_rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_investor_id INTEGER REFERENCES investors(id)
        );
        INSERT INTO funding_rounds(lead_investor_id) VALUES (1);

        CREATE TABLE funding_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            funding_round_id INTEGER REFERENCES funding_rounds(id),
            investor_id INTEGER REFERENCES investors(id)
        );
        INSERT INTO funding_records(funding_round_id, investor_id) VALUES (1, 1);

        CREATE TABLE approval_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_code TEXT NOT NULL
        );
        INSERT INTO approval_templates(template_code) VALUES ('KEEP');
        """
    )
    conn.commit()
    conn.close()

    report = retire_unused_tables(
        db_path,
        archive_path=archive_path,
        drop_tables=True,
        create_backup=False,
    )

    assert report["dropped_tables"] == [
        "funding_records",
        "funding_rounds",
        "investors",
        "currency_rates",
    ]
    assert report["archived_rows"]["currency_rates"] == 1
    assert report["archived_rows"]["funding_records"] == 1

    conn = sqlite3.connect(db_path)
    try:
        assert not _table_exists(conn, "currency_rates")
        assert not _table_exists(conn, "funding_records")
        assert not _table_exists(conn, "funding_rounds")
        assert not _table_exists(conn, "investors")
        assert _table_exists(conn, "approval_templates")
    finally:
        conn.close()

    archive = sqlite3.connect(archive_path)
    try:
        assert archive.execute("SELECT COUNT(*) FROM currency_rates").fetchone()[0] == 1
        assert archive.execute("SELECT COUNT(*) FROM funding_records").fetchone()[0] == 1
        assert archive.execute(
            "SELECT COUNT(*) FROM retired_table_manifest WHERE table_name='currency_rates'"
        ).fetchone()[0] == 1
    finally:
        archive.close()


def test_retired_models_are_not_registered_in_sqlalchemy_metadata():
    import app.models  # noqa: F401
    from app.models.base import Base

    retired_model_tables = {
        "after_sales_support_tickets",
        "change_approval_records",
        "data_scope_rules",
        "ecn_approval_matrix",
        "ecn_approvals",
        "lead_requirement_basic_v2",
        "lead_requirement_technical_v2",
        "lead_requirement_facility_v2",
        "quote_cost_histories",
        "quotation_templates",
        "presale_solution_templates",
        "role_data_scopes",
        "resource_conflict",
        "solution_versions",
        "sales_targets_v2",
        "target_breakdown_logs",
        "timesheet_approval_log",
    }

    assert retired_model_tables.isdisjoint(Base.metadata.tables)
    assert "production_resource_conflicts" in Base.metadata.tables
    assert all(
        foreign_key.column.table.name != "solution_versions"
        for table in Base.metadata.tables.values()
        for foreign_key in table.foreign_keys
    )
    assert all(
        foreign_key.column.table.name not in {"data_scope_rules", "role_data_scopes"}
        for table in Base.metadata.tables.values()
        for foreign_key in table.foreign_keys
    )
    assert all(
        foreign_key.column.table.name != "after_sales_support_tickets"
        for table in Base.metadata.tables.values()
        for foreign_key in table.foreign_keys
    )
    assert all(
        foreign_key.column.table.name != "change_approval_records"
        for table in Base.metadata.tables.values()
        for foreign_key in table.foreign_keys
    )
    assert all(
        foreign_key.column.table.name != "timesheet_approval_log"
        for table in Base.metadata.tables.values()
        for foreign_key in table.foreign_keys
    )
    assert all(
        foreign_key.column.table.name not in {"ecn_approvals", "ecn_approval_matrix"}
        for table in Base.metadata.tables.values()
        for foreign_key in table.foreign_keys
    )
    assert all(
        foreign_key.column.table.name != "quote_cost_histories"
        for table in Base.metadata.tables.values()
        for foreign_key in table.foreign_keys
    )


def test_retire_unused_tables_archives_quote_cost_histories_before_drop(tmp_path):
    from scripts.retire_unused_tables_20260705 import retire_unused_tables

    db_path = tmp_path / "app.db"
    archive_path = tmp_path / "retired_archive.db"

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE quote_cost_histories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_id INTEGER NOT NULL,
            quote_version_id INTEGER NOT NULL,
            total_price NUMERIC(12, 2),
            total_cost NUMERIC(12, 2),
            gross_margin NUMERIC(5, 2),
            cost_breakdown JSON,
            change_type TEXT,
            change_reason TEXT,
            changed_by INTEGER,
            created_at TEXT NOT NULL
        );
        INSERT INTO quote_cost_histories(
            quote_id, quote_version_id, total_price, total_cost, gross_margin, change_type, created_at
        )
        VALUES (1, 1, 1000, 700, 30, 'SEED', '2026-07-05 10:00:00');
        """
    )
    conn.commit()
    conn.close()

    report = retire_unused_tables(
        db_path,
        archive_path=archive_path,
        drop_tables=True,
        create_backup=False,
    )

    assert "quote_cost_histories" in report["dropped_tables"]
    assert report["archived_rows"]["quote_cost_histories"] == 1

    conn = sqlite3.connect(db_path)
    try:
        assert not _table_exists(conn, "quote_cost_histories")
    finally:
        conn.close()

    archive = sqlite3.connect(archive_path)
    try:
        assert archive.execute("SELECT COUNT(*) FROM quote_cost_histories").fetchone()[0] == 1
    finally:
        archive.close()


def test_retire_unused_tables_migrates_change_approval_records_before_drop(tmp_path):
    from scripts.retire_unused_tables_20260705 import retire_unused_tables

    db_path = tmp_path / "app.db"
    archive_path = tmp_path / "retired_archive.db"

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            real_name TEXT
        );
        INSERT INTO users(id, username, real_name) VALUES (1, 'submitter', '提交人'), (2, 'pm', '项目经理');

        CREATE TABLE change_requests (
            id INTEGER PRIMARY KEY,
            tenant_id INTEGER,
            change_code TEXT,
            title TEXT,
            project_id INTEGER,
            submitter_id INTEGER,
            submitter_name TEXT,
            submit_date TEXT,
            status TEXT
        );
        INSERT INTO change_requests(
            id, tenant_id, change_code, title, project_id, submitter_id, submitter_name, submit_date, status
        )
        VALUES (11, 1, 'CHG-11', '客户范围变更', 3, 1, '提交人', '2026-07-01 09:00:00', 'APPROVED');

        CREATE TABLE approval_templates (
            id INTEGER PRIMARY KEY,
            template_code TEXT NOT NULL UNIQUE,
            template_name TEXT NOT NULL,
            entity_type TEXT,
            is_active INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        INSERT INTO approval_templates(
            id, template_code, template_name, entity_type, is_active, created_at, updated_at
        )
        VALUES (4, 'TPL_PROJECT', '项目立项审批', 'PROJECT', 1, '2026-01-01', '2026-01-01');

        CREATE TABLE approval_flow_definitions (
            id INTEGER PRIMARY KEY,
            template_id INTEGER NOT NULL,
            flow_name TEXT NOT NULL,
            is_default INTEGER,
            is_active INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        INSERT INTO approval_flow_definitions(
            id, template_id, flow_name, is_default, is_active, created_at, updated_at
        )
        VALUES (5, 4, '项目默认审批流', 1, 1, '2026-01-01', '2026-01-01');

        CREATE TABLE approval_instances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER,
            instance_no TEXT NOT NULL UNIQUE,
            template_id INTEGER NOT NULL,
            flow_id INTEGER NOT NULL,
            entity_type TEXT,
            entity_id INTEGER,
            initiator_id INTEGER NOT NULL,
            initiator_name TEXT,
            form_data TEXT,
            status TEXT NOT NULL,
            title TEXT,
            summary TEXT,
            submitted_at TEXT,
            completed_at TEXT,
            final_comment TEXT,
            final_approver_id INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE approval_action_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER,
            instance_id INTEGER NOT NULL,
            operator_id INTEGER NOT NULL,
            operator_name TEXT,
            action TEXT NOT NULL,
            action_detail TEXT,
            comment TEXT,
            attachments TEXT,
            before_status TEXT,
            after_status TEXT,
            action_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE change_approval_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER,
            change_request_id INTEGER NOT NULL,
            approver_id INTEGER NOT NULL,
            approver_name TEXT,
            approver_role TEXT,
            approval_date TEXT,
            decision TEXT NOT NULL,
            comments TEXT,
            attachments TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        INSERT INTO change_approval_records(
            id, tenant_id, change_request_id, approver_id, approver_name, approver_role,
            approval_date, decision, comments, attachments, created_at, updated_at
        )
        VALUES (
            7, 1, 11, 2, '项目经理', 'PM', '2026-07-01 10:00:00',
            'APPROVED', '同意', '[{"name":"review.pdf"}]', '2026-07-01 10:00:00', '2026-07-01 10:00:00'
        );
        """
    )
    conn.commit()
    conn.close()

    report = retire_unused_tables(
        db_path,
        archive_path=archive_path,
        drop_tables=True,
        create_backup=False,
    )

    assert "change_approval_records" in report["dropped_tables"]
    assert report["archived_rows"]["change_approval_records"] == 1
    assert report["migrated_change_approval_records"] == {
        "source_rows": 1,
        "inserted_instances": 1,
        "existing_instances": 0,
        "inserted_logs": 1,
        "skipped_rows": 0,
    }

    conn = sqlite3.connect(db_path)
    try:
        assert not _table_exists(conn, "change_approval_records")
        instance = conn.execute(
            """
            SELECT id, entity_type, entity_id, status
            FROM approval_instances
            WHERE entity_type = 'PROJECT_CHANGE_REQUEST' AND entity_id = 11
            """
        ).fetchone()
        assert instance is not None
        assert instance[3] == "APPROVED"
        log = conn.execute(
            """
            SELECT action, operator_id, comment, attachments
            FROM approval_action_logs
            WHERE instance_id = ?
            """,
            (instance[0],),
        ).fetchone()
        assert log == ("APPROVE", 2, "同意", '[{"name":"review.pdf"}]')
    finally:
        conn.close()


def test_retire_unused_tables_migrates_timesheet_approval_log_before_drop(tmp_path):
    from scripts.retire_unused_tables_20260705 import retire_unused_tables

    db_path = tmp_path / "app.db"
    archive_path = tmp_path / "retired_archive.db"

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            real_name TEXT
        );
        INSERT INTO users(id, username, real_name)
        VALUES (1, 'engineer', '工程师'), (2, 'manager', '经理'), (3, 'orphan', '孤儿审批人');

        CREATE TABLE timesheet (
            id INTEGER PRIMARY KEY,
            tenant_id INTEGER,
            timesheet_no TEXT,
            user_id INTEGER,
            user_name TEXT,
            work_date TEXT,
            hours NUMERIC,
            project_id INTEGER,
            project_name TEXT,
            submit_time TEXT,
            approve_time TEXT,
            status TEXT
        );
        INSERT INTO timesheet(
            id, tenant_id, timesheet_no, user_id, user_name, work_date, hours,
            project_id, project_name, submit_time, approve_time, status
        )
        VALUES (
            21, 1, 'TS-21', 1, '工程师', '2026-07-01', 8,
            5, '项目A', '2026-07-01 09:00:00', '2026-07-01 12:00:00', 'APPROVED'
        );

        CREATE TABLE approval_templates (
            id INTEGER PRIMARY KEY,
            template_code TEXT NOT NULL UNIQUE,
            template_name TEXT NOT NULL,
            entity_type TEXT,
            is_active INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        INSERT INTO approval_templates(
            id, template_code, template_name, entity_type, is_active, created_at, updated_at
        )
        VALUES (8, 'TIMESHEET_APPROVAL', '工时审批', 'TIMESHEET', 1, '2026-01-01', '2026-01-01');

        CREATE TABLE approval_flow_definitions (
            id INTEGER PRIMARY KEY,
            template_id INTEGER NOT NULL,
            flow_name TEXT NOT NULL,
            is_default INTEGER,
            is_active INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        INSERT INTO approval_flow_definitions(
            id, template_id, flow_name, is_default, is_active, created_at, updated_at
        )
        VALUES (11, 8, '工时审批-标准流程', 1, 1, '2026-01-01', '2026-01-01');

        CREATE TABLE approval_instances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER,
            instance_no TEXT NOT NULL UNIQUE,
            template_id INTEGER NOT NULL,
            flow_id INTEGER NOT NULL,
            entity_type TEXT,
            entity_id INTEGER,
            initiator_id INTEGER NOT NULL,
            initiator_name TEXT,
            form_data TEXT,
            status TEXT NOT NULL,
            title TEXT,
            summary TEXT,
            submitted_at TEXT,
            completed_at TEXT,
            final_comment TEXT,
            final_approver_id INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE approval_action_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER,
            instance_id INTEGER NOT NULL,
            operator_id INTEGER NOT NULL,
            operator_name TEXT,
            action TEXT NOT NULL,
            action_detail TEXT,
            comment TEXT,
            attachments TEXT,
            before_status TEXT,
            after_status TEXT,
            action_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE timesheet_approval_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER,
            timesheet_id INTEGER,
            batch_id INTEGER,
            approver_id INTEGER NOT NULL,
            approver_name TEXT,
            action TEXT NOT NULL,
            comment TEXT,
            approved_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        INSERT INTO timesheet_approval_log(
            id, tenant_id, timesheet_id, batch_id, approver_id, approver_name,
            action, comment, approved_at, created_at, updated_at
        )
        VALUES (
            7, 1, 21, NULL, 2, '经理',
            'APPROVE', '同意', '2026-07-01 12:00:00', '2026-07-01 12:00:00', '2026-07-01 12:00:00'
        );
        INSERT INTO timesheet_approval_log(
            id, tenant_id, timesheet_id, batch_id, approver_id, action, created_at, updated_at
        )
        VALUES (
            8, 1, NULL, NULL, 3, 'timesheet_appr230118', '2026-07-01 13:00:00', '2026-07-01 13:00:00'
        );
        """
    )
    conn.commit()
    conn.close()

    report = retire_unused_tables(
        db_path,
        archive_path=archive_path,
        drop_tables=True,
        create_backup=False,
    )

    assert "timesheet_approval_log" in report["dropped_tables"]
    assert report["archived_rows"]["timesheet_approval_log"] == 2
    assert report["migrated_timesheet_approval_log"] == {
        "source_rows": 2,
        "inserted_instances": 1,
        "existing_instances": 0,
        "inserted_logs": 1,
        "skipped_rows": 1,
    }

    conn = sqlite3.connect(db_path)
    try:
        assert not _table_exists(conn, "timesheet_approval_log")
        instance = conn.execute(
            """
            SELECT id, entity_type, entity_id, status, initiator_id
            FROM approval_instances
            WHERE entity_type = 'TIMESHEET' AND entity_id = 21
            """
        ).fetchone()
        assert instance is not None
        assert instance[3] == "APPROVED"
        assert instance[4] == 1
        log = conn.execute(
            """
            SELECT action, operator_id, comment, action_detail
            FROM approval_action_logs
            WHERE instance_id = ?
            """,
            (instance[0],),
        ).fetchone()
        assert log[0:3] == ("APPROVE", 2, "同意")
        assert '"source": "timesheet_approval_log"' in log[3]
        assert '"source_id": 7' in log[3]
    finally:
        conn.close()

    archive = sqlite3.connect(archive_path)
    try:
        assert archive.execute("SELECT COUNT(*) FROM timesheet_approval_log").fetchone()[0] == 2
    finally:
        archive.close()


def test_retire_unused_tables_migrates_ecn_approvals_before_drop(tmp_path):
    from scripts.retire_unused_tables_20260705 import retire_unused_tables

    db_path = tmp_path / "app.db"
    archive_path = tmp_path / "retired_archive.db"

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            real_name TEXT
        );
        INSERT INTO users(id, username, real_name)
        VALUES (1, 'designer', '设计员'), (2, 'manager', '经理');

        CREATE TABLE ecn (
            id INTEGER PRIMARY KEY,
            tenant_id INTEGER,
            ecn_no TEXT,
            ecn_title TEXT,
            ecn_type TEXT,
            project_id INTEGER,
            applicant_id INTEGER,
            applicant_name TEXT,
            applied_at TEXT,
            status TEXT
        );
        INSERT INTO ecn(
            id, tenant_id, ecn_no, ecn_title, ecn_type, project_id,
            applicant_id, applicant_name, applied_at, status
        )
        VALUES (
            31, 1, 'ECN-31', '相机选型变更', 'NORMAL', 9,
            1, '设计员', '2026-07-01 09:00:00', 'APPROVED'
        );

        CREATE TABLE approval_templates (
            id INTEGER PRIMARY KEY,
            template_code TEXT NOT NULL UNIQUE,
            template_name TEXT NOT NULL,
            entity_type TEXT,
            is_active INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        INSERT INTO approval_templates(
            id, template_code, template_name, entity_type, is_active, created_at, updated_at
        )
        VALUES (3, 'ECN_STANDARD', 'ECN工程变更审批', 'ECN', 1, '2026-01-01', '2026-01-01');

        CREATE TABLE approval_flow_definitions (
            id INTEGER PRIMARY KEY,
            template_id INTEGER NOT NULL,
            flow_name TEXT NOT NULL,
            is_default INTEGER,
            is_active INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        INSERT INTO approval_flow_definitions(
            id, template_id, flow_name, is_default, is_active, created_at, updated_at
        )
        VALUES (13, 3, 'ECN默认审批流', 1, 1, '2026-01-01', '2026-01-01');

        CREATE TABLE approval_instances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER,
            instance_no TEXT NOT NULL UNIQUE,
            template_id INTEGER NOT NULL,
            flow_id INTEGER NOT NULL,
            entity_type TEXT,
            entity_id INTEGER,
            initiator_id INTEGER NOT NULL,
            initiator_name TEXT,
            form_data TEXT,
            status TEXT NOT NULL,
            title TEXT,
            summary TEXT,
            submitted_at TEXT,
            completed_at TEXT,
            final_comment TEXT,
            final_approver_id INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE approval_action_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER,
            instance_id INTEGER NOT NULL,
            operator_id INTEGER NOT NULL,
            operator_name TEXT,
            action TEXT NOT NULL,
            action_detail TEXT,
            comment TEXT,
            attachments TEXT,
            before_status TEXT,
            after_status TEXT,
            action_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE ecn_approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER,
            ecn_id INTEGER NOT NULL,
            approval_level INTEGER NOT NULL,
            approval_role TEXT NOT NULL,
            approver_id INTEGER,
            approver_name TEXT,
            approval_result TEXT,
            approval_opinion TEXT,
            status TEXT,
            approved_at TEXT,
            due_date TEXT,
            is_overdue INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        INSERT INTO ecn_approvals(
            id, tenant_id, ecn_id, approval_level, approval_role,
            approver_id, approver_name, approval_result, approval_opinion,
            status, approved_at, due_date, is_overdue, created_at, updated_at
        )
        VALUES (
            5, 1, 31, 1, '项目经理',
            2, '经理', 'APPROVED', '同意', 'APPROVED',
            '2026-07-01 12:00:00', '2026-07-02 12:00:00', 0,
            '2026-07-01 10:00:00', '2026-07-01 12:00:00'
        );

        CREATE TABLE ecn_approval_matrix (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER,
            ecn_type TEXT,
            condition_type TEXT NOT NULL,
            condition_min NUMERIC,
            condition_max NUMERIC,
            approval_level INTEGER NOT NULL,
            approval_role TEXT NOT NULL,
            is_active INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        INSERT INTO ecn_approval_matrix(
            id, tenant_id, ecn_type, condition_type, approval_level, approval_role,
            is_active, created_at, updated_at
        )
        VALUES (9, 1, 'NORMAL', 'ALWAYS', 1, '项目经理', 1, '2026-07-01', '2026-07-01');
        """
    )
    conn.commit()
    conn.close()

    report = retire_unused_tables(
        db_path,
        archive_path=archive_path,
        drop_tables=True,
        create_backup=False,
    )

    assert report["dropped_tables"] == ["ecn_approvals", "ecn_approval_matrix"]
    assert report["archived_rows"]["ecn_approvals"] == 1
    assert report["archived_rows"]["ecn_approval_matrix"] == 1
    assert report["migrated_ecn_approvals"] == {
        "source_rows": 1,
        "inserted_instances": 1,
        "existing_instances": 0,
        "inserted_logs": 1,
        "skipped_rows": 0,
    }

    conn = sqlite3.connect(db_path)
    try:
        assert not _table_exists(conn, "ecn_approvals")
        assert not _table_exists(conn, "ecn_approval_matrix")
        instance = conn.execute(
            """
            SELECT id, entity_type, entity_id, status, initiator_id
            FROM approval_instances
            WHERE entity_type = 'ECN' AND entity_id = 31
            """
        ).fetchone()
        assert instance is not None
        assert instance[3] == "APPROVED"
        assert instance[4] == 1
        log = conn.execute(
            """
            SELECT action, operator_id, comment, action_detail
            FROM approval_action_logs
            WHERE instance_id = ?
            """,
            (instance[0],),
        ).fetchone()
        assert log[0:3] == ("APPROVE", 2, "同意")
        assert '"source": "ecn_approvals"' in log[3]
        assert '"approval_level": 1' in log[3]
    finally:
        conn.close()

    archive = sqlite3.connect(archive_path)
    try:
        assert archive.execute("SELECT COUNT(*) FROM ecn_approvals").fetchone()[0] == 1
        assert archive.execute("SELECT COUNT(*) FROM ecn_approval_matrix").fetchone()[0] == 1
    finally:
        archive.close()


def test_retire_unused_tables_archives_empty_data_scope_tables_before_drop(tmp_path):
    from scripts.retire_unused_tables_20260705 import retire_unused_tables

    db_path = tmp_path / "app.db"
    archive_path = tmp_path / "retired_archive.db"

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE data_scope_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_code TEXT NOT NULL,
            rule_name TEXT NOT NULL,
            scope_type TEXT NOT NULL
        );

        CREATE TABLE role_data_scopes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id INTEGER NOT NULL,
            resource_type TEXT NOT NULL,
            scope_rule_id INTEGER NOT NULL REFERENCES data_scope_rules(id),
            is_active BOOLEAN DEFAULT 1
        );

        CREATE TABLE roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_code TEXT NOT NULL,
            data_scope TEXT DEFAULT 'OWN'
        );
        INSERT INTO roles(role_code, data_scope) VALUES ('SALES', 'DEPARTMENT');
        """
    )
    conn.commit()
    conn.close()

    report = retire_unused_tables(
        db_path,
        archive_path=archive_path,
        drop_tables=True,
        create_backup=False,
    )

    assert report["dropped_tables"] == ["role_data_scopes", "data_scope_rules"]
    assert report["archived_rows"] == {"role_data_scopes": 0, "data_scope_rules": 0}

    conn = sqlite3.connect(db_path)
    try:
        assert not _table_exists(conn, "role_data_scopes")
        assert not _table_exists(conn, "data_scope_rules")
        assert _table_exists(conn, "roles")
    finally:
        conn.close()

    archive = sqlite3.connect(archive_path)
    try:
        assert archive.execute("SELECT COUNT(*) FROM data_scope_rules").fetchone()[0] == 0
        assert archive.execute("SELECT COUNT(*) FROM role_data_scopes").fetchone()[0] == 0
        archived_tables = {
            row[0]
            for row in archive.execute("SELECT table_name FROM retired_table_manifest")
        }
        assert {"data_scope_rules", "role_data_scopes"} <= archived_tables
    finally:
        archive.close()


def test_retire_unused_tables_repoints_empty_after_sales_ticket_dependents(tmp_path):
    from scripts.retire_unused_tables_20260705 import retire_unused_tables

    db_path = tmp_path / "app.db"
    archive_path = tmp_path / "retired_archive.db"

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE service_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_no TEXT NOT NULL
        );

        CREATE TABLE after_sales_support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_no TEXT
        );

        CREATE TABLE after_sales_field_services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER REFERENCES after_sales_support_tickets(id),
            service_no TEXT UNIQUE
        );

        CREATE TABLE after_sales_sla (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER REFERENCES after_sales_support_tickets(id)
        );

        CREATE TABLE after_sales_satisfaction (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER REFERENCES after_sales_support_tickets(id),
            field_service_id INTEGER REFERENCES after_sales_field_services(id)
        );
        """
    )
    conn.commit()
    conn.close()

    report = retire_unused_tables(
        db_path,
        archive_path=archive_path,
        drop_tables=True,
        create_backup=False,
    )

    assert "after_sales_support_tickets" in report["dropped_tables"]
    assert report["archived_rows"]["after_sales_support_tickets"] == 0
    assert sorted(report["rebuilt_tables"]) == [
        "after_sales_field_services",
        "after_sales_satisfaction",
        "after_sales_sla",
    ]

    conn = sqlite3.connect(db_path)
    try:
        assert not _table_exists(conn, "after_sales_support_tickets")
        for table_name in (
            "after_sales_field_services",
            "after_sales_sla",
            "after_sales_satisfaction",
        ):
            assert _table_exists(conn, table_name)
        fk_targets = {
            row[2]
            for row in conn.execute('PRAGMA foreign_key_list("after_sales_field_services")')
        }
        assert "service_tickets" in fk_targets
        assert "after_sales_support_tickets" not in fk_targets
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        conn.close()

    archive = sqlite3.connect(archive_path)
    try:
        assert archive.execute(
            "SELECT COUNT(*) FROM retired_table_manifest WHERE table_name='after_sales_support_tickets'"
        ).fetchone()[0] == 1
    finally:
        archive.close()


def test_retire_unused_tables_drops_dependent_views_before_tables(tmp_path):
    from scripts.retire_unused_tables_20260705 import retire_unused_tables

    db_path = tmp_path / "app.db"
    archive_path = tmp_path / "retired_archive.db"

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE user_role_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role_id INTEGER NOT NULL,
            status TEXT DEFAULT 'ACTIVE'
        );
        INSERT INTO user_role_assignments(user_id, role_id, status) VALUES (1, 2, 'ACTIVE');

        CREATE VIEW v_user_active_roles AS
        SELECT id AS assignment_id, user_id, role_id
        FROM user_role_assignments
        WHERE status = 'ACTIVE';
        """
    )
    conn.commit()
    conn.close()

    report = retire_unused_tables(
        db_path,
        archive_path=archive_path,
        drop_tables=True,
        create_backup=False,
    )

    assert report["dropped_views"] == ["v_user_active_roles"]
    assert report["dropped_tables"] == ["user_role_assignments"]

    conn = sqlite3.connect(db_path)
    try:
        assert not _table_exists(conn, "user_role_assignments")
        assert (
            conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='view' AND name='v_user_active_roles'"
            ).fetchone()
            is None
        )
    finally:
        conn.close()

    archive = sqlite3.connect(archive_path)
    try:
        assert archive.execute("SELECT COUNT(*) FROM user_role_assignments").fetchone()[0] == 1
        view_sql = archive.execute(
            "SELECT source_sql FROM retired_view_manifest WHERE view_name='v_user_active_roles'"
        ).fetchone()[0]
        assert "user_role_assignments" in view_sql
    finally:
        archive.close()


def test_retire_unused_tables_archives_history_only_tables(tmp_path):
    from scripts.retire_unused_tables_20260705 import retire_unused_tables

    db_path = tmp_path / "app.db"
    archive_path = tmp_path / "retired_archive.db"

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE legacy_approval_archives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_table TEXT NOT NULL,
            source_id INTEGER,
            snapshot_json TEXT NOT NULL,
            archived_at TEXT NOT NULL
        );
        INSERT INTO legacy_approval_archives(source_table, source_id, snapshot_json, archived_at)
        VALUES ('quote_approvals', 10, '{}', '2026-07-05T00:00:00Z');

        CREATE TABLE tasks_deprecated (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL
        );
        INSERT INTO tasks_deprecated(title) VALUES ('old task');

        CREATE TABLE task_id_map (
            old_task_id INTEGER PRIMARY KEY,
            new_task_id INTEGER NOT NULL,
            migrated_at TEXT
        );
        INSERT INTO task_id_map(old_task_id, new_task_id, migrated_at)
        VALUES (1, 101, '2026-07-05T00:00:00Z');
        """
    )
    conn.commit()
    conn.close()

    report = retire_unused_tables(
        db_path,
        archive_path=archive_path,
        drop_tables=True,
        create_backup=False,
    )

    assert report["dropped_tables"] == [
        "legacy_approval_archives",
        "tasks_deprecated",
        "task_id_map",
    ]
    assert report["archived_rows"] == {
        "legacy_approval_archives": 1,
        "tasks_deprecated": 1,
        "task_id_map": 1,
    }

    conn = sqlite3.connect(db_path)
    try:
        assert not _table_exists(conn, "legacy_approval_archives")
        assert not _table_exists(conn, "tasks_deprecated")
        assert not _table_exists(conn, "task_id_map")
    finally:
        conn.close()

    archive = sqlite3.connect(archive_path)
    try:
        assert archive.execute("SELECT COUNT(*) FROM legacy_approval_archives").fetchone()[0] == 1
        assert archive.execute("SELECT COUNT(*) FROM tasks_deprecated").fetchone()[0] == 1
        assert archive.execute("SELECT COUNT(*) FROM task_id_map").fetchone()[0] == 1
    finally:
        archive.close()


def test_retire_unused_tables_merges_sales_target_v2_before_drop(tmp_path):
    from scripts.retire_unused_tables_20260705 import retire_unused_tables

    db_path = tmp_path / "app.db"
    archive_path = tmp_path / "retired_archive.db"

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dept_name TEXT NOT NULL,
            dept_code TEXT
        );
        INSERT INTO departments(id, dept_name, dept_code) VALUES (2, '销售部', 'D01');

        CREATE TABLE sales_targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER,
            target_scope TEXT NOT NULL,
            user_id INTEGER,
            department_id INTEGER,
            team_id INTEGER,
            target_type TEXT NOT NULL,
            target_period TEXT NOT NULL,
            period_value TEXT NOT NULL,
            target_value NUMERIC NOT NULL,
            description TEXT,
            status TEXT,
            created_by INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE sales_targets_v2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER,
            target_period TEXT NOT NULL,
            target_year INTEGER NOT NULL,
            target_month INTEGER,
            target_quarter INTEGER,
            target_type TEXT NOT NULL,
            team_id INTEGER,
            user_id INTEGER,
            sales_target NUMERIC NOT NULL,
            payment_target NUMERIC NOT NULL,
            new_customer_target INTEGER NOT NULL,
            lead_target INTEGER NOT NULL,
            opportunity_target INTEGER NOT NULL,
            deal_target INTEGER NOT NULL,
            actual_sales NUMERIC NOT NULL,
            actual_payment NUMERIC NOT NULL,
            actual_new_customers INTEGER NOT NULL,
            actual_leads INTEGER NOT NULL,
            actual_opportunities INTEGER NOT NULL,
            actual_deals INTEGER NOT NULL,
            completion_rate NUMERIC,
            parent_target_id INTEGER,
            description TEXT,
            remark TEXT,
            created_by INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        INSERT INTO sales_targets_v2 (
            id, tenant_id, target_period, target_year, target_type, team_id,
            sales_target, payment_target, new_customer_target, lead_target,
            opportunity_target, deal_target, actual_sales, actual_payment,
            actual_new_customers, actual_leads, actual_opportunities, actual_deals,
            description, created_by, created_at, updated_at
        )
        VALUES (
            10, 1, '2026', 2026, 'team', 7,
            100, 80, 2, 12, 6, 3, 40, 20, 1, 5, 2, 1,
            '团队年度目标', 9, '2026-03-01 16:55:43', '2026-03-01 16:55:43'
        );
        INSERT INTO sales_targets_v2 (
            id, tenant_id, target_period, target_year, target_type, sales_target,
            payment_target, new_customer_target, lead_target, opportunity_target,
            deal_target, actual_sales, actual_payment, actual_new_customers,
            actual_leads, actual_opportunities, actual_deals, created_by,
            created_at, updated_at
        )
        VALUES (
            11, 1, 'sales_t', 13, 'company', 10,
            10, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1,
            1, '2024-01-01 00:00:00', '2024-01-01 00:00:00'
        );

        CREATE TABLE target_breakdown_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_target_id INTEGER NOT NULL,
            breakdown_type TEXT NOT NULL,
            breakdown_method TEXT,
            breakdown_details TEXT,
            created_by INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        INSERT INTO target_breakdown_logs(
            parent_target_id, breakdown_type, breakdown_method, breakdown_details,
            created_by, created_at, updated_at
        )
        VALUES (10, 'AUTO', 'EQUAL', '{}', 9, '2026-03-01', '2026-03-01');
        """
    )
    conn.commit()
    conn.close()

    report = retire_unused_tables(
        db_path,
        archive_path=archive_path,
        drop_tables=True,
        create_backup=False,
    )

    assert report["merged_sales_target_v2"] == {
        "source_rows": 2,
        "valid_source_rows": 1,
        "skipped_source_rows": 1,
        "inserted_targets": 4,
        "duplicate_targets": 0,
        "skipped_metrics": 0,
    }
    assert "target_breakdown_logs" in report["dropped_tables"]
    assert "sales_targets_v2" in report["dropped_tables"]

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT target_scope, team_id, target_type, target_period, period_value,
                   target_value, description, created_by
            FROM sales_targets
            ORDER BY target_type
            """
        ).fetchall()
        assert len(rows) == 4
        assert {row[2] for row in rows} == {
            "COLLECTION_AMOUNT",
            "CONTRACT_AMOUNT",
            "LEAD_COUNT",
            "OPPORTUNITY_COUNT",
        }
        assert {row[0] for row in rows} == {"TEAM"}
        assert {row[1] for row in rows} == {7}
        assert {row[3] for row in rows} == {"YEARLY"}
        assert {row[4] for row in rows} == {"2026"}
        assert all("[merged_from:sales_targets_v2:10:" in row[6] for row in rows)
        assert {row[7] for row in rows} == {9}
        assert not _table_exists(conn, "sales_targets_v2")
        assert not _table_exists(conn, "target_breakdown_logs")
    finally:
        conn.close()

    archive = sqlite3.connect(archive_path)
    try:
        assert archive.execute("SELECT COUNT(*) FROM sales_targets_v2").fetchone()[0] == 2
        assert archive.execute("SELECT COUNT(*) FROM target_breakdown_logs").fetchone()[0] == 1
        assert archive.execute(
            """
            SELECT COUNT(*)
            FROM sales_target_v2_merge_manifest
            WHERE merge_action='inserted'
            """
        ).fetchone()[0] == 4
        assert archive.execute(
            """
            SELECT COUNT(*)
            FROM sales_target_v2_merge_manifest
            WHERE merge_action='skipped' AND reason LIKE 'invalid%'
            """
        ).fetchone()[0] == 1
    finally:
        archive.close()


def test_retire_unused_tables_merges_assigned_legacy_permissions_only(tmp_path):
    from scripts.retire_unused_tables_20260705 import retire_unused_tables

    db_path = tmp_path / "app.db"
    archive_path = tmp_path / "retired_archive.db"

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER,
            role_code TEXT NOT NULL,
            role_name TEXT NOT NULL
        );
        INSERT INTO roles(id, tenant_id, role_code, role_name)
        VALUES (1, 1, 'ops', '运营');

        CREATE TABLE permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            perm_code TEXT UNIQUE NOT NULL,
            perm_name TEXT,
            module TEXT,
            action TEXT,
            resource TEXT,
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT,
            updated_at TEXT,
            permission_type TEXT DEFAULT 'API',
            group_id INTEGER
        );
        INSERT INTO permissions(id, perm_code, perm_name, module, resource, action, description)
        VALUES
            (10, 'existing:read', '已有查看', 'existing', 'existing', 'read', 'old existing'),
            (11, 'legacy:manage', '旧管理', 'legacy', 'legacy', 'manage', 'old assigned'),
            (12, 'orphan:read', '孤儿查看', 'orphan', 'orphan', 'read', 'old unassigned');

        CREATE TABLE api_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id INTEGER,
            perm_code TEXT NOT NULL,
            perm_name TEXT NOT NULL,
            module TEXT,
            page_code TEXT,
            action TEXT,
            description TEXT,
            permission_type TEXT NOT NULL,
            group_id INTEGER,
            is_active BOOLEAN NOT NULL,
            is_system BOOLEAN NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(tenant_id, perm_code)
        );
        INSERT INTO api_permissions(
            id, tenant_id, perm_code, perm_name, module, action, description,
            permission_type, is_active, is_system, created_at, updated_at
        )
        VALUES (
            20, NULL, 'existing:read', '已有查看', 'existing', 'read', 'new existing',
            'API', 1, 1, '2026-01-01', '2026-01-01'
        );

        CREATE TABLE role_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id INTEGER NOT NULL,
            permission_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        INSERT INTO role_permissions(id, role_id, permission_id)
        VALUES (100, 1, 10), (101, 1, 11);

        CREATE TABLE role_api_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_id INTEGER NOT NULL,
            permission_id INTEGER NOT NULL,
            created_at TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            tenant_id INTEGER,
            UNIQUE(role_id, permission_id)
        );

        CREATE TABLE permission_cache_revisions (
            scope TEXT PRIMARY KEY,
            revision INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT
        );
        INSERT INTO permission_cache_revisions(scope, revision)
        VALUES ('system', 3), ('tenant:1', 4);
        """
    )
    conn.commit()
    conn.close()

    report = retire_unused_tables(
        db_path,
        archive_path=archive_path,
        drop_tables=True,
        create_backup=False,
    )

    assert report["merged_legacy_permissions"] == {
        "source_permissions": 3,
        "source_role_permissions": 2,
        "assigned_permissions": 2,
        "unassigned_permissions": 1,
        "existing_api_permissions": 1,
        "inserted_api_permissions": 1,
        "inserted_role_api_permissions": 2,
        "duplicate_role_api_permissions": 0,
        "skipped_role_permissions": 0,
        "cache_revisions_bumped": 2,
    }
    assert "role_permissions" in report["dropped_tables"]
    assert "permissions" in report["dropped_tables"]

    conn = sqlite3.connect(db_path)
    try:
        assert not _table_exists(conn, "role_permissions")
        assert not _table_exists(conn, "permissions")
        permission_codes = {
            row[0] for row in conn.execute("SELECT perm_code FROM api_permissions ORDER BY id")
        }
        assert permission_codes == {"existing:read", "legacy:manage"}
        assert "orphan:read" not in permission_codes
        role_permission_codes = {
            row[0]
            for row in conn.execute(
                """
                SELECT ap.perm_code
                FROM role_api_permissions rap
                JOIN api_permissions ap ON ap.id = rap.permission_id
                WHERE rap.role_id = 1
                """
            )
        }
        assert role_permission_codes == {"existing:read", "legacy:manage"}
        revisions = dict(conn.execute("SELECT scope, revision FROM permission_cache_revisions"))
        assert revisions["system"] == 4
        assert revisions["tenant:1"] == 5
    finally:
        conn.close()

    archive = sqlite3.connect(archive_path)
    try:
        assert archive.execute("SELECT COUNT(*) FROM permissions").fetchone()[0] == 3
        assert archive.execute("SELECT COUNT(*) FROM role_permissions").fetchone()[0] == 2
        actions = dict(
            archive.execute(
                """
                SELECT merge_action, COUNT(*)
                FROM legacy_permission_merge_manifest
                GROUP BY merge_action
                """
            )
        )
        assert actions == {
            "api_permission_existing": 1,
            "api_permission_inserted": 1,
            "role_api_permission_inserted": 2,
        }
    finally:
        archive.close()


def test_retire_unused_tables_merges_presale_ai_templates_before_drop(tmp_path):
    from scripts.retire_unused_tables_20260705 import retire_unused_tables

    db_path = tmp_path / "app.db"
    archive_path = tmp_path / "retired_archive.db"

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE presale_solution_template (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_no TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            industry TEXT,
            test_type TEXT,
            description TEXT,
            content_template TEXT,
            cost_template TEXT,
            attachments TEXT,
            use_count INTEGER,
            is_active BOOLEAN,
            created_by INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            tenant_id INTEGER
        );

        CREATE TABLE presale_solution_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT UNIQUE,
            industry TEXT,
            equipment_type TEXT,
            complexity_level TEXT,
            solution_content TEXT,
            architecture_diagram TEXT,
            bom_template TEXT,
            technical_specs TEXT,
            equipment_list TEXT,
            embedding TEXT,
            embedding_model TEXT,
            usage_count INTEGER,
            success_rate NUMERIC,
            avg_quality_score NUMERIC,
            typical_cost_range_min NUMERIC,
            typical_cost_range_max NUMERIC,
            tags TEXT,
            keywords TEXT,
            is_active INTEGER,
            created_by INTEGER,
            created_at TEXT,
            updated_at TEXT,
            tenant_id INTEGER
        );
        INSERT INTO presale_solution_templates(
            id, name, code, industry, equipment_type, complexity_level,
            solution_content, bom_template, technical_specs, equipment_list,
            usage_count, typical_cost_range_min, typical_cost_range_max,
            tags, keywords, is_active, created_by, created_at, updated_at, tenant_id
        )
        VALUES (
            7, 'AI FCT模板', 'AI-FCT-001', '家电', 'FCT测试', 'medium',
            '{"description":"AI模板内容"}', '{"items":[]}', '{"ct":"15s"}', '[{"name":"工装"}]',
            5, 100000, 200000,
            '["FCT"]', 'FCT 追溯', 1, 9, '2026-03-01', '2026-03-02', 2
        );
        """
    )
    conn.commit()
    conn.close()

    report = retire_unused_tables(
        db_path,
        archive_path=archive_path,
        drop_tables=True,
        create_backup=False,
    )

    assert "presale_solution_templates" in report["dropped_tables"]
    assert report["merged_presale_solution_templates"] == {
        "source_rows": 1,
        "inserted_templates": 1,
        "updated_existing_templates": 0,
        "duplicate_templates": 0,
        "skipped_templates": 0,
    }

    conn = sqlite3.connect(db_path)
    try:
        assert not _table_exists(conn, "presale_solution_templates")
        row = conn.execute(
            """
            SELECT template_no, name, industry, test_type, content_template,
                   cost_template, use_count, is_active, created_by, tenant_id
            FROM presale_solution_template
            """
        ).fetchone()
        assert row[0] == "AI-FCT-001"
        assert row[1] == "AI FCT模板"
        assert row[2] == "家电"
        assert row[3] == "FCT测试"
        assert "AI模板内容" in row[4]
        assert "typical_cost_range_min" in row[5]
        assert row[6] == 5
        assert row[7] == 1
        assert row[8] == 9
        assert row[9] == 2
    finally:
        conn.close()

    archive = sqlite3.connect(archive_path)
    try:
        assert archive.execute("SELECT COUNT(*) FROM presale_solution_templates").fetchone()[0] == 1
        assert archive.execute(
            """
            SELECT COUNT(*)
            FROM presale_solution_template_merge_manifest
            WHERE merge_action='inserted'
            """
        ).fetchone()[0] == 1
    finally:
        archive.close()


def test_retire_unused_tables_archives_empty_solution_versions_before_drop(tmp_path):
    from scripts.retire_unused_tables_20260705 import retire_unused_tables

    db_path = tmp_path / "app.db"
    archive_path = tmp_path / "retired_archive.db"

    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE solution_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            solution_id INTEGER NOT NULL,
            version_no TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            created_by INTEGER NOT NULL,
            created_at TEXT
        );
        """
    )
    conn.commit()
    conn.close()

    report = retire_unused_tables(
        db_path,
        archive_path=archive_path,
        drop_tables=True,
        create_backup=False,
    )

    assert report["dropped_tables"] == ["solution_versions"]
    assert report["archived_rows"] == {"solution_versions": 0}

    conn = sqlite3.connect(db_path)
    try:
        assert not _table_exists(conn, "solution_versions")
    finally:
        conn.close()

    archive = sqlite3.connect(archive_path)
    try:
        assert archive.execute(
            "SELECT row_count FROM retired_table_manifest WHERE table_name='solution_versions'"
        ).fetchone()[0] == 0
    finally:
        archive.close()
