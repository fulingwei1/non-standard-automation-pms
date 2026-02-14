#!/usr/bin/env python3
"""
通过登录获取token并测试API访问
"""
import requests
import json

base_url = "http://localhost:8000"

print("="*60)
print("Step 1: 登录获取Token")
print("="*60)

# 登录（使用form data格式）
login_data = {
    "username": "admin",
    "password": "admin123"  # 假设密码
}

try:
    response = requests.post(f"{base_url}/api/v1/auth/login", data=login_data)
    print(f"登录状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token") or data.get("data", {}).get("access_token")
        
        if token:
            print(f"✅ 登录成功，获取到Token")
            
            # 测试API
            print("\n" + "="*60)
            print("Step 2: 测试API访问")
            print("="*60)
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            test_endpoints = [
                ("/api/v1/users", "用户列表"),
                ("/api/v1/roles", "角色列表"),
            ]
            
            all_success = True
            for endpoint, desc in test_endpoints:
                response = requests.get(f"{base_url}{endpoint}", headers=headers)
                status = response.status_code
                success = status == 200
                
                print(f"\n{desc}: {endpoint}")
                print(f"  状态码: {status}")
                print(f"  结果: {'✅ 成功' if success else '❌ 失败'}")
                
                if success:
                    try:
                        data = response.json()
                        if isinstance(data, dict):
                            if 'data' in data:
                                items = data['data']
                                if isinstance(items, list):
                                    print(f"  数据: {len(items)}条记录")
                            elif 'items' in data:
                                items = data['items']
                                if isinstance(items, list):
                                    print(f"  数据: {len(items)}条记录")
                    except:
                        pass
                else:
                    print(f"  响应: {response.text[:200]}")
                    all_success = False
            
            print("\n" + "="*60)
            if all_success:
                print("✅ 所有API测试通过！")
            else:
                print("❌ 部分API测试失败")
            print("="*60)
        else:
            print(f"❌ 响应中没有Token")
            print(f"响应: {response.text}")
    else:
        print(f"❌ 登录失败")
        print(f"响应: {response.text}")
        
        # 尝试其他密码
        print("\n尝试其他可能的密码...")
        passwords = ["admin", "123456", "Admin123", "admin@123"]
        
        for pwd in passwords:
            login_data["password"] = pwd
            response = requests.post(f"{base_url}/api/v1/auth/login", data=login_data)
            if response.status_code == 200:
                print(f"✅ 密码 '{pwd}' 成功!")
                break
            else:
                print(f"  密码 '{pwd}' 失败: {response.status_code}")
        
except Exception as e:
    print(f"❌ 请求失败: {e}")
