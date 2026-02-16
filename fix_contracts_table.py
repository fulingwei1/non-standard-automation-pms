#!/usr/bin/env python3
"""
修复contracts表的缺失列
"""
import sqlite3
from pathlib import Path

db_path = Path("data/app.db")
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("🔧 开始修复contracts表...\n")

# 获取现有列
cursor.execute("PRAGMA table_info(contracts);")
existing_columns = {row[1] for row in cursor.fetchall()}
print(f"📊 现有列数: {len(existing_columns)}")
print(f"现有列: {sorted(existing_columns)}\n")

# 需要添加的列（根据Contract模型定义）
columns_to_add = [
    ("contract_name", "VARCHAR(200)"),
    ("contract_type", "VARCHAR(20)"),
    ("total_amount", "DECIMAL(15,2)"),
    ("received_amount", "DECIMAL(15,2)", "0"),
    ("unreceived_amount", "DECIMAL(15,2)"),
    ("signing_date", "DATE"),
    ("effective_date", "DATE"),
    ("expiry_date", "DATE"),
    ("contract_period", "INTEGER"),
    ("contract_subject", "TEXT"),
    ("payment_terms", "TEXT"),
    ("delivery_terms", "TEXT"),
    ("sales_owner_id", "INTEGER"),
    ("contract_manager_id", "INTEGER"),
]

# 添加缺失的列
added_count = 0
for col_info in columns_to_add:
    col_name = col_info[0]
    col_type = col_info[1]
    default = col_info[2] if len(col_info) > 2 else None
    
    if col_name not in existing_columns:
        try:
            if default:
                sql = f"ALTER TABLE contracts ADD COLUMN {col_name} {col_type} DEFAULT {default}"
            else:
                sql = f"ALTER TABLE contracts ADD COLUMN {col_name} {col_type}"
            
            cursor.execute(sql)
            added_count += 1
            print(f"   ✓ 添加列: {col_name} ({col_type})")
        except Exception as e:
            print(f"   ✗ 添加列失败 {col_name}: {e}")

conn.commit()

# 验证
cursor.execute("PRAGMA table_info(contracts);")
new_columns = {row[1] for row in cursor.fetchall()}

conn.close()

print(f"\n✅ 完成！添加了 {added_count} 个列")
print(f"📊 现在共有 {len(new_columns)} 个列")
