#!/usr/bin/env python3
"""
API权限初始化和验证脚本（简化版）
直接使用SQL查询，避免模型导入问题
"""
import sys
import os
import sqlite3
from pathlib import Path
import datetime

# 数据库路径
DB_PATH = Path(__file__).parent / "data" / "app.db"


def execute_sql_file(conn, sql_file_path):
    """执行SQL文件"""
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 按分号分割语句
    statements = []
    current_stmt = []
    for line in sql_content.split('\n'):
        stripped = line.strip()
        if not stripped or stripped.startswith('--'):
            continue
        current_stmt.append(line)
        if stripped.endswith(';'):
            statements.append('\n'.join(current_stmt))
            current_stmt = []
    
    executed = 0
    for stmt in statements:
        stmt = stmt.strip()
        if stmt and not stmt.startswith('--'):
            try:
                conn.execute(stmt)
                executed += 1
            except sqlite3.IntegrityError:
                # 已存在，跳过
                pass
            except Exception as e:
                print(f"⚠ SQL执行警告: {e}")
    
    conn.commit()
    return executed


def verify_database():
    """验证数据库中的权限数据"""
    print("\n" + "="*60)
    print("步骤1: 验证数据库中的API权限数据")
    print("="*60)
    
    if not DB_PATH.exists():
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return 0, 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. 检查权限表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='api_permissions'")
        if not cursor.fetchone():
            print("❌ api_permissions 表不存在")
            return 0, 0
        
        # 2. 检查当前权限数
        cursor.execute("SELECT COUNT(*) FROM api_permissions")
        perm_count = cursor.fetchone()[0]
        print(f"\n当前 api_permissions 表记录数: {perm_count}")
        
        # 3. 如果为空，执行初始化
        if perm_count == 0:
            print("\n⚠ 权限表为空，开始初始化...")
            sql_file = Path(__file__).parent / "migrations" / "20260205_api_permissions_seed_sqlite.sql"
            if sql_file.exists():
                executed = execute_sql_file(conn, sql_file)
                print(f"✓ 执行了 {executed} 条SQL语句")
                
                cursor.execute("SELECT COUNT(*) FROM api_permissions")
                perm_count = cursor.fetchone()[0]
                print(f"✓ 初始化完成，现有记录数: {perm_count}")
            else:
                print(f"❌ SQL种子文件不存在: {sql_file}")
                return 0, 0
        
        # 4. 显示权限示例
        cursor.execute("SELECT perm_code, perm_name, module, action FROM api_permissions LIMIT 10")
        sample_perms = cursor.fetchall()
        print("\n权限示例（前10条）:")
        for row in sample_perms:
            print(f"  - {row[0]}: {row[1]} ({row[2]}:{row[3]})")
        
        # 5. 检查映射表
        cursor.execute("SELECT COUNT(*) FROM role_api_permissions")
        mapping_count = cursor.fetchone()[0]
        print(f"\n✓ role_api_permissions 映射数: {mapping_count}")
        
        # 6. 检查管理员角色的权限
        cursor.execute("SELECT id FROM roles WHERE role_code = 'admin' OR role_name = 'admin'")
        admin_role = cursor.fetchone()
        if admin_role:
            admin_role_id = admin_role[0]
            cursor.execute(
                "SELECT COUNT(*) FROM role_api_permissions WHERE role_id = ?",
                (admin_role_id,)
            )
            admin_perms = cursor.fetchone()[0]
            print(f"\n✓ 管理员角色(ID:{admin_role_id})拥有权限数: {admin_perms}")
            
            # 显示管理员权限
            cursor.execute("""
                SELECT ap.perm_code, ap.perm_name, ap.module 
                FROM role_api_permissions rap
                JOIN api_permissions ap ON rap.permission_id = ap.id
                WHERE rap.role_id = ?
                ORDER BY ap.module, ap.perm_code
                LIMIT 20
            """, (admin_role_id,))
            
            admin_perm_details = cursor.fetchall()
            print("\n管理员权限示例（前20条）:")
            for row in admin_perm_details:
                print(f"  - {row[0]}: {row[1]} ({row[2]})")
        else:
            print("\n⚠ 未找到管理员角色")
        
        # 验收标准检查
        print("\n" + "="*60)
        print("验收标准检查:")
        print("="*60)
        if perm_count >= 100:
            print(f"✅ api_permissions表有{perm_count}条记录 (≥100)")
        else:
            print(f"❌ api_permissions表只有{perm_count}条记录 (<100)")
        
        if mapping_count > 0:
            print(f"✅ role_api_permissions映射完整 ({mapping_count}条)")
        else:
            print(f"❌ role_api_permissions映射为空")
        
        return perm_count, mapping_count
        
    finally:
        conn.close()


def test_api_access():
    """测试管理员API访问"""
    print("\n" + "="*60)
    print("步骤2: 测试管理员API访问")
    print("="*60)
    
    try:
        import requests
        from jose import jwt
        from datetime import timedelta
    except ImportError as e:
        print(f"⚠ 缺少依赖库: {e}")
        print("跳过API测试...")
        return None
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 获取管理员用户
        cursor.execute("SELECT id, username FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()
        if not admin_user:
            print("❌ 未找到管理员用户")
            return None
        
        # 创建访问令牌
        secret_key = os.getenv("SECRET_KEY", "dev-secret-key-for-testing")
        to_encode = {
            "sub": "admin",
            "exp": datetime.datetime.utcnow() + timedelta(minutes=30)
        }
        token = jwt.encode(to_encode, secret_key, algorithm="HS256")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 测试API端点
        base_url = "http://localhost:8000"
        test_endpoints = [
            "/api/v1/users",
            "/api/v1/roles",
        ]
        
        results = []
        for endpoint in test_endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=5)
                status = response.status_code
                success = status == 200
                
                print(f"\n测试端点: {endpoint}")
                print(f"  状态码: {status}")
                print(f"  结果: {'✅ 成功' if success else '❌ 失败'}")
                
                if not success:
                    print(f"  响应: {response.text[:200]}")
                
                results.append({
                    "endpoint": endpoint,
                    "status": status,
                    "success": success
                })
            except requests.exceptions.ConnectionError:
                print(f"\n测试端点: {endpoint}")
                print(f"  ⚠ 服务器未运行或无法连接")
                results.append({
                    "endpoint": endpoint,
                    "error": "Connection refused",
                    "success": False
                })
            except Exception as e:
                print(f"\n测试端点: {endpoint}")
                print(f"  ❌ 请求失败: {e}")
                results.append({
                    "endpoint": endpoint,
                    "error": str(e),
                    "success": False
                })
        
        # 验收标准检查
        print("\n" + "="*60)
        print("API访问验收标准:")
        print("="*60)
        all_success = all(r.get("success", False) for r in results)
        if all_success:
            print("✅ 管理员可以正常访问所有测试API（200状态码）")
        else:
            print("⚠ 部分API访问失败（可能服务器未启动）")
        
        return results
        
    finally:
        conn.close()


def generate_report(perm_count, mapping_count, api_results):
    """生成验证报告"""
    print("\n" + "="*60)
    print("生成验证报告")
    print("="*60)
    
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    report = f"""# API权限初始化和验证报告

**生成时间:** {timestamp}

## 1. 数据库验证

### 1.1 api_permissions表
- 记录数: **{perm_count}**
- 验收标准: ≥100 条
- 结果: {'✅ 通过' if perm_count >= 100 else '❌ 未通过'}

### 1.2 role_api_permissions映射
- 映射数: **{mapping_count}**
- 验收标准: >0 条
- 结果: {'✅ 通过' if mapping_count > 0 else '❌ 未通过'}

## 2. API访问测试

### 2.1 测试结果汇总
"""
    
    if api_results:
        report += "\n| 端点 | 状态码 | 结果 |\n"
        report += "|------|--------|------|\n"
        for result in api_results:
            endpoint = result.get("endpoint", "N/A")
            status = result.get("status", result.get("error", "ERROR"))
            success = "✅ 成功" if result.get("success", False) else "❌ 失败"
            report += f"| {endpoint} | {status} | {success} |\n"
        
        all_success = all(r.get("success", False) for r in api_results)
        report += f"\n### 2.2 验收标准\n"
        report += f"- 管理员访问API: {'✅ 通过（所有API返回200）' if all_success else '⚠ 未通过（可能服务器未启动）'}\n"
    else:
        report += "\n⚠ API测试未执行（缺少依赖或服务器未启动）\n"
    
    # 总结
    report += "\n## 3. 总体结论\n\n"
    
    checks = [
        ("api_permissions表记录数≥100", perm_count >= 100),
        ("role_api_permissions映射完整", mapping_count > 0),
    ]
    
    if api_results:
        all_api_success = all(r.get("success", False) for r in api_results)
        checks.append(("管理员API访问正常", all_api_success))
    
    passed = sum(1 for _, success in checks if success)
    total = len(checks)
    
    for name, success in checks:
        report += f"- {name}: {'✅' if success else '❌'}\n"
    
    report += f"\n**通过率: {passed}/{total} ({passed*100//total}%)**\n"
    
    if passed == total:
        report += "\n🎉 **所有验收标准已通过！**\n"
    else:
        report += "\n⚠ **部分验收标准未通过。**\n"
        
        if perm_count < 100:
            report += "\n### 需要修复的问题:\n"
            report += f"- api_permissions表记录不足（当前{perm_count}，需要≥100）\n"
            report += "  - 建议：检查SQL种子文件是否完整\n"
        
        if mapping_count == 0:
            report += "\n### 需要修复的问题:\n"
            report += "- role_api_permissions映射为空\n"
            report += "  - 建议：检查SQL种子文件中的映射语句\n"
    
    # 保存报告
    report_file = "API权限初始化验证报告.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n✓ 报告已保存到: {report_file}")
    
    return report


if __name__ == "__main__":
    print("开始API权限初始化和验证...")
    print(f"数据库路径: {DB_PATH}")
    
    # 验证数据库
    perm_count, mapping_count = verify_database()
    
    # 测试API访问
    api_results = test_api_access()
    
    # 生成报告
    generate_report(perm_count, mapping_count, api_results)
    
    print("\n✓ 验证完成！")
