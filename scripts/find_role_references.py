#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找所有引用 roles 表的表
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, inspect
from app.models.base import get_db_session, get_engine

# 获取引擎
engine = get_engine()

# 获取所有表
inspector = inspect(engine)
tables = inspector.get_table_names()

print("查找所有引用 roles 表的表:")
print("=" * 60)

with get_db_session() as session:
    for table_name in tables:
        try:
            # 获取外键
            foreign_keys = inspector.get_foreign_keys(table_name)
            for fk in foreign_keys:
                if fk['referred_table'] == 'roles':
                    print(f"\n表: {table_name}")
                    print(f"  外键: {fk['name']}")
                    print(f"  列: {fk['constrained_columns']}")
                    print(f"  引用: {fk['referred_table']}.{fk['referred_columns']}")
                    
                    # 检查是否有数据
                    if fk['constrained_columns']:
                        col = fk['constrained_columns'][0]
                        result = session.execute(text(f"""
                            SELECT COUNT(*) FROM {table_name} WHERE {col} IS NOT NULL
                        """))
                        count = result.scalar()
                        print(f"  数据行数: {count}")
        except Exception as e:
            pass  # 忽略错误
