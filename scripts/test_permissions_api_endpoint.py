#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试权限API端点，诊断500错误
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.models.base import get_db_session
from app.schemas.auth import PermissionResponse
from app.models.user import User

def test_sql_query():
    """测试SQL查询"""
    print("=" * 60)
    print("测试1: SQL查询")
    print("=" * 60)
    try:
        with get_db_session() as db:
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
                LIMIT 5
            """
            result = db.execute(text(sql))
            rows = result.fetchall()
            print(f"✅ SQL查询成功，找到 {len(rows)} 条权限")
            return True
    except Exception as e:
        print(f"❌ SQL查询失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_serialization():
    """测试序列化"""
    print("\n" + "=" * 60)
    print("测试2: 数据序列化")
    print("=" * 60)
    try:
        with get_db_session() as db:
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
                LIMIT 3
            """
            result = db.execute(text(sql))
            rows = result.fetchall()
            
            permissions = []
            for row in rows:
                perm_dict = {
                    'id': row[0],
                    'permission_code': row[1] if row[1] else '',
                    'permission_name': row[2] if row[2] else '',
                    'module': row[3],
                    'resource': row[4],
                    'action': row[5],
                    'description': row[6],
                    'is_active': bool(row[7]) if row[7] is not None else True,
                    'created_at': row[8],
                    'updated_at': row[9],
                }
                perm_response = PermissionResponse(**perm_dict)
                permissions.append(perm_response)
            
            print(f"✅ 序列化成功，{len(permissions)} 条权限")
            return True
    except Exception as e:
        print(f"❌ 序列化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_user_model():
    """测试User模型"""
    print("\n" + "=" * 60)
    print("测试3: User模型查询")
    print("=" * 60)
    try:
        with get_db_session() as db:
            # 尝试查询一个用户（不加载关系）
            from sqlalchemy import text as sql_text
            result = db.execute(sql_text("SELECT id, username FROM users LIMIT 1"))
            user_row = result.fetchone()
            if user_row:
                print(f"✅ 找到用户: ID={user_row[0]}, username={user_row[1]}")
                return True
            else:
                print("⚠️  未找到用户")
                return False
    except Exception as e:
        print(f"❌ User查询失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_permission_model():
    """测试Permission模型（可能失败因为其他模型关系错误）"""
    print("\n" + "=" * 60)
    print("测试4: Permission模型ORM查询（可能失败）")
    print("=" * 60)
    try:
        from app.models.user import Permission
        with get_db_session() as db:
            # 尝试使用ORM查询
            perms = db.query(Permission).limit(1).all()
            print(f"✅ ORM查询成功，找到 {len(perms)} 条权限")
            return True
    except Exception as e:
        print(f"⚠️  ORM查询失败（预期）: {e}")
        print("   这是因为其他模型的关系定义错误，但不影响SQL查询")
        return False

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("权限API端点诊断测试")
    print("=" * 60)
    
    results = []
    results.append(("SQL查询", test_sql_query()))
    results.append(("数据序列化", test_serialization()))
    results.append(("User模型", test_user_model()))
    results.append(("Permission模型ORM", test_permission_model()))
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name:20} {status}")
    
    # 诊断建议
    print("\n" + "=" * 60)
    print("诊断建议")
    print("=" * 60)
    if results[0][1] and results[1][1]:
        print("✅ SQL查询和序列化都正常")
        print("   500错误可能是以下原因之一：")
        print("   1. 用户未登录或token无效（401错误会显示为500）")
        print("   2. 数据库连接问题")
        print("   3. 其他模型的关系定义错误导致应用启动失败")
        print("\n   建议：")
        print("   - 检查后端日志，查看具体错误信息")
        print("   - 确认用户已登录且token有效")
        print("   - 检查后端服务是否正常启动")
    else:
        print("❌ 基础功能测试失败，需要修复")

if __name__ == "__main__":
    main()
