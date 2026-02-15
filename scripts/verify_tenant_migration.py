#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据迁移验证脚本

验证：
1. 是否有 NULL tenant_id
2. 外键完整性
3. 数据一致性

Usage:
    python scripts/verify_tenant_migration.py [--output-report]
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from app.models.base import get_db_session, get_engine
from app.models.tenant import Tenant

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 需要验证的表配置
TABLES_TO_VERIFY = {
    # 用户和权限
    'users': {'tenant_field': 'tenant_id', 'required': True},
    'roles': {'tenant_field': 'tenant_id', 'required': True},
    'api_keys': {'tenant_field': 'tenant_id', 'required': False},
    'api_permissions': {'tenant_field': 'tenant_id', 'required': False},
    'data_scope_rules': {'tenant_field': 'tenant_id', 'required': False},
    'menu_items': {'tenant_field': 'tenant_id', 'required': False},
    
    # 项目管理
    'projects': {'tenant_field': 'tenant_id', 'required': True},
    'project_members': {'tenant_field': 'tenant_id', 'required': True},
    'project_milestones': {'tenant_field': 'tenant_id', 'required': True},
    'project_risks': {'tenant_field': 'tenant_id', 'required': True},
    'project_changes': {'tenant_field': 'tenant_id', 'required': True},
    
    # 任务管理
    'task_unified': {'tenant_field': 'tenant_id', 'required': True},
    
    # 生产管理
    'production_orders': {'tenant_field': 'tenant_id', 'required': True},
    'production_schedules': {'tenant_field': 'tenant_id', 'required': True},
    
    # 物料管理
    'materials': {'tenant_field': 'tenant_id', 'required': True},
    'bom_headers': {'tenant_field': 'tenant_id', 'required': True},
    
    # 售前管理
    'presales': {'tenant_field': 'tenant_id', 'required': True},
    
    # 财务管理
    'project_costs': {'tenant_field': 'tenant_id', 'required': True},
    
    # 工时管理
    'timesheets': {'tenant_field': 'tenant_id', 'required': True},
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


def verify_table(db, engine, table_name: str, config: Dict) -> Dict:
    """
    验证单个表
    
    Returns:
        验证结果字典
    """
    result = {
        'table': table_name,
        'exists': False,
        'has_tenant_column': False,
        'total_records': 0,
        'null_tenant_count': 0,
        'invalid_tenant_count': 0,
        'valid_tenant_count': 0,
        'status': 'unknown',
        'issues': []
    }
    
    # 检查表是否存在
    if not check_table_exists(engine, table_name):
        result['status'] = 'skipped'
        result['issues'].append('表不存在')
        return result
    
    result['exists'] = True
    
    # 检查 tenant_id 列是否存在
    tenant_field = config['tenant_field']
    if not check_column_exists(engine, table_name, tenant_field):
        result['status'] = 'skipped'
        result['issues'].append(f'{tenant_field} 列不存在')
        return result
    
    result['has_tenant_column'] = True
    
    # 统计记录数
    try:
        # 总记录数
        total_query = text(f"SELECT COUNT(*) as count FROM {table_name}")
        total_result = db.execute(total_query).fetchone()
        result['total_records'] = total_result[0] if total_result else 0
        
        # NULL tenant_id 记录数
        null_query = text(f"""
            SELECT COUNT(*) as count 
            FROM {table_name} 
            WHERE {tenant_field} IS NULL
        """)
        null_result = db.execute(null_query).fetchone()
        result['null_tenant_count'] = null_result[0] if null_result else 0
        
        # 无效 tenant_id（不存在的租户）记录数
        invalid_query = text(f"""
            SELECT COUNT(*) as count 
            FROM {table_name} t
            WHERE t.{tenant_field} IS NOT NULL 
            AND NOT EXISTS (
                SELECT 1 FROM tenants WHERE id = t.{tenant_field}
            )
        """)
        invalid_result = db.execute(invalid_query).fetchone()
        result['invalid_tenant_count'] = invalid_result[0] if invalid_result else 0
        
        # 有效记录数
        result['valid_tenant_count'] = (
            result['total_records'] 
            - result['null_tenant_count'] 
            - result['invalid_tenant_count']
        )
        
        # 判断状态
        if result['total_records'] == 0:
            result['status'] = 'empty'
        elif result['null_tenant_count'] > 0:
            result['status'] = 'failed'
            result['issues'].append(f'存在 {result["null_tenant_count"]} 条 NULL tenant_id 记录')
        elif result['invalid_tenant_count'] > 0:
            result['status'] = 'failed'
            result['issues'].append(f'存在 {result["invalid_tenant_count"]} 条无效 tenant_id 记录')
        else:
            result['status'] = 'passed'
        
        # 如果是必须字段且有 NULL 值
        if config.get('required', False) and result['null_tenant_count'] > 0:
            result['issues'].append('必须字段但存在 NULL 值')
            
    except Exception as e:
        result['status'] = 'error'
        result['issues'].append(f'验证失败: {str(e)}')
        logger.error(f"验证表 {table_name} 时出错: {e}")
    
    return result


def verify_all_tables() -> Dict:
    """验证所有表"""
    engine = get_engine()
    verification_results = {
        'timestamp': datetime.now().isoformat(),
        'database': str(engine.url),
        'total_tables': 0,
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'empty': 0,
        'error': 0,
        'details': []
    }
    
    with get_db_session() as db:
        for table_name, config in TABLES_TO_VERIFY.items():
            verification_results['total_tables'] += 1
            
            result = verify_table(db, engine, table_name, config)
            verification_results['details'].append(result)
            
            # 更新统计
            status = result['status']
            if status == 'passed':
                verification_results['passed'] += 1
            elif status == 'failed':
                verification_results['failed'] += 1
            elif status == 'skipped':
                verification_results['skipped'] += 1
            elif status == 'empty':
                verification_results['empty'] += 1
            elif status == 'error':
                verification_results['error'] += 1
    
    return verification_results


def print_verification_report(results: Dict):
    """打印验证报告"""
    logger.info("")
    logger.info("=" * 70)
    logger.info("📋 数据迁移验证报告")
    logger.info("=" * 70)
    logger.info(f"验证时间: {results['timestamp']}")
    logger.info(f"数据库: {results['database']}")
    logger.info("")
    logger.info(f"总表数: {results['total_tables']}")
    logger.info(f"✅ 通过: {results['passed']}")
    logger.info(f"❌ 失败: {results['failed']}")
    logger.info(f"⚠️  跳过: {results['skipped']}")
    logger.info(f"📭 空表: {results['empty']}")
    logger.info(f"🔴 错误: {results['error']}")
    logger.info("=" * 70)
    
    # 打印详细结果
    logger.info("")
    logger.info("详细结果:")
    logger.info("-" * 70)
    
    for detail in results['details']:
        status_icon = {
            'passed': '✅',
            'failed': '❌',
            'skipped': '⚠️ ',
            'empty': '📭',
            'error': '🔴'
        }.get(detail['status'], '?')
        
        logger.info(f"{status_icon} {detail['table']}")
        
        if detail['exists'] and detail['has_tenant_column']:
            logger.info(f"   总记录: {detail['total_records']}")
            logger.info(f"   有效: {detail['valid_tenant_count']}")
            if detail['null_tenant_count'] > 0:
                logger.info(f"   NULL: {detail['null_tenant_count']}")
            if detail['invalid_tenant_count'] > 0:
                logger.info(f"   无效: {detail['invalid_tenant_count']}")
        
        if detail['issues']:
            for issue in detail['issues']:
                logger.info(f"   ⚠️  {issue}")
        
        logger.info("")
    
    logger.info("=" * 70)
    
    # 总结
    if results['failed'] == 0 and results['error'] == 0:
        logger.info("✅ 所有验证通过！")
    else:
        logger.error("❌ 验证发现问题，请检查上述详细信息")
    
    logger.info("=" * 70)


def save_report(results: Dict, output_path: str):
    """保存验证报告到文件"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"📄 验证报告已保存到: {output_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='验证租户数据迁移')
    parser.add_argument('--output-report', type=str, help='输出验证报告到指定文件 (JSON格式)')
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("🔍 开始验证数据迁移")
    logger.info("=" * 70)
    
    try:
        # 执行验证
        results = verify_all_tables()
        
        # 打印报告
        print_verification_report(results)
        
        # 保存报告
        if args.output_report:
            save_report(results, args.output_report)
        
        # 返回结果
        success = (results['failed'] == 0 and results['error'] == 0)
        return success
        
    except Exception as e:
        logger.error(f"❌ 验证过程发生错误: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
