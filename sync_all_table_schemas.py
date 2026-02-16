#!/usr/bin/env python3
"""
系统性Schema同步脚本

对比所有表的SQLAlchemy模型定义与数据库实际schema，
生成并执行ALTER TABLE语句，确保数据库schema完整。
"""
import sys
import sqlite3
from pathlib import Path
from typing import Dict, Set, List, Tuple
from sqlalchemy import create_engine, inspect
from sqlalchemy.types import (
    Integer, String, Text, Boolean, Date, DateTime, 
    Numeric, Float, JSON, DECIMAL
)

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.models.base import Base
from app.core.config import settings

def get_db_schema(db_path: Path) -> Dict[str, Set[str]]:
    """获取数据库中所有表的列"""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = {}
    
    for (table_name,) in cursor.fetchall():
        if table_name.startswith('sqlite_'):
            continue
        
        # 获取每个表的列
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = {row[1] for row in cursor.fetchall()}
        tables[table_name] = columns
    
    conn.close()
    return tables

def get_model_schema() -> Dict[str, Dict[str, any]]:
    """获取SQLAlchemy模型定义的所有表和列"""
    # 导入所有模型
    import app.models
    
    tables = {}
    for table_name, table in Base.metadata.tables.items():
        columns = {}
        for column in table.columns:
            columns[column.name] = {
                'type': column.type,
                'nullable': column.nullable,
                'primary_key': column.primary_key,
                'default': column.default
            }
        tables[table_name] = columns
    
    return tables

def sqlalchemy_type_to_sqlite(col_type) -> str:
    """将SQLAlchemy类型转换为SQLite类型"""
    type_class = type(col_type).__name__
    
    if isinstance(col_type, (Integer,)):
        return "INTEGER"
    elif isinstance(col_type, String):
        if col_type.length:
            return f"VARCHAR({col_type.length})"
        return "VARCHAR(255)"
    elif isinstance(col_type, Text):
        return "TEXT"
    elif isinstance(col_type, Boolean):
        return "BOOLEAN"
    elif isinstance(col_type, (Date,)):
        return "DATE"
    elif isinstance(col_type, DateTime):
        return "DATETIME"
    elif isinstance(col_type, (Numeric, DECIMAL)):
        if hasattr(col_type, 'precision') and hasattr(col_type, 'scale'):
            return f"DECIMAL({col_type.precision},{col_type.scale})"
        return "DECIMAL(15,2)"
    elif isinstance(col_type, Float):
        return "FLOAT"
    elif isinstance(col_type, JSON):
        return "TEXT"  # SQLite存储JSON为TEXT
    else:
        # 默认处理
        return "TEXT"

def generate_alter_statements(
    db_schema: Dict[str, Set[str]], 
    model_schema: Dict[str, Dict[str, any]]
) -> List[Tuple[str, str, str]]:
    """生成ALTER TABLE语句"""
    alter_statements = []
    
    for table_name in sorted(model_schema.keys()):
        if table_name not in db_schema:
            # 表不存在，跳过（应该已经被create_missing_tables_sql.py创建了）
            continue
        
        db_columns = db_schema[table_name]
        model_columns = model_schema[table_name]
        
        # 找出缺失的列
        missing_columns = set(model_columns.keys()) - db_columns
        
        for col_name in sorted(missing_columns):
            col_info = model_columns[col_name]
            col_type_str = sqlalchemy_type_to_sqlite(col_info['type'])
            
            # 构建ALTER TABLE语句
            sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type_str}"
            
            # 添加默认值（如果有）
            if col_info['default'] is not None:
                default_value = col_info['default']
                if hasattr(default_value, 'arg'):
                    default_arg = default_value.arg
                    if isinstance(default_arg, str):
                        sql += f" DEFAULT '{default_arg}'"
                    elif isinstance(default_arg, bool):
                        sql += f" DEFAULT {1 if default_arg else 0}"
                    elif isinstance(default_arg, (int, float)):
                        sql += f" DEFAULT {default_arg}"
            
            alter_statements.append((table_name, col_name, sql))
    
    return alter_statements

def execute_alter_statements(
    db_path: Path, 
    statements: List[Tuple[str, str, str]],
    dry_run: bool = False
) -> Tuple[int, int]:
    """执行ALTER TABLE语句"""
    if dry_run:
        print("🔍 DRY RUN 模式 - 仅显示SQL，不执行\n")
        for table_name, col_name, sql in statements:
            print(f"[{table_name}] {col_name}")
            print(f"  {sql}")
        return len(statements), 0
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    success_count = 0
    fail_count = 0
    
    for table_name, col_name, sql in statements:
        try:
            cursor.execute(sql)
            success_count += 1
            print(f"   ✓ [{table_name}] {col_name}")
        except Exception as e:
            fail_count += 1
            print(f"   ✗ [{table_name}] {col_name}: {e}")
    
    conn.commit()
    conn.close()
    
    return success_count, fail_count

def main():
    print("="*60)
    print("🔧 系统性Schema同步脚本")
    print("="*60)
    print()
    
    # 数据库路径
    db_path = Path("data/app.db")  # 直接使用已知路径
    if not db_path.exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        sys.exit(1)
    
    print(f"📊 数据库: {db_path}")
    print()
    
    # 步骤1: 获取数据库schema
    print("1️⃣  扫描数据库schema...")
    db_schema = get_db_schema(db_path)
    print(f"   ✓ 找到 {len(db_schema)} 个表")
    print()
    
    # 步骤2: 获取模型schema
    print("2️⃣  加载SQLAlchemy模型定义...")
    model_schema = get_model_schema()
    print(f"   ✓ 加载 {len(model_schema)} 个模型")
    print()
    
    # 步骤3: 对比并生成ALTER语句
    print("3️⃣  对比schema差异...")
    alter_statements = generate_alter_statements(db_schema, model_schema)
    
    if not alter_statements:
        print("   ✅ 所有表的schema都是完整的！无需修复。")
        return
    
    print(f"   ⚠️  发现 {len(alter_statements)} 个缺失的列")
    print()
    
    # 按表统计
    table_stats = {}
    for table_name, col_name, sql in alter_statements:
        if table_name not in table_stats:
            table_stats[table_name] = []
        table_stats[table_name].append(col_name)
    
    print(f"   📋 影响 {len(table_stats)} 个表:")
    for table_name in sorted(table_stats.keys())[:20]:
        cols = table_stats[table_name]
        print(f"      • {table_name}: {len(cols)} 个列")
    if len(table_stats) > 20:
        print(f"      ... 还有 {len(table_stats) - 20} 个表")
    print()
    
    # 步骤4: 执行修复
    print("4️⃣  执行ALTER TABLE...")
    print()
    success_count, fail_count = execute_alter_statements(
        db_path, 
        alter_statements, 
        dry_run=False
    )
    print()
    
    # 步骤5: 验证结果
    print("5️⃣  验证修复结果...")
    db_schema_after = get_db_schema(db_path)
    still_missing = []
    
    for table_name, col_name, sql in alter_statements:
        if col_name not in db_schema_after.get(table_name, set()):
            still_missing.append((table_name, col_name))
    
    print()
    print("="*60)
    print("📊 修复统计")
    print("="*60)
    print(f"✅ 成功添加: {success_count} 个列")
    print(f"❌ 添加失败: {fail_count} 个列")
    if still_missing:
        print(f"⚠️  仍然缺失: {len(still_missing)} 个列")
        for table, col in still_missing[:10]:
            print(f"   - {table}.{col}")
        if len(still_missing) > 10:
            print(f"   ... 还有 {len(still_missing) - 10} 个")
    print()
    
    # 生成报告
    report_path = Path("schema_sync_report.txt")
    with open(report_path, "w") as f:
        f.write("Schema同步报告\n")
        f.write("="*60 + "\n\n")
        f.write(f"执行时间: {Path(__file__).stat().st_mtime}\n")
        f.write(f"数据库: {db_path}\n")
        f.write(f"总共检查: {len(model_schema)} 个表\n")
        f.write(f"需要修复: {len(table_stats)} 个表\n")
        f.write(f"缺失列数: {len(alter_statements)} 个\n")
        f.write(f"成功添加: {success_count} 个\n")
        f.write(f"添加失败: {fail_count} 个\n\n")
        
        f.write("详细列表:\n")
        f.write("-"*60 + "\n")
        for table_name in sorted(table_stats.keys()):
            f.write(f"\n{table_name}:\n")
            for col_name in table_stats[table_name]:
                f.write(f"  - {col_name}\n")
    
    print(f"📄 详细报告已保存: {report_path}")
    print()
    
    if success_count == len(alter_statements) and fail_count == 0:
        print("🎉 所有列已成功添加！Schema完全同步。")
        sys.exit(0)
    else:
        print("⚠️  部分列添加失败，请检查错误信息。")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
