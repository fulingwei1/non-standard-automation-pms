-- Drop confirmed unused/generated-residue tables.
-- Rows should be archived with scripts/retire_unused_tables_20260705.py before
-- applying this migration to a live database.

PRAGMA foreign_keys=OFF;

DROP VIEW IF EXISTS v_user_active_roles;

DROP TABLE IF EXISTS lead_requirement_facility_v2;
DROP TABLE IF EXISTS lead_requirement_technical_v2;
DROP TABLE IF EXISTS lead_requirement_basic_v2;

DROP TABLE IF EXISTS funding_records;
DROP TABLE IF EXISTS equity_structures;
DROP TABLE IF EXISTS funding_usages;
DROP TABLE IF EXISTS funding_rounds;
DROP TABLE IF EXISTS investors;

DROP TABLE IF EXISTS department_default_roles;
DROP TABLE IF EXISTS department_role_admins;
DROP TABLE IF EXISTS role_template_permissions;
DROP TABLE IF EXISTS role_audits;

DROP TABLE IF EXISTS currency_rates;
DROP TABLE IF EXISTS currency_history;
DROP TABLE IF EXISTS ecn_records;
DROP TABLE IF EXISTS ecn_approvals;
DROP TABLE IF EXISTS ecn_approval_matrix;
DROP TABLE IF EXISTS shortage_alerts;
DROP TABLE IF EXISTS mat_shortage_alert;
DROP TABLE IF EXISTS quote_cost_histories;
DROP TABLE IF EXISTS quotation_templates;
DROP TABLE IF EXISTS after_sales_support_tickets;
DROP TABLE IF EXISTS change_approval_records;
DROP TABLE IF EXISTS timesheet_approval_log;
DROP TABLE IF EXISTS presale_solution_templates;
DROP TABLE IF EXISTS role_exclusions;
DROP TABLE IF EXISTS user_role_assignments;
DROP TABLE IF EXISTS legacy_approval_archives;
DROP TABLE IF EXISTS tasks_deprecated;
DROP TABLE IF EXISTS task_id_map;
DROP TABLE IF EXISTS solution_versions;
DROP TABLE IF EXISTS role_data_scopes;
DROP TABLE IF EXISTS data_scope_rules;
DROP TABLE IF EXISTS target_breakdown_logs;
DROP TABLE IF EXISTS sales_targets_v2;
DROP TABLE IF EXISTS role_permissions;
DROP TABLE IF EXISTS permissions;

PRAGMA foreign_keys=ON;
