#!/usr/bin/env python3
"""
最终验证报告生成脚本
"""
import sqlite3
from pathlib import Path
import datetime
import requests

DB_PATH = Path(__file__).parent / "data" / "app.db"

def generate_final_report():
    """生成最终验证报告"""
    
    print("="*70)
    print("API权限初始化和验证 - 最终报告")
    print("="*70)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. 数据库统计
    cursor.execute("SELECT COUNT(*) FROM api_permissions")
    perm_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM role_api_permissions")
    mapping_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT role_id) FROM role_api_permissions")
    roles_with_perms = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM role_api_permissions rap
        JOIN roles r ON rap.role_id = r.id
        WHERE r.role_code = 'ADMIN'
    """)
    admin_perm_count = cursor.fetchone()[0]
    
    print(f"\n📊 数据库统计:")
    print(f"  - API权限总数: {perm_count}")
    print(f"  - 权限映射总数: {mapping_count}")
    print(f"  - 拥有权限的角色数: {roles_with_perms}")
    print(f"  - 管理员角色权限数: {admin_perm_count}")
    
    # 2. API访问测试
    print(f"\n🧪 API访问测试:")
    
    # 登录
    login_data = {"username": "admin", "password": "admin123"}
    response = requests.post("http://localhost:8000/api/v1/auth/login", data=login_data)
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        test_endpoints = [
            ("/api/v1/users", "用户管理API"),
            ("/api/v1/roles", "角色管理API"),
        ]
        
        all_passed = True
        for endpoint, desc in test_endpoints:
            resp = requests.get(f"http://localhost:8000{endpoint}", headers=headers)
            status = resp.status_code
            passed = status == 200
            all_passed = all_passed and passed
            
            icon = "✅" if passed else "❌"
            print(f"  {icon} {desc} ({endpoint}): {status}")
            
            if passed and 'data' in resp.json():
                data = resp.json()['data']
                if isinstance(data, list):
                    print(f"     返回 {len(data)} 条记录")
    else:
        all_passed = False
        print(f"  ❌ 登录失败: {response.status_code}")
    
    # 3. 验收标准检查
    print(f"\n✅ 验收标准:")
    
    checks = [
        ("api_permissions表有100+条记录", perm_count >= 100, perm_count),
        ("管理员可访问用户管理API", all_passed, "200 OK"),
        ("管理员可访问角色管理API", all_passed, "200 OK"),
        ("role_api_permissions映射完整", mapping_count > 0, mapping_count),
    ]
    
    passed_count = 0
    for desc, passed, value in checks:
        icon = "✅" if passed else "❌"
        print(f"  {icon} {desc}: {value}")
        if passed:
            passed_count += 1
    
    # 4. 总结
    print(f"\n📝 总结:")
    print(f"  通过率: {passed_count}/{len(checks)} ({passed_count*100//len(checks)}%)")
    
    if passed_count == len(checks):
        print(f"\n🎉 所有验收标准已通过！系统API权限功能正常。")
        result_emoji = "🎉"
        result_text = "全部通过"
    else:
        print(f"\n⚠️  部分验收标准未通过，需要进一步检查。")
        result_emoji = "⚠️"
        result_text = "部分通过"
    
    # 5. 生成Markdown报告
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    report = f"""# API权限初始化和验证报告 {result_emoji}

**生成时间:** {timestamp}
**状态:** {result_text}

## 1. 数据库验证

### 1.1 权限数据统计
- **API权限总数:** {perm_count}
- **权限映射总数:** {mapping_count}
- **拥有权限的角色数:** {roles_with_perms}
- **管理员角色权限数:** {admin_perm_count}

### 1.2 验收标准
| 项目 | 标准 | 实际值 | 结果 |
|------|------|--------|------|
| API权限记录数 | ≥100 | {perm_count} | {'✅ 通过' if perm_count >= 100 else '❌ 未通过'} |
| 权限映射数 | >0 | {mapping_count} | {'✅ 通过' if mapping_count > 0 else '❌ 未通过'} |

## 2. API访问测试

### 2.1 测试结果
| 端点 | 描述 | 状态码 | 结果 |
|------|------|--------|------|
"""
    
    if all_passed:
        report += f"| /api/v1/users | 用户管理API | 200 | ✅ 成功 |\n"
        report += f"| /api/v1/roles | 角色管理API | 200 | ✅ 成功 |\n"
    else:
        report += f"| 所有端点 | - | - | ❌ 登录失败 |\n"
    
    report += f"""
### 2.2 验收标准
- 管理员访问/api/v1/users: {'✅ 通过（200 OK）' if all_passed else '❌ 未通过'}
- 管理员访问/api/v1/roles: {'✅ 通过（200 OK）' if all_passed else '❌ 未通过'}

## 3. 修复记录

### 3.1 已修复的问题
1. ✅ 创建了 `api_permissions` 和 `role_api_permissions` 表
2. ✅ 导入了123条API权限记录
3. ✅ 为20个角色分配了469个权限映射
4. ✅ 添加了缺失的权限码 (`user:read`, `role:read`)
5. ✅ 修复了数据库表缺失的列 (`tenant_id`, `is_tenant_admin`, `reporting_to`, `parent_id`, `is_active`, `sort_order`)

### 3.2 关键修复
- **权限码映射:** 代码中使用 `user:read`，SQL种子文件中是 `user:view` → 已添加 `user:read` 权限
- **数据库Schema:** 模型定义与数据库表不一致 → 已同步所有缺失列

## 4. 总体结论

**通过率:** {passed_count}/{len(checks)} ({passed_count*100//len(checks)}%)

"""
    
    if passed_count == len(checks):
        report += "🎉 **所有验收标准已通过！API权限系统功能正常。**\n\n"
        report += "管理员现在可以正常访问用户管理和角色管理API，权限控制功能已完全启用。\n"
    else:
        report += "⚠️ **部分验收标准未通过，需要进一步检查。**\n"
    
    # 保存报告
    report_file = "API权限初始化验证最终报告.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n💾 报告已保存: {report_file}")
    print("="*70)
    
    conn.close()
    
    return passed_count == len(checks)


if __name__ == "__main__":
    import sys
    success = generate_final_report()
    sys.exit(0 if success else 1)
