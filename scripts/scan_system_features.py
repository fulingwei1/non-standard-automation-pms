#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描系统功能并更新功能注册表
- 扫描API路由注册
- 统计API端点数量
- 统计权限数量
- 统计前端页面数量
- 更新功能表
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.models.base import get_db_session

# 路径配置
PROJECT_ROOT = Path(__file__).parent.parent
API_FILE = PROJECT_ROOT / "app" / "api" / "v1" / "api.py"
ENDPOINTS_DIR = PROJECT_ROOT / "app" / "api" / "v1" / "endpoints"
FRONTEND_PAGES_DIR = PROJECT_ROOT / "frontend" / "src" / "pages"
MIGRATIONS_DIR = PROJECT_ROOT / "migrations"


def parse_api_registration() -> List[Dict]:
    """解析API注册文件，获取所有已注册的模块"""
    features = []

    with open(API_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 匹配 include_router 调用
    pattern = r'api_router\.include_router\((\w+)\.router,\s*prefix=["\']([^"\']+)["\'],\s*tags=\[["\']([^"\']+)["\']\]\)'
    matches = re.findall(pattern, content)

    for module_name, prefix, tag in matches:
        api_file = ENDPOINTS_DIR / f"{module_name}.py"
        features.append(
            {
                "code": tag or module_name,
                "name": tag or module_name,
                "module": tag or module_name,
                "api_file": str(api_file.relative_to(PROJECT_ROOT)),
                "api_prefix": prefix,
                "endpoint_file": module_name,
            }
        )

    return features


def count_api_endpoints(file_path: Path) -> int:
    """统计API端点数量"""
    if not file_path.exists():
        return 0

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 匹配路由装饰器
    pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'
    matches = re.findall(pattern, content)

    return len(matches)


def count_permissions(feature_code: str) -> tuple:
    """统计权限数量"""
    has_permission = False
    permission_count = 0

    # 查找权限迁移脚本
    permission_files = list(MIGRATIONS_DIR.glob("*permission*.sql"))

    for file_path in permission_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查是否包含该功能的权限
        if feature_code in content.lower() or f"module.*{feature_code}" in content:
            has_permission = True
            # 统计INSERT语句数量
            pattern = r"INSERT.*INTO permissions.*VALUES"
            matches = re.findall(pattern, content, re.IGNORECASE)
            permission_count += len(matches)

    return has_permission, permission_count


def count_frontend_pages(feature_code: str) -> tuple:
    """统计前端页面数量"""
    has_frontend = False
    page_count = 0

    # 简单的关键词匹配（可以根据实际情况优化）
    keywords = [
        feature_code,
        feature_code.replace("_", ""),
        feature_code.replace("-", ""),
    ]

    for file_path in FRONTEND_PAGES_DIR.rglob("*.jsx"):
        file_name = file_path.name.lower()
        file_content = file_path.read_text(encoding="utf-8").lower()

        for keyword in keywords:
            if keyword.lower() in file_name or keyword.lower() in file_content:
                has_frontend = True
                page_count += 1
                break

    return has_frontend, page_count


def scan_all_features() -> List[Dict]:
    """扫描所有功能"""
    features = parse_api_registration()

    for feature in features:
        # 统计API端点
        api_file_path = PROJECT_ROOT / feature["api_file"]
        feature["api_endpoint_count"] = count_api_endpoints(api_file_path)

        # 统计权限
        has_perm, perm_count = count_permissions(feature["code"])
        feature["has_permission"] = has_perm
        feature["permission_count"] = perm_count

        # 统计前端页面
        has_frontend, page_count = count_frontend_pages(feature["code"])
        feature["has_frontend"] = has_frontend
        feature["frontend_page_count"] = page_count

        # 默认启用
        feature["is_enabled"] = True
        feature["priority"] = "medium"

    return features


def update_feature_table(features: List[Dict]):
    """更新功能表"""
    with get_db_session() as session:
        # 检查表是否存在
        try:
            session.execute(text("SELECT 1 FROM system_features LIMIT 1"))
        except Exception:
            # 创建表
            session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS system_features (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feature_code VARCHAR(100) UNIQUE NOT NULL,
                    feature_name VARCHAR(200) NOT NULL,
                    module VARCHAR(50),
                    description TEXT,
                    api_file VARCHAR(200),
                    api_prefix VARCHAR(100),
                    api_endpoint_count INTEGER DEFAULT 0,
                    has_permission BOOLEAN DEFAULT 0,
                    permission_count INTEGER DEFAULT 0,
                    has_frontend BOOLEAN DEFAULT 0,
                    frontend_page_count INTEGER DEFAULT 0,
                    is_enabled BOOLEAN DEFAULT 1,
                    priority VARCHAR(20) DEFAULT 'medium',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
                )
            )
            session.commit()

        # 更新或插入功能
        for feature in features:
            session.execute(
                text(
                    """
                INSERT OR REPLACE INTO system_features (
                    feature_code, feature_name, module, api_file, api_prefix,
                    api_endpoint_count, has_permission, permission_count,
                    has_frontend, frontend_page_count, is_enabled, priority,
                    updated_at
                ) VALUES (
                    :code, :name, :module, :api_file, :api_prefix,
                    :api_endpoint_count, :has_permission, :permission_count,
                    :has_frontend, :frontend_page_count, :is_enabled, :priority,
                    CURRENT_TIMESTAMP
                )
            """
                ),
                {
                    "code": feature["code"],
                    "name": feature.get("name", feature["code"]),
                    "module": feature.get("module", feature["code"]),
                    "api_file": feature["api_file"],
                    "api_prefix": feature["api_prefix"],
                    "api_endpoint_count": feature["api_endpoint_count"],
                    "has_permission": 1 if feature["has_permission"] else 0,
                    "permission_count": feature["permission_count"],
                    "has_frontend": 1 if feature["has_frontend"] else 0,
                    "frontend_page_count": feature["frontend_page_count"],
                    "is_enabled": 1 if feature.get("is_enabled", True) else 0,
                    "priority": feature.get("priority", "medium"),
                },
            )

        session.commit()
        print(f"✅ 已更新 {len(features)} 个功能到功能表")


def print_report(features: List[Dict]):
    """打印扫描报告"""
    print("=" * 80)
    print("系统功能扫描报告")
    print("=" * 80)
    print()

    print(f"📊 总体统计:")
    print(f"  总功能数: {len(features)}")
    print(f"  有API端点: {sum(1 for f in features if f['api_endpoint_count'] > 0)}")
    print(f"  有权限配置: {sum(1 for f in features if f['has_permission'])}")
    print(f"  有前端页面: {sum(1 for f in features if f['has_frontend'])}")
    print()

    print(f"📋 功能清单:")
    for feature in sorted(features, key=lambda x: x["code"]):
        status = []
        if feature["api_endpoint_count"] > 0:
            status.append(f"API({feature['api_endpoint_count']})")
        if feature["has_permission"]:
            status.append(f"权限({feature['permission_count']})")
        if feature["has_frontend"]:
            status.append(f"前端({feature['frontend_page_count']})")

        status_str = ", ".join(status) if status else "无"
        print(f"  - {feature['code']:30} | {status_str}")
    print()

    # 缺失项提醒
    missing_permission = [
        f for f in features if f["api_endpoint_count"] > 0 and not f["has_permission"]
    ]
    missing_frontend = [
        f for f in features if f["api_endpoint_count"] > 0 and not f["has_frontend"]
    ]

    if missing_permission:
        print(f"⚠️  有API但无权限的功能 ({len(missing_permission)} 个):")
        for f in missing_permission:
            print(f"    - {f['code']}")
        print()

    if missing_frontend:
        print(f"⚠️  有API但无前端的功能 ({len(missing_frontend)} 个):")
        for f in missing_frontend:
            print(f"    - {f['code']}")
        print()


def main():
    print("🔍 开始扫描系统功能...")
    features = scan_all_features()

    print("\n")
    print_report(features)

    print("\n💾 更新功能表...")
    update_feature_table(features)

    print("\n✅ 扫描完成！")
    print("\n💡 提示：运行以下命令查看详细报告：")
    print("   python scripts/generate_feature_report.py")


if __name__ == "__main__":
    main()
