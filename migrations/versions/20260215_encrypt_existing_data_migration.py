"""
现有数据加密迁移（Alembic版本）

将明文敏感数据加密存储
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import text
from app.core.encryption import data_encryption


def encrypt_table_data(connection, table_name: str, column_mapping: dict):
    """
    加密表中的数据
    
    Args:
        connection: 数据库连接
        table_name: 表名
        column_mapping: 字段映射 {明文字段: 加密字段}
    
    Example:
        encrypt_table_data(
            connection,
            "employees",
            {
                "id_card": "id_card_encrypted",
                "bank_account": "bank_account_encrypted",
            }
        )
    """
    print(f"\n📦 正在加密 {table_name} 表数据...")
    
    # 检查表是否存在
    result = connection.execute(text(
        f"SELECT COUNT(*) FROM information_schema.tables "
        f"WHERE table_name = '{table_name}'"
    )).scalar()
    
    if result == 0:
        print(f"⚠️  {table_name} 表不存在，跳过迁移")
        return
    
    # 获取所有记录
    columns = list(column_mapping.keys())
    query = text(f"SELECT id, {', '.join(columns)} FROM {table_name}")
    results = connection.execute(query).fetchall()
    
    total = len(results)
    encrypted_count = 0
    
    print(f"  📊 找到 {total} 条记录")
    
    if total == 0:
        return
    
    # 加密每条记录
    for i, row in enumerate(results, 1):
        record_id = row[0]
        updates = {}
        
        # 进度显示
        if i % 100 == 0 or i == total:
            print(f"  进度: {i}/{total} ({i*100//total}%)")
        
        # 加密每个字段
        for idx, (source_col, target_col) in enumerate(column_mapping.items()):
            old_value = row[idx + 1]
            
            if not old_value:
                continue  # 跳过空值
            
            try:
                # 加密
                new_value = data_encryption.encrypt(str(old_value))
                updates[target_col] = new_value
            except Exception as e:
                print(f"  ❌ [错误] ID={record_id}, {source_col}: {e}")
                continue
        
        # 更新数据库
        if updates:
            try:
                set_clause = ', '.join([f"{col} = :{col}" for col in updates.keys()])
                update_query = text(f"UPDATE {table_name} SET {set_clause} WHERE id = :id")
                connection.execute(update_query, {"id": record_id, **updates})
                encrypted_count += len(updates)
            except Exception as e:
                print(f"  ❌ [更新失败] ID={record_id}: {e}")
    
    connection.commit()
    print(f"  ✅ 加密完成: {encrypted_count} 个字段")


def drop_plaintext_columns(connection, table_name: str, columns: list):
    """
    删除明文字段（加密完成后）
    
    ⚠️ 警告：此操作不可逆！请确保数据已正确加密！
    
    Args:
        connection: 数据库连接
        table_name: 表名
        columns: 要删除的字段列表
    """
    print(f"\n⚠️  准备删除 {table_name} 表的明文字段...")
    
    for column in columns:
        try:
            connection.execute(text(f"ALTER TABLE {table_name} DROP COLUMN {column}"))
            print(f"  ✅ 删除字段: {column}")
        except Exception as e:
            print(f"  ❌ 删除字段失败 {column}: {e}")
    
    connection.commit()


def rename_encrypted_columns(connection, table_name: str, column_mapping: dict):
    """
    重命名加密字段（去掉 _encrypted 后缀）
    
    Args:
        connection: 数据库连接
        table_name: 表名
        column_mapping: 字段映射 {加密字段: 新名称}
    
    Example:
        rename_encrypted_columns(
            connection,
            "employees",
            {
                "id_card_encrypted": "id_card",
                "bank_account_encrypted": "bank_account",
            }
        )
    """
    print(f"\n📝 正在重命名 {table_name} 表的加密字段...")
    
    for old_name, new_name in column_mapping.items():
        try:
            connection.execute(text(
                f"ALTER TABLE {table_name} CHANGE COLUMN {old_name} {new_name} VARCHAR(200)"
            ))
            print(f"  ✅ 重命名: {old_name} → {new_name}")
        except Exception as e:
            print(f"  ❌ 重命名失败 {old_name}: {e}")
    
    connection.commit()


def run_migration():
    """执行迁移"""
    from app.core.config import settings
    from sqlalchemy import create_engine
    
    print("\n" + "="*60)
    print("🔒 现有数据加密迁移")
    print("="*60)
    
    # 创建数据库连接
    engine = create_engine(settings.DATABASE_URL)
    connection = engine.connect()
    
    try:
        # 1. 加密员工表数据
        encrypt_table_data(
            connection,
            "employees",
            {
                "id_card": "id_card_encrypted",
                "bank_account": "bank_account_encrypted",
                "phone": "phone_encrypted",
                "address": "address_encrypted",
                "emergency_contact": "emergency_contact_encrypted",
                "salary": "salary_encrypted",
            }
        )
        
        # 2. 验证加密是否成功
        print("\n🔍 验证加密数据...")
        result = connection.execute(text(
            "SELECT id, id_card_encrypted FROM employees LIMIT 1"
        )).fetchone()
        
        if result and result[1]:
            print(f"  ✅ 加密数据示例（前50字符）: {result[1][:50]}...")
        
        # 3. （可选）删除明文字段
        # ⚠️ 警告：此操作不可逆！请确保数据已正确加密！
        # print("\n⚠️  删除明文字段...")
        # response = input("是否删除明文字段？(yes/no): ")
        # if response.lower() == 'yes':
        #     drop_plaintext_columns(
        #         connection,
        #         "employees",
        #         ["id_card", "bank_account", "phone", "address", "emergency_contact", "salary"]
        #     )
        #     
        #     # 4. 重命名加密字段
        #     rename_encrypted_columns(
        #         connection,
        #         "employees",
        #         {
        #             "id_card_encrypted": "id_card",
        #             "bank_account_encrypted": "bank_account",
        #             "phone_encrypted": "phone",
        #             "address_encrypted": "address",
        #             "emergency_contact_encrypted": "emergency_contact",
        #             "salary_encrypted": "salary",
        #         }
        #     )
        
        print("\n" + "="*60)
        print("✅ 数据加密迁移完成！")
        print("="*60)
        print("\n下一步：")
        print("1. 验证加密数据是否正确")
        print("2. 更新模型文件，使用加密字段类型（EncryptedString/EncryptedText）")
        print("3. （可选）删除明文字段，重命名加密字段")
        print("\n⚠️  重要提示：")
        print("   - 备份数据库后再执行删除操作！")
        print("   - 确保加密密钥已妥善保管！")
        print("\n" + "="*60 + "\n")
    
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        connection.rollback()
        raise
    
    finally:
        connection.close()


if __name__ == '__main__':
    run_migration()
