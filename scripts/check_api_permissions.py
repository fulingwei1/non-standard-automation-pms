#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查API端点的权限配置情况
- 扫描所有API端点文件
- 检查哪些端点使用了权限检查
- 检查权限编码是否在数据库中存在
- 生成缺失权限报告
"""

import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.models.base import get_db_session


class APIPermissionChecker:
    def __init__(self):
        self.endpoints_dir = Path(__file__).parent.parent / "app" / "api" / "v1" / "endpoints"
        self.endpoints_with_permission: List[Dict] = []
        self.endpoints_without_permission: List[Dict] = []
        self.permission_codes_used: Set[str] = set()
        self.permission_codes_in_db: Set[str] = set()

    def scan_endpoint_files(self) -> Dict[str, List[Dict]]:
        """扫描所有API端点文件，提取端点信息"""
        results = {
            "with_permission": [],
            "without_permission": [],
            "public": [],  # 公开API（如登录、注册等）
        }

        # 公开API路径（不需要权限检查）
        public_paths = {
            "/auth/login",
            "/auth/register",
            "/auth/refresh",
            "/health",
        }

        for file_path in self.endpoints_dir.glob("*.py"):
            if file_path.name == "__init__.py":
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    ''.join(lines)

                # 使用正则表达式查找路由装饰器和权限检查
                # 匹配 @router.get/post/put/delete("path")
                route_pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'
                # 匹配 require_permission("code")
                permission_pattern = r'require_permission\(["\']([^"\']+)["\']\)'

                # 查找所有路由定义
                for i, line in enumerate(lines, 1):
                    route_match = re.search(route_pattern, line)
                    if route_match:
                        method = route_match.group(1).upper()
                        path = route_match.group(2)

                        # 检查接下来20行内是否有权限检查
                        has_permission = False
                        permission_code = None

                        search_end = min(i + 20, len(lines))
                        for j in range(i, search_end):
                            perm_match = re.search(permission_pattern, lines[j])
                            if perm_match:
                                has_permission = True
                                permission_code = perm_match.group(1)
                                self.permission_codes_used.add(permission_code)
                                break

                        # 提取函数名（下一行应该是函数定义）
                        func_name = None
                        if i < len(lines):
                            func_match = re.search(r"def\s+(\w+)", lines[i])
                            if func_match:
                                func_name = func_match.group(1)

                        endpoint_info = {
                            "file": file_path.name,
                            "function": func_name or "unknown",
                            "path": path,
                            "method": method,
                            "has_permission": has_permission,
                            "permission_code": permission_code,
                            "line": i,
                        }

                        # 检查是否为公开API
                        if any(public_path in path for public_path in public_paths):
                            results["public"].append(endpoint_info)
                        elif has_permission:
                            results["with_permission"].append(endpoint_info)
                        else:
                            results["without_permission"].append(endpoint_info)

            except Exception as e:
                print(f"⚠️  解析文件 {file_path.name} 时出错: {e}")

        return results

    def check_permissions_in_db(self):
        """检查数据库中是否存在这些权限编码"""
        with get_db_session() as session:
            result = session.execute(
                text(
                    """
                SELECT perm_code, perm_name, module, action
                FROM permissions
                WHERE is_active = 1 OR is_active IS NULL
            """
                )
            )

            for row in result:
                self.permission_codes_in_db.add(row[0])

    def generate_report(self, results: Dict):
        """生成检查报告"""
        print("=" * 80)
        print("API端点权限配置检查报告")
        print("=" * 80)
        print()

        # 统计信息
        total_endpoints = (
            len(results["with_permission"])
            + len(results["without_permission"])
            + len(results["public"])
        )

        print(f"📊 统计信息:")
        print(f"  总端点数: {total_endpoints}")
        print(f"  ✅ 已配置权限: {len(results['with_permission'])}")
        print(f"  ⚠️  未配置权限: {len(results['without_permission'])}")
        print(f"  🔓 公开API: {len(results['public'])}")
        print()

        # 缺失权限的端点
        if results["without_permission"]:
            print("=" * 80)
            print("⚠️  未配置权限的API端点:")
            print("=" * 80)

            # 按文件分组
            by_file = defaultdict(list)
            for endpoint in results["without_permission"]:
                by_file[endpoint["file"]].append(endpoint)

            for filename, endpoints in sorted(by_file.items()):
                print(f"\n📄 {filename}:")
                for endpoint in endpoints:
                    method = endpoint["method"].ljust(6)
                    path = endpoint["path"].ljust(40)
                    func = endpoint["function"]
                    line = endpoint["line"]
                    print(f"   {method} {path} -> {func} (行 {line})")
            print()

        # 使用的权限编码
        if self.permission_codes_used:
            print("=" * 80)
            print("🔑 代码中使用的权限编码:")
            print("=" * 80)

            # 检查哪些权限在数据库中不存在
            missing_permissions = self.permission_codes_used - self.permission_codes_in_db
            existing_permissions = self.permission_codes_used & self.permission_codes_in_db

            if existing_permissions:
                print(f"\n✅ 已存在于数据库 ({len(existing_permissions)} 个):")
                for perm in sorted(existing_permissions):
                    print(f"   - {perm}")

            if missing_permissions:
                print(f"\n❌ 数据库中不存在 ({len(missing_permissions)} 个):")
                for perm in sorted(missing_permissions):
                    print(f"   - {perm}")
            print()

        # 数据库中的权限（按模块分组）
        print("=" * 80)
        print("📋 数据库中的权限列表（按模块分组）:")
        print("=" * 80)

        with get_db_session() as session:
            result = session.execute(
                text(
                    """
                SELECT module, perm_code, perm_name, action
                FROM permissions
                WHERE is_active = 1 OR is_active IS NULL
                ORDER BY module, perm_code
            """
                )
            )

            by_module = defaultdict(list)
            for row in result:
                by_module[row[0] or "未分类"].append(
                    {"code": row[1], "name": row[2], "action": row[3]}
                )

            for module, perms in sorted(by_module.items()):
                print(f"\n📦 {module} ({len(perms)} 个权限):")
                for perm in perms:
                    print(f"   - {perm['code']:30} | {perm['name']:20} | {perm['action']}")
            print()

        # 建议
        print("=" * 80)
        print("💡 建议:")
        print("=" * 80)
        print()

        if results["without_permission"]:
            print("1. 为未配置权限的API端点添加权限检查:")
            print("   - 使用 require_permission('module:resource:action') 装饰器")
            print("   - 在 migrations/ 目录下创建权限迁移脚本")
            print()

        if missing_permissions:
            print("2. 在数据库中创建缺失的权限:")
            print("   - 创建迁移脚本: migrations/YYYYMMDD_new_permissions_sqlite.sql")
            print(
                "   - 使用格式: INSERT INTO permissions (perm_code, perm_name, module, action) VALUES ..."
            )
            print()

        print("3. 权限编码规范:")
        print("   - 格式: {module}:{resource}:{action}")
        print("   - 示例: project:read, material:bom:manage, performance:evaluation:create")
        print()


def main():
    checker = APIPermissionChecker()

    print("🔍 开始扫描API端点...")
    results = checker.scan_endpoint_files()

    print("🔍 检查数据库中的权限...")
    checker.check_permissions_in_db()

    print("\n")
    checker.generate_report(results)


if __name__ == "__main__":
    main()
