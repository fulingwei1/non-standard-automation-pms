#!/usr/bin/env python3
"""
导入公司员工名单 → 自动创建用户 + 分配角色权限

用法:
  python scripts/import_employees.py employees.csv
  python scripts/import_employees.py employees.xlsx
  python scripts/import_employees.py --template  # 生成模板

CSV/Excel格式:
  姓名, 部门, 职位, 手机号(可选), 工号(可选), 邮箱(可选)

职位→角色自动映射规则:
  总经理/副总/董事 → ROLE_EXEC (总经办高管)
  总监/部长         → ROLE_DIRECTOR (部门总监)
  经理/主管         → ROLE_MANAGER (部门经理)
  主任/组长         → ROLE_LEAD (班组长)
  工程师/专员/助理  → ROLE_STAFF (普通员工)
  其他              → ROLE_STAFF
"""
import csv
import os
import re
import sqlite3
import sys
from datetime import datetime

import bcrypt
from pypinyin import lazy_pinyin

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "app.db"
)
DEFAULT_PASSWORD = "jkb123456"

# 职位关键词 → 角色映射
POSITION_ROLE_MAP = [
    # (关键词列表, 角色code, 角色名, 数据范围)
    (
        ["总经理", "副总", "董事", "董秘", "CEO", "VP", "CFO", "CTO", "COO"],
        "ROLE_EXEC",
        "高管",
        "ALL",
    ),
    (["总监", "部长", "院长"], "ROLE_DIRECTOR", "部门总监", "DEPT_AND_BELOW"),
    (["经理", "主管"], "ROLE_MANAGER", "部门经理", "DEPT"),
    (["主任", "组长", "班长", "队长"], "ROLE_LEAD", "班组长", "TEAM"),
    (
        ["工程师", "专员", "助理", "文员", "技术员", "操作员", "实习"],
        "ROLE_STAFF",
        "普通员工",
        "SELF",
    ),
]

# 部门名称标准化
DEPT_NORMALIZE = {
    "总经办": "总经办",
    "总经理办公室": "总经办",
    "行政": "总经办",
    "销售": "销售部",
    "销售部": "销售部",
    "市场": "销售部",
    "商务": "销售部",
    "项目": "项目管理部",
    "项目管理部": "项目管理部",
    "PMO": "项目管理部",
    "PM": "项目管理部",
    "研发": "研发部",
    "研发部": "研发部",
    "技术": "研发部",
    "软件": "研发部",
    "R&D": "研发部",
    "生产": "生产部",
    "生产部": "生产部",
    "制造": "生产部",
    "车间": "生产部",
    "PMC": "生产部",
    "客服": "客服部",
    "客服部": "客服部",
    "售后": "客服部",
    "服务": "客服部",
    "采购": "采购部",
    "采购部": "采购部",
    "供应链": "采购部",
    "财务": "财务部",
    "财务部": "财务部",
    "会计": "财务部",
    "品质": "品质部",
    "品质部": "品质部",
    "QA": "品质部",
    "QC": "品质部",
    "人事": "人力资源部",
    "人力": "人力资源部",
    "HR": "人力资源部",
    "仓库": "仓储部",
    "仓储": "仓储部",
    "物流": "仓储部",
}

DEPT_CODE_MAP = {
    "总经办": "EXEC",
    "销售部": "SALES",
    "项目管理部": "PM",
    "研发部": "RD",
    "生产部": "PROD",
    "客服部": "SERVICE",
    "采购部": "PURCHASE",
    "财务部": "FINANCE",
    "品质部": "QA",
    "人力资源部": "HR",
    "仓储部": "WH",
}


def name_to_pinyin(name: str) -> str:
    """姓名转拼音作为用户名"""
    try:
        py = "".join(lazy_pinyin(name))
        return re.sub(r"[^a-z]", "", py.lower())
    except Exception:
        return name.lower().replace(" ", "")


def match_role(position: str) -> tuple:
    """根据职位匹配角色"""
    for keywords, code, name, scope in POSITION_ROLE_MAP:
        for kw in keywords:
            if kw in position:
                return code, name, scope
    return "ROLE_STAFF", "普通员工", "SELF"


def generate_template():
    """生成CSV导入模板"""
    template = os.path.join(os.path.dirname(os.path.abspath(__file__)), "employees_template.csv")
    with open(template, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["姓名", "部门", "职位", "手机号", "工号", "邮箱"])
        w.writerow(["张三", "销售部", "销售经理", "13800138001", "E001", "zhangsan@jkb.com"])
        w.writerow(["李四", "研发部", "软件工程师", "13800138002", "E002", ""])
        w.writerow(["王五", "生产部", "车间主任", "", "", ""])
    print(f"✅ 模板已生成: {template}")
    print("   编辑后运行: python scripts/import_employees.py employees_template.csv")


def read_file(filepath: str) -> list:
    """读取CSV或Excel文件"""
    ext = os.path.splitext(filepath)[1].lower()
    rows = []

    if ext == ".csv":
        # 尝试多种编码
        for enc in ["utf-8-sig", "utf-8", "gbk", "gb2312", "gb18030"]:
            try:
                with open(filepath, encoding=enc) as f:
                    reader = csv.reader(f)
                    header = next(reader)
                    for row in reader:
                        if row and row[0].strip():
                            rows.append(row)
                break
            except (UnicodeDecodeError, StopIteration):
                continue
    elif ext in (".xlsx", ".xls"):
        try:
            import openpyxl

            wb = openpyxl.load_workbook(filepath, read_only=True)
            ws = wb.active
            first = True
            for row in ws.iter_rows(values_only=True):
                if first:
                    first = False
                    continue
                if row and row[0]:
                    rows.append([str(cell or "") for cell in row])
        except ImportError:
            print("❌ 读取Excel需要 openpyxl: pip install openpyxl")
            sys.exit(1)
    else:
        print(f"❌ 不支持的文件格式: {ext} (支持 .csv / .xlsx)")
        sys.exit(1)

    return rows


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    if sys.argv[1] == "--template":
        generate_template()
        return

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        return

    rows = read_file(filepath)
    if not rows:
        print("❌ 文件为空或格式不对")
        return

    print(f"📋 读取到 {len(rows)} 条员工记录")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")
    c = conn.cursor()
    now = datetime.now().isoformat()
    pw_hash = bcrypt.hashpw(DEFAULT_PASSWORD.encode(), bcrypt.gensalt()).decode()

    # 确保角色存在
    roles_created = set()
    for _, role_code, role_name, data_scope in POSITION_ROLE_MAP:
        if role_code not in roles_created:
            c.execute(
                """INSERT OR IGNORE INTO roles 
                (role_code, role_name, data_scope, is_system, is_active, sort_order, created_at, updated_at)
                VALUES (?, ?, ?, 0, 1, 0, ?, ?)""",
                (role_code, role_name, data_scope, now, now),
            )
            roles_created.add(role_code)

    # 获取角色ID映射
    role_id_map = {}
    for row in c.execute("SELECT id, role_code FROM roles"):
        role_id_map[row[1]] = row[0]

    # 获取现有用户名，避免冲突
    existing_usernames = set(r[0] for r in c.execute("SELECT username FROM users"))

    # 获取最大ID
    max_emp_id = c.execute("SELECT COALESCE(MAX(id), 1) FROM employees").fetchone()[0]
    max_user_id = c.execute("SELECT COALESCE(MAX(id), 1) FROM users").fetchone()[0]
    next_id = max(max_emp_id, max_user_id) + 1

    # 确保部门存在
    existing_depts = {}
    for row in c.execute("SELECT id, dept_name FROM departments"):
        existing_depts[row[1]] = row[0]
    max_dept_id = c.execute("SELECT COALESCE(MAX(id), 0) FROM departments").fetchone()[0]

    created = 0
    skipped = 0

    for row in rows:
        name = row[0].strip()
        dept_raw = row[1].strip() if len(row) > 1 else ""
        position = row[2].strip() if len(row) > 2 else "员工"
        phone = row[3].strip() if len(row) > 3 else ""
        emp_code = row[4].strip() if len(row) > 4 else ""
        email = row[5].strip() if len(row) > 5 else ""

        if not name:
            continue

        # 标准化部门
        dept_name = DEPT_NORMALIZE.get(dept_raw, dept_raw or "总经办")

        # 确保部门存在
        if dept_name not in existing_depts:
            max_dept_id += 1
            dept_code = DEPT_CODE_MAP.get(dept_name, dept_name[:4].upper())
            c.execute(
                "INSERT INTO departments (id,dept_code,dept_name,is_active,created_at,updated_at) VALUES (?,?,?,1,?,?)",
                (max_dept_id, dept_code, dept_name, now, now),
            )
            existing_depts[dept_name] = max_dept_id
            print(f"  📁 新建部门: {dept_name}")

        dept_id = existing_depts[dept_name]

        # 生成用户名
        username = name_to_pinyin(name)
        if not username:
            username = f"user{next_id}"
        orig_username = username
        suffix = 1
        while username in existing_usernames:
            username = f"{orig_username}{suffix}"
            suffix += 1
        existing_usernames.add(username)

        # 生成工号
        if not emp_code:
            emp_code = f"E{next_id:03d}"

        # 匹配角色
        role_code, role_name, _ = match_role(position)

        # 创建员工
        c.execute(
            "INSERT OR REPLACE INTO employees (id,employee_code,name,department,role,phone,is_active,created_at,updated_at) VALUES (?,?,?,?,?,?,1,?,?)",
            (next_id, emp_code, name, dept_name, position, phone, now, now),
        )

        # 创建用户
        c.execute(
            "INSERT OR REPLACE INTO users (id,username,password_hash,employee_id,real_name,department,position,department_id,email,phone,is_active,is_superuser,solution_credits,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,1,0,0,?,?)",
            (
                next_id,
                username,
                pw_hash,
                next_id,
                name,
                dept_name,
                position,
                dept_id,
                email,
                phone,
                now,
                now,
            ),
        )

        # 分配角色
        if role_code in role_id_map:
            c.execute(
                "INSERT OR IGNORE INTO user_roles (user_id,role_id,created_at,updated_at) VALUES (?,?,?,?)",
                (next_id, role_id_map[role_code], now, now),
            )

        print(f"  ✅ {name} ({dept_name}/{position}) → 用户名: {username}, 角色: {role_name}")
        next_id += 1
        created += 1

    conn.commit()
    conn.close()

    print(f"\n🎉 导入完成！")
    print(f"   创建: {created} 个用户")
    print(f"   默认密码: {DEFAULT_PASSWORD}")
    print(f"   角色分配规则:")
    for kws, _, rname, _ in POSITION_ROLE_MAP:
        print(f"     {rname}: {', '.join(kws[:3])}...")
    print(f"\n⚠️  请提醒用户首次登录后修改密码！")


if __name__ == "__main__":
    main()
