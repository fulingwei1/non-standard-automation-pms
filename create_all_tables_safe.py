#!/usr/bin/env python3
"""
安全地创建所有缺失的数据库表（禁用外键检查）
"""
import sys
import sqlite3
from pathlib import Path
from sqlalchemy import create_engine, event

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.models.base import Base

def create_all_tables():
    """创建所有模型定义的表"""
    print("🔧 开始系统性创建所有数据库表...\n")
    
    # 数据库路径
    db_path = Path("data/app.db")
    if not db_path.parent.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建数据目录: {db_path.parent}\n")
    
    # 创建引擎
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, echo=False)
    
    # 禁用外键检查（SQLite特定）
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys = OFF")
        cursor.close()
    
    # 导入所有模型
    print("📦 导入所有模型...")
    import app.models
    print(f"✅ 已注册 {len(Base.metadata.tables)} 个表定义\n")
    
    # 获取现有表
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    existing_tables = {row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')}
    conn.close()
    
    print(f"📊 数据库中已存在 {len(existing_tables)} 个表\n")
    
    # 确定需要创建的表
    all_tables = set(Base.metadata.tables.keys())
    missing_tables = all_tables - existing_tables
    
    if not missing_tables:
        print("✅ 所有表已存在，无需创建新表！")
        return True
    
    print(f"🔨 需要创建 {len(missing_tables)} 个缺失的表:\n")
    sorted_missing = sorted(missing_tables)
    for i, table in enumerate(sorted_missing[:20], 1):
        print(f"   {i:2d}. {table}")
    if len(missing_tables) > 20:
        print(f"   ... 还有 {len(missing_tables) - 20} 个表")
    print()
    
    # 创建所有表
    print("🚀 开始创建表...")
    print("   ⚠️  已禁用外键检查以避免依赖问题\n")
    
    try:
        # 使用原生连接禁用外键
        with engine.begin() as connection:
            connection.exec_driver_sql("PRAGMA foreign_keys = OFF")
            Base.metadata.create_all(bind=connection, checkfirst=True)
        
        print("✅ 所有表创建成功！\n")
        
        # 验证 - 重新连接
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        new_existing_tables = {row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')}
        conn.close()
        
        newly_created = new_existing_tables - existing_tables
        
        print(f"✅ 成功创建了 {len(newly_created)} 个新表")
        print(f"📊 数据库现在共有 {len(new_existing_tables)} 个表\n")
        
        # 显示新创建的表
        if newly_created:
            print("🎉 新创建的表 (前20个):")
            for i, table in enumerate(sorted(newly_created)[:20], 1):
                print(f"   {i:2d}. ✓ {table}")
            if len(newly_created) > 20:
                print(f"   ... 还有 {len(newly_created) - 20} 个表")
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
        
    except Exception as e:
        print(f"❌ 创建表时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = create_all_tables()
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
