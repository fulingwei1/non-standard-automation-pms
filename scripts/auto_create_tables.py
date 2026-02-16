#!/usr/bin/env python3
"""
自动创建所有缺失的数据库表和列
使用SQLAlchemy的metadata.create_all()
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, inspect
from app.models.base import Base
from app.core.config import settings

# 导入所有models以注册到Base.metadata
print("导入所有models...")
import app.models  # This triggers all model registrations

print(f"\n数据库URL: {settings.DATABASE_URL or f'sqlite:///{settings.SQLITE_DB_PATH}'}")

# 创建engine
if settings.DATABASE_URL:
    engine = create_engine(settings.DATABASE_URL)
else:
    db_path = settings.SQLITE_DB_PATH
    if not db_path.startswith('/'):
        db_path = os.path.join(os.getcwd(), db_path)
    engine = create_engine(f"sqlite:///{db_path}")

print(f"\n检查当前数据库状态...")
inspector = inspect(engine)
existing_tables = inspector.get_table_names()
print(f"当前存在 {len(existing_tables)} 个表")

# 获取所有应该存在的表
all_tables = set(Base.metadata.tables.keys())
missing_tables = all_tables - set(existing_tables)

print(f"\n总计应有表: {len(all_tables)}")
print(f"缺失的表: {len(missing_tables)}")

if missing_tables:
    print("\n缺失的表列表:")
    for table in sorted(missing_tables):
        print(f"  - {table}")

print("\n开始创建所有缺失的表...")
try:
    # 创建所有表（已存在的会被跳过）
    Base.metadata.create_all(bind=engine, checkfirst=True)
    print("✅ 成功！")
    
    # 验证
    inspector = inspect(engine)
    new_tables = inspector.get_table_names()
    print(f"\n当前数据库共有 {len(new_tables)} 个表")
    
    # 检查是否所有表都已创建
    still_missing = all_tables - set(new_tables)
    if still_missing:
        print(f"\n⚠️  仍然缺失 {len(still_missing)} 个表:")
        for table in sorted(still_missing):
            print(f"  - {table}")
    else:
        print("\n✅ 所有表都已成功创建！")
        
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n完成！")
