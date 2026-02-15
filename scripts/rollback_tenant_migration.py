#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据迁移回滚脚本

将 tenant_id 设置回 NULL，回滚到单租户模式

⚠️  警告：此操作不可逆，执行前请确保已备份数据库！

Usage:
    python scripts/rollback_tenant_migration.py [--dry-run] [--confirm]
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from app.models.base import get_db_session, get_engine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 需要回滚的表配置
TABLES_TO_ROLLBACK = {
    # 用户和权限
    'users': {'tenant_field': 'tenant_id'},
    'roles': {'tenant_field': 'tenant_id'},
    'api_keys': {'tenant_field': 'tenant_id'},
    'api_permissions': {'tenant_field': 'tenant_id'},
    'data_scope_rules': {'tenant_field': 'tenant_id'},
    'menu_items': {'tenant_field': 'tenant_id'},
    
    # 项目管理
    'projects': {'tenant_field': 'tenant_id'},
    'project_members': {'tenant_field': 'tenant_id'},
    'project_milestones': {'tenant_field': 'tenant_id'},
    'project_risks': {'tenant_field': 'tenant_id'},
    'project_changes': {'tenant_field': 'tenant_id'},
    'project_reviews': {'tenant_field': 'tenant_id'},
    'project_statuses': {'tenant_field': 'tenant_id'},
    
    # 任务管理
    'task_unified': {'tenant_field': 'tenant_id'},
    'task_dependencies': {'tenant_field': 'tenant_id'},
    
    # 生产管理
    'production_orders': {'tenant_field': 'tenant_id'},
    'production_schedules': {'tenant_field': 'tenant_id'},
    'production_progress': {'tenant_field': 'tenant_id'},
    'work_orders': {'tenant_field': 'tenant_id'},
    
    # 物料管理
    'materials': {'tenant_field': 'tenant_id'},
    'bom_headers': {'tenant_field': 'tenant_id'},
    'bom_items': {'tenant_field': 'tenant_id'},
    
    # 采购管理
    'purchase_requisitions': {'tenant_field': 'tenant_id'},
    'purchase_orders': {'tenant_field': 'tenant_id'},
    
    # 售前管理
    'presales': {'tenant_field': 'tenant_id'},
    'presale_solutions': {'tenant_field': 'tenant_id'},
    'presale_quotations': {'tenant_field': 'tenant_id'},
    
    # 财务管理
    'project_costs': {'tenant_field': 'tenant_id'},
    'standard_costs': {'tenant_field': 'tenant_id'},
    
    # 工时管理
    'timesheets': {'tenant_field': 'tenant_id'},
    
    # 文档和报告
    'documents': {'tenant_field': 'tenant_id'},
    'reports': {'tenant_field': 'tenant_id'},
}


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
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def rollback_table(db, engine, table_name: str, config: Dict, dry_run: bool = False) -> Dict:
    """
    回滚单个表
    
    Returns:
        回滚结果字典
    """
    tenant_field = config['tenant_field']
    
    # 检查表是否存在
    if not check_table_exists(engine, table_name):
        logger.warning(f"⚠️  表 {table_name} 不存在，跳过")
        return {'status': 'skipped', 'reason': 'table_not_exists'}
    
    # 检查 tenant_id 列是否存在
    if not check_column_exists(engine, table_name, tenant_field):
        logger.warning(f"⚠️  表 {table_name} 没有 {tenant_field} 列，跳过")
        return {'status': 'skipped', 'reason': 'column_not_exists'}
    
    # 统计需要回滚的记录数
    count_query = text(f"""
        SELECT COUNT(*) as count 
        FROM {table_name} 
        WHERE {tenant_field} IS NOT NULL
    """)
    result = db.execute(count_query).fetchone()
    not_null_count = result[0] if result else 0
    
    if not_null_count == 0:
        logger.info(f"✓ 表 {table_name}: 无需回滚")
        return {'status': 'success', 'rolled_back': 0}
    
    if dry_run:
        logger.info(f"🔍 [DRY-RUN] 表 {table_name}: 将回滚 {not_null_count} 条记录")
        return {'status': 'dry_run', 'would_rollback': not_null_count}
    
    # 执行回滚
    try:
        update_query = text(f"""
            UPDATE {table_name}
            SET {tenant_field} = NULL
            WHERE {tenant_field} IS NOT NULL
        """)
        result = db.execute(update_query)
        updated = result.rowcount
        
        logger.info(f"✅ 表 {table_name}: 成功回滚 {updated} 条记录")
        return {'status': 'success', 'rolled_back': updated}
        
    except Exception as e:
        logger.error(f"❌ 表 {table_name}: 回滚失败 - {e}")
        return {'status': 'error', 'error': str(e)}


def rollback_all_tables(dry_run: bool = False) -> Dict:
    """
    回滚所有表
    
    Returns:
        回滚统计信息
    """
    engine = get_engine()
    stats = {
        'total_tables': 0,
        'rolled_back_tables': 0,
        'skipped_tables': 0,
        'error_tables': 0,
        'total_records': 0,
        'details': {}
    }
    
    with get_db_session() as db:
        for table_name, config in TABLES_TO_ROLLBACK.items():
            stats['total_tables'] += 1
            
            result = rollback_table(db, engine, table_name, config, dry_run)
            stats['details'][table_name] = result
            
            if result['status'] == 'success':
                stats['rolled_back_tables'] += 1
                stats['total_records'] += result.get('rolled_back', 0)
            elif result['status'] == 'skipped':
                stats['skipped_tables'] += 1
            elif result['status'] == 'error':
                stats['error_tables'] += 1
            elif result['status'] == 'dry_run':
                stats['total_records'] += result.get('would_rollback', 0)
    
    return stats


def print_summary(stats: Dict, dry_run: bool = False):
    """打印回滚摘要"""
    logger.info("")
    logger.info("=" * 60)
    if dry_run:
        logger.info("📋 回滚预览（DRY-RUN）")
    else:
        logger.info("📊 回滚完成摘要")
    logger.info("=" * 60)
    logger.info(f"总表数: {stats['total_tables']}")
    logger.info(f"成功回滚: {stats['rolled_back_tables']}")
    logger.info(f"跳过: {stats['skipped_tables']}")
    logger.info(f"错误: {stats['error_tables']}")
    if dry_run:
        logger.info(f"将回滚记录数: {stats['total_records']}")
    else:
        logger.info(f"已回滚记录数: {stats['total_records']}")
    logger.info("=" * 60)
    
    if stats['error_tables'] > 0:
        logger.info("")
        logger.info("错误详情:")
        for table, result in stats['details'].items():
            if result['status'] == 'error':
                logger.error(f"  - {table}: {result['error']}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='回滚租户数据迁移')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际执行回滚')
    parser.add_argument('--confirm', action='store_true', help='确认执行回滚（必须提供此参数）')
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("⚠️  数据迁移回滚工具")
    logger.info("=" * 60)
    
    if not args.dry_run and not args.confirm:
        logger.error("")
        logger.error("❌ 错误：回滚操作需要确认！")
        logger.error("")
        logger.error("请使用以下命令之一：")
        logger.error("  1. 预览回滚（安全）：")
        logger.error("     python scripts/rollback_tenant_migration.py --dry-run")
        logger.error("")
        logger.error("  2. 执行回滚（危险，不可逆）：")
        logger.error("     python scripts/rollback_tenant_migration.py --confirm")
        logger.error("")
        logger.error("⚠️  执行前请确保已备份数据库！")
        logger.error("=" * 60)
        return False
    
    if not args.dry_run:
        logger.warning("")
        logger.warning("⚠️  ⚠️  ⚠️  警告 ⚠️  ⚠️  ⚠️")
        logger.warning("")
        logger.warning("您即将执行数据回滚操作！")
        logger.warning("此操作将：")
        logger.warning("  1. 将所有表的 tenant_id 设置为 NULL")
        logger.warning("  2. 系统将回到单租户模式")
        logger.warning("  3. 此操作不可逆！")
        logger.warning("")
        logger.warning("⚠️  请确保您已经备份了数据库！")
        logger.warning("")
        
        response = input("确定要继续吗？输入 'YES' 继续: ")
        if response != 'YES':
            logger.info("已取消回滚操作")
            return False
        
        logger.warning("")
        logger.warning("🚀 开始执行回滚...")
        logger.warning("")
    else:
        logger.info("")
        logger.info("🔍 回滚预览模式（DRY-RUN）")
        logger.info("")
    
    try:
        engine = get_engine()
        logger.info(f"数据库: {engine.url}")
        logger.info("")
        
        # 执行回滚
        stats = rollback_all_tables(args.dry_run)
        
        # 打印摘要
        print_summary(stats, args.dry_run)
        
        if args.dry_run:
            logger.info("")
            logger.info("💡 这只是预览，要实际执行回滚请运行:")
            logger.info("   python scripts/rollback_tenant_migration.py --confirm")
            logger.info("")
            logger.info("⚠️  执行前请确保已备份数据库！")
            return True
        
        if stats['error_tables'] > 0:
            logger.warning("")
            logger.warning("⚠️  部分表回滚失败，请检查错误信息")
            return False
        
        logger.info("")
        logger.info("✅ 数据回滚完成！")
        logger.info("")
        logger.info("下一步：")
        logger.info("  1. 验证数据完整性")
        logger.info("  2. 如需删除租户表，请手动执行")
        logger.info("  3. 更新应用代码，移除多租户逻辑")
        return True
        
    except Exception as e:
        logger.error(f"❌ 回滚过程发生错误: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
