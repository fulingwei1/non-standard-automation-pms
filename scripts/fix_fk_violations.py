#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 SQLite 数据库中的历史外键违规 (PRAGMA foreign_key_check)

历史问题分析：
1. 179 条采购/物料/外协记录外键关联 vendors (supplier_id/vendor_id IN (1, 2, 3))，但 vendors 表中缺失 ID 1, 2, 3。
2. 48 条工单 (work_order.assigned_to IN (36, 37, 38, 39)) 关联已删除的测试工人。
3. 4 条售前费用 (presale_expenses.project_id = 0) 关联不存在的项目 0。
4. 2 条盘点明细 (stock_count_detail.task_id IN (4, 7)) 与实际盘点任务 ID (3, 6) 偏移。
5. 2 条 BOM (bom_headers.created_by IN (196, 197)) 关联已清理的测试账号。
6. 2 条权限审计 (permission_audits.operator_id = 199) 关联已清理的测试账号。

用法:
    python scripts/fix_fk_violations.py [--db data/app.db] [--backup]
"""
from __future__ import annotations

import argparse
import logging
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT_DIR / "data" / "app.db"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fix_fk_violations")


def repair_foreign_keys(db_path: Path, backup: bool = True) -> int:
    if not db_path.exists():
        logger.error(f"数据库文件不存在: {db_path}")
        return -1

    if backup:
        backup_path = db_path.with_suffix(f".before_fk_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        shutil.copy2(db_path, backup_path)
        logger.info(f"已创建数据库备份: {backup_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_key_check")
    initial_violations = len(cursor.fetchall())
    logger.info(f"修复前外键违规数量: {initial_violations}")

    now = "2026-01-01 00:00:00"

    # 1. 补齐历史供应商数据 (修复 179 处外键关联)
    historical_vendors = [
        (1, "V001", "汇川技术（历史供应商）"),
        (2, "V002", "西门子（历史供应商）"),
        (3, "V003", "欧姆龙（历史供应商）"),
    ]
    for vid, code, name in historical_vendors:
        cursor.execute(
            """
            INSERT OR IGNORE INTO vendors (id, supplier_code, supplier_name, vendor_type, created_at, updated_at, tenant_id)
            VALUES (?, ?, ?, 'MATERIAL', ?, ?, 1)
            """,
            (vid, code, name, now, now),
        )

    # 2. 补齐历史工人档案 (修复 48 处工单外键关联)
    for wid in [36, 37, 38, 39]:
        cursor.execute(
            """
            INSERT OR IGNORE INTO worker (id, worker_no, worker_name, status, is_active, created_at, updated_at, tenant_id)
            VALUES (?, ?, ?, 'ACTIVE', 1, ?, ?, 1)
            """,
            (wid, f"WORKER{wid:06d}", f"装配工程师_{wid}", now, now),
        )

    # 3. 修正售前费用关联的不存在项目 0 -> 默认项目 1 (4 处)
    cursor.execute("UPDATE presale_expenses SET project_id = 1 WHERE project_id = 0")

    # 4. 修正盘点明细任务关联偏移 (4->3, 7->6) (2 处)
    cursor.execute("UPDATE stock_count_detail SET task_id = 3 WHERE task_id = 4")
    cursor.execute("UPDATE stock_count_detail SET task_id = 6 WHERE task_id = 7")

    # 5. 修正 BOM 关联的历史已清理测试用户 -> 系统管理员 1 (2 处)
    cursor.execute("UPDATE bom_headers SET created_by = 1 WHERE created_by IN (196, 197)")

    # 6. 修正权限审计关联的历史已清理测试用户 -> 系统管理员 1 (2 处)
    cursor.execute("UPDATE permission_audits SET operator_id = 1 WHERE operator_id = 199")

    conn.commit()

    cursor.execute("PRAGMA foreign_key_check")
    remaining_violations = len(cursor.fetchall())
    logger.info(f"修复后外键违规数量: {remaining_violations}")
    conn.close()

    return remaining_violations


def main():
    parser = argparse.ArgumentParser(description="修复 SQLite 外键违规数据")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="数据库路径")
    parser.add_argument("--no-backup", action="store_true", help="跳过备份")
    args = parser.parse_args()

    remaining = repair_foreign_keys(args.db, backup=not args.no_backup)
    if remaining == 0:
        logger.info("外键完整性修复成功，所有约束校验通过！")
    else:
        logger.warning(f"仍存在 {remaining} 条外键违规，需进一步排查。")


if __name__ == "__main__":
    main()
