#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成系统功能状态报告
- 从功能表读取数据
- 生成Markdown报告
- 显示功能完整度
"""

import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.models.base import get_db_session

REPORT_FILE = Path(__file__).parent.parent / "docs" / "SYSTEM_FEATURES_REPORT.md"


def generate_report():
    """生成功能状态报告"""
    with get_db_session() as session:
        # 检查表是否存在
        try:
            result = session.execute(text("SELECT 1 FROM system_features LIMIT 1"))
        except Exception:
            print("❌ 功能表不存在，请先运行 scan_system_features.py")
            return

        # 获取所有功能
        result = session.execute(
            text(
                """
            SELECT
                feature_code, feature_name, module,
                api_file, api_prefix,
                api_endpoint_count, has_permission, permission_count,
                has_frontend, frontend_page_count,
                is_enabled, priority
            FROM system_features
            ORDER BY module, feature_code
        """
            )
        )

        features = []
        for row in result:
            features.append(
                {
                    "code": row[0],
                    "name": row[1],
                    "module": row[2],
                    "api_file": row[3],
                    "api_prefix": row[4],
                    "api_endpoint_count": row[5] or 0,
                    "has_permission": bool(row[6]),
                    "permission_count": row[7] or 0,
                    "has_frontend": bool(row[8]),
                    "frontend_page_count": row[9] or 0,
                    "is_enabled": bool(row[10]),
                    "priority": row[11] or "medium",
                }
            )

        # 统计
        total = len(features)
        with_api = sum(1 for f in features if f["api_endpoint_count"] > 0)
        with_permission = sum(1 for f in features if f["has_permission"])
        with_frontend = sum(1 for f in features if f["has_frontend"])
        enabled = sum(1 for f in features if f["is_enabled"])

        # 按模块分组
        by_module = {}
        for feature in features:
            module = feature["module"] or "未分类"
            if module not in by_module:
                by_module[module] = []
            by_module[module].append(feature)

        # 生成报告
        report = f"""# 系统功能状态报告

> 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> 数据来源：`system_features` 表

## 📊 总体统计

| 指标 | 数量 | 占比 |
|------|------|------|
| **总功能数** | {total} | 100% |
| **有API端点** | {with_api} | {with_api / total * 100:.1f}% |
| **有权限配置** | {with_permission} | {with_permission / total * 100:.1f}% |
| **有前端页面** | {with_frontend} | {with_frontend / total * 100:.1f}% |
| **已启用** | {enabled} | {enabled / total * 100:.1f}% |

---

## 📋 功能清单（按模块分组）

"""

        for module in sorted(by_module.keys()):
            module_features = by_module[module]
            report += f"### {module} ({len(module_features)} 个功能)\n\n"
            report += "| 功能编码 | 功能名称 | API端点 | 权限 | 前端 | 状态 |\n"
            report += "|---------|---------|--------|------|------|------|\n"

            for f in sorted(module_features, key=lambda x: x["code"]):
                api_status = (
                    f"✅ {f['api_endpoint_count']}" if f["api_endpoint_count"] > 0 else "❌ 0"
                )
                perm_status = f"✅ {f['permission_count']}" if f["has_permission"] else "❌ 无"
                frontend_status = f"✅ {f['frontend_page_count']}" if f["has_frontend"] else "❌ 无"
                enabled_status = "✅ 启用" if f["is_enabled"] else "❌ 禁用"

                report += f"| `{f['code']}` | {f['name']} | {api_status} | {perm_status} | {frontend_status} | {enabled_status} |\n"

            report += "\n"

        # 缺失项提醒
        missing_permission = [
            f for f in features if f["api_endpoint_count"] > 0 and not f["has_permission"]
        ]
        missing_frontend = [
            f for f in features if f["api_endpoint_count"] > 0 and not f["has_frontend"]
        ]
        disabled = [f for f in features if not f["is_enabled"]]

        report += "---\n\n"
        report += "## ⚠️ 缺失项提醒\n\n"

        if missing_permission:
            report += f"### 有API但无权限的功能 ({len(missing_permission)} 个)\n\n"
            for f in missing_permission:
                report += f"- `{f['code']}` - {f['name']} ({f['api_endpoint_count']} 个端点)\n"
            report += "\n"

        if missing_frontend:
            report += f"### 有API但无前端的功能 ({len(missing_frontend)} 个)\n\n"
            for f in missing_frontend:
                report += f"- `{f['code']}` - {f['name']} ({f['api_endpoint_count']} 个端点)\n"
            report += "\n"

        if disabled:
            report += f"### 已禁用的功能 ({len(disabled)} 个)\n\n"
            for f in disabled:
                report += f"- `{f['code']}` - {f['name']}\n"
            report += "\n"

        # 保存报告
        REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
        REPORT_FILE.write_text(report, encoding="utf-8")

        print(f"✅ 报告已生成：{REPORT_FILE}")
        print(f"\n📊 统计：")
        print(f"  总功能数: {total}")
        print(f"  有API: {with_api}")
        print(f"  有权限: {with_permission}")
        print(f"  有前端: {with_frontend}")
        if missing_permission:
            print(f"  ⚠️  缺失权限: {len(missing_permission)}")
        if missing_frontend:
            print(f"  ⚠️  缺失前端: {len(missing_frontend)}")


if __name__ == "__main__":
    generate_report()
