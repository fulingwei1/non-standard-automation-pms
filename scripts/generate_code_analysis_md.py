#!/usr/bin/env python3
"""
生成代码质量分析报告（Markdown）。

相比 `scripts/generate_code_analysis_pdf.py` 的硬编码版本，本脚本会动态扫描仓库代码文件，
输出当前最新的统计信息与大文件清单。
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


CODE_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx"}
PAGE_EXTS = {".jsx", ".tsx"}

# 常见非源码目录（会被递归跳过）
EXCLUDED_DIR_NAMES = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "htmlcov",
    "coverage",
    ".next",
}


@dataclass(frozen=True)
class FileStat:
    rel_path: str
    lines: int


def count_newlines(path: Path) -> int:
    """Count lines using wc -l semantics (counts '\\n')."""
    newline_count = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            newline_count += chunk.count(b"\n")
    return newline_count


def iter_code_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIR_NAMES]
        for filename in filenames:
            path = Path(dirpath) / filename
            if path.suffix.lower() not in CODE_EXTS:
                continue
            yield path


def md_escape(cell: str) -> str:
    return cell.replace("|", "\\|")


def md_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    header = rows[0]
    out = [
        "| " + " | ".join(md_escape(h) for h in header) + " |",
        "| " + " | ".join(["---"] * len(header)) + " |",
    ]
    for row in rows[1:]:
        out.append("| " + " | ".join(md_escape(c) for c in row) + " |")
    return "\n".join(out)


def describe_file(rel_path: str) -> str:
    if rel_path == "app/utils/scheduled_tasks.py":
        return "定时任务全堆一个文件"
    if rel_path == "frontend/src/services/api.js":
        return "API 调用全集中"
    if rel_path.startswith("frontend/src/pages/"):
        filename = Path(rel_path).name
        if "Dashboard" in filename:
            return "仪表板功能过多"
        if "Detail" in filename:
            return "详情页组件过大"
        if "Management" in filename:
            return "管理页面臃肿"
        return "单页面组件过大"
    if rel_path.startswith("app/api/v1/endpoints/"):
        return "端点模块过大"
    if rel_path.startswith("app/services/"):
        return "业务服务逻辑过于集中"
    if rel_path.startswith("app/schemas/"):
        return "Schema 臃肿"
    return "文件过大，建议拆分"


def format_int(value: int) -> str:
    return f"{value:,}"


def build_report(root: Path, file_stats: list[FileStat]) -> str:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    total_lines = sum(s.lines for s in file_stats)

    pages_count = sum(
        1
        for s in file_stats
        if s.rel_path.startswith("frontend/src/pages/")
        and Path(s.rel_path).suffix.lower() in PAGE_EXTS
    )
    models_count = sum(
        1
        for s in file_stats
        if s.rel_path.startswith("app/models/") and s.rel_path.endswith(".py")
    )
    endpoints_count = sum(
        1
        for s in file_stats
        if s.rel_path.startswith("app/api/v1/endpoints/") and s.rel_path.endswith(".py")
    )
    services_count = sum(
        1
        for s in file_stats
        if s.rel_path.startswith("app/services/") and s.rel_path.endswith(".py")
    )

    critical = sorted([s for s in file_stats if s.lines > 2000], key=lambda s: s.lines, reverse=True)
    warning = sorted(
        [s for s in file_stats if 1500 <= s.lines <= 2000],
        key=lambda s: s.lines,
        reverse=True,
    )

    # Derived signals for analysis section
    large_pages = [s for s in file_stats if s.rel_path.startswith("frontend/src/pages/") and s.lines >= 1500]
    large_endpoints = [s for s in file_stats if s.rel_path.startswith("app/api/v1/endpoints/") and s.lines >= 1500]
    schema_candidates = [s for s in file_stats if s.rel_path.startswith("app/schemas/") and s.lines >= 1000]
    api_js = next((s for s in file_stats if s.rel_path == "frontend/src/services/api.js"), None)

    overview_rows = [
        ["类别", "数量", "说明"],
        ["前端页面 (Pages)", str(pages_count), "frontend/src/pages/*.(jsx|tsx)"],
        ["后端模型 (Models)", str(models_count), "app/models/*.py"],
        ["API 端点模块", str(endpoints_count), "app/api/v1/endpoints/**/*.py"],
        ["业务服务 (Services)", str(services_count), "app/services/*.py"],
        ["总代码行数", format_int(total_lines), "包含 .py/.js/.jsx/.ts/.tsx"],
    ]

    critical_rows = [["文件路径", "行数", "问题描述"]]
    for s in critical:
        critical_rows.append([s.rel_path, str(s.lines), describe_file(s.rel_path)])

    warning_rows = [["文件路径", "行数"]]
    for s in warning:
        warning_rows.append([s.rel_path, str(s.lines)])

    # Priority suggestions (keep it short & actionable)
    priority_rows = [["优先级", "文件", "建议方案"]]
    scheduled_tasks = next((s for s in file_stats if s.rel_path == "app/utils/scheduled_tasks.py"), None)
    if scheduled_tasks:
        priority_rows.append(["P0", scheduled_tasks.rel_path, "按任务类型拆分多个模块（并引入统一入口/注册表）"])
    if api_js:
        priority_rows.append(["P0", api_js.rel_path, "按业务域拆分（project/、sales/、hr/、ecn/…），避免单文件膨胀"])

    for s in sorted(
        [x for x in critical if x.rel_path.startswith("frontend/src/pages/")],
        key=lambda x: x.lines,
        reverse=True,
    )[:2]:
        priority_rows.append(["P1", s.rel_path, "抽离 Tab/表格/对话框/常量与 hooks；将数据请求下沉到 service/hook"])

    for s in sorted(
        [x for x in critical if x.rel_path.startswith("app/api/v1/endpoints/")],
        key=lambda x: x.lines,
        reverse=True,
    )[:2]:
        priority_rows.append(["P2", s.rel_path, "按子资源/子流程拆分路由模块；复用依赖/校验/响应构建函数"])

    for s in sorted(schema_candidates, key=lambda x: x.lines, reverse=True)[:1]:
        priority_rows.append(["P2", s.rel_path, "按领域拆分 schema；移除重复结构与超大单文件"])

    parts: list[str] = []
    parts.append("# 代码质量分析报告")
    parts.append("")
    parts.append("非标自动化项目管理系统")
    parts.append("")
    parts.append(f"> 生成时间: {now_str}")
    parts.append("")
    parts.append("## 1. 项目规模统计")
    parts.append("")
    parts.append(md_table(overview_rows))
    parts.append("")

    parts.append("## 2. 严重超标文件 (>2000 行)")
    parts.append("")
    if len(critical) == 0:
        parts.append("当前未发现行数超过 2000 的单文件。")
    else:
        parts.append(md_table(critical_rows))
    parts.append("")

    parts.append("## 3. 需要关注的文件 (1500-2000 行)")
    parts.append("")
    if len(warning) == 0:
        parts.append("当前未发现行数介于 1500-2000 的单文件。")
    else:
        parts.append(md_table(warning_rows))
    parts.append("")

    parts.append("## 4. 问题分析")
    parts.append("")
    parts.append(f"- 上帝组件倾向：前端 pages ≥1500 行的文件 {len(large_pages)} 个；后端 endpoints ≥1500 行的文件 {len(large_endpoints)} 个")
    if api_js:
        parts.append(f"- API 集中化：`{api_js.rel_path}` 目前为 {api_js.lines} 行，建议按业务域拆分")
    if schema_candidates:
        top_schema = sorted(schema_candidates, key=lambda x: x.lines, reverse=True)[0]
        parts.append(f"- Schema 臃肿：`{top_schema.rel_path}` 为 {top_schema.lines} 行，建议按领域拆分")
    parts.append("- 建议优先用 `selectinload/joinedload` 解决 N+1，并用 `func.count/sum` 将聚合统计下推到数据库")
    parts.append("")

    parts.append("## 5. 重构优先级建议")
    parts.append("")
    parts.append(md_table(priority_rows))
    parts.append("")

    parts.append("## 6. 后端核心模块概览（参考）")
    parts.append("")
    parts.append(md_table([
        ["模块", "文件（示例）", "说明"],
        ["项目管理", "project.py, machine.py", "项目与设备管理"],
        ["物料采购", "material.py, purchase.py", "物料采购与 BOM"],
        ["工程变更", "ecn.py", "工程变更通知 ECN"],
        ["验收管理", "acceptance.py", "FAT/SAT 验收"],
        ["外协管理", "outsourcing.py, supplier.py", "外协与供应商"],
        ["销售管理", "sales.py, presale.py", "销售与售前"],
        ["生产进度", "production.py, progress.py", "生产与进度跟踪"],
        ["组织人员", "user.py, organization.py", "用户与组织架构"],
        ["预警通知", "alert.py, notification.py", "预警与通知"],
        ["绩效工时", "performance.py, timesheet.py", "绩效与工时管理"],
    ]))
    parts.append("")

    parts.append("## 生成方式")
    parts.append("")
    parts.append("在项目根目录执行：")
    parts.append("")
    parts.append("```bash")
    parts.append("python3 scripts/generate_code_analysis_md.py")
    parts.append("```")
    parts.append("")

    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate code analysis report (Markdown).")
    parser.add_argument(
        "--root",
        default=None,
        help="Repository root (default: auto-detect from script location).",
    )
    parser.add_argument(
        "--output",
        default="docs/代码质量分析报告.md",
        help="Output markdown path (relative to root).",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    output = root / args.output

    file_stats: list[FileStat] = []
    for path in iter_code_files(root):
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            continue
        try:
            lines = count_newlines(path)
        except OSError:
            continue
        file_stats.append(FileStat(rel_path=rel, lines=lines))

    report = build_report(root, file_stats)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(f"Wrote: {output.relative_to(root).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

