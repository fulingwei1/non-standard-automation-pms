#!/usr/bin/env python3
"""
金凯博 BLM + BEM 战略管理完整种子数据
BLM (Business Leadership Model) — 战略制定
BEM (Business Execution Model) — 战略解码执行

行业：非标自动化测试设备 (ICT/FCT/EOL/烧录/老化/视觉检测)
客户：新能源(比亚迪/宁德时代)、消费电子(华为/小米)、半导体(汇川/中芯)
"""
import hashlib
import json
import sqlite3
from datetime import date, datetime

DB_PATH = "data/app.db"


def hash_password(password: str) -> str:
    """简单密码哈希 (开发环境)"""
    # 使用 bcrypt 格式兼容
    try:
        import bcrypt
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    except ImportError:
        # fallback: sha256
        return hashlib.sha256(password.encode()).hexdigest()


def seed():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = date.today().strftime("%Y-%m-%d")

    # ============================================================
    # 0. 基础数据：租户 + 部门 + 员工 + 用户 + 角色
    # ============================================================

    # 0.1 租户
    c.execute("""INSERT OR REPLACE INTO tenants (id, tenant_name, tenant_code, status, created_at, updated_at)
        VALUES (1, '深圳金凯博自动化测试', 'JKB', 'active', ?, ?)""", (now, now))

    # 0.2 部门结构 (金凯博实际组织架构)
    departments = [
        (1, "D00", "总经办",       None, None, 0, 0),
        (2, "D01", "销售部",       1,    None, 1, 1),
        (3, "D02", "技术研发部",   1,    None, 1, 2),
        (4, "D03", "项目管理部",   1,    None, 1, 3),
        (5, "D04", "生产制造部",   1,    None, 1, 4),
        (6, "D05", "采购部",       1,    None, 1, 5),
        (7, "D06", "品质部",       1,    None, 1, 6),
        (8, "D07", "人事行政部",   1,    None, 1, 7),
        (9, "D08", "财务部",       1,    None, 1, 8),
        (10, "D09", "售后服务部",  1,    None, 1, 9),
    ]
    for d in departments:
        c.execute("""INSERT OR REPLACE INTO departments
            (id, dept_code, dept_name, parent_id, manager_id, level, sort_order, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""", (*d, now, now))

    # 0.3 员工 (核心管理层 + 骨干)
    # employees表字段: id, employee_code, name, department, role, phone, is_active, created_at, updated_at
    employees = [
        # (id, code, name, department, role, phone)
        (1,  "JKB001", "符凌维", "总经办",     "总经理",       "13800000001"),
        (2,  "JKB002", "张志强", "销售部",     "销售总监",     "13800000002"),
        (3,  "JKB003", "李明华", "技术研发部", "技术总监",     "13800000003"),
        (4,  "JKB004", "王建国", "项目管理部", "PMO总监",      "13800000004"),
        (5,  "JKB005", "赵德胜", "生产制造部", "生产总监",     "13800000005"),
        (6,  "JKB006", "陈伟",   "采购部",     "采购经理",     "13800000006"),
        (7,  "JKB007", "刘芳",   "品质部",     "品质经理",     "13800000007"),
        (8,  "JKB008", "周丽",   "人事行政部", "人事经理",     "13800000008"),
        (9,  "JKB009", "黄志远", "财务部",     "财务经理",     "13800000009"),
        (10, "JKB010", "林海",   "售后服务部", "售后经理",     "13800000010"),
        (11, "JKB011", "杨超",   "销售部",     "大客户经理",   "13800000011"),
        (12, "JKB012", "吴磊",   "销售部",     "区域销售经理", "13800000012"),
        (13, "JKB013", "郑强",   "技术研发部", "机械设计主管", "13800000013"),
        (14, "JKB014", "孙涛",   "技术研发部", "电气设计主管", "13800000014"),
        (15, "JKB015", "马丽",   "技术研发部", "软件开发主管", "13800000015"),
        (16, "JKB016", "何俊",   "项目管理部", "高级项目经理", "13800000016"),
        (17, "JKB017", "胡勇",   "项目管理部", "项目经理",     "13800000017"),
        (18, "JKB018", "徐刚",   "生产制造部", "装配组长",     "13800000018"),
        (19, "JKB019", "朱亮",   "生产制造部", "调试组长",     "13800000019"),
        (20, "JKB020", "高峰",   "品质部",     "质量工程师",   "13800000020"),
    ]
    for emp in employees:
        eid, code, name, dept, role, phone = emp
        c.execute("""INSERT OR REPLACE INTO employees
            (id, employee_code, name, department, role, phone, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)""",
            (eid, code, name, dept, role, phone, now, now))

    # 更新部门经理
    dept_managers = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10}
    for dept_id, mgr_id in dept_managers.items():
        c.execute("UPDATE departments SET manager_id = ? WHERE id = ?", (mgr_id, dept_id))

    # 0.4 角色
    roles = [
        (1, "admin",            "系统管理员",   "SYSTEM",   1),
        (2, "gm",               "总经理",       "BUSINESS", 1),
        (3, "sales_director",   "销售总监",     "BUSINESS", 1),
        (4, "tech_director",    "技术总监",     "BUSINESS", 1),
        (5, "pmo_director",     "PMO总监",      "BUSINESS", 1),
        (6, "production_mgr",   "生产总监",     "BUSINESS", 1),
        (7, "procurement_mgr",  "采购经理",     "BUSINESS", 1),
        (8, "quality_mgr",      "品质经理",     "BUSINESS", 1),
        (9, "hr_manager",       "人事经理",     "BUSINESS", 1),
        (10, "finance_mgr",     "财务经理",     "BUSINESS", 1),
        (11, "service_mgr",     "售后经理",     "BUSINESS", 1),
        (12, "sales_rep",       "销售经理",     "BUSINESS", 1),
        (13, "engineer",        "工程师",       "BUSINESS", 1),
        (14, "pm",              "项目经理",     "BUSINESS", 1),
        (15, "worker",          "生产员工",     "BUSINESS", 1),
    ]
    for r in roles:
        c.execute("""INSERT OR REPLACE INTO roles
            (id, role_code, role_name, role_type, tenant_id, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?)""", (*r, now, now))

    # 0.5 用户 (登录账号)
    # users表: id, tenant_id, is_tenant_admin, employee_id, username, password_hash,
    #          email, phone, real_name, department_id, department, position, is_active, is_superuser
    pwd = hash_password("123456")
    admin_pwd = hash_password("admin123")
    users = [
        # (id, employee_id, username, pwd, email, real_name, dept_id, dept_name, position, is_super, role_id)
        (1,  1,  "fulingwei",  admin_pwd, "fulingwei@jkb.com", "符凌维", 1,  "总经办",     "总经理",       True,  2),
        (2,  2,  "zhangzq",    pwd,       "zhangzq@jkb.com",   "张志强", 2,  "销售部",     "销售总监",     False, 3),
        (3,  3,  "limh",       pwd,       "limh@jkb.com",      "李明华", 3,  "技术研发部", "技术总监",     False, 4),
        (4,  4,  "wangjg",     pwd,       "wangjg@jkb.com",    "王建国", 4,  "项目管理部", "PMO总监",      False, 5),
        (5,  5,  "zhaods",     pwd,       "zhaods@jkb.com",    "赵德胜", 5,  "生产制造部", "生产总监",     False, 6),
        (6,  6,  "chenw",      pwd,       "chenw@jkb.com",     "陈伟",   6,  "采购部",     "采购经理",     False, 7),
        (7,  7,  "liuf",       pwd,       "liuf@jkb.com",      "刘芳",   7,  "品质部",     "品质经理",     False, 8),
        (8,  8,  "zhoul",      pwd,       "zhoul@jkb.com",     "周丽",   8,  "人事行政部", "人事经理",     False, 9),
        (9,  9,  "huangzy",    pwd,       "huangzy@jkb.com",   "黄志远", 9,  "财务部",     "财务经理",     False, 10),
        (10, 10, "linh",       pwd,       "linh@jkb.com",      "林海",   10, "售后服务部", "售后经理",     False, 11),
        (11, 11, "yangc",      pwd,       "yangc@jkb.com",     "杨超",   2,  "销售部",     "大客户经理",   False, 12),
        (12, 12, "wul",        pwd,       "wul@jkb.com",       "吴磊",   2,  "销售部",     "区域销售经理", False, 12),
        (13, 16, "hej",        pwd,       "hej@jkb.com",       "何俊",   4,  "项目管理部", "高级项目经理", False, 14),
        (14, 17, "huy",        pwd,       "huy@jkb.com",       "胡勇",   4,  "项目管理部", "项目经理",     False, 14),
        (15, None,"admin",     admin_pwd, "admin@jkb.com",     "管理员", None, None,       "系统管理员",   True,  1),
    ]
    for u in users:
        uid, emp_id, uname, upwd, email, real_name, dept_id, dept_name, position, is_super, role_id = u
        c.execute("""INSERT OR REPLACE INTO users
            (id, tenant_id, employee_id, username, password_hash, email,
             real_name, department_id, department, position,
             is_superuser, is_active, solution_credits, created_at, updated_at)
            VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, ?, ?)""",
            (uid, emp_id, uname, upwd, email, real_name, dept_id, dept_name, position,
             1 if is_super else 0, now, now))
        # 用户角色关联
        c.execute("""INSERT OR REPLACE INTO user_roles (user_id, role_id) VALUES (?, ?)""",
            (uid, role_id))

    # ============================================================
    # 1. BLM 战略制定 — Strategy 主表
    # ============================================================

    # 2026年战略 (当前生效)
    c.execute("""INSERT OR REPLACE INTO strategies
        (id, code, name, vision, mission, slogan, year, start_date, end_date,
         status, created_by, is_active, published_at, created_at, updated_at)
        VALUES (1, 'STR-2026', '金凯博2026年战略规划',
        '成为中国非标自动化测试设备领域的技术领导者，三年内进入行业TOP10',
        '以技术创新驱动，为新能源、消费电子、半导体客户提供高可靠性、高效率的自动化测试解决方案，助力中国制造业质量升级',
        '精测智造 引领未来',
        2026, '2026-01-01', '2026-12-31', 'published', 1, 1, ?, ?, ?)""",
        (now, now, now))

    # 2025年战略 (用于同比)
    c.execute("""INSERT OR REPLACE INTO strategies
        (id, code, name, vision, mission, slogan, year, start_date, end_date,
         status, created_by, is_active, published_at, created_at, updated_at)
        VALUES (2, 'STR-2025', '金凯博2025年战略规划',
        '成为华南地区非标自动化测试设备领军企业',
        '为制造业客户提供可靠的自动化测试解决方案',
        '品质为先 创新致远',
        2025, '2025-01-01', '2025-12-31', 'archived', 1, 0, ?, ?, ?)""",
        (now, now, now))

    # ============================================================
    # 2. BEM 战略解码 — CSF (BSC 四维度)
    # ============================================================
    # 金凯博行业特点：
    # - 财务：非标项目制，毛利率波动大，回款周期长
    # - 客户：大客户集中度高(比亚迪/宁德占60%+)，定制化需求
    # - 内部：项目交付效率、设计复用率、调试一次通过率
    # - 学习：技术人才稀缺，知识沉淀不足

    csfs = [
        # 财务维度 (3个CSF)
        (1,  1, "financial", "CSF-F01", "营收规模增长",
         "BLM洞察：新能源+半导体双赛道驱动。目标营收1.5亿，同比增长30%。通过大客户深耕+新行业拓展双轮驱动。",
         "FOUR_PARAM", 12, 1, 2, 1),
        (2,  1, "financial", "CSF-F02", "项目毛利率提升",
         "BLM洞察：非标项目毛利率波动大(25-45%)。通过标准模块复用(目标60%复用率)和精准报价降低成本偏差。",
         "VALUE_CHAIN", 10, 2, 3, 3),
        (3,  1, "financial", "CSF-F03", "现金流健康",
         "BLM洞察：非标设备回款周期长(90-150天)。优化合同条款(预付30%+到货40%+验收30%)，加强催收。",
         "FIVE_SOURCE", 8, 3, 9, 9),

        # 客户维度 (3个CSF)
        (4,  1, "customer", "CSF-C01", "大客户战略合作",
         "BLM客户选择：聚焦比亚迪/宁德时代/华为三大战略客户，建立年度框架协议。TOP5客户营收占比>60%。",
         "FOUR_PARAM", 10, 1, 2, 2),
        (5,  1, "customer", "CSF-C02", "半导体行业突破",
         "BLM创新焦点：新能源增速放缓，半导体测试设备是第二增长曲线。目标签约3个芯片测试客户。",
         "FIVE_SOURCE", 8, 2, 2, 11),
        (6,  1, "customer", "CSF-C03", "客户满意度与复购",
         "BLM价值主张：非标设备客户选择成本高，高满意度=高复购。NPS>70，复购率>80%。",
         "FOUR_PARAM", 7, 3, 10, 10),

        # 内部流程维度 (4个CSF)
        (7,  1, "internal", "CSF-I01", "项目交付效率",
         "BEM关键流程：从签约到验收平均95天→目标75天。瓶颈在设计(30天)和调试(25天)阶段。",
         "VALUE_CHAIN", 8, 1, 4, 4),
        (8,  1, "internal", "CSF-I02", "设计标准化与复用",
         "BEM关键流程：非标=高成本。机械/电气/软件模块标准化复用率从30%→60%，降低设计周期40%。",
         "VALUE_CHAIN", 7, 2, 3, 13),
        (9,  1, "internal", "CSF-I03", "生产质量管控",
         "BEM关键流程：调试一次通过率88%→95%。导入SPC统计过程控制，关键工序检验覆盖100%。",
         "VALUE_CHAIN", 7, 3, 7, 7),
        (10, 1, "internal", "CSF-I04", "供应链成本优化",
         "BEM关键流程：关键物料(伺服/PLC/传感器)采购成本降10%。建立战略供应商体系，集中采购。",
         "VALUE_CHAIN", 5, 4, 6, 6),

        # 学习与成长维度 (3个CSF)
        (11, 1, "learning", "CSF-L01", "核心人才梯队建设",
         "BLM组织能力：技术骨干流失率高(18%→目标<10%)。建立技术职级体系+导师制+项目经理培养计划。",
         "INTANGIBLE", 7, 1, 8, 8),
        (12, 1, "learning", "CSF-L02", "数字化管理升级",
         "BLM关键任务：PMS系统覆盖100%项目，实现项目全生命周期数据化管理，支撑决策。",
         "INTANGIBLE", 6, 2, 4, 4),
        (13, 1, "learning", "CSF-L03", "技术创新与知识沉淀",
         "BLM创新焦点：申请3项发明专利。建立标准工艺库(300+标准工序)，知识库(100+调试经验)。",
         "INTANGIBLE", 5, 3, 3, 15),
    ]
    for csf in csfs:
        cid, sid, dim, code, name, desc, method, weight, sort, dept_id, user_id = csf
        c.execute("""INSERT OR REPLACE INTO csfs
            (id, strategy_id, dimension, code, name, description, derivation_method,
             weight, sort_order, owner_dept_id, owner_user_id, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
            (cid, sid, dim, code, name, desc, method, weight, sort, dept_id, user_id, now, now))

    # ============================================================
    # 3. BEM KPI指标 (IPOOC分类)
    # ============================================================
    # 非标自动化行业特色KPI：
    # - 设计复用率、BOM准确率、调试一次通过率
    # - 项目交付周期、验收一次通过率
    # - 关键物料到货及时率

    kpis = [
        # (id, csf_id, code, name, desc, ipooc, unit, direction,
        #  target, baseline, current, excellent, good, warning, source, freq, weight)

        # === 财务维度 KPI ===
        (1,  1, "KPI-F01", "年度营收", "公司年度总营收", "OUTPUT", "万元", "UP",
         15000, 11500, 3310, 16000, 14000, 12000, "MANUAL", "MONTHLY", 8),
        (2,  1, "KPI-F02", "新签合同额", "年度新签合同总金额", "OUTPUT", "万元", "UP",
         18000, 14000, 5100, 19000, 17000, 15000, "MANUAL", "MONTHLY", 6),
        (3,  2, "KPI-F03", "综合毛利率", "所有项目加权平均毛利率", "OUTPUT", "%", "UP",
         35, 28, 31.2, 38, 34, 30, "AUTO", "MONTHLY", 6),
        (4,  2, "KPI-F04", "报价准确率", "实际成本vs报价偏差<10%的项目比例", "PROCESS", "%", "UP",
         85, 65, 72, 90, 82, 70, "AUTO", "QUARTERLY", 4),
        (5,  3, "KPI-F05", "应收账款周转天数", "平均回款天数", "OUTPUT", "天", "DOWN",
         90, 125, 108, 80, 95, 110, "MANUAL", "MONTHLY", 5),
        (6,  3, "KPI-F06", "经营性现金流", "经营活动净现金流", "OUTPUT", "万元", "UP",
         2000, 800, 520, 2500, 1800, 1200, "MANUAL", "MONTHLY", 3),

        # === 客户维度 KPI ===
        (7,  4, "KPI-C01", "TOP5客户营收占比", "前5大客户营收占总营收比例", "OUTPUT", "%", "UP",
         60, 52, 58, 65, 58, 50, "AUTO", "QUARTERLY", 5),
        (8,  4, "KPI-C02", "战略客户框架协议签约", "与战略客户签订年度框架协议数", "OUTPUT", "个", "UP",
         3, 1, 1, 4, 3, 2, "MANUAL", "QUARTERLY", 4),
        (9,  5, "KPI-C03", "半导体新客户签约", "半导体行业新客户签约数量", "OUTPUT", "个", "UP",
         3, 0, 0, 4, 3, 1, "MANUAL", "QUARTERLY", 4),
        (10, 5, "KPI-C04", "半导体行业营收", "半导体行业客户营收额", "OUTPUT", "万元", "UP",
         1500, 0, 120, 2000, 1500, 800, "MANUAL", "QUARTERLY", 3),
        (11, 6, "KPI-C05", "客户NPS评分", "净推荐值", "OUTCOME", "分", "UP",
         70, 55, 62, 75, 68, 58, "MANUAL", "QUARTERLY", 3),
        (12, 6, "KPI-C06", "客户复购率", "12个月内复购客户比例", "OUTCOME", "%", "UP",
         80, 65, 72, 85, 78, 68, "AUTO", "QUARTERLY", 3),

        # === 内部流程 KPI ===
        (13, 7, "KPI-I01", "平均交付周期", "签约到验收平均天数", "PROCESS", "天", "DOWN",
         75, 95, 88, 70, 80, 90, "AUTO", "MONTHLY", 5),
        (14, 7, "KPI-I02", "验收一次通过率", "首次验收即通过的项目比例", "PROCESS", "%", "UP",
         85, 68, 74, 90, 82, 72, "AUTO", "MONTHLY", 4),
        (15, 8, "KPI-I03", "设计模块复用率", "使用标准化模块的设计比例", "PROCESS", "%", "UP",
         60, 30, 42, 70, 55, 40, "AUTO", "MONTHLY", 4),
        (16, 8, "KPI-I04", "BOM准确率", "BOM与实际物料一致的比例", "PROCESS", "%", "UP",
         95, 82, 88, 97, 93, 85, "AUTO", "MONTHLY", 3),
        (17, 9, "KPI-I05", "调试一次通过率", "设备调试首次通过率", "PROCESS", "%", "UP",
         95, 88, 91, 97, 94, 90, "AUTO", "MONTHLY", 4),
        (18, 9, "KPI-I06", "关键工序检验覆盖率", "关键工序100%来料/过程/出货检验", "PROCESS", "%", "UP",
         100, 75, 88, 100, 95, 85, "AUTO", "MONTHLY", 3),
        (19, 10, "KPI-I07", "关键物料采购成本降幅", "伺服/PLC/传感器等采购成本同比", "PROCESS", "%", "UP",
         10, 0, 3.5, 12, 9, 5, "MANUAL", "QUARTERLY", 3),
        (20, 10, "KPI-I08", "物料到货及时率", "关键物料按时到货比例", "PROCESS", "%", "UP",
         95, 82, 88, 97, 93, 85, "AUTO", "MONTHLY", 2),

        # === 学习成长 KPI ===
        (21, 11, "KPI-L01", "核心人才留存率", "技术骨干年度留存率", "INPUT", "%", "UP",
         90, 82, 88, 95, 88, 85, "MANUAL", "QUARTERLY", 4),
        (22, 11, "KPI-L02", "项目经理培养", "新晋合格项目经理人数", "INPUT", "人", "UP",
         5, 2, 2, 6, 5, 3, "MANUAL", "QUARTERLY", 3),
        (23, 12, "KPI-L03", "PMS系统覆盖率", "使用PMS管理的项目比例", "INPUT", "%", "UP",
         100, 45, 78, 100, 90, 70, "AUTO", "MONTHLY", 3),
        (24, 12, "KPI-L04", "数据驱动决策比例", "基于系统数据的管理决策比例", "OUTCOME", "%", "UP",
         80, 30, 55, 85, 75, 50, "MANUAL", "QUARTERLY", 2),
        (25, 13, "KPI-L05", "发明专利申请", "年度发明专利申请数", "INPUT", "项", "UP",
         3, 1, 1, 4, 3, 2, "MANUAL", "QUARTERLY", 2),
        (26, 13, "KPI-L06", "标准工艺库条目", "标准化工序/调试经验库条目数", "INPUT", "条", "UP",
         300, 80, 145, 350, 280, 200, "AUTO", "MONTHLY", 2),
    ]
    for kpi in kpis:
        kid, csf_id, code, name, desc, ipooc, unit, direction, \
            target, baseline, current, excellent, good, warning, source, freq, weight = kpi
        c.execute("""INSERT OR REPLACE INTO kpis
            (id, csf_id, code, name, description, ipooc_type, unit, direction,
             target_value, baseline_value, current_value,
             excellent_threshold, good_threshold, warning_threshold,
             data_source_type, frequency, weight, owner_user_id, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?)""",
            (kid, csf_id, code, name, desc, ipooc, unit, direction,
             target, baseline, current, excellent, good, warning, source, freq, weight, now, now))

    # ============================================================
    # 4. KPI 月度历史数据 (1-3月)
    # ============================================================
    history_data = [
        # 年度营收 (KPI-F01)
        (1,  1, "2026-01-31", "MONTHLY", 1050, 1250, 84.0,  "WARNING", "1月开门红"),
        (2,  1, "2026-02-28", "MONTHLY", 980,  1250, 78.4,  "WARNING", "春节月份低谷"),
        (3,  1, "2026-03-15", "MONTHLY", 1280, 1250, 102.4, "GOOD",    "Q1收官冲刺"),
        # 新签合同额 (KPI-F02)
        (4,  2, "2026-01-31", "MONTHLY", 1800, 1500, 120.0, "EXCELLENT", "比亚迪大单"),
        (5,  2, "2026-02-28", "MONTHLY", 1200, 1500, 80.0,  "WARNING",   "春节影响"),
        (6,  2, "2026-03-15", "MONTHLY", 2100, 1500, 140.0, "EXCELLENT", "宁德时代EOL项目"),
        # 综合毛利率 (KPI-F03)
        (7,  3, "2026-01-31", "MONTHLY", 32.5, 35, 92.9, "GOOD",    None),
        (8,  3, "2026-02-28", "MONTHLY", 29.8, 35, 85.1, "WARNING", "春节固定成本分摊高"),
        (9,  3, "2026-03-15", "MONTHLY", 31.2, 35, 89.1, "WARNING", "BOM偏差导致成本超支2项"),
        # 应收周转天数 (KPI-F05)
        (10, 5, "2026-01-31", "MONTHLY", 118, 90, 76.3, "DANGER",  "年底集中催收中"),
        (11, 5, "2026-02-28", "MONTHLY", 112, 90, 80.4, "WARNING", "春节前回款一批"),
        (12, 5, "2026-03-15", "MONTHLY", 108, 90, 83.3, "WARNING", "持续改善中"),
        # 平均交付周期 (KPI-I01)
        (13, 13, "2026-01-31", "MONTHLY", 92, 75, 81.5, "WARNING", None),
        (14, 13, "2026-02-28", "MONTHLY", 90, 75, 83.3, "WARNING", "春节停工影响"),
        (15, 13, "2026-03-15", "MONTHLY", 88, 75, 85.2, "WARNING", "设计阶段仍是瓶颈"),
        # 调试一次通过率 (KPI-I05)
        (16, 17, "2026-01-31", "MONTHLY", 89, 95, 93.7, "WARNING", None),
        (17, 17, "2026-02-28", "MONTHLY", 92, 95, 96.8, "GOOD",    "质量改进措施生效"),
        (18, 17, "2026-03-15", "MONTHLY", 91, 95, 95.8, "GOOD",    None),
        # 设计模块复用率 (KPI-I03)
        (19, 15, "2026-01-31", "MONTHLY", 35, 60, 58.3, "DANGER",  "刚开始推标准化"),
        (20, 15, "2026-02-28", "MONTHLY", 38, 60, 63.3, "DANGER",  None),
        (21, 15, "2026-03-15", "MONTHLY", 42, 60, 70.0, "WARNING", "3个标准模块入库"),
        # PMS覆盖率 (KPI-L03)
        (22, 23, "2026-01-31", "MONTHLY", 55, 100, 55.0, "DANGER",  "新项目强制入PMS"),
        (23, 23, "2026-02-28", "MONTHLY", 68, 100, 68.0, "WARNING", "历史项目补录中"),
        (24, 23, "2026-03-15", "MONTHLY", 78, 100, 78.0, "GOOD",    "推广顺利"),
        # NPS (KPI-C05)
        (25, 11, "2026-03-15", "QUARTERLY", 62, 70, 88.6, "WARNING", "Q1客户满意度调查"),
        # 核心人才留存率 (KPI-L01)
        (26, 21, "2026-03-15", "QUARTERLY", 88, 90, 97.8, "GOOD",   "Q1离职1人(电气)"),
    ]
    for h in history_data:
        hid, kpi_id, snap_date, period, value, target, completion, health, remark = h
        c.execute("""INSERT OR REPLACE INTO kpi_history
            (id, kpi_id, snapshot_date, snapshot_period, value, target_value,
             completion_rate, health_level, remark, source_type, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'MANUAL', ?, ?)""",
            (hid, kpi_id, snap_date, period, value, target, completion, health, remark, now, now))

    # ============================================================
    # 5. BEM 年度重点工作 (VOC法导出, 10项)
    # ============================================================
    works = [
        # (id, csf_id, code, name, desc, voc_source, pain_point, solution, target,
        #  year, start, end, actual_start, actual_end, owner_user, owner_dept,
        #  status, progress, priority, budget, actual_cost, risk, remark)
        (1, 1, "AW-01", "新能源电池包EOL测试平台V2",
         "开发模块化电池包EOL测试平台，兼容比亚迪/宁德多款电芯",
         "CUSTOMER", "现有EOL平台换型周期长(3天)，客户要求<4小时",
         "模块化夹具+快换接口+AI视觉定位",
         "完成3个标准型号，换型时间<4小时",
         2026, "2026-01-15", "2026-08-31", "2026-01-20", None,
         3, 3, "IN_PROGRESS", 45, "HIGH", 280, 125, "传感器选型存在技术风险", None),

        (2, 2, "AW-02", "毛利率提升专项（精准报价+标准化）",
         "通过历史项目数据分析优化报价模型，提升标准模块复用",
         "SHAREHOLDER", "毛利率波动大(25-45%)，部分项目亏损",
         "建立成本数据库+报价AI辅助+模块化设计",
         "综合毛利率≥35%，报价偏差<10%",
         2026, "2026-02-01", "2026-12-31", "2026-02-05", None,
         9, 3, "IN_PROGRESS", 28, "HIGH", 100, 35, None, None),

        (3, 5, "AW-03", "半导体芯片测试设备开发",
         "进入半导体后道测试领域，开发晶圆级/封装级测试设备",
         "CUSTOMER", "新能源增速放缓，需要第二增长曲线",
         "与半导体设备代理商合作+引进2名专家",
         "签约3个芯片测试客户，营收1500万",
         2026, "2026-03-01", "2026-11-30", None, None,
         2, 2, "NOT_STARTED", 8, "HIGH", 200, 15,
         "技术门槛高，人才招聘难度大", None),

        (4, 7, "AW-04", "项目交付效率提升专项",
         "优化项目全流程，缩短设计→采购→装配→调试周期",
         "EMPLOYEE", "项目经理反映设计变更频繁导致交付延期",
         "并行工程+设计评审前置+关键路径管控",
         "平均交付周期从95天→75天",
         2026, "2026-01-01", "2026-09-30", "2026-01-10", None,
         4, 4, "IN_PROGRESS", 40, "HIGH", 60, 22, None, None),

        (5, 8, "AW-05", "设计标准化模块库建设",
         "建立机械/电气/软件标准模块库，提升复用率",
         "EMPLOYEE", "每个项目从头设计，效率低且质量不稳定",
         "抽取高频模块+标准化+库管理+培训",
         "标准模块60个，复用率≥60%",
         2026, "2026-02-01", "2026-10-31", "2026-02-10", None,
         3, 3, "IN_PROGRESS", 32, "HIGH", 80, 28, None, None),

        (6, 9, "AW-06", "SPC质量管控体系导入",
         "导入统计过程控制，实现关键工序数据化质量管控",
         "COMPLIANCE", "客户审厂要求SPC，部分项目因质量问题返工",
         "SPC软件+检测设备+培训+试点3条线",
         "调试一次通过率≥95%，关键工序SPC覆盖100%",
         2026, "2026-04-01", "2026-10-31", None, None,
         7, 7, "NOT_STARTED", 5, "MEDIUM", 120, 8, None, None),

        (7, 10, "AW-07", "战略供应商体系建设",
         "建立分级供应商管理体系，集中采购降成本",
         "SHAREHOLDER", "采购分散，议价能力弱，到货不及时",
         "供应商分级+年度框架协议+第二供应商开发",
         "关键物料成本降10%，到货及时率≥95%",
         2026, "2026-01-15", "2026-09-30", "2026-01-20", None,
         6, 6, "IN_PROGRESS", 35, "MEDIUM", 40, 12, None, None),

        (8, 11, "AW-08", "技术人才梯队建设计划",
         "建立技术职级体系+导师制+项目经理培养",
         "EMPLOYEE", "核心技术人员流失率18%，知识断层严重",
         "技术T1-T7职级+资深带新人+PM轮岗培养",
         "骨干留存率≥90%，培养5名项目经理",
         2026, "2026-02-01", "2026-12-31", "2026-02-15", None,
         8, 8, "IN_PROGRESS", 22, "HIGH", 50, 15, None, None),

        (9, 12, "AW-09", "PMS系统全面推广上线",
         "非标自动化项目管理系统覆盖全部项目",
         "EMPLOYEE", "项目管理靠Excel和经验，数据不透明",
         "系统部署+数据迁移+培训+流程优化",
         "100%新项目入PMS，历史项目补录完成",
         2026, "2026-01-01", "2026-06-30", "2026-01-05", None,
         4, 4, "IN_PROGRESS", 75, "HIGH", 80, 52, None, None),

        (10, 13, "AW-10", "技术创新与知识库建设",
         "建立标准工艺库和调试经验知识库",
         "EMPLOYEE", "技术知识在个人脑中，人走知识丢",
         "知识管理系统+经验模板+评审入库机制",
         "标准工序300条，调试经验100条，专利3项",
         2026, "2026-03-01", "2026-12-31", "2026-03-10", None,
         3, 3, "IN_PROGRESS", 18, "MEDIUM", 45, 10, None, None),
    ]
    for w in works:
        wid, csf_id, code, name, desc, voc, pain, sol, target, \
            year, start, end, astart, aend, owner_u, owner_d, \
            status, progress, priority, budget, cost, risk, remark = w
        c.execute("""INSERT OR REPLACE INTO annual_key_works
            (id, csf_id, code, name, description, voc_source, pain_point, solution, target,
             year, start_date, end_date, actual_start_date, actual_end_date,
             owner_user_id, owner_dept_id,
             status, progress_percent, priority, budget, actual_cost,
             risk_description, remark, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
            (wid, csf_id, code, name, desc, voc, pain, sol, target,
             year, start, end, astart, aend, owner_u, owner_d,
             status, progress, priority, budget, cost, risk, remark, now, now))

    # ============================================================
    # 6. BEM 部门目标分解 (战略→部门OKR)
    # ============================================================
    dept_objectives = [
        # 销售部
        (1, 1, 2, 2026, None,
         json.dumps(["完成1.8亿新签合同", "TOP5战略客户框架协议3个", "半导体行业突破3个新客户", "回款率>85%"], ensure_ascii=False),
         json.dumps(["Q1新签5000万(实际5100万✅)", "Q2签订比亚迪/宁德框架协议", "Q2拜访5家半导体企业", "每月催收跟踪"], ensure_ascii=False),
         json.dumps([
             {"kpi_name": "新签合同额", "target": 18000, "unit": "万元", "weight": 40},
             {"kpi_name": "TOP5客户复购率", "target": 80, "unit": "%", "weight": 25},
             {"kpi_name": "半导体新客户", "target": 3, "unit": "个", "weight": 20},
             {"kpi_name": "回款率", "target": 85, "unit": "%", "weight": 15},
         ], ensure_ascii=False),
         "IN_PROGRESS", 2, None, None),

        # 技术研发部
        (2, 1, 3, 2026, None,
         json.dumps(["EOL平台V2开发完成", "标准模块库60个", "设计复用率≥60%", "专利申请3项"], ensure_ascii=False),
         json.dumps(["Q1完成方案评审(实际完成✅)", "Q2完成3个电池包适配", "每月入库5个标准模块", "Q2/Q3各申请1项专利"], ensure_ascii=False),
         json.dumps([
             {"kpi_name": "设计模块复用率", "target": 60, "unit": "%", "weight": 30},
             {"kpi_name": "BOM准确率", "target": 95, "unit": "%", "weight": 25},
             {"kpi_name": "专利申请", "target": 3, "unit": "项", "weight": 20},
             {"kpi_name": "标准模块入库", "target": 60, "unit": "个", "weight": 25},
         ], ensure_ascii=False),
         "IN_PROGRESS", 3, None, None),

        # 项目管理部
        (3, 1, 4, 2026, None,
         json.dumps(["平均交付周期≤75天", "验收一次通过率≥85%", "PMS覆盖率100%", "培养5名PM"], ensure_ascii=False),
         json.dumps(["Q1并行工程试点2个项目", "Q2设计评审前置全覆盖", "Q1新项目100%入PMS", "每季度PM培训"], ensure_ascii=False),
         json.dumps([
             {"kpi_name": "平均交付周期", "target": 75, "unit": "天", "weight": 30},
             {"kpi_name": "验收一次通过率", "target": 85, "unit": "%", "weight": 25},
             {"kpi_name": "PMS覆盖率", "target": 100, "unit": "%", "weight": 25},
             {"kpi_name": "PM培养", "target": 5, "unit": "人", "weight": 20},
         ], ensure_ascii=False),
         "IN_PROGRESS", 4, None, None),

        # 生产制造部
        (4, 1, 5, 2026, None,
         json.dumps(["调试一次通过率≥95%", "装配效率提升20%", "产能满足1.5亿营收需求"], ensure_ascii=False),
         json.dumps(["Q1标准工序库100条", "Q2导入SPC(3条产线)", "Q3柔性产线改造", "每月质量复盘会"], ensure_ascii=False),
         json.dumps([
             {"kpi_name": "调试一次通过率", "target": 95, "unit": "%", "weight": 35},
             {"kpi_name": "装配人均产出", "target": 120, "unit": "%", "weight": 25},
             {"kpi_name": "质量问题关闭率", "target": 95, "unit": "%", "weight": 20},
             {"kpi_name": "标准工序入库", "target": 300, "unit": "条", "weight": 20},
         ], ensure_ascii=False),
         "IN_PROGRESS", 5, None, None),

        # 采购部
        (5, 1, 6, 2026, None,
         json.dumps(["关键物料成本降10%", "到货及时率≥95%", "建立战略供应商体系"], ensure_ascii=False),
         json.dumps(["Q1供应商分级评审", "Q2签订5家年度框架协议", "Q3开发3家第二供应商", "季度供应商考核"], ensure_ascii=False),
         json.dumps([
             {"kpi_name": "采购成本降幅", "target": 10, "unit": "%", "weight": 35},
             {"kpi_name": "到货及时率", "target": 95, "unit": "%", "weight": 30},
             {"kpi_name": "战略供应商数", "target": 10, "unit": "家", "weight": 20},
             {"kpi_name": "供应商考核完成率", "target": 100, "unit": "%", "weight": 15},
         ], ensure_ascii=False),
         "IN_PROGRESS", 6, None, None),

        # 品质部
        (6, 1, 7, 2026, None,
         json.dumps(["SPC覆盖100%关键工序", "客户投诉率<2%", "质量成本占比<3%"], ensure_ascii=False),
         json.dumps(["Q1质量体系审核", "Q2 SPC试点3条线", "Q3全面推广", "月度质量分析报告"], ensure_ascii=False),
         json.dumps([
             {"kpi_name": "关键工序SPC覆盖率", "target": 100, "unit": "%", "weight": 30},
             {"kpi_name": "客户投诉率", "target": 2, "unit": "%", "weight": 30},
             {"kpi_name": "质量成本占比", "target": 3, "unit": "%", "weight": 20},
             {"kpi_name": "纠正预防关闭率", "target": 95, "unit": "%", "weight": 20},
         ], ensure_ascii=False),
         "IN_PROGRESS", 7, None, None),

        # 人事行政部
        (7, 1, 8, 2026, None,
         json.dumps(["技术骨干留存率≥90%", "技术职级体系落地", "培训计划完成率100%"], ensure_ascii=False),
         json.dumps(["Q1发布技术职级标准", "Q2导师制启动", "Q3组织PM集训", "每月人才盘点"], ensure_ascii=False),
         json.dumps([
             {"kpi_name": "核心人才留存率", "target": 90, "unit": "%", "weight": 35},
             {"kpi_name": "培训计划完成率", "target": 100, "unit": "%", "weight": 25},
             {"kpi_name": "招聘到岗率", "target": 90, "unit": "%", "weight": 20},
             {"kpi_name": "员工满意度", "target": 80, "unit": "分", "weight": 20},
         ], ensure_ascii=False),
         "IN_PROGRESS", 8, None, None),
    ]
    for obj in dept_objectives:
        oid, sid, dept_id, year, quarter, objectives, key_results, kpis_config, \
            status, owner_user, approved_by, approved_at = obj
        c.execute("""INSERT OR REPLACE INTO department_objectives
            (id, strategy_id, department_id, year, quarter, objectives, key_results, kpis_config,
             status, owner_user_id, approved_by, approved_at, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
            (oid, sid, dept_id, year, quarter, objectives, key_results, kpis_config,
             status, owner_user, approved_by, approved_at, now, now))

    # ============================================================
    # 7. BEM 个人KPI (经理级 → 示范)
    # ============================================================
    personal_kpis = [
        # 销售总监 张志强
        (1, 2, 2026, 1, "CSF_KPI", 2, 1,
         "Q1新签合同额", "负责全公司Q1新签合同达成", "万元", 5000, 5100, 102.0, 30,
         5, "超额完成，比亚迪大单贡献大", 5, "表现优秀，继续保持大客户战略", "MANAGER_RATED"),
        (2, 2, 2026, 1, "CSF_KPI", 9, 1,
         "半导体客户开发", "Q1完成半导体行业调研和5家拜访", "家", 5, 3, 60.0, 20,
         3, "受春节影响延后", None, None, "SELF_RATED"),

        # 技术总监 李明华
        (3, 3, 2026, 1, "CSF_KPI", 15, 2,
         "标准模块入库", "Q1完成15个标准模块设计入库", "个", 15, 12, 80.0, 25,
         4, "已入库12个，3个在评审", None, None, "SELF_RATED"),
        (4, 3, 2026, 1, "ANNUAL_WORK", 1, 2,
         "EOL平台V2进度", "Q1完成方案设计和评审", "%", 100, 100, 100.0, 30,
         5, "方案评审通过，进入详细设计", 5, "按计划推进", "MANAGER_RATED"),

        # PMO总监 王建国
        (5, 4, 2026, 1, "CSF_KPI", 13, 3,
         "项目交付周期控制", "Q1在执行项目平均交付周期", "天", 85, 88, 96.5, 25,
         4, "设计阶段是瓶颈", None, None, "SELF_RATED"),
        (6, 4, 2026, 1, "CSF_KPI", 23, 3,
         "PMS系统推广", "Q1新项目100%入PMS", "%", 100, 100, 100.0, 25,
         5, "已完成，历史项目补录78%", 5, "推广力度好", "MANAGER_RATED"),

        # 生产总监 赵德胜
        (7, 5, 2026, 1, "CSF_KPI", 17, 4,
         "调试一次通过率", "Q1生产线调试一次通过率", "%", 93, 91, 97.8, 30,
         4, "Q1平均91%，还差目标", 4, "Q2导入SPC后预期提升", "MANAGER_RATED"),

        # 采购经理 陈伟
        (8, 6, 2026, 1, "CSF_KPI", 19, 5,
         "采购成本控制", "Q1关键物料采购成本降幅", "%", 3, 3.5, 116.7, 35,
         5, "伺服电机集中采购成功", 4, "后续空间有限", "MANAGER_RATED"),

        # 品质经理 刘芳
        (9, 7, 2026, 1, "CSF_KPI", 18, 6,
         "检验覆盖率提升", "Q1关键工序检验覆盖率", "%", 90, 88, 97.8, 30,
         4, "2条线已覆盖", None, None, "SELF_RATED"),

        # 大客户经理 杨超
        (10, 11, 2026, 1, "CSF_KPI", 7, 1,
         "战略客户营收", "Q1 TOP5客户营收达成", "万元", 2000, 2150, 107.5, 40,
         5, "比亚迪贡献1200万", 5, "客户关系维护好", "MANAGER_RATED"),

        # 高级PM 何俊
        (11, 13, 2026, 1, "ANNUAL_WORK", 4, 3,
         "并行工程试点", "Q1完成2个项目并行工程试点", "个", 2, 2, 100.0, 25,
         5, "2个项目试点完成，周期缩短15%", 4, "效果好但推广需培训", "MANAGER_RATED"),
    ]
    for p in personal_kpis:
        pid, emp_id, year, quarter, source_type, source_id, dept_obj_id, \
            kpi_name, kpi_desc, unit, target, actual, completion, weight, \
            self_rating, self_comment, mgr_rating, mgr_comment, status = p
        c.execute("""INSERT OR REPLACE INTO personal_kpis
            (id, employee_id, year, quarter, source_type, source_id, department_objective_id,
             kpi_name, kpi_description, unit, target_value, actual_value, completion_rate, weight,
             self_rating, self_comment, manager_rating, manager_comment, status,
             is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
            (pid, emp_id, year, quarter, source_type, source_id, dept_obj_id,
             kpi_name, kpi_desc, unit, target, actual, completion, weight,
             self_rating, self_comment, mgr_rating, mgr_comment, status, now, now))

    # ============================================================
    # 8. 战略审视记录 (Q1)
    # ============================================================
    c.execute("""INSERT OR REPLACE INTO strategy_reviews
        (id, strategy_id, review_type, review_date, review_period, reviewer_id,
         health_score, financial_score, customer_score, internal_score, learning_score,
         findings, achievements, recommendations, decisions, action_items,
         meeting_minutes, attendees, meeting_duration, next_review_date,
         is_active, created_at, updated_at)
        VALUES (1, 1, 'QUARTERLY', '2026-03-28', '2026-Q1', 1,
         72, 75, 65, 70, 78,
         ?, ?, ?, ?, ?,
         '2026年Q1战略审视会议纪要。与会人员：总经理符凌维、各部门总监/经理共10人。会议对Q1战略执行情况进行全面审视。',
         ?, 120, '2026-06-28', 1, ?, ?)""",
        (
            json.dumps([
                "营收Q1累计3310万，完成率88.3%，略低于预期",
                "半导体行业拓展进度滞后，尚未签约新客户",
                "应收账款周转108天，仍高于90天目标",
                "设计模块复用率42%，距60%目标差距较大",
                "综合毛利率31.2%，BOM偏差是主因"
            ], ensure_ascii=False),
            json.dumps([
                "新签合同额5100万，超额完成(目标4500万)",
                "EOL平台V2方案评审通过，进入详细设计",
                "PMS系统覆盖率78%，推广顺利",
                "技术骨干留存率88%，好于去年同期",
                "3个标准模块入库，标准化启动良好",
                "采购成本降幅3.5%，超Q1目标(3%)"
            ], ensure_ascii=False),
            json.dumps([
                "Q2加大半导体行业投入，拨专项预算80万",
                "成立报价优化小组，目标毛利率偏差<10%",
                "加速标准模块入库，Q2目标25个",
                "回款催收专项，Q2目标周转天数<100天",
                "SPC导入提前到Q2启动(原计划Q2)"
            ], ensure_ascii=False),
            json.dumps([
                "批准半导体行业拓展专项预算80万",
                "成立报价优化小组(技术+销售+财务)",
                "Q2增加2名标准化工程师编制",
                "启动客户分级回款机制"
            ], ensure_ascii=False),
            json.dumps([
                {"task": "半导体行业详细调研报告", "owner": "销售部张志强", "deadline": "2026-04-15"},
                {"task": "报价偏差分析及优化方案", "owner": "技术部李明华+财务黄志远", "deadline": "2026-04-30"},
                {"task": "SPC导入实施计划", "owner": "品质部刘芳", "deadline": "2026-04-20"},
                {"task": "标准模块库Q2入库计划", "owner": "技术部郑强", "deadline": "2026-04-10"},
                {"task": "客户分级回款方案", "owner": "销售部张志强+财务黄志远", "deadline": "2026-04-25"}
            ], ensure_ascii=False),
            json.dumps(["符凌维", "张志强", "李明华", "王建国", "赵德胜", "陈伟", "刘芳", "周丽", "黄志远", "林海"], ensure_ascii=False),
            now, now
        ))

    # ============================================================
    # 9. 战略日历事件 (例行管理节奏)
    # ============================================================
    calendar_events = [
        # Q1审视（已完成）
        (1, 1, "QUARTERLY_REVIEW", "Q1战略审视会", "2026年Q1战略执行回顾与评估",
         2026, 3, 1, "2026-03-28", "2026-03-28", "2026-03-25", 1, "QUARTERLY", 1,
         json.dumps([1,2,3,4,5,6,7,8,9,10], ensure_ascii=False), "COMPLETED", 1, 3, 1),
        # 4月KPI采集
        (2, 1, "KPI_COLLECTION", "4月KPI数据采集", "月度KPI数据更新与录入",
         2026, 4, None, "2026-04-05", None, "2026-04-03", 1, "MONTHLY", 4,
         None, "PLANNED", None, 2, 0),
        # 4月重点工作检查
        (3, 1, "MONTHLY_TRACKING", "4月重点工作月检", "检查10项年度重点工作进展",
         2026, 4, None, "2026-04-15", None, "2026-04-12", 1, "MONTHLY", 4,
         None, "PLANNED", None, 3, 0),
        # 5月KPI采集
        (4, 1, "KPI_COLLECTION", "5月KPI数据采集", "月度KPI数据更新与录入",
         2026, 5, None, "2026-05-05", None, "2026-05-03", 1, "MONTHLY", 4,
         None, "PLANNED", None, 2, 0),
        # Q2审视
        (5, 1, "QUARTERLY_REVIEW", "Q2战略审视会", "2026年Q2战略执行回顾与评估",
         2026, 6, 2, "2026-06-28", None, "2026-06-25", 1, "QUARTERLY", 1,
         json.dumps([1,2,3,4,5,6,7,8,9,10], ensure_ascii=False), "PLANNED", None, 5, 0),
        # 年中深度复盘
        (6, 1, "ANNUAL_PLANNING", "年中战略深度复盘", "半年度战略执行深度评估，调整下半年重点",
         2026, 7, None, "2026-07-15", None, "2026-07-10", 0, None, 1,
         json.dumps([1,2,3,4,5,6,7,8,9,10], ensure_ascii=False), "PLANNED", None, 7, 0),
        # Q3审视
        (7, 1, "QUARTERLY_REVIEW", "Q3战略审视会", "2026年Q3战略执行回顾与评估",
         2026, 9, 3, "2026-09-28", None, "2026-09-25", 1, "QUARTERLY", 1,
         json.dumps([1,2,3,4,5,6,7,8,9,10], ensure_ascii=False), "PLANNED", None, 5, 0),
        # 部门目标分解
        (8, 1, "DECOMPOSITION", "Q2个人KPI分解下达", "Q2个人KPI设定与确认",
         2026, 4, 2, "2026-04-08", None, "2026-04-05", 1, "QUARTERLY", 8,
         None, "PLANNED", None, 3, 0),
        # 年度绩效评估
        (9, 1, "ASSESSMENT", "Q1绩效评估", "Q1个人绩效自评+上级评价",
         2026, 4, 1, "2026-04-10", None, "2026-04-08", 1, "QUARTERLY", 8,
         None, "PLANNED", None, 3, 0),
    ]
    for e in calendar_events:
        eid, sid, etype, name, desc, year, month, quarter, \
            sched_date, actual_date, deadline, is_recur, recur_rule, owner, \
            participants, status, review_id, reminder_days, reminder_sent = e
        c.execute("""INSERT OR REPLACE INTO strategy_calendar_events
            (id, strategy_id, event_type, name, description, year, month, quarter,
             scheduled_date, actual_date, deadline, is_recurring, recurrence_rule,
             owner_user_id, participants, status, review_id, reminder_days, reminder_sent,
             is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
            (eid, sid, etype, name, desc, year, month, quarter,
             sched_date, actual_date, deadline, is_recur, recur_rule, owner,
             participants, status, review_id, reminder_days, reminder_sent, now, now))

    # ============================================================
    # 10. 同比分析 (2026 vs 2025)
    # ============================================================
    c.execute("""INSERT OR REPLACE INTO strategy_comparisons
        (id, current_strategy_id, previous_strategy_id, current_year, previous_year,
         generated_date, generated_by,
         current_health_score, previous_health_score, health_change,
         current_financial_score, previous_financial_score, financial_change,
         current_customer_score, previous_customer_score, customer_change,
         current_internal_score, previous_internal_score, internal_change,
         current_learning_score, previous_learning_score, learning_change,
         kpi_completion_rate, previous_kpi_completion_rate, kpi_completion_change,
         work_completion_rate, previous_work_completion_rate, work_completion_change,
         summary, highlights, improvements, recommendations,
         is_active, created_at, updated_at)
        VALUES (1, 1, 2, 2026, 2025, ?, 1,
         72, 62, 10,
         75, 65, 10,
         65, 58, 7,
         70, 61, 9,
         78, 55, 23,
         82.5, 71.2, 11.3,
         30.8, 25.0, 5.8,
         ?, ?, ?, ?,
         1, ?, ?)""",
        (
            today,
            json.dumps("2026年Q1战略执行整体优于2025年同期。总健康度提升10分(72 vs 62)。学习成长维度提升最大(+23分)，得益于PMS系统推广和标准化启动。客户维度提升最小(+7分)，半导体行业拓展尚未突破。", ensure_ascii=False),
            json.dumps([
                "学习成长维度大幅提升(+23分) — PMS覆盖率从45%→78%",
                "新签合同额Q1超额完成(5100万 vs 目标4500万)",
                "财务维度提升10分 — 采购成本优化3.5%",
                "调试一次通过率改善(91% vs 去年85%)",
                "技术骨干留存率提升(88% vs 去年82%)"
            ], ensure_ascii=False),
            json.dumps([
                "客户维度提升最小(+7分) — 半导体拓展0签约",
                "毛利率31.2%仍低于35%目标 — BOM偏差是主因",
                "应收账款108天 — 回款效率需大幅改善",
                "设计复用率42% — 距离60%目标还有差距",
                "验收一次通过率74% — 低于85%目标"
            ], ensure_ascii=False),
            json.dumps([
                "Q2半导体行业必须突破 — 建议参加SEMICON China展会",
                "成立报价优化小组 — 从BOM准确率和工时预估两头抓",
                "加大标准模块库投入 — Q2目标从15→25个",
                "建立客户分级回款机制 — 大客户30/60/90天节奏",
                "SPC导入提前启动 — 先从调试工序切入"
            ], ensure_ascii=False),
            now, now
        ))

    conn.commit()
    conn.close()

    print("=" * 60)
    print("✅ 金凯博 BLM + BEM 战略管理种子数据导入完成!")
    print("=" * 60)
    print()
    print("📊 数据概览:")
    print(f"  🏢 租户: 1 (深圳金凯博)")
    print(f"  🏗️ 部门: 10 个 (总经办+9个职能部门)")
    print(f"  👤 员工: 20 人 (管理层10+骨干10)")
    print(f"  🔑 用户: 15 个 (含admin)")
    print(f"  🎭 角色: 15 个")
    print()
    print("📈 BLM 战略制定:")
    print(f"  🎯 战略: 2 个 (2025归档 + 2026生效)")
    print()
    print("📋 BEM 战略解码:")
    print(f"  🔑 CSF: 13 个 (BSC四维度: 财务3/客户3/内部4/学习3)")
    print(f"  📊 KPI: 26 个 (IPOOC分类, 含阈值和当前值)")
    print(f"  📈 KPI历史: 26 条 (1-3月月度快照)")
    print(f"  📋 重点工作: 10 项 (VOC法导出)")
    print(f"  🏢 部门目标: 7 个 (7个部门OKR)")
    print(f"  👤 个人KPI: 11 条 (经理级Q1)")
    print(f"  🔍 审视记录: 1 条 (Q1季度审视)")
    print(f"  📅 日历事件: 9 个 (全年管理节奏)")
    print(f"  📊 同比分析: 1 条 (2026 vs 2025)")
    print()
    print("🔗 BLM→BEM 全链路:")
    print("  战略(BLM市场洞察/愿景) → CSF(BSC四维度)")
    print("  → KPI(IPOOC量化) → 重点工作(VOC法)")
    print("  → 部门目标(OKR) → 个人KPI(PBC)")
    print("  → 审视(PDCA) → 同比(持续改进)")
    print()
    print("👥 登录账号:")
    print("  admin / admin123    — 系统管理员(全量权限)")
    print("  fulingwei / admin123 — 总经理(战略全景)")
    print("  zhangzq / 123456    — 销售总监(部门视角)")
    print("  limh / 123456       — 技术总监(部门视角)")
    print("  wangjg / 123456     — PMO总监(部门视角)")
    print("  其他部门经理 / 123456")


if __name__ == "__main__":
    seed()
