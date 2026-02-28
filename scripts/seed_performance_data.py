#!/usr/bin/env python3
"""
绩效考核模块种子数据
创建考核周期、指标、考核结果、评价记录
"""
import sqlite3
import json
from datetime import datetime

DB_PATH = "data/app.db"

def seed():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ==================== 1. 考核周期 ====================
    periods = [
        (1, '2026-Q1', '2026年第一季度考核', 'quarterly', '2026-01-01', '2026-03-31', 'completed', 1, '2026-04-05', '2026-04-10', '2026-04-15', None),
        (2, '2026-Q2', '2026年第二季度考核', 'quarterly', '2026-04-01', '2026-06-30', 'in_progress', 1, '2026-07-05', '2026-07-10', None, None),
        (3, '2026-03', '2026年3月月度考核', 'monthly', '2026-03-01', '2026-03-31', 'completed', 1, '2026-04-03', '2026-04-05', '2026-04-08', None),
        (4, '2026-04', '2026年4月月度考核', 'monthly', '2026-04-01', '2026-04-30', 'in_progress', 1, '2026-05-03', '2026-05-05', None, None),
        (5, '2025-ANNUAL', '2025年度考核', 'annual', '2025-01-01', '2025-12-31', 'completed', 1, '2026-01-15', '2026-01-20', '2026-01-25', None),
    ]
    for p in periods:
        c.execute("""INSERT OR REPLACE INTO performance_period
            (id, period_code, period_name, period_type, start_date, end_date, status, is_active,
             calculate_date, review_deadline, finalize_date, remarks, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (*p, now, now))

    # ==================== 2. 考核指标 ====================
    indicators = [
        # 通用指标
        (1, 'IND-001', '工作量完成率', 'quantitative', '实际完成工时/计划工时*100', 'PMS系统', 20, 
         json.dumps({"90-100": 20, "80-89": 16, "70-79": 12, "60-69": 8, "<60": 4}, ensure_ascii=False),
         20, 0, json.dumps(["engineer", "manager"], ensure_ascii=False), None, 1, 1),
        (2, 'IND-002', '任务按时完成率', 'quantitative', '按时完成任务数/总任务数*100', 'PMS系统', 15,
         json.dumps({"95-100": 15, "85-94": 12, "75-84": 9, "65-74": 6, "<65": 3}, ensure_ascii=False),
         15, 0, json.dumps(["engineer", "manager"], ensure_ascii=False), None, 1, 2),
        (3, 'IND-003', '质量评分', 'quantitative', '项目质量检查得分', '质量部', 15,
         json.dumps({"90-100": 15, "80-89": 12, "70-79": 9, "<70": 5}, ensure_ascii=False),
         15, 0, json.dumps(["engineer"], ensure_ascii=False), None, 1, 3),
        (4, 'IND-004', '团队协作', 'qualitative', '跨部门协作和沟通能力评价', '360评价', 10,
         json.dumps({"优秀": 10, "良好": 8, "合格": 6, "待改进": 3}, ensure_ascii=False),
         10, 0, json.dumps(["engineer", "manager"], ensure_ascii=False), None, 1, 4),
        (5, 'IND-005', '创新与改进', 'qualitative', '流程改进建议、技术创新贡献', '上级评价', 10,
         json.dumps({"突出": 10, "良好": 8, "一般": 5, "无": 2}, ensure_ascii=False),
         10, 0, json.dumps(["engineer", "manager"], ensure_ascii=False), None, 1, 5),
        (6, 'IND-006', '客户满意度', 'quantitative', '客户满意度评分', '客服部', 15,
         json.dumps({"90-100": 15, "80-89": 12, "70-79": 9, "<70": 5}, ensure_ascii=False),
         15, 0, json.dumps(["manager"], ensure_ascii=False), None, 1, 6),
        (7, 'IND-007', '部门目标达成率', 'quantitative', '部门KPI达成比例', '战略管理', 15,
         json.dumps({"90-100": 15, "80-89": 12, "70-79": 9, "<70": 5}, ensure_ascii=False),
         15, 0, json.dumps(["manager"], ensure_ascii=False), None, 1, 7),
    ]
    for ind in indicators:
        c.execute("""INSERT OR REPLACE INTO performance_indicator
            (id, indicator_code, indicator_name, indicator_type, calculation_formula,
             data_source, weight, scoring_rules, max_score, min_score,
             apply_to_roles, apply_to_depts, is_active, sort_order, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (*ind, now, now))

    # ==================== 3. 考核结果 ====================
    # Q1 results for several employees
    results = [
        # (id, period_id, user_id, user_name, dept_id, dept_name, total_score, level, workload, task, quality, collab, growth, indicator_scores, dept_rank)
        (1, 1, 2, '郑汝才', 1, '销售部', 87.5, 'A', 18, 14, 13, 9, 8,
         json.dumps({"IND-001": 18, "IND-002": 14, "IND-003": 13, "IND-004": 9, "IND-005": 8, "IND-006": 13, "IND-007": 12.5}, ensure_ascii=False), 1),
        (2, 1, 3, '骆奕兴', 3, '研发部', 82.0, 'B+', 16, 13, 14, 8, 9,
         json.dumps({"IND-001": 16, "IND-002": 13, "IND-003": 14, "IND-004": 8, "IND-005": 9, "IND-006": 12, "IND-007": 10}, ensure_ascii=False), 1),
        (3, 1, 4, '符凌维', 8, '总经办', 91.0, 'A+', 19, 14, 14, 10, 9,
         json.dumps({"IND-001": 19, "IND-002": 14, "IND-003": 14, "IND-004": 10, "IND-005": 9, "IND-006": 13, "IND-007": 12}, ensure_ascii=False), 1),
        (4, 1, 5, '宋魁', 4, '生产部', 78.5, 'B', 16, 12, 12, 7, 7,
         json.dumps({"IND-001": 16, "IND-002": 12, "IND-003": 12, "IND-004": 7, "IND-005": 7, "IND-006": 12, "IND-007": 12.5}, ensure_ascii=False), 1),
        (5, 1, 6, '郑琴', 7, '财务部', 85.0, 'A-', 17, 14, 13, 9, 8,
         json.dumps({"IND-001": 17, "IND-002": 14, "IND-003": 13, "IND-004": 9, "IND-005": 8, "IND-006": 12, "IND-007": 12}, ensure_ascii=False), 1),
        (6, 1, 7, '姚洪', 3, '研发部', 80.0, 'B+', 16, 12, 13, 8, 8,
         json.dumps({"IND-001": 16, "IND-002": 12, "IND-003": 13, "IND-004": 8, "IND-005": 8, "IND-006": 11, "IND-007": 12}, ensure_ascii=False), 2),
        (7, 1, 8, '常雄', 6, '采购部', 76.0, 'B', 15, 12, 11, 7, 7,
         json.dumps({"IND-001": 15, "IND-002": 12, "IND-003": 11, "IND-004": 7, "IND-005": 7, "IND-006": 12, "IND-007": 12}, ensure_ascii=False), 1),
        (8, 1, 9, '高勇', 4, '生产部', 83.0, 'B+', 17, 13, 13, 8, 8,
         json.dumps({"IND-001": 17, "IND-002": 13, "IND-003": 13, "IND-004": 8, "IND-005": 8, "IND-006": 12, "IND-007": 12}, ensure_ascii=False), 2),
        (9, 1, 10, '陈亮', 5, '客服部', 84.0, 'B+', 17, 13, 12, 9, 8,
         json.dumps({"IND-001": 17, "IND-002": 13, "IND-003": 12, "IND-004": 9, "IND-005": 8, "IND-006": 13, "IND-007": 12}, ensure_ascii=False), 1),
    ]
    for r in results:
        c.execute("""INSERT OR REPLACE INTO performance_result
            (id, period_id, user_id, user_name, department_id, department_name,
             total_score, level, workload_score, task_score, quality_score,
             collaboration_score, growth_score, indicator_scores, dept_rank,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (*r, now, now))

    # ==================== 4. 评价记录 ====================
    evaluations = [
        # (id, result_id, evaluator_id, evaluator_name, evaluator_role, overall_comment, strength, improvement, adjusted_level, adjustment_reason)
        (1, 1, 4, '符凌维', 'direct_manager', '郑汝才Q1销售业绩突出，新签合同额超目标15%', '客户关系维护能力强，大客户复购率高', '需要加强新行业客户拓展', None, None),
        (2, 2, 4, '符凌维', 'direct_manager', '骆奕兴技术能力扎实，新能源平台方案设计出色', '技术创新能力强，专利意识好', '项目进度把控可以更紧', None, None),
        (3, 3, 1, '系统管理员', 'hr', '符凌维统筹全局能力强，PMS系统推进有力', '战略思维清晰，执行力强', '需要更多授权给部门经理', 'A+', '综合表现优秀'),
        (4, 4, 4, '符凌维', 'direct_manager', '宋魁生产管理基本到位，但交付周期控制需改进', '现场管理经验丰富', '需要提升数字化管理能力', None, None),
        (5, 5, 4, '符凌维', 'direct_manager', '郑琴财务管理规范，预算控制良好', '财务分析能力强，风险意识好', '需要更主动参与业务决策', None, None),
    ]
    for e in evaluations:
        c.execute("""INSERT OR REPLACE INTO performance_evaluation
            (id, result_id, evaluator_id, evaluator_name, evaluator_role,
             overall_comment, strength_comment, improvement_comment,
             adjusted_level, adjustment_reason, evaluated_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (*e, now, now, now))

    # ==================== 5. 绩效排名快照 ====================
    c.execute("""SELECT name FROM sqlite_master WHERE type='table' AND name='performance_ranking_snapshot'""")
    if c.fetchone():
        rankings = [
            (1, 1, 3, '符凌维', 8, '总经办', 91.0, 'A+', 1, 1, 9),
            (2, 1, 2, '郑汝才', 1, '销售部', 87.5, 'A', 2, 1, 9),
            (3, 1, 6, '郑琴', 7, '财务部', 85.0, 'A-', 3, 1, 9),
            (4, 1, 10, '陈亮', 5, '客服部', 84.0, 'B+', 4, 1, 9),
            (5, 1, 9, '高勇', 4, '生产部', 83.0, 'B+', 5, 2, 9),
            (6, 1, 3, '骆奕兴', 3, '研发部', 82.0, 'B+', 6, 1, 9),
            (7, 1, 7, '姚洪', 3, '研发部', 80.0, 'B+', 7, 2, 9),
            (8, 1, 5, '宋魁', 4, '生产部', 78.5, 'B', 8, 1, 9),
            (9, 1, 8, '常雄', 6, '采购部', 76.0, 'B', 9, 1, 9),
        ]
        cols = "PRAGMA table_info(performance_ranking_snapshot)"
        c.execute(cols)
        col_names = [row[1] for row in c.fetchall()]
        if 'company_rank' in col_names:
            for r in rankings:
                c.execute("""INSERT OR REPLACE INTO performance_ranking_snapshot
                    (id, period_id, user_id, user_name, department_id, department_name,
                     total_score, level, company_rank, dept_rank, total_employees,
                     created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (*r, now))
            print("  ✓ 绩效排名快照已创建")
        else:
            print("  ⚠ performance_ranking_snapshot 表结构不匹配，跳过")
    else:
        print("  ⚠ performance_ranking_snapshot 表不存在，跳过")

    conn.commit()
    conn.close()
    print("✅ 绩效考核种子数据已导入:")
    print("  - 5个考核周期 (Q1完成/Q2进行中/3月完成/4月进行中/2025年度)")
    print("  - 7个考核指标 (定量+定性)")
    print("  - 9条Q1考核结果 (含评分和排名)")
    print("  - 5条评价记录")

if __name__ == "__main__":
    seed()
