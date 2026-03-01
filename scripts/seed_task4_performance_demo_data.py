#!/usr/bin/env python3
"""
任务 4/6：生成绩效评价演示数据

目标：
1. 部门绩效（hr_project_performance）10 个部门
2. 个人绩效（performance_evaluation_record）150 人，周期 2026-Q1
3. 绩效指标覆盖：财务 / 客户 / 内部流程 / 学习成长
4. 公司总人数补齐到 190（users / employees）
"""

from __future__ import annotations

import json
import random
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


RNG_SEED = 20260301
TARGET_COMPANY_SIZE = 190
EVALUATION_COUNT = 150
PERIOD = "2026-Q1"
SUMMARY_PREFIX = "[TASK4-2026Q1]"
ROLE_CODE_PREFIX = "TASK4-DEPT-"
USER_PREFIX = "t4_2026q1_"
EMP_PREFIX = "T4E260"

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "app.db"
REPORT_PATH = ROOT_DIR / "reports" / "task4_performance_demo_summary_2026Q1.md"


@dataclass(frozen=True)
class DepartmentConfig:
    name: str
    dept_code: str
    role_name: str
    headcount_weight: int
    actual_range: tuple[float, float]
    coeff_range: tuple[float, float]


DEPARTMENTS: list[DepartmentConfig] = [
    DepartmentConfig("研发中心", "PERF_RD", "研发工程师", 18, (91.0, 98.0), (1.12, 1.25)),
    DepartmentConfig("生产中心", "PERF_PD", "生产管理", 16, (84.0, 93.0), (0.98, 1.12)),
    DepartmentConfig("销售部", "PERF_SL", "销售经理", 15, (88.0, 97.0), (1.08, 1.23)),
    DepartmentConfig("采购部", "PERF_PR", "采购专员", 10, (78.0, 88.0), (0.90, 1.05)),
    DepartmentConfig("质量部", "PERF_QA", "质量工程师", 10, (86.0, 95.0), (1.02, 1.16)),
    DepartmentConfig("售后服务", "PERF_AS", "售后工程师", 9, (80.0, 90.0), (0.93, 1.08)),
    DepartmentConfig("财务部", "PERF_FN", "财务主管", 8, (82.0, 92.0), (0.96, 1.12)),
    DepartmentConfig("人力资源部", "PERF_HR", "HRBP", 6, (76.0, 87.0), (0.88, 1.04)),
    DepartmentConfig("行政部", "PERF_AD", "行政专员", 4, (75.0, 85.0), (0.85, 1.00)),
    DepartmentConfig("管理层", "PERF_MG", "管理层", 4, (92.0, 98.0), (1.15, 1.25)),
]


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def sample_truncated_gauss(
    rng: random.Random, mean: float, std: float, low: float, high: float
) -> float:
    for _ in range(100):
        value = rng.gauss(mean, std)
        if low <= value <= high:
            return value
    return clamp(mean, low, high)


def allocate_counts(total: int, weights: list[int]) -> list[int]:
    weight_sum = sum(weights)
    base = [int(total * w / weight_sum) for w in weights]
    remainder = total - sum(base)
    remainders = [
        (idx, (total * w / weight_sum) - base[idx]) for idx, w in enumerate(weights)
    ]
    remainders.sort(key=lambda x: x[1], reverse=True)
    for idx, _ in remainders[:remainder]:
        base[idx] += 1
    return base


def ensure_departments(
    conn: sqlite3.Connection, timestamp: str
) -> dict[str, dict[str, Any]]:
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(id), 0) FROM departments")
    max_dept_id = int(cur.fetchone()[0])

    dept_map: dict[str, dict[str, Any]] = {}
    for config in DEPARTMENTS:
        cur.execute(
            "SELECT id, dept_code FROM departments WHERE dept_code = ? LIMIT 1",
            (config.dept_code,),
        )
        row = cur.fetchone()
        if row:
            dept_id = int(row[0])
        else:
            max_dept_id += 1
            dept_id = max_dept_id
            cur.execute(
                """
                INSERT INTO departments
                    (id, dept_code, dept_name, parent_id, manager_id, level, sort_order, is_active, created_at, updated_at)
                VALUES
                    (?, ?, ?, NULL, NULL, 1, ?, 1, ?, ?)
                """,
                (dept_id, config.dept_code, config.name, dept_id, timestamp, timestamp),
            )
        dept_map[config.name] = {
            "id": dept_id,
            "dept_code": config.dept_code,
            "config": config,
        }
    return dept_map


def get_password_hash(conn: sqlite3.Connection) -> str:
    cur = conn.cursor()
    cur.execute(
        "SELECT password_hash FROM users WHERE password_hash IS NOT NULL ORDER BY id LIMIT 1"
    )
    row = cur.fetchone()
    if row and row[0]:
        return str(row[0])
    return "demo_password_hash_task4"


def create_employees_and_users(
    conn: sqlite3.Connection,
    dept_map: dict[str, dict[str, Any]],
    rng: random.Random,
    timestamp: str,
) -> dict[str, Any]:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    current_users = int(cur.fetchone()[0])
    need_create = max(0, TARGET_COMPANY_SIZE - current_users)

    cur.execute("SELECT COALESCE(MAX(id), 0) FROM employees")
    max_emp_id = int(cur.fetchone()[0])
    cur.execute("SELECT COALESCE(MAX(id), 0) FROM users")
    max_user_id = int(cur.fetchone()[0])
    password_hash = get_password_hash(conn)

    dept_names = [config.name for config in DEPARTMENTS]
    weights = [config.headcount_weight for config in DEPARTMENTS]
    created_user_ids: list[int] = []

    for i in range(need_create):
        dept_name = rng.choices(dept_names, weights=weights, k=1)[0]
        config = dept_map[dept_name]["config"]
        dept_id = int(dept_map[dept_name]["id"])
        max_emp_id += 1
        max_user_id += 1

        employee_code = f"{EMP_PREFIX}{max_emp_id:04d}"
        username = f"{USER_PREFIX}{max_user_id:04d}"
        email = f"{username}@demo.local"
        real_name = f"绩效员工{max_user_id:03d}"

        cur.execute(
            """
            INSERT INTO employees
                (id, employee_code, name, department, role, is_active, created_at, updated_at)
            VALUES
                (?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (
                max_emp_id,
                employee_code,
                real_name,
                dept_name,
                config.role_name,
                timestamp,
                timestamp,
            ),
        )

        cur.execute(
            """
            INSERT INTO users
                (id, employee_id, username, password_hash, email, real_name, department, position, department_id,
                 is_active, is_superuser, solution_credits, created_at, updated_at)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, 0, ?, ?)
            """,
            (
                max_user_id,
                max_emp_id,
                username,
                password_hash,
                email,
                real_name,
                dept_name,
                config.role_name,
                dept_id,
                timestamp,
                timestamp,
            ),
        )
        created_user_ids.append(max_user_id)

    cur.execute("SELECT COUNT(*) FROM users")
    final_users = int(cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM employees")
    final_employees = int(cur.fetchone()[0])

    return {
        "created_count": need_create,
        "created_user_ids": created_user_ids,
        "final_users": final_users,
        "final_employees": final_employees,
    }


def clean_previous_task4_data(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM monthly_work_summary WHERE period = ? AND work_content LIKE ?",
        (PERIOD, f"{SUMMARY_PREFIX}%"),
    )
    summary_ids = [int(row[0]) for row in cur.fetchall()]

    if summary_ids:
        placeholders = ",".join("?" * len(summary_ids))
        cur.execute(
            f"DELETE FROM performance_evaluation_record WHERE summary_id IN ({placeholders})",
            summary_ids,
        )
        cur.execute(
            f"DELETE FROM monthly_work_summary WHERE id IN ({placeholders})", summary_ids
        )

    cur.execute(
        "DELETE FROM hr_project_performance WHERE role_code LIKE ?",
        (f"{ROLE_CODE_PREFIX}%",),
    )


def fetch_project_ids(conn: sqlite3.Connection) -> list[int]:
    cur = conn.cursor()
    cur.execute("SELECT id FROM projects ORDER BY id")
    return [int(row[0]) for row in cur.fetchall()]


def build_evaluation_user_pool(
    conn: sqlite3.Connection, required_count: int
) -> list[dict[str, Any]]:
    cur = conn.cursor()
    selected_ids: list[int] = []

    cur.execute(
        "SELECT id FROM users WHERE username LIKE ? ORDER BY id",
        (f"{USER_PREFIX}%",),
    )
    selected_ids.extend(int(row[0]) for row in cur.fetchall())

    remaining = required_count - len(selected_ids)
    if remaining > 0:
        cur.execute(
            """
            SELECT id
            FROM users
            WHERE id NOT IN ({})
              AND COALESCE(is_active, 1) = 1
              AND real_name IS NOT NULL
            ORDER BY id
            LIMIT ?
            """.format(",".join("?" * len(selected_ids)) if selected_ids else "SELECT 0"),
            (*selected_ids, remaining) if selected_ids else (remaining,),
        )
        selected_ids.extend(int(row[0]) for row in cur.fetchall())

    remaining = required_count - len(selected_ids)
    if remaining > 0:
        cur.execute(
            """
            SELECT id
            FROM users
            WHERE id NOT IN ({})
            ORDER BY id
            LIMIT ?
            """.format(",".join("?" * len(selected_ids)) if selected_ids else "SELECT 0"),
            (*selected_ids, remaining) if selected_ids else (remaining,),
        )
        selected_ids.extend(int(row[0]) for row in cur.fetchall())

    selected_ids = selected_ids[:required_count]
    if len(selected_ids) < required_count:
        raise RuntimeError(
            f"可用用户不足，期望 {required_count} 人，实际 {len(selected_ids)} 人。"
        )

    placeholders = ",".join("?" * len(selected_ids))
    cur.execute(
        f"""
        SELECT
            u.id,
            u.employee_id,
            COALESCE(u.real_name, e.name, '员工' || u.id) AS real_name,
            COALESCE(u.department, e.department, '') AS dept_name
        FROM users u
        LEFT JOIN employees e ON e.id = u.employee_id
        WHERE u.id IN ({placeholders})
        """,
        selected_ids,
    )

    rows = cur.fetchall()
    row_map = {int(row[0]): row for row in rows}
    result = []
    for user_id in selected_ids:
        row = row_map[user_id]
        result.append(
            {
                "user_id": int(row[0]),
                "employee_id": int(row[1]) if row[1] is not None else None,
                "name": str(row[2]),
                "dept_name": str(row[3]) if row[3] is not None else "",
            }
        )
    return result


def build_department_performance(
    conn: sqlite3.Connection,
    dept_map: dict[str, dict[str, Any]],
    rng: random.Random,
    timestamp: str,
) -> list[dict[str, Any]]:
    cur = conn.cursor()
    project_ids = fetch_project_ids(conn)
    if len(project_ids) < len(DEPARTMENTS):
        raise RuntimeError("项目数量不足，无法为 10 个部门创建绩效数据。")

    cur.execute("SELECT COALESCE(MAX(id), 0) FROM hr_project_performance")
    perf_id = int(cur.fetchone()[0])

    evaluator_id = 1
    cur.execute("SELECT 1 FROM users WHERE id = 1")
    if not cur.fetchone():
        cur.execute("SELECT id FROM users ORDER BY id LIMIT 1")
        evaluator_id = int(cur.fetchone()[0])

    department_rows: list[dict[str, Any]] = []
    for idx, config in enumerate(DEPARTMENTS):
        dept_name = config.name
        dept_cfg = dept_map[dept_name]
        dept_id = int(dept_cfg["id"])

        cur.execute(
            """
            SELECT id
            FROM employees
            WHERE department = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (dept_name,),
        )
        row = cur.fetchone()
        if row:
            employee_id = int(row[0])
        else:
            cur.execute("SELECT id FROM employees ORDER BY id DESC LIMIT 1")
            fallback = cur.fetchone()
            employee_id = int(fallback[0])

        actual_score = round(
            sample_truncated_gauss(
                rng,
                mean=(config.actual_range[0] + config.actual_range[1]) / 2,
                std=2.2,
                low=config.actual_range[0],
                high=config.actual_range[1],
            ),
            1,
        )
        coefficient = round(
            sample_truncated_gauss(
                rng,
                mean=(config.coeff_range[0] + config.coeff_range[1]) / 2,
                std=0.04,
                low=config.coeff_range[0],
                high=config.coeff_range[1],
            ),
            2,
        )

        financial = round(clamp(actual_score + rng.gauss(1.5, 2.0), 75.0, 100.0), 1)
        customer = round(clamp(actual_score + rng.gauss(0.8, 2.4), 75.0, 100.0), 1)
        internal_process = round(
            clamp(actual_score + rng.gauss(0.5, 2.6), 75.0, 100.0), 1
        )
        learning_growth = round(
            clamp(actual_score + rng.gauss(-0.2, 2.8), 70.0, 100.0), 1
        )

        if coefficient >= 1.15:
            contribution = "CORE"
        elif coefficient >= 1.05:
            contribution = "MAJOR"
        elif coefficient >= 0.95:
            contribution = "NORMAL"
        else:
            contribution = "MINOR"

        project_id = project_ids[-len(DEPARTMENTS) + idx]
        perf_id += 1
        comments = {
            "source": "task4_demo_seed",
            "period": PERIOD,
            "department": dept_name,
            "target_score": 100,
            "actual_score": actual_score,
            "performance_coefficient": coefficient,
            "kpi_completion": {
                "financial": financial,
                "customer": customer,
                "internal_process": internal_process,
                "learning_growth": learning_growth,
            },
        }
        cur.execute(
            """
            INSERT INTO hr_project_performance
                (id, employee_id, project_id, role_code, role_name, performance_score, quality_score,
                 collaboration_score, on_time_rate, contribution_level, hours_spent,
                 evaluation_date, evaluator_id, comments, created_at, updated_at)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                perf_id,
                employee_id,
                project_id,
                f"{ROLE_CODE_PREFIX}{idx + 1:02d}",
                dept_name,
                actual_score,
                financial,
                customer,
                internal_process,
                contribution,
                round(160 + rng.uniform(10, 70), 1),
                "2026-03-31",
                evaluator_id,
                json.dumps(comments, ensure_ascii=False),
                timestamp,
                timestamp,
            ),
        )

        department_rows.append(
            {
                "department": dept_name,
                "department_id": dept_id,
                "target_score": 100,
                "actual_score": actual_score,
                "coefficient": coefficient,
                "financial": financial,
                "customer": customer,
                "internal_process": internal_process,
                "learning_growth": learning_growth,
            }
        )
    return department_rows


def generate_personal_evaluations(
    conn: sqlite3.Connection,
    users: list[dict[str, Any]],
    dept_rows: list[dict[str, Any]],
    rng: random.Random,
    timestamp: str,
) -> dict[str, Any]:
    cur = conn.cursor()
    project_ids = fetch_project_ids(conn)

    dept_lookup = {row["department"]: row for row in dept_rows}
    weights = [config.headcount_weight for config in DEPARTMENTS]
    quotas = allocate_counts(EVALUATION_COUNT, weights)
    assigned_depts: list[str] = []
    for idx, config in enumerate(DEPARTMENTS):
        assigned_depts.extend([config.name] * quotas[idx])
    rng.shuffle(assigned_depts)

    if len(assigned_depts) != EVALUATION_COUNT:
        raise RuntimeError("部门配额计算异常，人数不等于 150。")

    grade_list = ["A"] * 45 + ["B"] * 75 + ["C"] * 30
    grade_order = {"A": 3, "B": 2, "C": 1}

    entries = []
    for idx, user in enumerate(users):
        dept_name = assigned_depts[idx]
        dept_coeff = float(dept_lookup[dept_name]["coefficient"])
        score_priority = dept_coeff + rng.uniform(-0.02, 0.02)
        entry = {
            "user_id": user["user_id"],
            "employee_id": user["employee_id"],
            "name": user["name"],
            "dept_name": dept_name,
            "dept_coeff": dept_coeff,
            "priority": score_priority,
        }
        entries.append(entry)

    entries.sort(key=lambda x: x["priority"], reverse=True)
    grade_list.sort(key=lambda g: grade_order[g], reverse=True)

    cur.execute("SELECT COALESCE(MAX(id), 0) FROM monthly_work_summary")
    summary_id = int(cur.fetchone()[0])
    cur.execute("SELECT COALESCE(MAX(id), 0) FROM performance_evaluation_record")
    eval_id = int(cur.fetchone()[0])

    evaluator_id = 1
    cur.execute("SELECT 1 FROM users WHERE id = 1")
    if not cur.fetchone():
        cur.execute("SELECT id FROM users ORDER BY id LIMIT 1")
        evaluator_id = int(cur.fetchone()[0])

    bonuses: list[int] = []
    score_counter: Counter[str] = Counter()
    scores: list[int] = []

    for idx, entry in enumerate(entries):
        grade = grade_list[idx]
        dept_name = entry["dept_name"]
        dept_actual = float(dept_lookup[dept_name]["actual_score"])
        dept_coeff = float(entry["dept_coeff"])

        if grade == "A":
            score_raw = sample_truncated_gauss(rng, 93.0, 2.0, 90.0, 98.0)
        elif grade == "B":
            score_raw = sample_truncated_gauss(rng, 84.5, 2.2, 80.0, 89.0)
        else:
            score_raw = sample_truncated_gauss(rng, 74.5, 2.0, 70.0, 79.0)

        dept_shift = (dept_actual - 86.0) / 15.0
        if grade == "A":
            score = int(round(clamp(score_raw + dept_shift, 90.0, 98.0)))
        elif grade == "B":
            score = int(round(clamp(score_raw + dept_shift, 80.0, 89.0)))
        else:
            score = int(round(clamp(score_raw + dept_shift, 70.0, 79.0)))

        financial = round(clamp(score + rng.gauss(1.2, 3.0), 65.0, 100.0), 1)
        customer = round(clamp(score + rng.gauss(0.8, 3.3), 65.0, 100.0), 1)
        internal_process = round(clamp(score + rng.gauss(0.5, 3.5), 65.0, 100.0), 1)
        learning_growth = round(clamp(score + rng.gauss(0.2, 3.8), 60.0, 100.0), 1)

        base_bonus = 3000 + ((score - 70) / 28.0) * 12000
        coeff_bonus = (dept_coeff - 1.0) * 3200
        noise = rng.gauss(0, 600)
        bonus_amount = int(round(clamp(base_bonus + coeff_bonus + noise, 3000, 20000) / 100.0) * 100)

        qualification_payload = {
            "source": "task4_demo_seed",
            "period": PERIOD,
            "department": dept_name,
            "grade": grade,
            "target_score": 100,
            "bonus_amount": bonus_amount,
            "performance_coefficient": dept_coeff,
            "kpi_completion": {
                "financial": financial,
                "customer": customer,
                "internal_process": internal_process,
                "learning_growth": learning_growth,
            },
        }

        summary_id += 1
        work_content = f"{SUMMARY_PREFIX} {dept_name}员工{entry['name']}完成Q1重点目标。"
        cur.execute(
            """
            INSERT INTO monthly_work_summary
                (id, employee_id, period, work_content, self_evaluation, highlights, problems, next_month_plan,
                 status, submit_date, created_at, updated_at)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                summary_id,
                entry["user_id"],
                PERIOD,
                work_content,
                f"{entry['name']}在{PERIOD}完成核心目标并保持稳定交付。",
                f"核心指标：财务{financial}、客户{customer}、内部流程{internal_process}、学习成长{learning_growth}。",
                "暂无重大问题，持续优化跨部门协同。",
                "下季度聚焦效率提升和质量改进。",
                "SUBMITTED",
                "2026-03-31 18:00:00",
                timestamp,
                timestamp,
            ),
        )

        evaluator_type = "direct_manager"
        if dept_name in ("人力资源部", "管理层"):
            evaluator_type = "hr"

        eval_id += 1
        cur.execute(
            """
            INSERT INTO performance_evaluation_record
                (id, summary_id, evaluator_id, evaluator_type, project_id, project_weight, score, comment,
                 qualification_level_id, qualification_score, status, evaluated_at, created_at, updated_at)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?)
            """,
            (
                eval_id,
                summary_id,
                evaluator_id,
                evaluator_type,
                rng.choice(project_ids),
                100,
                score,
                f"{PERIOD}绩效评价：得分{score}，等级{grade}，建议奖金¥{bonus_amount}。",
                json.dumps(qualification_payload, ensure_ascii=False),
                "COMPLETED",
                "2026-04-05 10:00:00",
                timestamp,
                timestamp,
            ),
        )

        bonuses.append(bonus_amount)
        score_counter[grade] += 1
        scores.append(score)

    distribution = {
        "A": score_counter["A"],
        "B": score_counter["B"],
        "C": score_counter["C"],
    }
    if distribution != {"A": 45, "B": 75, "C": 30}:
        raise RuntimeError(f"分布异常：{distribution}")

    return {
        "distribution": distribution,
        "bonuses": bonuses,
        "scores": scores,
        "entries": entries,
    }


def format_department_table(rows: list[dict[str, Any]]) -> str:
    header = (
        "| 部门 | 目标分数 | 实际分数 | 绩效系数 | 财务指标 | 客户指标 | 内部流程 | 学习成长 |\n"
        "|---|---:|---:|---:|---:|---:|---:|---:|"
    )
    body = "\n".join(
        [
            f"| {row['department']} | {row['target_score']} | {row['actual_score']:.1f} | {row['coefficient']:.2f} | "
            f"{row['financial']:.1f} | {row['customer']:.1f} | {row['internal_process']:.1f} | {row['learning_growth']:.1f} |"
            for row in rows
        ]
    )
    return f"{header}\n{body}"


def write_report(
    staff_info: dict[str, Any],
    dept_rows: list[dict[str, Any]],
    eval_result: dict[str, Any],
) -> None:
    bonuses = eval_result["bonuses"]
    distribution = eval_result["distribution"]
    total_bonus = sum(bonuses)
    avg_bonus = total_bonus / len(bonuses)
    avg_score = sum(eval_result["scores"]) / len(eval_result["scores"])

    lines = [
        "# 任务 4/6：绩效评价演示数据（2026-Q1）",
        "",
        "## 规模与覆盖",
        f"- 公司人数（users）：{staff_info['final_users']} 人",
        f"- 员工人数（employees）：{staff_info['final_employees']} 人",
        f"- 本次个人绩效评价：{len(eval_result['scores'])} 人",
        f"- 新增员工/用户：{staff_info['created_count']} 人",
        "",
        "## 部门绩效汇总（hr_project_performance）",
        format_department_table(dept_rows),
        "",
        "## 个人绩效分布（performance_evaluation_record）",
        "| 等级 | 分数区间 | 人数 | 占比 |",
        "|---|---|---:|---:|",
        f"| A | 90+ | {distribution['A']} | {distribution['A'] / EVALUATION_COUNT:.1%} |",
        f"| B | 80-89 | {distribution['B']} | {distribution['B'] / EVALUATION_COUNT:.1%} |",
        f"| C | 70-79 | {distribution['C']} | {distribution['C'] / EVALUATION_COUNT:.1%} |",
        "",
        "## 奖金汇总",
        f"- 奖金总额：¥{total_bonus:,.0f}",
        f"- 人均奖金：¥{avg_bonus:,.0f}",
        f"- 最高奖金：¥{max(bonuses):,.0f}",
        f"- 最低奖金：¥{min(bonuses):,.0f}",
        f"- 平均绩效分：{avg_score:.2f}",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def print_console_summary(
    staff_info: dict[str, Any],
    dept_rows: list[dict[str, Any]],
    eval_result: dict[str, Any],
) -> None:
    bonuses = eval_result["bonuses"]
    distribution = eval_result["distribution"]
    total_bonus = sum(bonuses)

    print("✅ 任务 4/6 完成：绩效评价演示数据已生成")
    print(f"  - 公司人数：{staff_info['final_users']} 人（目标 190）")
    print(f"  - 部门绩效：{len(dept_rows)} 个部门")
    print(f"  - 个人绩效：{len(eval_result['scores'])} 人（周期 {PERIOD}）")
    print("  - 分布：A={A}，B={B}，C={C}".format(**distribution))
    print(f"  - 奖金总额：¥{total_bonus:,.0f}")
    print(f"  - 报告：{REPORT_PATH}")


def main() -> None:
    rng = random.Random(RNG_SEED)
    timestamp = now_str()

    if not DB_PATH.exists():
        raise FileNotFoundError(f"数据库不存在：{DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        dept_map = ensure_departments(conn, timestamp)
        staff_info = create_employees_and_users(conn, dept_map, rng, timestamp)
        clean_previous_task4_data(conn)

        users = build_evaluation_user_pool(conn, EVALUATION_COUNT)
        dept_rows = build_department_performance(conn, dept_map, rng, timestamp)
        eval_result = generate_personal_evaluations(conn, users, dept_rows, rng, timestamp)

        conn.commit()
        write_report(staff_info, dept_rows, eval_result)
        print_console_summary(staff_info, dept_rows, eval_result)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
