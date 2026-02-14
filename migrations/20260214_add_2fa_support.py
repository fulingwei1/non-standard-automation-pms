#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移：添加双因素认证（2FA）支持

创建时间：2026-02-14
功能：
  1. 在 users 表添加 2FA 相关字段
  2. 创建 user_2fa_secrets 表（加密存储TOTP密钥）
  3. 创建 user_2fa_backup_codes 表（备用恢复码）
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.orm import Session


def upgrade(db: Session):
    """执行升级"""
    print("开始执行 2FA 功能迁移...")
    
    # 检测数据库类型
    from sqlalchemy import inspect
    inspector = inspect(db.bind)
    dialect_name = db.bind.dialect.name
    
    # 1. 在 users 表添加 2FA 字段
    print(f"  [1/3] 在 users 表添加 2FA 字段... (数据库类型: {dialect_name})")
    
    # 检查列是否已存在
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'two_factor_enabled' not in columns:
        if dialect_name == 'mysql':
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN two_factor_enabled BOOLEAN DEFAULT FALSE COMMENT '是否启用2FA'
            """))
        else:  # SQLite
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN two_factor_enabled BOOLEAN DEFAULT FALSE
            """))
        db.commit()
    
    if 'two_factor_method' not in columns:
        if dialect_name == 'mysql':
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN two_factor_method VARCHAR(20) COMMENT '2FA方式: totp'
            """))
        else:  # SQLite
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN two_factor_method VARCHAR(20)
            """))
        db.commit()
    
    if 'two_factor_verified_at' not in columns:
        if dialect_name == 'mysql':
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN two_factor_verified_at DATETIME COMMENT '2FA验证时间'
            """))
        else:  # SQLite
            db.execute(text("""
                ALTER TABLE users 
                ADD COLUMN two_factor_verified_at DATETIME
            """))
        db.commit()
    
    # 2. 创建 user_2fa_secrets 表（存储加密的TOTP密钥）
    print("  [2/3] 创建 user_2fa_secrets 表...")
    if dialect_name == 'mysql':
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS user_2fa_secrets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL COMMENT '用户ID',
                secret_encrypted TEXT NOT NULL COMMENT '加密的TOTP密钥',
                method VARCHAR(20) NOT NULL DEFAULT 'totp' COMMENT '2FA方式',
                is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                UNIQUE KEY uk_user_method (user_id, method),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_active (user_id, is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户2FA密钥表'
        """))
    else:  # SQLite
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS user_2fa_secrets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                secret_encrypted TEXT NOT NULL,
                method VARCHAR(20) NOT NULL DEFAULT 'totp',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE (user_id, method)
            )
        """))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_user_active ON user_2fa_secrets(user_id, is_active)"))
    db.commit()
    
    # 3. 创建 user_2fa_backup_codes 表（备用恢复码）
    print("  [3/3] 创建 user_2fa_backup_codes 表...")
    if dialect_name == 'mysql':
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS user_2fa_backup_codes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL COMMENT '用户ID',
                code_hash VARCHAR(255) NOT NULL COMMENT '备用码哈希值',
                used BOOLEAN DEFAULT FALSE COMMENT '是否已使用',
                used_at DATETIME COMMENT '使用时间',
                used_ip VARCHAR(50) COMMENT '使用IP',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_unused (user_id, used),
                INDEX idx_code_hash (code_hash)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户2FA备用码表'
        """))
    else:  # SQLite
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS user_2fa_backup_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                code_hash VARCHAR(255) NOT NULL,
                used BOOLEAN DEFAULT 0,
                used_at DATETIME,
                used_ip VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_user_unused ON user_2fa_backup_codes(user_id, used)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_code_hash ON user_2fa_backup_codes(code_hash)"))
    db.commit()
    
    print("✅ 2FA 功能迁移完成！")


def downgrade(db: Session):
    """执行降级"""
    print("开始回滚 2FA 功能迁移...")
    
    # 删除表
    print("  [1/3] 删除 user_2fa_backup_codes 表...")
    db.execute(text("DROP TABLE IF EXISTS user_2fa_backup_codes"))
    db.commit()
    
    print("  [2/3] 删除 user_2fa_secrets 表...")
    db.execute(text("DROP TABLE IF EXISTS user_2fa_secrets"))
    db.commit()
    
    # 删除 users 表字段
    print("  [3/3] 删除 users 表的 2FA 字段...")
    db.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS two_factor_enabled"))
    db.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS two_factor_method"))
    db.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS two_factor_verified_at"))
    db.commit()
    
    print("✅ 2FA 功能迁移已回滚！")


if __name__ == "__main__":
    """直接运行此脚本进行迁移"""
    from app.models.base import get_db
    
    db = next(get_db())
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
            downgrade(db)
        else:
            upgrade(db)
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()
