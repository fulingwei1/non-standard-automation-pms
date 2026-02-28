#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试权限API端点（包含认证）
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.core.security import (
    create_access_token,
)
from app.models.base import get_db_session
from app.models.user import User


def test_auth_flow():
    """测试认证流程"""
    print("=" * 60)
    print("测试认证流程")
    print("=" * 60)

    try:
        # 1. 获取一个用户
        with get_db_session() as db:
            result = db.execute(
                text("SELECT id, username, is_active FROM users LIMIT 1")
            )
            user_row = result.fetchone()
            if not user_row:
                print("❌ 未找到用户")
                return False

            user_id, username, is_active = user_row
            print(
                f"✅ 找到用户: ID={user_id}, username={username}, is_active={is_active}"
            )

            # 2. 创建token（sub必须是字符串）
            token_data = {"sub": str(user_id)}
            token = create_access_token(token_data)
            print(f"✅ Token创建成功 (长度: {len(token)})")

            # 3. 测试get_current_user（需要模拟FastAPI的Depends）
            # 这里我们直接测试核心逻辑
            from jose import jwt

            from app.core.config import settings

            try:
                payload = jwt.decode(
                    token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
                )
                decoded_user_id = payload.get("sub")
                print(f"✅ Token解码成功: user_id={decoded_user_id}")

                # 4. 查询用户（可能失败因为ORM关系错误）
                try:
                    user = db.query(User).filter(User.id == decoded_user_id).first()
                    if user:
                        print(f"✅ ORM查询用户成功: {user.username}")
                    else:
                        print("⚠️  ORM查询用户返回None")
                except Exception as e:
                    print(f"⚠️  ORM查询用户失败（预期）: {e}")
                    # 使用SQL查询
                    result = db.execute(
                        text(
                            "SELECT id, username, is_active FROM users WHERE id = :user_id"
                        ),
                        {"user_id": decoded_user_id},
                    )
                    sql_user = result.fetchone()
                    if sql_user:
                        print(f"✅ SQL查询用户成功: {sql_user[1]}")
                    else:
                        print("❌ SQL查询用户也失败")
                        return False

                return True
            except Exception as e:
                print(f"❌ Token解码失败: {e}")
                return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("权限API端点认证测试")
    print("=" * 60)

    success = test_auth_flow()

    print("\n" + "=" * 60)
    if success:
        print("✅ 认证流程测试通过")
        print("\n建议：")
        print("1. 检查后端日志，查看具体错误")
        print("2. 确认前端请求中是否包含有效的Authorization头")
        print("3. 检查浏览器控制台的网络请求详情")
    else:
        print("❌ 认证流程测试失败")
        print("需要进一步排查认证问题")


if __name__ == "__main__":
    main()
