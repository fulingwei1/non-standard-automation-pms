"""
新增加密字段迁移

用于在现有表中添加加密字段
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import text


def upgrade_employees_table(connection):
    """
    升级员工表，添加加密字段
    
    注意：
    - 加密字段长度需要足够大（建议200+），因为加密后会增加约1.5-2倍
    - 如果原有字段需要加密，建议先创建新字段，迁移数据后再删除旧字段
    """
    print("📦 正在升级 employees 表...")
    
    # 检查表是否存在
    result = connection.execute(text(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_name = 'employees'"
    )).scalar()
    
    if result == 0:
        print("⚠️  employees 表不存在，跳过迁移")
        return
    
    # 添加加密字段
    columns_to_add = [
        ("id_card_encrypted", "VARCHAR(200)", "身份证号（加密）"),
        ("bank_account_encrypted", "VARCHAR(200)", "银行卡号（加密）"),
        ("phone_encrypted", "VARCHAR(200)", "手机号（加密）"),
        ("address_encrypted", "TEXT", "家庭住址（加密）"),
        ("emergency_contact_encrypted", "TEXT", "紧急联系人信息（加密）"),
        ("salary_encrypted", "VARCHAR(200)", "工资（加密）"),
    ]
    
    for column_name, column_type, comment in columns_to_add:
        # 检查字段是否已存在
        result = connection.execute(text(
            f"SELECT COUNT(*) FROM information_schema.columns "
            f"WHERE table_name = 'employees' AND column_name = '{column_name}'"
        )).scalar()
        
        if result > 0:
            print(f"  ⏭️  字段 {column_name} 已存在，跳过")
            continue
        
        # 添加字段
        connection.execute(text(
            f"ALTER TABLE employees ADD COLUMN {column_name} {column_type} COMMENT '{comment}'"
        ))
        print(f"  ✅ 添加字段: {column_name}")
    
    connection.commit()
    print("✅ employees 表升级完成")


def upgrade_custom_table(connection, table_name: str, encrypted_columns: list):
    """
    升级自定义表，添加加密字段
    
    Args:
        connection: 数据库连接
        table_name: 表名
        encrypted_columns: 加密字段列表 [(字段名, 类型, 注释), ...]
    
    Example:
        upgrade_custom_table(
            connection,
            "customer_info",
            [
                ("phone_encrypted", "VARCHAR(200)", "手机号（加密）"),
                ("address_encrypted", "TEXT", "地址（加密）"),
            ]
        )
    """
    print(f"\n📦 正在升级 {table_name} 表...")
    
    # 检查表是否存在
    result = connection.execute(text(
        f"SELECT COUNT(*) FROM information_schema.tables "
        f"WHERE table_name = '{table_name}'"
    )).scalar()
    
    if result == 0:
        print(f"⚠️  {table_name} 表不存在，跳过迁移")
        return
    
    for column_name, column_type, comment in encrypted_columns:
        # 检查字段是否已存在
        result = connection.execute(text(
            f"SELECT COUNT(*) FROM information_schema.columns "
            f"WHERE table_name = '{table_name}' AND column_name = '{column_name}'"
        )).scalar()
        
        if result > 0:
            print(f"  ⏭️  字段 {column_name} 已存在，跳过")
            continue
        
        # 添加字段
        connection.execute(text(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} COMMENT '{comment}'"
        ))
        print(f"  ✅ 添加字段: {column_name}")
    
    connection.commit()
    print(f"✅ {table_name} 表升级完成")


def run_migration():
    """执行迁移"""
    from app.core.config import settings
    from sqlalchemy import create_engine
    
    print("\n" + "="*60)
    print("🚀 数据加密字段迁移")
    print("="*60)
    
    # 创建数据库连接
    engine = create_engine(settings.DATABASE_URL)
    connection = engine.connect()
    
    try:
        # 1. 升级员工表
        upgrade_employees_table(connection)
        
        # 2. 根据需要添加其他表的迁移
        # upgrade_custom_table(
        #     connection,
        #     "customer_info",
        #     [
        #         ("phone_encrypted", "VARCHAR(200)", "手机号（加密）"),
        #         ("address_encrypted", "TEXT", "地址（加密）"),
        #     ]
        # )
        
        print("\n" + "="*60)
        print("✅ 所有迁移完成！")
        print("="*60)
        print("\n下一步：")
        print("1. 运行数据加密脚本：")
        print("   python scripts/encrypt_existing_data.py --table employees --columns id_card,bank_account")
        print("\n2. 更新模型文件，使用加密字段类型")
        print("\n" + "="*60 + "\n")
    
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        connection.rollback()
        raise
    
    finally:
        connection.close()


if __name__ == '__main__':
    run_migration()
