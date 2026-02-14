#!/usr/bin/env python3
"""
测试API访问权限
"""
import sys
import os
import sqlite3
from pathlib import Path

# 添加项目路径
repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root))

import requests
from app.core.security import create_access_token

# 数据库路径
DB_PATH = repo_root / "data" / "app.db"

def test_api_with_admin():
    """使用管理员用户测试API访问"""
    print("="*60)
    print("测试管理员API访问权限")
    print("="*60)
    
    # 检查数据库中的管理员用户
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username FROM users WHERE username = 'admin'")
    admin = cursor.fetchone()
    
    if not admin:
        print("❌ 未找到管理员用户")
        conn.close()
        return False
    
    admin_id, username = admin
    print(f"\n✓ 找到管理员用户: {username} (ID: {admin_id})")
    
    # 检查管理员的角色
    cursor.execute("""
        SELECT r.id, r.role_code, r.role_name
        FROM user_roles ur
        JOIN roles r ON ur.role_id = r.id
        WHERE ur.user_id = ?
    """, (admin_id,))
    
    roles = cursor.fetchall()
    print(f"\n管理员的角色:")
    for role in roles:
        print(f"  - {role[1]}: {role[2]} (ID: {role[0]})")
    
    conn.close()
    
    # 创建JWT token
    token = create_access_token({"sub": username})
    print(f"\n✓ JWT Token已创建")
    
    # 测试API端点
    base_url = "http://localhost:8000"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    test_endpoints = [
        ("/api/v1/users", "用户列表"),
        ("/api/v1/roles", "角色列表"),
        ("/api/v1/permissions", "权限列表"),
    ]
    
    print("\n" + "="*60)
    print("API访问测试结果:")
    print("="*60)
    
    all_success = True
    for endpoint, desc in test_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=5)
            status = response.status_code
            success = status == 200
            
            print(f"\n{desc}: {endpoint}")
            print(f"  状态码: {status}")
            
            if success:
                print(f"  结果: ✅ 成功")
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        if 'data' in data:
                            count = len(data['data']) if isinstance(data['data'], list) else 'N/A'
                            print(f"  数据: {count}条记录")
                        elif 'items' in data:
                            count = len(data['items']) if isinstance(data['items'], list) else 'N/A'
                            print(f"  数据: {count}条记录")
                except:
                    pass
            else:
                print(f"  结果: ❌ 失败")
                print(f"  响应: {response.text[:200]}")
                all_success = False
                
        except Exception as e:
            print(f"\n{desc}: {endpoint}")
            print(f"  ❌ 请求失败: {e}")
            all_success = False
    
    print("\n" + "="*60)
    if all_success:
        print("✅ 所有API测试通过！管理员可以正常访问API")
    else:
        print("❌ 部分API测试失败")
    print("="*60)
    
    return all_success


if __name__ == "__main__":
    success = test_api_with_admin()
    sys.exit(0 if success else 1)
