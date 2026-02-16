#!/usr/bin/env python3
"""
通过生成SQL直接创建缺失的表（跳过外键验证）
"""
import sys
import sqlite3
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.schema import CreateTable

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.models.base import Base

def create_missing_tables():
    """生成SQL并直接创建缺失的表"""
    print("🔧 通过SQL直接创建所有缺失的数据库表...\n")
    
    # 数据库路径
    db_path = Path("data/app.db")
    if not db_path.parent.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 导入所有模型
    print("📦 导入所有模型...")
    import app.models
    print(f"✅ 已注册 {len(Base.metadata.tables)} 个表定义\n")
    
    # 获取现有表
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    existing_tables = {row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')}
    print(f"📊 数据库中已存在 {len(existing_tables)} 个表\n")
    
    # 确定需要创建的表
    all_tables = set(Base.metadata.tables.keys())
    missing_tables = all_tables - existing_tables
    
    if not missing_tables:
        print("✅ 所有表已存在，无需创建新表！")
        conn.close()
        return True
    
    print(f"🔨 需要创建 {len(missing_tables)} 个缺失的表\n")
    
    # 禁用外键检查
    cursor.execute("PRAGMA foreign_keys = OFF")
    
    # 为每个缺失的表生成并执行CREATE TABLE语句
    created_count = 0
    failed_tables = []
    
    # 创建一个临时引擎用于生成DDL
    temp_engine = create_engine("sqlite:///:memory:")
    
    for table_name in sorted(missing_tables):
        try:
            table = Base.metadata.tables[table_name]
            # 生成CREATE TABLE语句
            create_ddl = str(CreateTable(table).compile(temp_engine))
            
            # 执行创建表的语句
            cursor.execute(create_ddl)
            created_count += 1
            
            if created_count <= 20:
                print(f"   ✓ {created_count:3d}. {table_name}")
            elif created_count == 21:
                print(f"   ... 继续创建中...")
                
        except Exception as e:
            failed_tables.append((table_name, str(e)))
            if len(failed_tables) <= 5:
                print(f"   ✗ {table_name}: {str(e)[:80]}")
    
    # 提交事务
    conn.commit()
    
    # 验证
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    new_existing_tables = {row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')}
    newly_created = new_existing_tables - existing_tables
    
    conn.close()
    
    print(f"\n✅ 成功创建了 {len(newly_created)} 个新表")
    print(f"📊 数据库现在共有 {len(new_existing_tables)} 个表\n")
    
    if failed_tables:
        print(f"⚠️  {len(failed_tables)} 个表创建失败:")
        for table_name, error in failed_tables[:10]:
            print(f"   - {table_name}: {error[:100]}")
        if len(failed_tables) > 10:
            print(f"   ... 还有 {len(failed_tables) - 10} 个失败")
        print()
    
    # 确认所有需要的表都已创建
    still_missing = all_tables - new_existing_tables
    if still_missing:
        print(f"⚠️  仍有 {len(still_missing)} 个表未创建:")
        for table in sorted(still_missing)[:10]:
            print(f"   - {table}")
        if len(still_missing) > 10:
            print(f"   ... 还有 {len(still_missing) - 10} 个")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = create_missing_tables()
        if success:
            print("\n" + "="*60)
            print("🎉 数据库表创建完成！所有模型定义的表已同步。")
            print("="*60)
            sys.exit(0)
        else:
            print("\n" + "="*60)
            print("⚠️  部分表创建失败，请检查错误信息。")
            print("="*60)
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
