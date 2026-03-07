#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据迁移脚本 - 将现有数据关联到默认租户

此脚本将所有现有数据的 tenant_id 设置为默认租户ID

Usage:
    python scripts/migrate_to_default_tenant.py [--dry-run] [--tenant-id ID]
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect, text

from app.models.base import get_db_session, get_engine
from app.models.tenant import Tenant

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# 需要迁移的表和字段配置
# 格式: {表名: {'tenant_field': tenant_id字段名, 'id_field': 主键字段名}}
TABLES_TO_MIGRATE = {
    # 用户和权限
    "users": {"tenant_field": "tenant_id", "id_field": "id"},
    "roles": {"tenant_field": "tenant_id", "id_field": "id"},
    "api_keys": {"tenant_field": "tenant_id", "id_field": "id"},
    "api_permissions": {"tenant_field": "tenant_id", "id_field": "id"},
    "data_scope_rules": {"tenant_field": "tenant_id", "id_field": "id"},
    "menu_items": {"tenant_field": "tenant_id", "id_field": "id"},
    # 项目管理
    "projects": {"tenant_field": "tenant_id", "id_field": "id"},
    "project_members": {"tenant_field": "tenant_id", "id_field": "id"},
    "project_milestones": {"tenant_field": "tenant_id", "id_field": "id"},
    "project_risks": {"tenant_field": "tenant_id", "id_field": "id"},
    "project_changes": {"tenant_field": "tenant_id", "id_field": "id"},
    "project_reviews": {"tenant_field": "tenant_id", "id_field": "id"},
    "project_statuses": {"tenant_field": "tenant_id", "id_field": "id"},
    # 任务管理
    "task_unified": {"tenant_field": "tenant_id", "id_field": "id"},
    "task_dependencies": {"tenant_field": "tenant_id", "id_field": "id"},
    # 生产管理
    "production_orders": {"tenant_field": "tenant_id", "id_field": "id"},
    "production_schedules": {"tenant_field": "tenant_id", "id_field": "id"},
    "production_progress": {"tenant_field": "tenant_id", "id_field": "id"},
    "work_orders": {"tenant_field": "tenant_id", "id_field": "id"},
    # 物料管理
    "materials": {"tenant_field": "tenant_id", "id_field": "id"},
    "bom_headers": {"tenant_field": "tenant_id", "id_field": "id"},
    "bom_items": {"tenant_field": "tenant_id", "id_field": "id"},
    # 采购管理
    "purchase_requisitions": {"tenant_field": "tenant_id", "id_field": "id"},
    "purchase_orders": {"tenant_field": "tenant_id", "id_field": "id"},
    # 售前管理
    "presales": {"tenant_field": "tenant_id", "id_field": "id"},
    "presale_solutions": {"tenant_field": "tenant_id", "id_field": "id"},
    "presale_quotations": {"tenant_field": "tenant_id", "id_field": "id"},
    # 财务管理
    "project_costs": {"tenant_field": "tenant_id", "id_field": "id"},
    "standard_costs": {"tenant_field": "tenant_id", "id_field": "id"},
    # 工时管理
    "timesheets": {"tenant_field": "tenant_id", "id_field": "id"},
    # 文档和报告
    "documents": {"tenant_field": "tenant_id", "id_field": "id"},
    "reports": {"tenant_field": "tenant_id", "id_field": "id"},
}


def get_default_tenant(db) -> Tenant:
    """获取默认租户"""
    tenant = db.query(Tenant).filter(Tenant.tenant_code == "jinkaibo").first()

    if not tenant:
        logger.error("❌ 未找到默认租户，请先运行 create_default_tenant.py")
        sys.exit(1)

    return tenant


def check_table_exists(engine, table_name: str) -> bool:
    """检查表是否存在"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    return table_name in tables


def check_column_exists(engine, table_name: str, column_name: str) -> bool:
    """检查列是否存在"""
    if not check_table_exists(engine, table_name):
        return False

    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def migrate_table(
    db, engine, table_name: str, config: Dict, tenant_id: int, dry_run: bool = False
) -> Dict:
    """
    迁移单个表的数据

    Returns:
        统计信息字典
    """
    tenant_field = config['tenant_field']
    config['id_field']
    
    # 检查表是否存在
    if not check_table_exists(engine, table_name):
        logger.warning(f"⚠️  表 {table_name} 不存在，跳过")
        return {"status": "skipped", "reason": "table_not_exists"}

    # 检查 tenant_id 列是否存在
    if not check_column_exists(engine, table_name, tenant_field):
        logger.warning(f"⚠️  表 {table_name} 没有 {tenant_field} 列，跳过")
        return {"status": "skipped", "reason": "column_not_exists"}

    # 统计需要迁移的记录数
    count_query = text(
        f"""
        SELECT COUNT(*) as count 
        FROM {table_name} 
        WHERE {tenant_field} IS NULL
    """
    )
    result = db.execute(count_query).fetchone()
    null_count = result[0] if result else 0

    if null_count == 0:
        logger.info(f"✓ 表 {table_name}: 无需迁移")
        return {"status": "success", "migrated": 0, "skipped": 0}

    if dry_run:
        logger.info(f"🔍 [DRY-RUN] 表 {table_name}: 将迁移 {null_count} 条记录")
        return {"status": "dry_run", "would_migrate": null_count}

    # 执行迁移
    try:
        update_query = text(
            f"""
            UPDATE {table_name}
            SET {tenant_field} = :tenant_id
            WHERE {tenant_field} IS NULL
        """
        )
        result = db.execute(update_query, {"tenant_id": tenant_id})
        updated = result.rowcount

        logger.info(f"✅ 表 {table_name}: 成功迁移 {updated} 条记录")
        return {"status": "success", "migrated": updated}

    except Exception as e:
        logger.error(f"❌ 表 {table_name}: 迁移失败 - {e}")
        return {"status": "error", "error": str(e)}


def migrate_all_tables(tenant_id: int, dry_run: bool = False) -> Dict:
    """
    迁移所有表的数据

    Returns:
        迁移统计信息
    """
    engine = get_engine()
    stats = {
        "total_tables": 0,
        "migrated_tables": 0,
        "skipped_tables": 0,
        "error_tables": 0,
        "total_records": 0,
        "details": {},
    }

    with get_db_session() as db:
        for table_name, config in TABLES_TO_MIGRATE.items():
            stats["total_tables"] += 1

            result = migrate_table(db, engine, table_name, config, tenant_id, dry_run)
            stats["details"][table_name] = result

            if result["status"] == "success":
                stats["migrated_tables"] += 1
                stats["total_records"] += result.get("migrated", 0)
            elif result["status"] == "skipped":
                stats["skipped_tables"] += 1
            elif result["status"] == "error":
                stats["error_tables"] += 1
            elif result["status"] == "dry_run":
                stats["total_records"] += result.get("would_migrate", 0)

    return stats


def print_summary(stats: Dict, dry_run: bool = False):
    """打印迁移摘要"""
    logger.info("")
    logger.info("=" * 60)
    if dry_run:
        logger.info("📋 迁移预览（DRY-RUN）")
    else:
        logger.info("📊 迁移完成摘要")
    logger.info("=" * 60)
    logger.info(f"总表数: {stats['total_tables']}")
    logger.info(f"成功迁移: {stats['migrated_tables']}")
    logger.info(f"跳过: {stats['skipped_tables']}")
    logger.info(f"错误: {stats['error_tables']}")
    if dry_run:
        logger.info(f"将迁移记录数: {stats['total_records']}")
    else:
        logger.info(f"已迁移记录数: {stats['total_records']}")
    logger.info("=" * 60)

    if stats["error_tables"] > 0:
        logger.info("")
        logger.info("错误详情:")
        for table, result in stats["details"].items():
            if result["status"] == "error":
                logger.error(f"  - {table}: {result['error']}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="迁移数据到默认租户")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际执行迁移")
    parser.add_argument("--tenant-id", type=int, help="指定租户ID（默认使用 jinkaibo 租户）")
    args = parser.parse_args()

    logger.info("=" * 60)
    if args.dry_run:
        logger.info("🔍 数据迁移预览（DRY-RUN 模式）")
    else:
        logger.info("🚀 开始数据迁移")
    logger.info("=" * 60)

    try:
        engine = get_engine()
        logger.info(f"数据库: {engine.url}")

        # 获取租户ID
        if args.tenant_id:
            tenant_id = args.tenant_id
            logger.info(f"使用指定租户ID: {tenant_id}")
        else:
            with get_db_session() as db:
                tenant = get_default_tenant(db)
                tenant_id = tenant.id
                logger.info(f"使用默认租户: {tenant.tenant_code} (ID: {tenant_id})")

        logger.info("")

        # 执行迁移
        stats = migrate_all_tables(tenant_id, args.dry_run)

        # 打印摘要
        print_summary(stats, args.dry_run)

        if args.dry_run:
            logger.info("")
            logger.info("💡 这只是预览，要实际执行迁移请运行:")
            logger.info("   python scripts/migrate_to_default_tenant.py")
            return True

        if stats["error_tables"] > 0:
            logger.warning("")
            logger.warning("⚠️  部分表迁移失败，请检查错误信息")
            return False

        logger.info("")
        logger.info("✅ 数据迁移完成！")
        return True

    except Exception as e:
        logger.error(f"❌ 迁移过程发生错误: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
