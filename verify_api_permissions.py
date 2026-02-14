#!/usr/bin/env python3
"""
API权限初始化和验证脚本
"""
import sys
import os
import logging
from pathlib import Path

# 添加项目路径
repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root))

from sqlalchemy import text
from app.models.base import SessionLocal
from app.models.user import ApiPermission, User, Role
from app.utils.init_data import init_api_permissions
from app.core.security import create_access_token
import requests
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_database():
    """验证数据库中的权限数据"""
    print("\n" + "="*60)
    print("步骤1: 验证数据库中的API权限数据")
    print("="*60)
    
    db = SessionLocal()
    try:
        # 1. 检查 api_permissions 表
        perm_count = db.query(ApiPermission).count()
        print(f"\n✓ api_permissions 表记录数: {perm_count}")
        
        if perm_count == 0:
            print("⚠ 权限表为空，开始初始化...")
            init_api_permissions(db)
            db.commit()
            perm_count = db.query(ApiPermission).count()
            print(f"✓ 初始化完成，现有记录数: {perm_count}")
        
        # 显示一些权限示例
        sample_perms = db.query(ApiPermission).limit(10).all()
        print("\n权限示例（前10条）:")
        for perm in sample_perms:
            print(f"  - {perm.perm_code}: {perm.perm_name} ({perm.module}:{perm.action})")
        
        # 2. 检查 role_api_permissions 映射
        mapping_count = db.execute(
            text("SELECT COUNT(*) FROM role_api_permissions")
        ).scalar()
        print(f"\n✓ role_api_permissions 映射数: {mapping_count}")
        
        # 3. 检查管理员角色的权限
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if admin_role:
            admin_perms = db.execute(
                text("""
                    SELECT COUNT(*) FROM role_api_permissions 
                    WHERE role_id = :role_id
                """),
                {"role_id": admin_role.id}
            ).scalar()
            print(f"\n✓ 管理员角色(ID:{admin_role.id})拥有权限数: {admin_perms}")
            
            # 显示管理员的权限
            admin_perm_details = db.execute(
                text("""
                    SELECT ap.perm_code, ap.perm_name, ap.module 
                    FROM role_api_permissions rap
                    JOIN api_permissions ap ON rap.permission_id = ap.id
                    WHERE rap.role_id = :role_id
                    ORDER BY ap.module, ap.perm_code
                    LIMIT 20
                """),
                {"role_id": admin_role.id}
            ).fetchall()
            
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
        db.close()


def test_api_access():
    """测试管理员API访问"""
    print("\n" + "="*60)
    print("步骤2: 测试管理员API访问")
    print("="*60)
    
    db = SessionLocal()
    try:
        # 获取管理员用户
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("❌ 未找到管理员用户")
            return False
        
        # 创建访问令牌
        token = create_access_token({"sub": admin_user.username})
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
            print("❌ 部分API访问失败")
        
        return results
        
    finally:
        db.close()


def generate_report(perm_count, mapping_count, api_results):
    """生成验证报告"""
    print("\n" + "="*60)
    print("生成验证报告")
    print("="*60)
    
    report = f"""# API权限初始化和验证报告

**生成时间:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

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
            status = result.get("status", "ERROR")
            success = "✅ 成功" if result.get("success", False) else "❌ 失败"
            report += f"| {endpoint} | {status} | {success} |\n"
        
        all_success = all(r.get("success", False) for r in api_results)
        report += f"\n### 2.2 验收标准\n"
        report += f"- 管理员访问API: {'✅ 通过（所有API返回200）' if all_success else '❌ 未通过'}\n"
    else:
        report += "\n⚠ API测试未执行（可能服务器未启动）\n"
    
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
        report += "\n⚠ **部分验收标准未通过，需要修复。**\n"
    
    # 保存报告
    report_file = "API权限初始化验证报告.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n✓ 报告已保存到: {report_file}")
    print(report)
    
    return report


if __name__ == "__main__":
    try:
        import pandas as pd
    except ImportError:
        # 简单的时间戳
        import datetime
        class pd:
            class Timestamp:
                @staticmethod
                def now():
                    class DT:
                        def strftime(self, fmt):
                            return datetime.datetime.now().strftime(fmt)
                    return DT()
    
    print("开始API权限初始化和验证...")
    
    # 验证数据库
    perm_count, mapping_count = verify_database()
    
    # 测试API访问
    api_results = test_api_access()
    
    # 生成报告
    generate_report(perm_count, mapping_count, api_results)
    
    print("\n✓ 验证完成！")
