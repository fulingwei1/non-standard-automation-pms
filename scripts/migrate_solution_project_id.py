#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据迁移脚本：关联现有投标方案到项目

将现有的 PresaleSolution 通过以下方式关联到项目：
1. 通过 ticket_id → PresaleSupportTicket.project_id
2. 通过 opportunity_id → Project.opportunity_id

使用方法：
    cd /path/to/project
    python scripts/migrate_solution_project_id.py

    # 仅预览，不实际执行
    python scripts/migrate_solution_project_id.py --dry-run
"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def get_db_session():
    """获取数据库会话"""
    engine = create_engine(str(settings.DATABASE_URL))
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def migrate_solution_project_ids(dry_run: bool = False):
    """
    迁移投标方案的 project_id

    迁移策略：
    1. 优先通过 ticket_id 关联（工单明确关联项目）
    2. 其次通过 opportunity_id 关联（商机关联项目）
    """
    session = get_db_session()

    try:
        # 统计信息
        stats = {
            "total": 0,
            "already_linked": 0,
            "linked_via_ticket": 0,
            "linked_via_opportunity": 0,
            "no_link_found": 0,
        }

        # 查询所有投标方案
        solutions = session.execute(
            text("""
                SELECT id, ticket_id, opportunity_id, project_id, name
                FROM presale_solution
                ORDER BY id
            """)
        ).fetchall()

        stats["total"] = len(solutions)
        print(f"找到 {stats['total']} 个投标方案")

        updates = []

        for sol in solutions:
            sol_id, ticket_id, opportunity_id, project_id, name = sol

            # 已经有 project_id，跳过
            if project_id:
                stats["already_linked"] += 1
                continue

            new_project_id = None
            link_method = None

            # 方式1：通过 ticket_id 查找 project_id
            if ticket_id:
                result = session.execute(
                    text("""
                        SELECT project_id FROM presale_support_ticket
                        WHERE id = :ticket_id AND project_id IS NOT NULL
                    """),
                    {"ticket_id": ticket_id}
                ).fetchone()

                if result and result[0]:
                    new_project_id = result[0]
                    link_method = "ticket"

            # 方式2：通过 opportunity_id 查找 project_id
            if not new_project_id and opportunity_id:
                result = session.execute(
                    text("""
                        SELECT id FROM projects
                        WHERE opportunity_id = :opportunity_id
                        LIMIT 1
                    """),
                    {"opportunity_id": opportunity_id}
                ).fetchone()

                if result and result[0]:
                    new_project_id = result[0]
                    link_method = "opportunity"

            if new_project_id:
                updates.append({
                    "id": sol_id,
                    "project_id": new_project_id,
                    "name": name,
                    "method": link_method,
                })
                if link_method == "ticket":
                    stats["linked_via_ticket"] += 1
                else:
                    stats["linked_via_opportunity"] += 1
            else:
                stats["no_link_found"] += 1
                print(f"  [跳过] 方案 #{sol_id} '{name}' - 无法找到关联项目")

        # 执行更新
        if updates:
            print(f"\n准备更新 {len(updates)} 个投标方案...")

            for upd in updates:
                print(f"  方案 #{upd['id']} '{upd['name']}' → 项目 #{upd['project_id']} (via {upd['method']})")

                if not dry_run:
                    session.execute(
                        text("""
                            UPDATE presale_solution
                            SET project_id = :project_id
                            WHERE id = :id
                        """),
                        {"id": upd["id"], "project_id": upd["project_id"]}
                    )

            if not dry_run:
                session.commit()
                print("\n✅ 迁移完成!")
            else:
                print("\n[DRY RUN] 以上为预览，未实际执行更新")

        # 打印统计
        print("\n📊 迁移统计:")
        print(f"  总计方案数: {stats['total']}")
        print(f"  已有关联: {stats['already_linked']}")
        print(f"  通过工单关联: {stats['linked_via_ticket']}")
        print(f"  通过商机关联: {stats['linked_via_opportunity']}")
        print(f"  未找到关联: {stats['no_link_found']}")

    except Exception as e:
        session.rollback()
        print(f"❌ 迁移失败: {e}")
        raise
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="迁移投标方案的 project_id")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅预览，不实际执行更新"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("投标方案 project_id 迁移脚本")
    print("=" * 60)

    if args.dry_run:
        print("[DRY RUN 模式] 仅预览，不实际修改数据\n")

    migrate_solution_project_ids(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
