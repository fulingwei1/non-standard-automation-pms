#!/usr/bin/env python3
"""
战略管理模块种子数据
金凯博2026年战略 - BSC四维度完整数据链
"""
import sqlite3
import json
from datetime import datetime, date

DB_PATH = "data/app.db"

def seed():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = date.today().strftime("%Y-%m-%d")

    # ==================== 1. 战略 ====================
    c.execute("""INSERT OR REPLACE INTO strategies 
        (id, code, name, vision, mission, slogan, year, start_date, end_date, status, created_by, is_active, published_at, created_at, updated_at)
        VALUES (1, 'STR-2026', '金凯博2026年战略规划', 
        '成为中国非标自动化测试设备领域的技术领导者和解决方案首选供应商',
        '以技术创新驱动，为新能源、消费电子、半导体客户提供高可靠性、高效率的自动化测试解决方案',
        '精测智造 引领未来',
        2026, '2026-01-01', '2026-12-31', 'published', 1, 1, ?, ?, ?)""",
        (now, now, now))
    
    # 2025年战略（用于同比）
    c.execute("""INSERT OR REPLACE INTO strategies 
        (id, code, name, vision, mission, slogan, year, start_date, end_date, status, created_by, is_active, published_at, created_at, updated_at)
        VALUES (2, 'STR-2025', '金凯博2025年战略规划',
        '成为华南地区非标自动化测试设备领军企业',
        '为制造业客户提供可靠的自动化测试解决方案',
        '品质为先 创新致远',
        2025, '2025-01-01', '2025-12-31', 'archived', 1, 0, ?, ?, ?)""",
        (now, now, now))

    # ==================== 2. CSF 关键成功因素 (BSC四维度) ====================
    csfs = [
        # 财务维度
        (1, 1, 'financial', 'CSF-F01', '营收规模突破', '实现年营收1.5亿目标，同比增长30%', 'swot', 0.30, 1, 1, None),
        (2, 1, 'financial', 'CSF-F02', '毛利率提升', '综合毛利率提升至35%以上', 'benchmarking', 0.20, 2, 1, None),
        (3, 1, 'financial', 'CSF-F03', '回款效率优化', '应收账款周转天数控制在90天内', 'value_chain', 0.15, 3, 1, None),
        # 客户维度
        (4, 1, 'customer', 'CSF-C01', '大客户深耕', '比亚迪/宁德时代等TOP5客户复购率>80%', 'voc', 0.25, 1, 1, None),
        (5, 1, 'customer', 'CSF-C02', '新行业拓展', '进入半导体测试设备领域，获取3个新客户', 'swot', 0.20, 2, 1, None),
        (6, 1, 'customer', 'CSF-C03', '客户满意度提升', 'NPS评分达到70+', 'voc', 0.15, 3, 1, None),
        # 内部流程维度
        (7, 1, 'internal', 'CSF-I01', '项目交付效率', '项目平均交付周期缩短20%', 'value_chain', 0.25, 1, 1, None),
        (8, 1, 'internal', 'CSF-I02', '质量管理升级', '产品一次通过率>95%', 'benchmarking', 0.20, 2, 1, None),
        (9, 1, 'internal', 'CSF-I03', '供应链优化', '关键物料采购成本降低10%', 'value_chain', 0.15, 3, 1, None),
        # 学习与成长维度
        (10, 1, 'learning', 'CSF-L01', '核心人才培养', '技术骨干留存率>90%，培养5名项目经理', 'swot', 0.25, 1, 1, None),
        (11, 1, 'learning', 'CSF-L02', '数字化转型', 'PMS系统覆盖100%项目，实现数据驱动决策', 'benchmarking', 0.20, 2, 1, None),
        (12, 1, 'learning', 'CSF-L03', '技术创新储备', '申请3项发明专利，完成2个技术预研项目', 'swot', 0.15, 3, 1, None),
    ]
    for csf in csfs:
        c.execute("""INSERT OR REPLACE INTO csfs 
            (id, strategy_id, dimension, code, name, description, derivation_method, weight, sort_order, is_active, owner_dept_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (*csf, now, now))

    # ==================== 3. KPI ====================
    kpis = [
        # 财务KPI
        (1, 1, 'KPI-F01', '年度营收', '年度总营收金额', 'output', '万元', 'higher', 15000, 11500, 4200, 16000, 14000, 12000, 'manual', 'monthly', 0.15),
        (2, 1, 'KPI-F02', '新签合同额', '年度新签合同总额', 'output', '万元', 'higher', 18000, 14000, 5600, 19000, 17000, 15000, 'manual', 'monthly', 0.10),
        (3, 2, 'KPI-F03', '综合毛利率', '项目综合毛利率', 'output', '%', 'higher', 35, 28, 31, 38, 34, 30, 'system', 'monthly', 0.10),
        (4, 3, 'KPI-F04', '应收周转天数', '应收账款平均周转天数', 'output', '天', 'lower', 90, 120, 105, 80, 95, 110, 'manual', 'monthly', 0.08),
        # 客户KPI
        (5, 4, 'KPI-C01', 'TOP5客户复购率', '前5大客户复购率', 'output', '%', 'higher', 80, 65, 72, 85, 78, 70, 'manual', 'quarterly', 0.10),
        (6, 5, 'KPI-C02', '半导体新客户数', '半导体行业新客户签约数', 'output', '个', 'higher', 3, 0, 1, 4, 3, 2, 'manual', 'quarterly', 0.08),
        (7, 6, 'KPI-C03', 'NPS评分', '客户净推荐值评分', 'output', '分', 'higher', 70, 55, 62, 75, 68, 60, 'manual', 'quarterly', 0.07),
        # 内部流程KPI
        (8, 7, 'KPI-I01', '平均交付周期', '项目从签约到验收的平均天数', 'process', '天', 'lower', 75, 95, 88, 70, 80, 90, 'system', 'monthly', 0.08),
        (9, 8, 'KPI-I02', '一次通过率', '产品一次性通过率', 'process', '%', 'higher', 95, 88, 91, 97, 94, 90, 'system', 'monthly', 0.07),
        (10, 9, 'KPI-I03', '采购成本降幅', '关键物料采购成本同比降幅', 'process', '%', 'higher', 10, 0, 4.5, 12, 9, 6, 'manual', 'quarterly', 0.05),
        # 学习成长KPI
        (11, 10, 'KPI-L01', '技术骨干留存率', '核心技术人员年度留存率', 'input', '%', 'higher', 90, 82, 88, 95, 88, 85, 'manual', 'quarterly', 0.05),
        (12, 11, 'KPI-L02', 'PMS系统覆盖率', '项目管理系统覆盖项目百分比', 'input', '%', 'higher', 100, 45, 75, 100, 90, 70, 'system', 'monthly', 0.04),
        (13, 12, 'KPI-L03', '专利申请数', '年度发明专利申请数量', 'input', '项', 'higher', 3, 1, 1, 4, 3, 2, 'manual', 'quarterly', 0.03),
    ]
    for kpi in kpis:
        c.execute("""INSERT OR REPLACE INTO kpis 
            (id, csf_id, code, name, description, ipooc_type, unit, direction, 
             target_value, baseline_value, current_value, excellent_threshold, good_threshold, warning_threshold,
             data_source_type, frequency, weight, owner_user_id, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?)""",
            (*kpi, now, now))

    # ==================== 4. KPI历史数据 ====================
    kpi_history = [
        # (id, kpi_id, snapshot_date, snapshot_period, value, target_value, completion_rate, health_level, remark)
        (1, 1, '2026-01-31', '2026-01', 1050, 1250, 84.0, 'warning', '1月营收'),
        (2, 1, '2026-02-28', '2026-02', 980, 1250, 78.4, 'warning', '春节月份略低'),
        (3, 1, '2026-03-31', '2026-03', 1280, 1250, 102.4, 'good', 'Q1收官冲刺'),
        (4, 1, '2026-04-30', '2026-04', 890, 1250, 71.2, 'danger', None),
        (5, 3, '2026-01-31', '2026-01', 32.5, 35, 92.9, 'good', None),
        (6, 3, '2026-02-28', '2026-02', 30.8, 35, 88.0, 'warning', '春节期间固定成本分摊高'),
        (7, 3, '2026-03-31', '2026-03', 33.2, 35, 94.9, 'good', None),
        (8, 3, '2026-04-30', '2026-04', 31.5, 35, 90.0, 'warning', None),
        (9, 7, '2026-03-31', '2026-Q1', 62, 70, 88.6, 'warning', 'Q1客户满意度调查'),
        (10, 9, '2026-01-31', '2026-01', 89, 95, 93.7, 'warning', None),
        (11, 9, '2026-02-28', '2026-02', 92, 95, 96.8, 'good', '质量改进措施生效'),
        (12, 9, '2026-03-31', '2026-03', 91, 95, 95.8, 'good', None),
    ]
    for h in kpi_history:
        c.execute("""INSERT OR REPLACE INTO kpi_history 
            (id, kpi_id, snapshot_date, snapshot_period, value, target_value, completion_rate, health_level, remark, source_type, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'manual', ?, ?)""",
            (*h, now, now))

    # ==================== 5. 年度重点工作 ====================
    works = [
        (1, 1, 'AW-01', '新能源测试平台研发', '开发新一代电池包EOL测试平台', 'customer', '客户反馈现有测试效率低', '模块化设计+AI视觉检测', '完成3个标准化产品型号',
         2026, '2026-01-15', '2026-08-31', '2026-01-20', None, 1, None, 'in_progress', 45, 'high', 200, 85, None, None),
        (2, 2, 'AW-02', '综合毛利率提升专项', '通过设计优化和供应链改善提升毛利', 'internal', '毛利率低于行业平均', '标准化模块复用+集中采购', '毛利率达到35%',
         2026, '2026-02-01', '2026-12-31', '2026-02-05', None, 1, None, 'in_progress', 28, 'high', 150, 42, None, None),
        (3, 5, 'AW-03', '半导体行业拓展', '进入半导体芯片测试领域', 'market', '新能源增速放缓需要新增长点', '与半导体设备代理商合作', '签约3个半导体客户',
         2026, '2026-03-01', '2026-11-30', None, None, 1, None, 'planned', 10, 'medium', 80, 8, '技术门槛高，需要引进专业人才', None),
        (4, 7, 'AW-04', '项目管理数字化', 'PMS系统全面上线覆盖所有项目', 'internal', '项目管理靠Excel和经验', '部署PMS+培训+流程优化', '100%项目线上管理',
         2026, '2026-01-01', '2026-06-30', '2026-01-05', None, 1, None, 'in_progress', 75, 'high', 50, 38, None, None),
        (5, 10, 'AW-05', '技术骨干培养计划', '建立技术梯队和项目经理培养体系', 'internal', '核心人才流失风险', '导师制+轮岗+项目锻炼', '培养5名合格项目经理',
         2026, '2026-02-01', '2026-12-31', '2026-02-10', None, 1, None, 'in_progress', 20, 'medium', 30, 6, None, None),
        (6, 8, 'AW-06', '质量管理体系升级', '导入SPC统计过程控制', 'internal', '质量问题导致返工成本高', 'SPC+自动化测试+培训', '一次通过率>95%',
         2026, '2026-04-01', '2026-10-31', None, None, 1, None, 'planned', 5, 'medium', 40, 2, None, None),
    ]
    for w in works:
        c.execute("""INSERT OR REPLACE INTO annual_key_works
            (id, csf_id, code, name, description, voc_source, pain_point, solution, target,
             year, start_date, end_date, actual_start_date, actual_end_date, owner_user_id, owner_dept_id,
             status, progress_percent, priority, budget, actual_cost, risk_description, remark, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
            (*w, now, now))

    # ==================== 6. 部门目标分解 ====================
    dept_objectives = [
        (1, 1, 1, 2026, None,  # 研发部
         json.dumps(["完成3个标准化测试平台研发", "申请3项发明专利", "建立技术预研机制"], ensure_ascii=False),
         json.dumps(["Q2完成电池包EOL平台V2", "Q3完成ICT标准化模块", "每季度1项专利申请"], ensure_ascii=False),
         json.dumps([{"kpi_name": "研发项目完成率", "target": 90, "unit": "%"}, {"kpi_name": "专利申请数", "target": 3, "unit": "项"}], ensure_ascii=False),
         'active', 1, None, None),
        (2, 1, 2, 2026, None,  # 销售部
         json.dumps(["完成1.8亿新签合同", "拓展半导体行业客户", "TOP5客户复购率>80%"], ensure_ascii=False),
         json.dumps(["Q1新签5000万", "Q2锁定2个半导体意向客户", "每月客户回访"], ensure_ascii=False),
         json.dumps([{"kpi_name": "新签合同额", "target": 18000, "unit": "万元"}, {"kpi_name": "新客户数", "target": 8, "unit": "个"}], ensure_ascii=False),
         'active', 1, None, None),
        (3, 1, 3, 2026, None,  # 生产部
         json.dumps(["项目交付周期缩短20%", "一次通过率>95%", "产能提升25%"], ensure_ascii=False),
         json.dumps(["Q1建立标准工序库", "Q2导入SPC", "Q3实现产线柔性化"], ensure_ascii=False),
         json.dumps([{"kpi_name": "平均交付周期", "target": 75, "unit": "天"}, {"kpi_name": "一次通过率", "target": 95, "unit": "%"}], ensure_ascii=False),
         'active', 1, None, None),
        (4, 1, 4, 2026, None,  # 采购部
         json.dumps(["关键物料采购成本降低10%", "供应商准时交付率>95%", "建立战略供应商体系"], ensure_ascii=False),
         json.dumps(["Q1完成供应商分级", "Q2签订年度框架协议", "Q3导入第二供应商"], ensure_ascii=False),
         json.dumps([{"kpi_name": "采购成本降幅", "target": 10, "unit": "%"}, {"kpi_name": "准时交付率", "target": 95, "unit": "%"}], ensure_ascii=False),
         'active', 1, None, None),
    ]
    for obj in dept_objectives:
        c.execute("""INSERT OR REPLACE INTO department_objectives
            (id, strategy_id, department_id, year, quarter, objectives, key_results, kpis_config,
             status, owner_user_id, approved_by, approved_at, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
            (*obj, now, now))

    # ==================== 7. 个人KPI ====================
    personal = [
        (1, 1, 2026, 1, 'kpi', 1, 1, '季度营收目标', '负责区域季度营收达成', '万元', 3800, 4200, 110.5, 0.30, 5, '超额完成', 5, '表现优秀', 'completed'),
        (2, 2, 2026, 1, 'kpi', 5, 1, '客户拜访计划', '完成Q1客户拜访计划', '次', 20, 18, 90.0, 0.20, 4, '基本完成', 4, '部分客户因疫情取消', 'completed'),
        (3, 3, 2026, 1, 'work', 1, None, '新能源平台进度', 'Q1完成方案设计和原型', '%', 100, 95, 95.0, 0.25, 4, '方案已通过评审', None, None, 'in_progress'),
        (4, 4, 2026, 1, 'kpi', 8, 2, '交付周期控制', 'Q1项目平均交付周期', '天', 85, 88, 96.5, 0.15, 3, '略超目标', None, None, 'in_progress'),
        (5, 5, 2026, 1, 'kpi', 10, 3, '采购成本优化', 'Q1采购成本降幅', '%', 3, 2.5, 83.3, 0.20, 3, '已启动但效果待显现', None, None, 'in_progress'),
    ]
    for p in personal:
        c.execute("""INSERT OR REPLACE INTO personal_kpis
            (id, employee_id, year, quarter, source_type, source_id, department_objective_id,
             kpi_name, kpi_description, unit, target_value, actual_value, completion_rate, weight,
             self_rating, self_comment, manager_rating, manager_comment, status, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
            (*p, now, now))

    # ==================== 8. 战略审视记录 ====================
    reviews = [
        (1, 1, 'quarterly', '2026-03-28', 'Q1', 1, 72, 75, 68, 70, 73,
         json.dumps(["营收增速低于预期", "半导体拓展尚未突破", "PMS系统推广顺利"], ensure_ascii=False),
         json.dumps(["新能源平台方案通过评审", "毛利率环比改善", "3项专利已提交"], ensure_ascii=False),
         json.dumps(["加大半导体行业投入", "优化报价流程提升毛利", "加快PMS培训进度"], ensure_ascii=False),
         json.dumps(["批准半导体专项预算80万", "成立报价优化小组"], ensure_ascii=False),
         json.dumps([{"task": "半导体行业调研报告", "owner": "销售部", "deadline": "2026-04-15"},
                     {"task": "报价优化方案", "owner": "技术部", "deadline": "2026-04-30"}], ensure_ascii=False),
         '全体高管参加，讨论了Q1执行情况和Q2重点', '["符总","张总","李总","王总","赵总"]', 120, '2026-06-28'),
    ]
    for r in reviews:
        c.execute("""INSERT OR REPLACE INTO strategy_reviews
            (id, strategy_id, review_type, review_date, review_period, reviewer_id, health_score,
             financial_score, customer_score, internal_score, learning_score,
             findings, achievements, recommendations, decisions, action_items,
             meeting_minutes, attendees, meeting_duration, next_review_date, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
            (*r, now, now))

    # ==================== 9. 战略日历事件 ====================
    events = [
        (1, 1, 'strategy_review', 'Q1战略审视会', '2026年Q1战略执行回顾', 2026, 3, 1, '2026-03-28', '2026-03-28', '2026-03-25', 1, 'quarterly', 1, '["1","2","3","4","5"]', 'completed', None, 3, 1),
        (2, 1, 'strategy_review', 'Q2战略审视会', '2026年Q2战略执行回顾', 2026, 6, 2, '2026-06-28', None, '2026-06-25', 1, 'quarterly', 1, '["1","2","3","4","5"]', 'scheduled', None, 3, 0),
        (3, 1, 'kpi_collection', '4月KPI数据采集', '月度KPI数据更新', 2026, 4, None, '2026-04-05', None, '2026-04-03', 1, 'monthly', 1, None, 'scheduled', None, 2, 0),
        (4, 1, 'annual_work_review', '年度重点工作月度检查', '检查6项重点工作进展', 2026, 4, None, '2026-04-15', None, '2026-04-12', 1, 'monthly', 1, None, 'scheduled', None, 3, 0),
        (5, 1, 'strategy_review', '年中战略复盘', '半年度战略执行深度复盘', 2026, 7, None, '2026-07-15', None, '2026-07-10', 0, None, 1, '["1","2","3","4","5"]', 'scheduled', None, 5, 0),
    ]
    for e in events:
        c.execute("""INSERT OR REPLACE INTO strategy_calendar_events
            (id, strategy_id, event_type, name, description, year, month, quarter,
             scheduled_date, actual_date, deadline, is_recurring, recurrence_rule,
             owner_user_id, participants, status, review_id, reminder_days, reminder_sent,
             is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)""",
            (*e, now, now))

    # ==================== 10. 同比分析 ====================
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
         72, 65, 7, 75, 68, 7, 68, 62, 6, 70, 64, 6, 73, 60, 13,
         78.5, 71.2, 7.3, 65.0, 58.0, 7.0,
         ?, ?, ?, ?,
         1, ?, ?)""",
        (today, 
         json.dumps("2026年Q1整体战略执行优于2025年同期，健康度提升7分", ensure_ascii=False),
         json.dumps(["学习成长维度提升最大(+13分)", "PMS系统推广成效显著", "技术专利申请超进度"], ensure_ascii=False),
         json.dumps(["客户维度提升幅度最小(+6分)", "半导体行业拓展需加速", "回款效率仍需改善"], ensure_ascii=False),
         json.dumps(["加大半导体行业资源投入", "建立客户分级回款机制", "Q2重点推进质量管理升级"], ensure_ascii=False),
         now, now))

    conn.commit()
    conn.close()
    print("✅ 战略管理种子数据已导入:")
    print("  - 2条战略 (2025+2026)")
    print("  - 12个CSF (BSC四维度)")
    print("  - 13个KPI (含阈值和当前值)")
    print("  - 12条KPI历史数据")
    print("  - 6项年度重点工作")
    print("  - 4个部门目标分解")
    print("  - 5个个人KPI")
    print("  - 1条战略审视记录")
    print("  - 5个日历事件")
    print("  - 1条同比分析")

if __name__ == "__main__":
    seed()
