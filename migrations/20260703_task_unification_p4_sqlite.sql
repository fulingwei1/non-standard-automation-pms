-- 双任务表整合 P4：旧 tasks 物理表下线（改名保留一个版本周期后删除）
-- 注意：SQLite 直接执行本文件会因库内既有坏视图 v_bom_ready_rate 阻塞 RENAME，
-- 实际执行走 scripts/migrate_tasks_to_unified.py --p4（内含 PRAGMA legacy_alter_table=ON）
ALTER TABLE tasks RENAME TO tasks_deprecated;
