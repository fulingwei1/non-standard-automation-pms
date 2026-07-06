-- Final cleanup for retired approval tables after older compatibility migrations.
-- Historical rows must be archived into legacy_approval_archives before this runs
-- on a live database.

PRAGMA foreign_keys=OFF;

DROP TABLE IF EXISTS approval_history;
DROP TABLE IF EXISTS approval_records;
DROP TABLE IF EXISTS approval_workflow_steps;
DROP TABLE IF EXISTS approval_workflows;
DROP TABLE IF EXISTS contract_approvals;
DROP TABLE IF EXISTS invoice_approvals;
DROP TABLE IF EXISTS quotation_approvals;
DROP TABLE IF EXISTS quote_approvals;
DROP TABLE IF EXISTS quote_cost_approvals;
DROP TABLE IF EXISTS role_assignment_approvals;
DROP TABLE IF EXISTS task_approval_workflows;

PRAGMA foreign_keys=ON;
