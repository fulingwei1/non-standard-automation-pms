#!/usr/bin/env python3
"""
Coverage Analysis Script
Analyzes coverage.json to compute coverage delta per module and identify top uncovered by fan-out.
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any


def load_coverage_json(json_path: str = "coverage.json") -> Dict[str, Any]:
    """Load coverage.json file."""
    coverage_path = Path(json_path)
    if not coverage_path.exists():
        print(
            f"Error: {json_path} not found. Run tests first: pytest --cov=app --cov-report=json"
        )
        sys.exit(1)

    with open(coverage_path) as f:
        return json.load(f)


def compute_module_coverage(coverage_data: Dict[str, Any]) -> Dict[str, Dict]:
    """
    Compute coverage per module/directory.
    Returns dict mapping module path to coverage metrics.
    """
    modules = {}

    files = coverage_data.get("files", {})
    for filename, file_data in files.items():
        # Skip non-app files
        if not filename.startswith("app/"):
            continue

        # Extract module path (e.g., services, models, api/v1/endpoints)
        parts = filename.split("/")
        if len(parts) < 2:
            continue

        # Determine module key
        if "services" in parts:
            services_idx = parts.index("services")
            if services_idx + 1 < len(parts):
                # services/module_name or services/subdir/module_name
                module_name = "/".join(parts[services_idx : services_idx + 2])
                module_key = module_name
            else:
                continue
        elif "models" in parts:
            models_idx = parts.index("models")
            module_key = (
                "models/" + parts[models_idx + 1]
                if models_idx + 1 < len(parts)
                else "models"
            )
        elif "api" in parts:
            api_idx = parts.index("api")
            if api_idx + 1 < len(parts):
                module_key = "/".join(parts[api_idx : api_idx + 2])
            else:
                module_key = "api"
        else:
            continue

        # Initialize module if not exists
        if module_key not in modules:
            modules[module_key] = {
                "files": 0,
                "lines_total": 0,
                "lines_covered": 0,
                "branches_total": 0,
                "branches_covered": 0,
            }

        # Accumulate metrics
        summary = file_data.get("summary", {})

        modules[module_key]["files"] += 1
        modules[module_key]["lines_total"] += summary.get("num_statements", 0)
        modules[module_key]["lines_covered"] += summary.get("covered_lines", 0)
        modules[module_key]["branches_total"] += summary.get("num_branches", 0)
        modules[module_key]["branches_covered"] += summary.get("covered_branches", 0)

    return modules


def compute_coverage_delta(modules: Dict[str, Dict]) -> List[Tuple]:
    """
    Compute coverage delta for each module.
    Returns sorted list by missing lines (descending).
    """
    results = []

    for module, metrics in modules.items():
        lines_total = metrics["lines_total"]
        lines_covered = metrics["lines_covered"]
        branches_total = metrics["branches_total"]
        branches_covered = metrics["branches_covered"]

        if lines_total == 0:
            continue

        line_coverage = (lines_covered / lines_total) * 100 if lines_total > 0 else 0
        branch_coverage = (
            (branches_covered / branches_total) * 100 if branches_total > 0 else 0
        )
        lines_missing = lines_total - lines_covered

        results.append(
            (
                module,
                line_coverage,
                branch_coverage,
                lines_missing,
                lines_total,
                lines_covered,
                metrics["files"],
            )
        )

    # Sort by missing lines (highest impact first)
    results.sort(key=lambda x: x[3], reverse=True)
    return results


def print_coverage_report(
    coverage_data: Dict[str, Any], modules_results: List[Tuple], limit: int = 30
):
    """Print comprehensive coverage report."""

    # Overall coverage
    totals = coverage_data.get("totals", {})

    print("\n" + "=" * 95)
    print("OVERALL COVERAGE SUMMARY")
    print("=" * 95)
    print(
        f"Line Coverage:    {totals.get('covered_lines', 0)}/{totals.get('num_statements', 0)} "
        f"({totals.get('percent_covered', 0):.2f}%)"
    )
    print(
        f"Branch Coverage: {totals.get('covered_branches', 0)}/{totals.get('num_branches', 0)} "
        f"({totals.get('percent_branches_covered', 0):.2f}%)"
    )

    # Module coverage
    print("\n" + "=" * 95)
    print(f"TOP {limit} MODULES BY MISSING LINES (HIGH PRIORITY FOR TESTING)")
    print("=" * 95)
    print(
        f"{'Module':45s} {'Files':>5s} {'Line%':>7s} {'Branch%':>9s} {'Missing':>8s} {'Total':>8s}"
    )
    print("-" * 95)

    for module, line_cov, branch_cov, missing, total, covered, files in modules_results[
        :limit
    ]:
        marker = "***" if line_cov < 10 else " .." if line_cov < 50 else "    "
        print(
            f"{marker} {module:42s} {files:5} {line_cov:6.1f}% {branch_cov:8.1f}% {missing:8} {total:8}"
        )

    print("\nLegend: *** = <10% coverage,  .. = 10-49%, (blank) = 50%+")


def print_low_coverage_details(modules_results: List[Tuple]):
    """Print detailed report for modules with <50% coverage."""
    print("\n" + "=" * 95)
    print("MODULES WITH <50% COVERAGE (NEED IMMEDIATE ATTENTION)")
    print("=" * 95)

    low_coverage = [r for r in modules_results if r[1] < 50]

    if not low_coverage:
        print("All modules have >=50% coverage! Great job!")
        return

    print(f"{'Module':45s} {'Line%':>7s} {'Branch%':>9s} {'Missing':>8s} {'Total':>8s}")
    print("-" * 95)

    for module, line_cov, branch_cov, missing, total, covered, files in low_coverage:
        print(f"{module:45s} {line_cov:6.1f}% {branch_cov:8.1f}% {missing:8} {total:8}")


def estimate_fan_out(module_name: str) -> int:
    """
    Estimate fan-out (number of dependents) based on module type.
    This is a heuristic - for accurate results, use static analysis tools.
    """
    # Core services with high fan-out
    high_fan_out = [
        "permission_service",
        "cache_service",
        "data_scope_service_v2",
        "data_sync_service",
    ]

    # Medium fan-out
    medium_fan_out = [
        "auth",
        "security",
        "models",
        "schemas",
        "api",
    ]

    # Low fan-out (feature-specific)
    low_fan_out = [
        "win_rate_prediction_service",
        "sales_prediction_service",
        "export_service",
        "import_service",
    ]

    module_lower = module_name.lower()

    for high in high_fan_out:
        if high in module_lower:
            return 5

    for medium in medium_fan_out:
        if medium in module_lower:
            return 3

    for low in low_fan_out:
        if low in module_lower:
            return 1

    return 2  # Default


def print_priority_ranking(modules_results: List[Tuple]):
    """Print modules prioritized by impact (fan-out * missing_lines)."""
    print("\n" + "=" * 95)
    print("PRIORITY RANKING (Impact = Fan-Out × Missing Lines)")
    print("=" * 95)

    ranked = []
    for module, line_cov, branch_cov, missing, total, covered, files in modules_results:
        fan_out = estimate_fan_out(module)
        impact = fan_out * missing
        ranked.append((module, fan_out, missing, impact, line_cov, total, files))

    ranked.sort(key=lambda x: x[3], reverse=True)

    print(
        f"{'Module':45s} {'Fan-Out':>8s} {'Missing':>8s} {'Impact':>8s} {'Line%':>7s}"
    )
    print("-" * 95)

    for module, fan_out, missing, impact, line_cov, total, files in ranked[:25]:
        print(f"{module:45s} {fan_out:8} {missing:8} {impact:8} {line_cov:6.1f}%")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze test coverage and identify high-priority gaps"
    )
    parser.add_argument(
        "--json-path",
        default="coverage.json",
        help="Path to coverage.json (default: coverage.json)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=30,
        help="Number of modules to show in top list (default: 30)",
    )
    parser.add_argument(
        "--full", action="store_true", help="Show all modules, not just top N"
    )
    args = parser.parse_args()

    # Load and analyze coverage
    coverage_data = load_coverage_json(args.json_path)
    modules = compute_module_coverage(coverage_data)
    modules_results = compute_coverage_delta(modules)

    # Print reports
    limit = len(modules_results) if args.full else args.limit
    print_coverage_report(coverage_data, modules_results, limit)
    print_low_coverage_details(modules_results)
    print_priority_ranking(modules_results)

    # Summary statistics
    print("\n" + "=" * 95)
    print("SUMMARY STATISTICS")
    print("=" * 95)

    total_modules = len(modules_results)
    low_coverage = sum(1 for r in modules_results if r[1] < 10)
    medium_coverage = sum(1 for r in modules_results if 10 <= r[1] < 50)
    high_coverage = sum(1 for r in modules_results if r[1] >= 50)

    print(f"Total modules analyzed: {total_modules}")
    print(
        f"  - <10% coverage:   {low_coverage} ({low_coverage / total_modules * 100:.1f}%)"
    )
    print(
        f"  - 10-49% coverage: {medium_coverage} ({medium_coverage / total_modules * 100:.1f}%)"
    )
    print(
        f"  - 50%+ coverage:   {high_coverage} ({high_coverage / total_modules * 100:.1f}%)"
    )


if __name__ == "__main__":
    main()
