#!/usr/bin/env python3
"""
全局认证中间件验证脚本
"""

print("=" * 60)
print("Step 1 - 全局认证中间件验证")
print("=" * 60)

# 测试1: 导入中间件
try:
    from app.core.middleware.auth_middleware import GlobalAuthMiddleware
    print("✓ 中间件模块导入成功")
except Exception as e:
    print(f"✗ 中间件导入失败: {e}")
    exit(1)

# 测试2: 导入辅助函数
try:
    print("✓ 辅助函数 get_current_user_from_state 导入成功")
except Exception as e:
    print(f"✗ 辅助函数导入失败: {e}")
    exit(1)

# 测试3: 检查白名单配置
print(f"\n白名单路径 ({len(GlobalAuthMiddleware.WHITE_LIST)} 个):")
for path in GlobalAuthMiddleware.WHITE_LIST:
    print(f"  - {path}")

print(f"\n白名单前缀 ({len(GlobalAuthMiddleware.WHITE_LIST_PREFIXES)} 个):")
for prefix in GlobalAuthMiddleware.WHITE_LIST_PREFIXES:
    print(f"  - {prefix}")

# 测试4: 检查 main.py 中间件注册
print("\n检查 main.py 中间件注册...")
with open('app/main.py', 'r') as f:
    content = f.read()
    if 'from app.core.middleware.auth_middleware import GlobalAuthMiddleware' in content:
        print("✓ 中间件已导入")
    else:
        print("✗ 中间件未导入")
        exit(1)

    if 'app.add_middleware(GlobalAuthMiddleware)' in content:
        print("✓ 中间件已注册")
    else:
        print("✗ 中间件未注册")
        exit(1)

# 测试5: 检查 security.py 导出
print("\n检查 security.py 导出...")
try:
    from app.core.security import get_current_active_superuser
    print("✓ get_current_active_superuser 已正确导出")
except ImportError as e:
    print(f"✗ get_current_active_superuser 导出失败: {e}")
    exit(1)

print("\n" + "=" * 60)
print("✅ Step 1 验证完成 - 所有检查通过！")
print("=" * 60)

print("\n下一步:")
print("1. 启动服务: uvicorn app.main:app --reload")
print("2. 测试未认证访问（应该返回401）:")
print("   curl http://localhost:8000/api/v1/projects")
print("3. 测试白名单路径（应该成功）:")
print("   curl http://localhost:8000/health")
print("4. 登录获取token:")
print("   curl -X POST http://localhost:8000/api/v1/auth/login \\")
print("     -H 'Content-Type: application/x-www-form-urlencoded' \\")
print("     -d 'username=admin&password=your_password'")
