#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目变更管理模块验证脚本
用于验证所有组件是否正确创建和配置
"""

import os
import sys
from pathlib import Path


def check_file_exists(path: str, description: str) -> bool:
    """检查文件是否存在"""
    if os.path.exists(path):
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ {description}: {path} (NOT FOUND)")
        return False


def check_imports() -> bool:
    """检查模块导入"""
    try:
        from app.models.change_request import (
            ChangeRequest,
            ChangeApprovalRecord,
            ChangeNotification,
        )
        from app.models.enums import (
            ChangeTypeEnum,
            ChangeSourceEnum,
            ChangeStatusEnum,
            ImpactLevelEnum,
            ApprovalDecisionEnum,
        )
        print("✅ Models and Enums imported successfully")
        
        from app.schemas.change_request import (
            ChangeRequestCreate,
            ChangeRequestUpdate,
            ChangeRequestResponse,
        )
        print("✅ Schemas imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


def check_syntax(file_path: str) -> bool:
    """检查Python文件语法"""
    import py_compile
    try:
        py_compile.compile(file_path, doraise=True)
        return True
    except Exception as e:
        print(f"❌ Syntax error in {file_path}: {e}")
        return False


def main():
    """主验证函数"""
    print("=" * 60)
    print("项目变更管理模块验证")
    print("=" * 60)
    
    all_ok = True
    
    # 1. 检查数据模型文件
    print("\n📦 检查数据模型文件...")
    files_to_check = [
        ("app/models/change_request.py", "变更请求模型"),
        ("app/models/enums/workflow.py", "工作流枚举"),
    ]
    
    for file_path, desc in files_to_check:
        if not check_file_exists(file_path, desc):
            all_ok = False
        elif not check_syntax(file_path):
            all_ok = False
    
    # 2. 检查Schema文件
    print("\n📝 检查Schema文件...")
    if not check_file_exists("app/schemas/change_request.py", "变更请求Schema"):
        all_ok = False
    elif not check_syntax("app/schemas/change_request.py"):
        all_ok = False
    
    # 3. 检查API端点文件
    print("\n🌐 检查API端点文件...")
    if not check_file_exists("app/api/v1/endpoints/projects/change_requests.py", "变更管理API"):
        all_ok = False
    elif not check_syntax("app/api/v1/endpoints/projects/change_requests.py"):
        all_ok = False
    
    # 4. 检查数据库迁移脚本
    print("\n🗄️ 检查数据库迁移脚本...")
    migrations = [
        ("migrations/20260214_change_management_sqlite.sql", "SQLite迁移"),
        ("migrations/20260214_change_management_mysql.sql", "MySQL迁移"),
    ]
    
    for file_path, desc in migrations:
        if not check_file_exists(file_path, desc):
            all_ok = False
    
    # 5. 检查测试文件
    print("\n🧪 检查测试文件...")
    if not check_file_exists("tests/unit/test_change_request_service.py", "单元测试"):
        all_ok = False
    elif not check_syntax("tests/unit/test_change_request_service.py"):
        all_ok = False
    
    # 6. 检查文档文件
    print("\n📚 检查文档文件...")
    docs = [
        ("docs/change_management_user_guide.md", "用户指南"),
        ("docs/change_management_api.md", "API文档"),
        ("docs/change_management_workflow.md", "工作流文档"),
    ]
    
    for file_path, desc in docs:
        if not check_file_exists(file_path, desc):
            all_ok = False
    
    # 7. 检查模块导入
    print("\n🔍 检查模块导入...")
    if not check_imports():
        all_ok = False
    
    # 8. 统计代码行数
    print("\n📊 代码统计...")
    files_for_count = [
        "app/models/change_request.py",
        "app/schemas/change_request.py",
        "app/api/v1/endpoints/projects/change_requests.py",
        "tests/unit/test_change_request_service.py",
    ]
    
    total_lines = 0
    for file_path in files_for_count:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
                total_lines += lines
                print(f"  {file_path}: {lines} 行")
    
    print(f"  总代码行数: {total_lines} 行")
    
    # 9. 最终结果
    print("\n" + "=" * 60)
    if all_ok:
        print("✅ 所有验证通过！模块已成功实现。")
        print("\n下一步:")
        print("  1. 运行数据库迁移: sqlite3 data/pms.db < migrations/20260214_change_management_sqlite.sql")
        print("  2. 初始化权限: 在数据库中添加 change:* 权限")
        print("  3. 重启服务: ./stop.sh && ./start.sh")
        print("  4. 测试API: curl http://localhost:8000/api/v1/projects/1/changes")
        return 0
    else:
        print("❌ 部分验证失败，请检查上述错误。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
