-- Rename production scheduling conflict table to avoid confusion with
-- project resource planning conflicts (`resource_conflicts`).

PRAGMA foreign_keys=OFF;

ALTER TABLE resource_conflict RENAME TO production_resource_conflicts;

DROP INDEX IF EXISTS idx_conflict_schedule;
DROP INDEX IF EXISTS idx_conflict_type;
DROP INDEX IF EXISTS idx_conflict_status;
DROP INDEX IF EXISTS idx_conflict_resource;
DROP INDEX IF EXISTS idx_resource_conflict_tenant;

CREATE INDEX IF NOT EXISTS idx_production_conflict_schedule
    ON production_resource_conflicts(schedule_id);
CREATE INDEX IF NOT EXISTS idx_production_conflict_type
    ON production_resource_conflicts(conflict_type);
CREATE INDEX IF NOT EXISTS idx_production_conflict_status
    ON production_resource_conflicts(status);
CREATE INDEX IF NOT EXISTS idx_production_conflict_resource
    ON production_resource_conflicts(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_production_resource_conflicts_tenant
    ON production_resource_conflicts(tenant_id);

PRAGMA foreign_keys=ON;
