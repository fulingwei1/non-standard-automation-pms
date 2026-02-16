#!/usr/bin/env python3
"""
检查数据库schema与SQLAlchemy模型定义的同步情况
"""
import sqlite3
from pathlib import Path
from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import Session
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings

def get_db_tables():
    """获取数据库中的所有表"""
    db_path = Path(settings.SQLITE_DB_PATH)
    if not db_path.exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return {}
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = {}
    
    for (table_name,) in cursor.fetchall():
        if table_name.startswith('sqlite_'):
            continue
            
        # 获取每个表的列信息
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = {}
        for col in cursor.fetchall():
            col_id, col_name, col_type, not_null, default_val, is_pk = col
            columns[col_name] = {
                'type': col_type,
                'not_null': bool(not_null),
                'default': default_val,
                'primary_key': bool(is_pk)
            }
        tables[table_name] = columns
    
    conn.close()
    return tables

def get_model_tables():
    """获取SQLAlchemy模型定义的所有表"""
    from app.models.base import Base
    
    # 创建临时内存数据库来检查模型
    engine = create_engine("sqlite:///:memory:")
    
    # 导入所有模型（确保它们被注册到Base.metadata）
    import app.models
    
    tables = {}
    for table_name, table in Base.metadata.tables.items():
        columns = {}
        for column in table.columns:
            columns[column.name] = {
                'type': str(column.type),
                'nullable': column.nullable,
                'primary_key': column.primary_key,
                'default': str(column.default) if column.default else None
            }
        tables[table_name] = columns
    
    return tables

def compare_schemas():
    """比较数据库schema与模型定义"""
    print("🔍 开始检查数据库schema与模型定义的同步情况...\n")
    
    db_tables = get_db_tables()
    model_tables = get_model_tables()
    
    print(f"📊 数据库中的表数量: {len(db_tables)}")
    print(f"📊 模型定义的表数量: {len(model_tables)}\n")
    
    # 检查缺失的表
    missing_tables = set(model_tables.keys()) - set(db_tables.keys())
    if missing_tables:
        print(f"❌ 数据库中缺失的表 ({len(missing_tables)}):")
        for table in sorted(missing_tables):
            print(f"   - {table}")
        print()
    else:
        print("✅ 所有模型定义的表都存在于数据库中\n")
    
    # 检查多余的表
    extra_tables = set(db_tables.keys()) - set(model_tables.keys())
    if extra_tables:
        print(f"⚠️  数据库中多余的表 ({len(extra_tables)}):")
        for table in sorted(extra_tables):
            print(f"   - {table}")
        print()
    
    # 检查每个表的列
    column_issues = []
    for table_name in sorted(set(db_tables.keys()) & set(model_tables.keys())):
        db_cols = set(db_tables[table_name].keys())
        model_cols = set(model_tables[table_name].keys())
        
        missing_cols = model_cols - db_cols
        extra_cols = db_cols - model_cols
        
        if missing_cols or extra_cols:
            column_issues.append({
                'table': table_name,
                'missing': missing_cols,
                'extra': extra_cols
            })
    
    if column_issues:
        print(f"❌ 发现 {len(column_issues)} 个表的列定义不匹配:\n")
        for issue in column_issues:
            print(f"📋 表: {issue['table']}")
            if issue['missing']:
                print(f"   ❌ 缺失的列: {', '.join(sorted(issue['missing']))}")
            if issue['extra']:
                print(f"   ⚠️  多余的列: {', '.join(sorted(issue['extra']))}")
            print()
    else:
        print("✅ 所有表的列定义都匹配\n")
    
    # 生成修复SQL
    if missing_tables or column_issues:
        print("\n" + "="*60)
        print("🔧 建议的修复SQL:\n")
        
        # 缺失的表
        if missing_tables:
            print("-- 创建缺失的表:")
            print("-- 请使用Alembic或手动创建以下表:")
            for table in sorted(missing_tables):
                print(f"-- {table}")
            print()
        
        # 缺失的列
        if column_issues:
            print("-- 添加缺失的列:")
            for issue in column_issues:
                if not issue['missing']:
                    continue
                print(f"\n-- 表: {issue['table']}")
                for col_name in sorted(issue['missing']):
                    col_info = model_tables[issue['table']][col_name]
                    nullable = "NULL" if col_info['nullable'] else "NOT NULL"
                    print(f"ALTER TABLE {issue['table']} ADD COLUMN {col_name} {col_info['type']} {nullable};")
        print("\n" + "="*60)
    
    # 返回状态
    return len(missing_tables) == 0 and len(column_issues) == 0

if __name__ == "__main__":
    try:
        is_synced = compare_schemas()
        if is_synced:
            print("\n✅ 数据库schema与模型定义完全同步！")
            sys.exit(0)
        else:
            print("\n❌ 数据库schema与模型定义不同步，需要修复。")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 检查过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
