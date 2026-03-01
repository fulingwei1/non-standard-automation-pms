#!/usr/bin/env python3
"""
Verification script for seed data completeness and consistency.

Usage:
    python3 scripts/verify_seed_data.py
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from sqlalchemy import MetaData, inspect, text

from seed_complete_demo_data import (
    CORE_TABLE_EXACT,
    CORE_PREFIXES,
    CheckResult,
    business_rule_checks,
    classify_module,
    count_rows,
    create_db_engine,
    fk_integrity_issues,
    is_core_table,
)

REPORT_PATH = Path("reports/verify_seed_data_report.md")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify seeded data quality and coverage.")
    parser.add_argument("--database-url", default=None, help="Override database URL")
    parser.add_argument("--report-path", default=str(REPORT_PATH), help="Markdown report output path")
    return parser.parse_args()


def write_report(
    report_path: Path,
    database_url: str,
    total_tables: int,
    table_counts: dict[str, int],
    fk_issues: list[tuple[str, str, str, str, int]],
    business_checks: list[CheckResult],
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)

    non_empty_tables = sum(1 for value in table_counts.values() if value > 0)
    non_empty_coverage = (non_empty_tables / total_tables * 100.0) if total_tables else 0.0
    core_tables = [name for name in table_counts if is_core_table(name)]
    core_non_empty = sum(1 for name in core_tables if table_counts[name] > 0)
    core_coverage = (core_non_empty / len(core_tables) * 100.0) if core_tables else 100.0
    all_checks_pass = all(item.passed for item in business_checks)

    lines: list[str] = []
    lines.append("# Seed Data Verification Report")
    lines.append("")
    lines.append(f"- Generated at: {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"- Database: `{database_url}`")
    lines.append(f"- Total tables: **{total_tables}**")
    lines.append(f"- Non-empty tables: **{non_empty_tables}** ({non_empty_coverage:.2f}%)")
    lines.append(f"- Core tables configured: **{len(core_tables)}**")
    lines.append(f"- Core non-empty: **{core_non_empty}** ({core_coverage:.2f}%)")
    lines.append("")
    lines.append("## Criteria Status")
    lines.append("")
    lines.append(
        f"- {'PASS' if non_empty_coverage >= 95.0 else 'FAIL'} 95%+ tables non-empty "
        f"({non_empty_coverage:.2f}%)"
    )
    lines.append(
        f"- {'PASS' if core_coverage >= 100.0 else 'FAIL'} core tables 100% non-empty "
        f"({core_non_empty}/{len(core_tables)})"
    )
    lines.append(f"- {'PASS' if not fk_issues else 'FAIL'} no FK orphan records (issues: {len(fk_issues)})")
    lines.append(
        f"- {'PASS' if all_checks_pass else 'FAIL'} business logic checks "
        f"({sum(1 for item in business_checks if item.passed)}/{len(business_checks)})"
    )
    lines.append("")

    lines.append("## FK Integrity")
    lines.append("")
    if fk_issues:
        lines.append("| Child Table | Child Column | Parent Table | Parent Column | Orphans |")
        lines.append("| --- | --- | --- | --- | ---: |")
        for table_name, child_col, parent_table, parent_col, orphan_count in fk_issues[:300]:
            lines.append(f"| {table_name} | {child_col} | {parent_table} | {parent_col} | {orphan_count} |")
        if len(fk_issues) > 300:
            lines.append("")
            lines.append(f"- (truncated, total issues: {len(fk_issues)})")
    else:
        lines.append("- No FK issues found.")
    lines.append("")

    lines.append("## Business Checks")
    lines.append("")
    for check in business_checks:
        mark = "PASS" if check.passed else "FAIL"
        lines.append(f"- [{mark}] `{check.name}` - {check.detail}")
    lines.append("")

    lines.append("## Table Counts")
    lines.append("")
    lines.append("| Module | Table | Rows |")
    lines.append("| --- | --- | ---: |")
    for table_name in sorted(table_counts):
        module = classify_module(table_name)
        lines.append(f"| {module} | {table_name} | {table_counts[table_name]} |")
    lines.append("")

    lines.append("## Core Table Rules")
    lines.append("")
    lines.append(f"- Exact core table names configured: {len(CORE_TABLE_EXACT)}")
    lines.append(f"- Core prefixes configured: {', '.join(CORE_PREFIXES)}")

    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    engine = create_db_engine(args.database_url)
    report_path = Path(args.report_path)

    metadata = MetaData()
    metadata.reflect(bind=engine)
    tables_by_name = dict(metadata.tables)
    table_names = sorted(tables_by_name.keys())
    inspector_obj = inspect(engine)

    with engine.connect() as conn:
        if str(engine.url).startswith("sqlite"):
            conn.execute(text("PRAGMA foreign_keys = ON"))
            conn.commit()

        table_counts = {name: count_rows(conn, table_obj) for name, table_obj in tables_by_name.items()}
        fk_issues = fk_integrity_issues(conn, inspector_obj, table_names)
        checks = business_rule_checks(conn, tables_by_name)

    total_tables = len(table_counts)
    non_empty_tables = sum(1 for value in table_counts.values() if value > 0)
    coverage = (non_empty_tables / total_tables * 100.0) if total_tables else 0.0
    core_tables = [name for name in table_counts if is_core_table(name)]
    core_non_empty = sum(1 for name in core_tables if table_counts[name] > 0)
    core_coverage = (core_non_empty / len(core_tables) * 100.0) if core_tables else 100.0
    passed_checks = sum(1 for item in checks if item.passed)

    write_report(
        report_path=report_path,
        database_url=str(engine.url),
        total_tables=total_tables,
        table_counts=table_counts,
        fk_issues=fk_issues,
        business_checks=checks,
    )

    print("=" * 72)
    print("Seed verification complete")
    print("=" * 72)
    print(f"database: {engine.url}")
    print(f"total tables: {total_tables}")
    print(f"non-empty tables: {non_empty_tables} ({coverage:.2f}%)")
    print(f"core tables non-empty: {core_non_empty}/{len(core_tables)} ({core_coverage:.2f}%)")
    print(f"fk issues: {len(fk_issues)}")
    print(f"business checks: {passed_checks}/{len(checks)} passed")
    print(f"report: {report_path}")

    if coverage < 95.0 or core_coverage < 100.0 or fk_issues or passed_checks < len(checks):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
