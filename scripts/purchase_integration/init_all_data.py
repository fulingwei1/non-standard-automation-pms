# -*- coding: utf-8 -*-
"""
采购-物料-库存系统 - 数据初始化主脚本
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.database import SessionLocal
from init_suppliers import init_suppliers
from init_materials import init_materials


def main():
    """执行完整的数据初始化"""
    
    print("=" * 80)
    print("采购-物料-库存系统 数据初始化")
    print("=" * 80)
    print()
    
    db = SessionLocal()
    
    try:
        # 步骤1: 初始化供应商数据
        print("步骤1: 初始化供应商数据...")
        print("-" * 80)
        supplier_count = init_suppliers(db)
        print()
        
        # 步骤2: 初始化物料数据
        print("步骤2: 初始化物料数据...")
        print("-" * 80)
        material_count = init_materials(db)
        print()
        
        # 汇总
        print("=" * 80)
        print("数据初始化完成！")
        print("=" * 80)
        print(f"  供应商: {supplier_count}个")
        print(f"  物料: {material_count}个")
        print("=" * 80)
        print()
        print("✅ 所有数据初始化成功！")
        print()
        print("下一步:")
        print("  1. 运行演示数据生成脚本: python scripts/purchase_integration/generate_demo_data.py")
        print("  2. 启动服务器: python start.sh")
        print("  3. 访问系统测试功能")
        print()
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
