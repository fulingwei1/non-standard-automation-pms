#!/usr/bin/env python3
"""
二分法查找循环导入的模块
"""
import sys

# 要测试的端点模块列表（从 app/api/v1/api.py 提取）
endpoints = [
    "app.api.v1.endpoints.auth",
    "app.api.v1.endpoints.users",
    "app.api.v1.endpoints.roles",
    "app.api.v1.endpoints.permissions",
    "app.api.v1.endpoints.projects",
    "app.api.v1.endpoints.production",
    "app.api.v1.endpoints.timesheet",
    "app.api.v1.endpoints.rd_project",
    "app.api.v1.endpoints.sales",
]

def test_import(module_name):
    """测试单个模块导入"""
    try:
        # 清除之前的导入
        modules_to_remove = [k for k in sys.modules.keys() if k.startswith('app.')]
        for mod in modules_to_remove:
            del sys.modules[mod]
        
        __import__(module_name)
        return True, None
    except RecursionError as e:
        return False, "RecursionError"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:60]}"

print("=" * 70)
print("测试各个端点模块...")
print("=" * 70)

failed_modules = []

for endpoint in endpoints:
    print(f"\n测试: {endpoint}")
    success, error = test_import(endpoint)
    
    if success:
        print(f"  ✓ 成功")
    else:
        print(f"  ✗ 失败: {error}")
        failed_modules.append((endpoint, error))

print("\n" + "=" * 70)
print("总结:")
print("=" * 70)

if failed_modules:
    print(f"\n{len(failed_modules)} 个模块导入失败:")
    for mod, err in failed_modules:
        print(f"  ✗ {mod}")
        print(f"    原因: {err}")
else:
    print("\n✓ 所有模块都可以单独导入!")
    print("问题可能在 app.api.v1.api 的聚合层")
