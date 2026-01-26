#!/usr/bin/env python3
"""
重置admin用户密码脚本
"""

import sys
sys.path.insert(0, ".")

from app.core.security import get_password_hash
from app.models.base import get_session
from app.models.user import User

def reset_admin_password(new_password: str = "password123"):
    """重置admin用户密码"""
    with get_session() as db:
        # 查找admin用户
        admin = db.query(User).filter(User.username == "admin").first()

        if not admin:
            print("✗ 错误: admin用户不存在")
            return False

        # 更新密码
        admin.password_hash = get_password_hash(new_password)
        db.commit()

        print(f"✓ 成功: admin用户密码已重置为: {new_password}")
        print(f"  用户ID: {admin.id}")
        print(f"  真实姓名: {admin.real_name}")
        print(f"  超级用户: {admin.is_superuser}")
        return True

if __name__ == "__main__":
    reset_admin_password("password123")
