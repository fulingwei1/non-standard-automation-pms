#!/usr/bin/env python3
"""
创建测试用户
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from passlib.context import CryptContext
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 数据库连接
DB_PATH = "data/app.db"
engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(bind=engine)

# 测试用户配置
TEST_USERS = [
    {"username": "admin", "password": "admin123", "real_name": "系统管理员", "role_code": "ADMIN"},
    {"username": "pm001", "password": "pm123", "real_name": "项目经理张三", "role_code": "PM"},
    {"username": "sales001", "password": "sales123", "real_name": "销售李四", "role_code": "SALES"},
    {"username": "eng001", "password": "eng123", "real_name": "工程师王五", "role_code": "ME"},
]

def create_users():
    db = SessionLocal()
    try:
        for user_info in TEST_USERS:
            username = user_info["username"]
            password = user_info["password"]
            real_name = user_info["real_name"]
            role_code = user_info["role_code"]
            
            # 检查用户是否已存在
            result = db.execute(
                text("SELECT id FROM users WHERE username = :username"),
                {"username": username}
            ).fetchone()
            
            if result:
                print(f"⚠️  用户 {username} 已存在，跳过")
                continue
            
            # 加密密码（截断到72字节避免bcrypt错误）
            password_hash = pwd_context.hash(password[:72])
            
            # 先创建员工记录
            db.execute(
                text("""
                    INSERT INTO employees (employee_code, name, department, role, is_active, created_at)
                    VALUES (:employee_code, :name, :department, :role, 1, datetime('now'))
                """),
                {
                    "employee_code": username,
                    "name": real_name,
                    "department": "测试部门",
                    "role": role_code
                }
            )
            
            # 获取员工ID
            employee_id = db.execute(
                text("SELECT id FROM employees WHERE employee_code = :employee_code"),
                {"employee_code": username}
            ).fetchone()[0]
            
            # 插入用户
            db.execute(
                text("""
                    INSERT INTO users (username, password_hash, real_name, email, phone, employee_id, is_active, created_at)
                    VALUES (:username, :password_hash, :real_name, :email, :phone, :employee_id, 1, datetime('now'))
                """),
                {
                    "username": username,
                    "password_hash": password_hash,
                    "real_name": real_name,
                    "email": f"{username}@test.com",
                    "phone": "",
                    "employee_id": employee_id
                }
            )
            
            # 获取用户ID
            user_id = db.execute(
                text("SELECT id FROM users WHERE username = :username"),
                {"username": username}
            ).fetchone()[0]
            
            # 获取角色ID
            role_id = db.execute(
                text("SELECT id FROM roles WHERE role_code = :role_code"),
                {"role_code": role_code}
            ).fetchone()
            
            if not role_id:
                print(f"❌ 角色 {role_code} 不存在")
                continue
            
            role_id = role_id[0]
            
            # 分配角色
            db.execute(
                text("""
                    INSERT INTO user_roles (user_id, role_id, created_at)
                    VALUES (:user_id, :role_id, datetime('now'))
                """),
                {"user_id": user_id, "role_id": role_id}
            )
            
            db.commit()
            print(f"✅ 创建用户: {real_name:12s} ({username:12s}) - 角色: {role_code}")
        
        print()
        print("=" * 70)
        print("✅ 测试用户创建完成")
        print()
        print("登录信息:")
        for user_info in TEST_USERS:
            print(f"  {user_info['real_name']:12s}: {user_info['username']:12s} / {user_info['password']}")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ 创建用户失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_users()
