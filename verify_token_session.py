#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token和会话管理系统验证脚本
"""

import os
import sys

# 设置DEBUG模式
os.environ['DEBUG'] = 'true'

def verify_imports():
    """验证模块导入"""
    print("=" * 60)
    print("1. 验证模块导入")
    print("=" * 60)
    
    try:
        from app.models.session import UserSession
        print("✓ UserSession model 导入成功")
    except Exception as e:
        print(f"✗ UserSession model 导入失败: {e}")
        return False
    
    try:
        from app.schemas.session import SessionResponse, RefreshTokenRequest
        print("✓ Session schemas 导入成功")
    except Exception as e:
        print(f"✗ Session schemas 导入失败: {e}")
        return False
    
    try:
        from app.services.session_service import SessionService
        print("✓ SessionService 导入成功")
    except Exception as e:
        print(f"✗ SessionService 导入失败: {e}")
        return False
    
    try:
        from app.core.auth import (
            create_access_token,
            create_refresh_token,
            create_token_pair,
            verify_refresh_token,
            extract_jti_from_token,
        )
        print("✓ Auth functions 导入成功")
    except Exception as e:
        print(f"✗ Auth functions 导入失败: {e}")
        return False
    
    try:
        from app.api.v1.endpoints.sessions import router
        print("✓ Sessions router 导入成功")
    except Exception as e:
        print(f"✗ Sessions router 导入失败: {e}")
        return False
    
    print()
    return True


def verify_token_generation():
    """验证Token生成"""
    print("=" * 60)
    print("2. 验证Token生成")
    print("=" * 60)
    
    try:
        from app.core.auth import (
            create_access_token,
            create_refresh_token,
            create_token_pair,
            verify_refresh_token,
            extract_jti_from_token,
        )
        
        # 测试Access Token生成
        access_token = create_access_token({"sub": "123"})
        print(f"✓ Access Token 生成: {access_token[:30]}...")
        
        # 测试Refresh Token生成
        refresh_token = create_refresh_token({"sub": "123"})
        print(f"✓ Refresh Token 生成: {refresh_token[:30]}...")
        
        # 测试Token对生成
        at, rt, ajti, rjti = create_token_pair({"sub": "123"})
        print(f"✓ Token对 生成:")
        print(f"  - Access JTI: {ajti}")
        print(f"  - Refresh JTI: {rjti}")
        
        # 测试Refresh Token验证
        payload = verify_refresh_token(rt)
        if payload:
            print(f"✓ Refresh Token 验证成功: sub={payload.get('sub')}")
        else:
            print("✗ Refresh Token 验证失败")
            return False
        
        # 测试JTI提取
        extracted_jti = extract_jti_from_token(at)
        if extracted_jti == ajti:
            print(f"✓ JTI 提取成功: {extracted_jti}")
        else:
            print(f"✗ JTI 提取失败: expected={ajti}, got={extracted_jti}")
            return False
        
        print()
        return True
        
    except Exception as e:
        print(f"✗ Token生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_api_routes():
    """验证API路由"""
    print("=" * 60)
    print("3. 验证API路由")
    print("=" * 60)
    
    try:
        from app.api.v1.api import api_router
        
        routes = []
        for route in api_router.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        # 检查关键路由
        auth_routes = [r for r in routes if '/auth' in r]
        print(f"✓ 找到 {len(auth_routes)} 个认证相关路由:")
        for route in sorted(auth_routes):
            print(f"  - {route}")
        
        # 验证新增的路由
        expected_routes = [
            '/auth/sessions',
            '/auth/sessions/revoke',
            '/auth/sessions/revoke-all',
        ]
        
        found_new_routes = []
        for expected in expected_routes:
            if any(expected in r for r in routes):
                found_new_routes.append(expected)
                print(f"✓ 新路由已注册: {expected}")
        
        if len(found_new_routes) == len(expected_routes):
            print("\n✓ 所有新路由已成功注册")
        else:
            missing = set(expected_routes) - set(found_new_routes)
            print(f"\n✗ 缺少路由: {missing}")
            return False
        
        print()
        return True
        
    except Exception as e:
        print(f"✗ API路由验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_database_schema():
    """验证数据库Schema"""
    print("=" * 60)
    print("4. 验证数据库Schema")
    print("=" * 60)
    
    try:
        from app.models.session import UserSession
        
        # 检查表结构
        columns = UserSession.__table__.columns.keys()
        print(f"✓ UserSession 表包含 {len(columns)} 个字段:")
        
        expected_columns = [
            'id', 'user_id', 'access_token_jti', 'refresh_token_jti',
            'device_id', 'device_name', 'device_type',
            'ip_address', 'location', 'user_agent', 'browser', 'os',
            'is_active', 'login_at', 'last_activity_at', 'expires_at', 'logout_at',
            'is_suspicious', 'risk_score',
            'created_at', 'updated_at',
        ]
        
        missing_columns = set(expected_columns) - set(columns)
        if missing_columns:
            print(f"✗ 缺少字段: {missing_columns}")
            return False
        
        for col in expected_columns:
            print(f"  ✓ {col}")
        
        # 检查索引
        indexes = UserSession.__table__.indexes
        print(f"\n✓ 表索引数量: {len(indexes)}")
        
        print()
        return True
        
    except Exception as e:
        print(f"✗ 数据库Schema验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Token刷新和会话管理系统 - 验证脚本")
    print("=" * 60 + "\n")
    
    results = []
    
    # 1. 验证导入
    results.append(("模块导入", verify_imports()))
    
    # 2. 验证Token生成
    results.append(("Token生成", verify_token_generation()))
    
    # 3. 验证API路由
    results.append(("API路由", verify_api_routes()))
    
    # 4. 验证数据库Schema
    results.append(("数据库Schema", verify_database_schema()))
    
    # 总结
    print("=" * 60)
    print("验证结果总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name:.<40} {status}")
    
    print(f"\n总计: {passed}/{total} 项验证通过")
    
    if passed == total:
        print("\n🎉 所有验证通过！系统已就绪。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 项验证失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
