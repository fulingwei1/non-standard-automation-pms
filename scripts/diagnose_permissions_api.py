#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断权限API端点问题
模拟完整的API调用流程
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime

from jose import jwt
from sqlalchemy import text

from app.core.config import settings
from app.core.security import create_access_token
from app.models.base import get_db_session
from app.schemas.auth import PermissionResponse


def test_permissions_api():
    """测试权限API端点逻辑"""
    print("=" * 60)
    print("诊断：权限列表API")
    print("=" * 60)

    try:
        with get_db_session() as db:
            # 1. 测试SQL查询
            print("\n1. 测试SQL查询...")
            sql = """
                SELECT
                    id,
                    perm_code as permission_code,
                    perm_name as permission_name,
                    module,
                    resource,
                    action,
                    description,
                    is_active,
                    created_at,
                    updated_at
                FROM permissions
                WHERE is_active = 1
                ORDER BY module ASC, perm_code ASC
            """
            result = db.execute(text(sql))
            rows = result.fetchall()
            print(f"   ✅ 查询成功: {len(rows)} 条权限")

            if len(rows) == 0:
                print("   ⚠️  警告: 没有找到权限数据")
                return False

            # 2. 测试数据转换
            print("\n2. 测试数据转换...")
            permissions = []
            errors = []

            for i, row in enumerate(rows[:10], 1):  # 只测试前10条
                try:
                    # 处理datetime字段
                    created_at = row[8]
                    updated_at = row[9]

                    if isinstance(created_at, str) and created_at:
                        try:
                            created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                        except Exception as e:
                            print(f"   ⚠️  行{i} created_at转换失败: {e}")
                            created_at = None

                    if isinstance(updated_at, str) and updated_at:
                        try:
                            updated_at = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S')
                        except Exception as e:
                            print(f"   ⚠️  行{i} updated_at转换失败: {e}")
                            updated_at = None

                    perm_dict = {
                        'id': row[0],
                        'permission_code': row[1] if row[1] else '',
                        'permission_name': row[2] if row[2] else '',
                        'module': row[3],
                        'resource': row[4],
                        'action': row[5],
                        'description': row[6],
                        'is_active': bool(row[7]) if row[7] is not None else True,
                        'created_at': created_at,
                        'updated_at': updated_at,
                    }

                    # 3. 测试序列化
                    perm_response = PermissionResponse(**perm_dict)
                    permissions.append(perm_response)

                except Exception as e:
                    error_msg = f"行{i}处理失败: {e}"
                    errors.append(error_msg)
                    print(f"   ❌ {error_msg}")
                    print(f"      数据: {row}")
                    import traceback
                    traceback.print_exc()

            print(f"   ✅ 成功处理: {len(permissions)} 条")
            if errors:
                print(f"   ❌ 失败: {len(errors)} 条")
                return False

            # 4. 测试认证流程
            print("\n3. 测试认证流程...")
            result = db.execute(text('SELECT id, username FROM users LIMIT 1'))
            user_row = result.fetchone()
            if not user_row:
                print("   ❌ 未找到用户")
                return False

            user_id = user_row[0]
            token_data = {'sub': str(user_id)}
            token = create_access_token(token_data)

            # 解码token
            try:
                payload = jwt.decode(
                    token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
                )
                decoded_user_id = int(payload.get("sub"))
                print(f"   ✅ Token创建和解码成功: user_id={decoded_user_id}")
            except Exception as e:
                print(f"   ❌ Token解码失败: {e}")
                return False

            # 查询用户（使用SQL避免ORM错误）
            try:
                result = db.execute(
                    text("SELECT id, username, is_active, is_superuser FROM users WHERE id = :user_id"),
                    {"user_id": decoded_user_id}
                )
                user_row = result.fetchone()
                if user_row:
                    print(f"   ✅ 用户查询成功: {user_row[1]}")
                else:
                    print("   ❌ 用户不存在")
                    return False
            except Exception as e:
                print(f"   ❌ 用户查询失败: {e}")
                return False

            print("\n" + "=" * 60)
            print("✅ 所有测试通过！")
            print("=" * 60)
            print("\n建议：")
            print("1. 确认后端服务已重启")
            print("2. 检查后端日志中的具体错误信息")
            print("3. 确认前端请求中包含有效的Authorization头")
            return True

    except Exception as e:
        print(f"\n❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_permissions_api()
    sys.exit(0 if success else 1)
