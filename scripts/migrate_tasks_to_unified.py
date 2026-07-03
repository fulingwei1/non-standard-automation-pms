# -*- coding: utf-8 -*-
"""双任务表整合 P1：tasks → task_unified 数据迁移 + FK 重建 + 引用重接（幂等）。

用法：
    .venv/bin/python scripts/migrate_tasks_to_unified.py [--db data/app.db]   # 执行迁移
    .venv/bin/python scripts/migrate_tasks_to_unified.py --check              # 只做对账

步骤（见 TASK_UNIFICATION_DESIGN.md）：
1. tasks 全量迁入 task_unified（确定性 new_id = 10000 + old_id，零区间重叠，幂等跳过已映射行）；
2. 5 张引用表 DDL 重建：FK 由 REFERENCES tasks 改指 task_unified（SQLite 不支持 ALTER FK）；
3. 引用值重接 old_id → new_id；
4. PRAGMA foreign_key_check 校验后提交。旧表 tasks 全程不动（双读校验期）。
"""
import re
import sqlite3
import sys
from datetime import datetime

OFFSET = 10000
STATUS_MAP = {"TODO": "PENDING", "IN_PROGRESS": "IN_PROGRESS", "DONE": "COMPLETED",
              "BLOCKED": "PAUSED", None: "PENDING", "": "PENDING"}
REF_TABLES = {  # 表名 -> 引用列
    "task_dependencies": ["task_id", "depends_on_task_id"],
    "progress_logs": ["task_id"],
    "baseline_tasks": ["task_id"],
    "progress_reports": ["task_id"],
    "quality_risk_detection": ["task_id"],
}


def migrate(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    admin_id = cur.execute("SELECT id FROM users WHERE username='admin'").fetchone()
    admin_id = admin_id[0] if admin_id else 1
    projects = {r[0]: (r[1], r[2], r[3]) for r in cur.execute(
        "SELECT id, project_code, project_name, pm_id FROM projects")}
    users = {r[0]: r[1] for r in cur.execute(
        "SELECT id, COALESCE(real_name, username) FROM users")}
    mapped = {r[0] for r in cur.execute("SELECT old_task_id FROM task_id_map")}
    max_existing = cur.execute(
        "SELECT COALESCE(MAX(id),0) FROM task_unified WHERE id < ?", (OFFSET,)).fetchone()[0]
    assert max_existing < OFFSET, f"task_unified 现有 id({max_existing}) 越过偏移区间"

    inserted = skipped = 0
    for r in cur.execute(
            "SELECT id, project_id, machine_id, milestone_id, task_code, task_name, stage, status, "
            "owner_id, plan_start, plan_end, actual_start, actual_end, progress_percent, weight, "
            "block_reason, created_at, updated_at FROM tasks ORDER BY id").fetchall():
        (old_id, project_id, machine_id, milestone_id, task_code, task_name, stage, status,
         owner_id, plan_start, plan_end, actual_start, actual_end, progress_percent, weight,
         block_reason, created_at, updated_at) = r
        if old_id in mapped:
            skipped += 1
            continue
        pj = projects.get(project_id) or (None, None, None)
        assignee_id = owner_id or pj[2] or admin_id  # owner → 项目PM → admin 兜底
        new_id = OFFSET + old_id
        conn.execute(
            "INSERT INTO task_unified (id, task_code, title, task_type, source_type, source_id, "
            "source_name, project_id, project_code, project_name, assignee_id, assignee_name, "
            "plan_start_date, plan_end_date, actual_start_date, actual_end_date, status, progress, "
            "is_active, priority, project_stage, machine_id, milestone_id, weight, block_reason, "
            "created_by, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (new_id, task_code or f"PT-{old_id}", task_name or f"项目任务#{old_id}",
             "PROJECT", "PROJECT", project_id, pj[1], project_id, pj[0], pj[1],
             assignee_id, users.get(assignee_id), plan_start, plan_end, actual_start, actual_end,
             STATUS_MAP.get(status, "PENDING"), progress_percent or 0, 1, "MEDIUM",
             stage or None, machine_id, milestone_id, weight, block_reason,
             owner_id, created_at, updated_at))
        conn.execute("INSERT INTO task_id_map (old_task_id, new_task_id, migrated_at) VALUES (?,?,?)",
                     (old_id, new_id, now))
        inserted += 1
    print(f"迁移: 新增 {inserted} 行, 幂等跳过 {skipped} 行")

    # FK 重建：REFERENCES tasks -> task_unified（幂等：DDL 已指向则跳过）
    for tbl in REF_TABLES:
        ddl = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                           (tbl,)).fetchone()[0]
        if not re.search(r'REFERENCES\s+"?tasks"?\s*\(', ddl, re.I):
            print(f"FK重建 {tbl}: 已指向 task_unified，跳过")
            continue
        new_ddl = re.sub(r'REFERENCES\s+"?tasks"?\s*\(', 'REFERENCES task_unified (', ddl, flags=re.I)
        tmp = f"{tbl}__fkmig"
        new_ddl = re.sub(rf'CREATE TABLE\s+"?{tbl}"?', f'CREATE TABLE {tmp}', new_ddl, count=1, flags=re.I)
        cols = [r[1] for r in conn.execute(f'PRAGMA table_info("{tbl}")')]
        col_list = ", ".join(f'"{c}"' for c in cols)
        conn.execute(new_ddl)
        conn.execute(f'INSERT INTO {tmp} ({col_list}) SELECT {col_list} FROM "{tbl}"')
        conn.execute(f'DROP TABLE "{tbl}"')
        conn.execute(f'ALTER TABLE {tmp} RENAME TO "{tbl}"')
        print(f"FK重建 {tbl}: tasks -> task_unified 完成")

    # 引用重接（新旧区间零重叠，可安全重复执行）
    for tbl, cols in REF_TABLES.items():
        for col in cols:
            n = conn.execute(
                f"UPDATE {tbl} SET {col} = (SELECT new_task_id FROM task_id_map WHERE old_task_id = {tbl}.{col}) "
                f"WHERE {col} IN (SELECT old_task_id FROM task_id_map)").rowcount
            print(f"重接 {tbl}.{col}: {n} 行")

    # 完整性校验后提交
    violations = []
    for tbl in REF_TABLES:
        violations += conn.execute(f'PRAGMA foreign_key_check("{tbl}")').fetchall()
    if violations:
        conn.rollback()
        raise SystemExit(f"foreign_key_check 违规，已回滚: {violations[:5]}")
    conn.commit()
    print("foreign_key_check 通过，已提交")


def check(conn: sqlite3.Connection) -> bool:
    ok = True
    old_n = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    new_n = conn.execute("SELECT COUNT(*) FROM task_unified WHERE task_type='PROJECT'").fetchone()[0]
    print(f"行数对账: tasks={old_n} vs task_unified(PROJECT)={new_n}", "✅" if old_n == new_n else "❌")
    ok &= old_n == new_n

    old_by = dict(conn.execute("SELECT project_id, COUNT(*) FROM tasks GROUP BY 1"))
    new_by = dict(conn.execute(
        "SELECT project_id, COUNT(*) FROM task_unified WHERE task_type='PROJECT' GROUP BY 1"))
    diff = {k: (old_by.get(k, 0), new_by.get(k, 0))
            for k in set(old_by) | set(new_by) if old_by.get(k, 0) != new_by.get(k, 0)}
    print("每项目对账:", "✅ 一致" if not diff else f"❌ 差异 {diff}")
    ok &= not diff

    old_status = {}
    for k, v in conn.execute("SELECT status, COUNT(*) FROM tasks GROUP BY 1"):
        m = STATUS_MAP.get(k, "PENDING")
        old_status[m] = old_status.get(m, 0) + v
    new_status = dict(conn.execute(
        "SELECT status, COUNT(*) FROM task_unified WHERE task_type='PROJECT' GROUP BY 1"))
    sdiff = {k: (old_status.get(k, 0), new_status.get(k, 0))
             for k in set(old_status) | set(new_status)
             if old_status.get(k, 0) != new_status.get(k, 0)}
    print("状态分布对账:", "✅ 一致" if not sdiff else f"❌ 差异 {sdiff}")
    ok &= not sdiff

    for tbl, cols in REF_TABLES.items():
        for col in cols:
            stale = conn.execute(
                f"SELECT COUNT(*) FROM {tbl} WHERE {col} IS NOT NULL AND {col} < ?", (OFFSET,)).fetchone()[0]
            fk_bad = conn.execute(f'PRAGMA foreign_key_check("{tbl}")').fetchall()
            state = "✅" if (stale == 0 and not fk_bad) else f"❌ 未重接={stale} fk违规={len(fk_bad)}"
            print(f"引用完整性 {tbl}.{col}: {state}")
            ok &= stale == 0 and not fk_bad
    return ok


if __name__ == "__main__":
    db_path = "data/app.db"
    if "--db" in sys.argv:
        db_path = sys.argv[sys.argv.index("--db") + 1]
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=OFF")  # 重建/重接期间关闭，提交前 foreign_key_check 兜底
    # 库中存在既有坏视图 v_bom_ready_rate（引用不存在的 bi.ready_status），
    # 常规 RENAME 会触发全库视图校验而失败；legacy 模式跳过该校验
    conn.execute("PRAGMA legacy_alter_table=ON")
    try:
        if "--check" not in sys.argv:
            migrate(conn)
        sys.exit(0 if check(conn) else 1)
    finally:
        conn.close()
