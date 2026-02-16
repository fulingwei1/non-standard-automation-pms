#!/usr/bin/env python3
"""
系统性创建所有缺失的数据库表
"""
import sys
from pathlib import Path
from sqlalchemy import create_engine, inspect

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
    
    # 导入所有模型（确保它们被注册到Base.metadata）
    print("📦 导入所有模型...")
    import app.models
    print(f"✅ 已注册 {len(Base.metadata.tables)} 个表定义\n")
    
    # 获取当前数据库中的表
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    print(f"📊 数据库中已存在 {len(existing_tables)} 个表\n")
    
    # 确定需要创建的表
    all_tables = set(Base.metadata.tables.keys())
    missing_tables = all_tables - existing_tables
    
    if not missing_tables:
        print("✅ 所有表已存在，无需创建新表！")
        return True
    
    print(f"🔨 需要创建 {len(missing_tables)} 个缺失的表:\n")
    for table in sorted(missing_tables)[:20]:
        print(f"   - {table}")
    if len(missing_tables) > 20:
        print(f"   ... 还有 {len(missing_tables) - 20} 个表")
    print()
    
    # 创建所有表
    print("🚀 开始创建表...")
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("✅ 所有表创建成功！\n")
        
        # 验证
        inspector = inspect(engine)
        new_existing_tables = set(inspector.get_table_names())
        newly_created = new_existing_tables - existing_tables
        
        print(f"✅ 成功创建了 {len(newly_created)} 个新表")
        print(f"📊 数据库现在共有 {len(new_existing_tables)} 个表\n")
        
        # 显示一些新创建的表
        if newly_created:
            print("🎉 新创建的表示例:")
            for table in sorted(newly_created)[:10]:
                print(f"   ✓ {table}")
            if len(newly_created) > 10:
                print(f"   ... 还有 {len(newly_created) - 10} 个表")
        
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
            print("🎉 数据库表创建完成！")
            print("="*60)
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
