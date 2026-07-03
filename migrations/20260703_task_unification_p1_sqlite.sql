-- 双任务表整合 P1：task_unified 扩列 + ID 映射表（SQLite）
-- 见 TASK_UNIFICATION_DESIGN.md；数据迁移由 scripts/migrate_tasks_to_unified.py 执行（幂等）

ALTER TABLE task_unified ADD COLUMN project_stage VARCHAR(20);
ALTER TABLE task_unified ADD COLUMN machine_id INTEGER;
ALTER TABLE task_unified ADD COLUMN milestone_id INTEGER;
ALTER TABLE task_unified ADD COLUMN weight NUMERIC(5,2);
ALTER TABLE task_unified ADD COLUMN block_reason TEXT;

CREATE INDEX IF NOT EXISTS idx_tu_project_stage ON task_unified(project_id, project_stage);
CREATE INDEX IF NOT EXISTS idx_tu_machine ON task_unified(machine_id);

-- 旧 tasks.id -> 新 task_unified.id 映射（回滚与引用重接依据）
CREATE TABLE IF NOT EXISTS task_id_map (
    old_task_id INTEGER PRIMARY KEY,
    new_task_id INTEGER NOT NULL UNIQUE,
    migrated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
