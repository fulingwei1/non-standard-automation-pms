#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能分析和优化脚本
"""

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps


def analyze_database_performance() -> Dict[str, Any]:
    """分析数据库性能"""
    db = next(deps.get_db())

    results = {}

    try:
        # 1. 分析大表
        large_tables = db.execute(
            text(
                """
            SELECT
                schemaname,
                tablename,
                attname,
                n_distinct,
                correlation
            FROM pg_stats
            WHERE schemaname = 'public'
            ORDER BY tablename, attname;
        """
            )
        ).fetchall()

        results["large_tables"] = large_tables[:20]  # 取前20个最大的表

        # 2. 分析慢查询（如果有）
        slow_queries = (
            db.execute(
                text(
                    """
            SELECT query, mean_time, calls, total_time
            FROM pg_stat_statements
            ORDER BY mean_time DESC
            LIMIT 10;
        """
                )
            ).fetchall()
            if has_pg_stat_statements(db)
            else []
        )

        results["slow_queries"] = slow_queries

        # 3. 分析索引使用情况
        index_usage = db.execute(
            text(
                """
            SELECT
                schemaname,
                tablename,
                indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes
            ORDER BY idx_scan DESC;
        """
            )
        ).fetchall()

        results["index_usage"] = index_usage

        # 4. 检查缺失的索引
        missing_indexes = db.execute(
            text(
                """
            SELECT
                schemaname,
                tablename,
                attname,
                n_distinct,
                correlation
            FROM pg_stats
            WHERE schemaname = 'public'
              AND tablename IN ('project', 'issue', 'alert_record', 'shortage_report')
              AND attname NOT IN ('id', 'created_at', 'updated_at')
            ORDER BY n_distinct DESC;
        """
            )
        ).fetchall()

        results["missing_indexes"] = missing_indexes

    except Exception as e:
        results["error"] = str(e)
    finally:
        db.close()

    return results


def has_pg_stat_statements(db: Session) -> bool:
    """检查是否有pg_stat_statements扩展"""
    try:
        db.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'"))
        return True
    except Exception:
        return False


def analyze_code_complexity() -> Dict[str, Any]:
    """分析代码复杂度"""
    results = {}

    # 分析大型文件
    app_dir = project_root / "app"

    large_files = []
    for file_path in app_dir.rglob("*.py"):
        if "migrations" in str(file_path):
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = len(f.readlines())
                if lines > 300:  # 大于300行的文件
                    large_files.append(
                        {
                            "file": str(file_path.relative_to(project_root)),
                            "lines": lines,
                            "size_mb": os.path.getsize(file_path) / 1024 / 1024,
                        }
                    )
        except (OSError, UnicodeDecodeError):
            pass

    results["large_files"] = sorted(large_files, key=lambda x: x["lines"], reverse=True)[:20]

    # 分析函数复杂度
    complex_functions = []
    for file_path in app_dir.rglob("*.py"):
        if "migrations" in str(file_path):
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

                for i, line in enumerate(lines):
                    if "def " in line and ":" in line:
                        # 简单计算函数行数
                        func_lines = 0
                        indent_level = len(line) - len(line.lstrip())

                        for j in range(i + 1, len(lines)):
                            if lines[j].strip() == "":
                                continue
                            current_indent = len(lines[j]) - len(lines[j].lstrip())
                            if current_indent <= indent_level and lines[j].strip():
                                break
                            func_lines += 1

                        if func_lines > 50:  # 超过50行的函数
                            complex_functions.append(
                                {
                                    "file": str(file_path.relative_to(project_root)),
                                    "function": line.strip(),
                                    "line_number": i + 1,
                                    "complexity_lines": func_lines,
                                }
                            )
        except (OSError, UnicodeDecodeError, IndexError):
            pass

    results["complex_functions"] = sorted(
        complex_functions, key=lambda x: x["complexity_lines"], reverse=True
    )[:15]

    return results


def generate_performance_report() -> str:
    """生成性能报告"""
    report = []
    report.append("# 📊 代码质量和性能分析报告")
    report.append(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")

    # 数据库性能分析
    db_results = analyze_database_performance()
    report.append("## 🗄️ 数据库性能分析")

    if "large_tables" in db_results:
        report.append("### 📋 大型表统计")
        report.append("| 表名 | 字段 | 唯一值数 | 相关性 |")
        report.append("|------|------|----------|--------|")
        for table in db_results["large_tables"][:10]:
            report.append(
                f"| {table.tablename} | {table.attname} | {table.n_distinct} | {table.correlation:.2f} |"
            )
        report.append("")

    if "slow_queries" in db_results:
        report.append("### 🐌 慢查询分析")
        if db_results["slow_queries"]:
            report.append("| 查询 | 平均时间(ms) | 调用次数 | 总时间(ms) |")
            report.append("|------|---------------|----------|------------|")
            for query in db_results["slow_queries"]:
                report.append(
                    f"| `{query.query[:50]}...` | {query.mean_time:.2f} | {query.calls} | {query.total_time:.2f} |"
                )
        else:
            report.append("✅ 未发现明显的慢查询")
        report.append("")

    # 代码复杂度分析
    code_results = analyze_code_complexity()
    report.append("## 💻 代码复杂度分析")

    report.append("### 📏 大型文件 (>300行)")
    report.append("| 文件 | 行数 | 大小(MB) |")
    report.append("|------|------|----------|")
    for file_info in code_results["large_files"][:10]:
        report.append(
            f"| {file_info['file']} | {file_info['lines']} | {file_info['size_mb']:.2f} |"
        )
    report.append("")

    report.append("### 🔧 复杂函数 (>50行)")
    report.append("| 文件 | 函数 | 行号 | 复杂度 |")
    report.append("|------|------|------|--------|")
    for func_info in code_results["complex_functions"][:10]:
        report.append(
            f"| {func_info['file']} | {func_info['function']} | {func_info['line_number']} | {func_info['complexity_lines']} |"
        )
    report.append("")

    # 优化建议
    report.append("## 🚀 优化建议")
    report.append("")
    report.append("### 📈 性能优化")
    report.append("1. **数据库优化**:")
    report.append("   - 为常用查询字段添加索引")
    report.append("   - 优化复杂查询，避免N+1问题")
    report.append("   - 考虑读写分离和缓存")
    report.append("")
    report.append("2. **代码优化**:")
    report.append("   - 拆分大型函数，提高可读性")
    report.append("   - 提取重复代码到公共模块")
    report.append("   - 使用异步处理提升响应速度")
    report.append("")

    report.append("### 🛡️ 安全优化")
    report.append("1. **输入验证**:")
    report.append("   - 加强API参数验证")
    report.append("   - 防止SQL注入攻击")
    report.append("   - 添加请求频率限制")
    report.append("")

    report.append("2. **数据保护**:")
    report.append("   - 敏感数据加密存储")
    report.append("   - 实施访问控制")
    report.append("   - 定期安全审计")
    report.append("")

    return "\n".join(report)


def main():
    """主函数"""
    print("🔍 开始性能分析...")

    try:
        # 生成报告
        report = generate_performance_report()

        # 保存报告
        report_path = project_root / "performance_analysis_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"✅ 性能分析报告已生成: {report_path}")

        # 输出关键指标
        print("\n📊 关键指标:")
        code_results = analyze_code_complexity()
        print(f"- 大型文件数量: {len(code_results['large_files'])}")
        print(f"- 复杂函数数量: {len(code_results['complex_functions'])}")

        if code_results["large_files"]:
            max_file = max(code_results["large_files"], key=lambda x: x["lines"])
            print(f"- 最大文件: {max_file['file']} ({max_file['lines']}行)")

        if code_results["complex_functions"]:
            max_func = max(code_results["complex_functions"], key=lambda x: x["complexity_lines"])
            print(f"- 最复杂函数: {max_func['function']} ({max_func['complexity_lines']}行)")

    except Exception as e:
        print(f"❌ 分析失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
