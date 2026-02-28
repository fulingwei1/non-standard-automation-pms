#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
绩效合约种子数据脚本

创建示例绩效合约数据：
- 1 份 L1 合约（公司↔总经理，6 个经营指标）
- 2 份 L2 合约（总经理↔研发部经理、总经理↔销售部经理，各 5 个指标）
- 3 份 L3 合约（部门经理↔员工，各 4 个指标）

指标与战略 KPI 关联（source_type='kpi', source_id=对应 kpi 的 id）
"""

import sqlite3
import os
from datetime import datetime, timedelta

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), "../data/app.db")


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_existing_kpis():
    """获取现有的 KPI 列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name, target_value, unit FROM strategy_kpis WHERE is_deleted = 0 LIMIT 20")
        kpis = cursor.fetchall()
        conn.close()
        return kpis
    except sqlite3.OperationalError:
        # 表不存在
        conn.close()
        return []


def get_existing_annual_works():
    """获取现有的年度重点工作"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, name FROM strategy_annual_works LIMIT 10")
        works = cursor.fetchall()
        conn.close()
        return works
    except sqlite3.OperationalError:
        # 表不存在
        conn.close()
        return []


def generate_contract_no(contract_type, year, suffix=None):
    """生成合约编号"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    import random
    random_suffix = random.randint(1000, 9999) if suffix is None else suffix
    return f"PC-{contract_type}-{year}-{timestamp}-{random_suffix}"


def create_contract(conn, contract_data):
    """创建合约"""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO performance_contracts (
            contract_no, contract_type, year, quarter,
            signer_id, signer_name, signer_title,
            counterpart_id, counterpart_name, counterpart_title,
            department_id, department_name,
            strategy_id, status,
            sign_date, effective_date, expiry_date,
            remarks, created_by, total_weight
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        contract_data['contract_no'],
        contract_data['contract_type'],
        contract_data['year'],
        contract_data.get('quarter'),
        contract_data.get('signer_id'),
        contract_data['signer_name'],
        contract_data.get('signer_title'),
        contract_data.get('counterpart_id'),
        contract_data['counterpart_name'],
        contract_data.get('counterpart_title'),
        contract_data.get('department_id'),
        contract_data.get('department_name'),
        contract_data.get('strategy_id'),
        contract_data.get('status', 'draft'),
        contract_data.get('sign_date'),
        contract_data.get('effective_date'),
        contract_data.get('expiry_date'),
        contract_data.get('remarks'),
        contract_data.get('created_by', 1),
        0  # total_weight will be calculated after items are added
    ))
    return cursor.lastrowid


def create_item(conn, item_data):
    """创建指标条目"""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO performance_contract_items (
            contract_id, sort_order, category, indicator_name,
            indicator_description, weight, unit,
            target_value, challenge_value, baseline_value,
            scoring_rule, data_source, evaluation_method,
            source_type, source_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item_data['contract_id'],
        item_data['sort_order'],
        item_data['category'],
        item_data['indicator_name'],
        item_data.get('indicator_description'),
        item_data['weight'],
        item_data.get('unit'),
        item_data.get('target_value'),
        item_data.get('challenge_value'),
        item_data.get('baseline_value'),
        item_data.get('scoring_rule'),
        item_data.get('data_source'),
        item_data.get('evaluation_method'),
        item_data.get('source_type', 'custom'),
        item_data.get('source_id')
    ))
    return cursor.lastrowid


def init_tables():
    """初始化数据表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建绩效合约表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance_contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_no TEXT UNIQUE NOT NULL,
            contract_type TEXT NOT NULL CHECK(contract_type IN ('L1', 'L2', 'L3')),
            year INTEGER NOT NULL,
            quarter INTEGER,
            signer_id INTEGER,
            signer_name TEXT NOT NULL,
            signer_title TEXT,
            counterpart_id INTEGER,
            counterpart_name TEXT NOT NULL,
            counterpart_title TEXT,
            department_id INTEGER,
            department_name TEXT,
            strategy_id INTEGER,
            status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft', 'pending_review', 'pending_sign', 'active', 'completed', 'terminated')),
            total_weight REAL DEFAULT 0,
            sign_date DATE,
            effective_date DATE,
            expiry_date DATE,
            signer_signature DATETIME,
            counterpart_signature DATETIME,
            remarks TEXT,
            created_by INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建绩效合约指标条目表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance_contract_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER NOT NULL,
            sort_order INTEGER DEFAULT 0,
            category TEXT NOT NULL CHECK(category IN ('业绩指标', '管理指标', '能力指标', '态度指标')),
            indicator_name TEXT NOT NULL,
            indicator_description TEXT,
            weight REAL NOT NULL,
            unit TEXT,
            target_value TEXT,
            challenge_value TEXT,
            baseline_value TEXT,
            scoring_rule TEXT,
            data_source TEXT,
            evaluation_method TEXT,
            actual_value TEXT,
            score REAL,
            evaluator_comment TEXT,
            source_type TEXT CHECK(source_type IN ('kpi', 'work', 'custom')),
            source_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contract_id) REFERENCES performance_contracts(id) ON DELETE CASCADE
        )
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contract_type ON performance_contracts(contract_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contract_status ON performance_contracts(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contract_year ON performance_contracts(year)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_contract ON performance_contract_items(contract_id)")
    
    conn.commit()
    conn.close()
    print("✓ 数据表初始化完成")


def seed_performance_contracts():
    """主函数 - 创建种子数据"""
    print("🌱 开始创建绩效合约种子数据...")
    
    # 先初始化表
    init_tables()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 获取现有的 KPI 和年度工作
        kpis = get_existing_kpis()
        annual_works = get_existing_annual_works()
        
        print(f"   找到 {len(kpis)} 个 KPI, {len(annual_works)} 个年度重点工作")
        
        # 获取当前年份
        current_year = datetime.now().year
        
        contracts_created = []
        items_created = 0
        
        # ==================== L1 合约：公司↔总经理 ====================
        print("\n📋 创建 L1 合约（公司级）...")
        
        l1_contract = {
            'contract_no': generate_contract_no('L1', current_year),
            'contract_type': 'L1',
            'year': current_year,
            'signer_name': '张三',
            'signer_title': '总经理',
            'counterpart_name': '董事会',
            'counterpart_title': '董事长',
            'department_name': '公司管理层',
            'status': 'active',
            'sign_date': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            'effective_date': f'{current_year}-01-01',
            'expiry_date': f'{current_year}-12-31',
            'remarks': '年度经营目标责任状',
        }
        
        l1_contract_id = create_contract(conn, l1_contract)
        contracts_created.append(('L1', l1_contract_id))
        
        # L1 合约指标（6 个经营指标）
        l1_items = [
            {
                'contract_id': l1_contract_id,
                'sort_order': 1,
                'category': '业绩指标',
                'indicator_name': '年度营业收入',
                'indicator_description': '全年实现营业收入目标',
                'weight': 20,
                'unit': '万元',
                'target_value': '10000',
                'challenge_value': '12000',
                'baseline_value': '8000',
                'scoring_rule': '达成目标值得 100 分，每超 1% 加 1 分，每低 1% 扣 1 分',
                'data_source': '财务系统',
                'evaluation_method': '系统采集',
                'source_type': 'kpi',
                'source_id': kpis[0]['id'] if kpis else None,
            },
            {
                'contract_id': l1_contract_id,
                'sort_order': 2,
                'category': '业绩指标',
                'indicator_name': '净利润率',
                'indicator_description': '全年净利润率目标',
                'weight': 20,
                'unit': '%',
                'target_value': '15',
                'challenge_value': '18',
                'baseline_value': '12',
                'scoring_rule': '达成目标值得 100 分，每超 0.5% 加 2 分，每低 0.5% 扣 2 分',
                'data_source': '财务系统',
                'evaluation_method': '系统采集',
                'source_type': 'kpi',
                'source_id': kpis[1]['id'] if len(kpis) > 1 else None,
            },
            {
                'contract_id': l1_contract_id,
                'sort_order': 3,
                'category': '业绩指标',
                'indicator_name': '新签合同额',
                'indicator_description': '全年新签订单合同金额',
                'weight': 15,
                'unit': '万元',
                'target_value': '15000',
                'challenge_value': '18000',
                'baseline_value': '12000',
                'scoring_rule': '达成目标值得 100 分，按比例计算',
                'data_source': 'CRM 系统',
                'evaluation_method': '系统采集',
                'source_type': 'kpi',
                'source_id': kpis[2]['id'] if len(kpis) > 2 else None,
            },
            {
                'contract_id': l1_contract_id,
                'sort_order': 4,
                'category': '管理指标',
                'indicator_name': '客户满意度',
                'indicator_description': '年度客户满意度调查评分',
                'weight': 15,
                'unit': '分',
                'target_value': '90',
                'challenge_value': '95',
                'baseline_value': '85',
                'scoring_rule': '达成目标值得 100 分，每超 1 分加 2 分，每低 1 分扣 2 分',
                'data_source': '客服系统',
                'evaluation_method': '问卷调查',
                'source_type': 'kpi',
                'source_id': kpis[3]['id'] if len(kpis) > 3 else None,
            },
            {
                'contract_id': l1_contract_id,
                'sort_order': 5,
                'category': '管理指标',
                'indicator_name': '项目交付及时率',
                'indicator_description': '按时交付项目占比',
                'weight': 15,
                'unit': '%',
                'target_value': '95',
                'challenge_value': '98',
                'baseline_value': '90',
                'scoring_rule': '达成目标值得 100 分，每超 1% 加 1 分，每低 1% 扣 2 分',
                'data_source': '项目管理系统',
                'evaluation_method': '系统统计',
                'source_type': 'kpi',
                'source_id': kpis[4]['id'] if len(kpis) > 4 else None,
            },
            {
                'contract_id': l1_contract_id,
                'sort_order': 6,
                'category': '能力指标',
                'indicator_name': '团队建设与人才培养',
                'indicator_description': '核心员工保留率及人才培养计划完成情况',
                'weight': 15,
                'unit': '%',
                'target_value': '90',
                'challenge_value': '95',
                'baseline_value': '85',
                'scoring_rule': '核心员工保留率达 90% 得 100 分，人才培养计划完成度占比 50%',
                'data_source': 'HR 系统',
                'evaluation_method': 'HR 评估',
                'source_type': 'custom',
            },
        ]
        
        for item in l1_items:
            create_item(conn, item)
            items_created += 1
        
        # 更新 L1 合约总权重
        cursor.execute(
            "UPDATE performance_contracts SET total_weight = 100 WHERE id = ?",
            (l1_contract_id,)
        )
        
        print(f"   ✓ L1 合约创建成功 (ID: {l1_contract_id}, 指标数：6)")
        
        # ==================== L2 合约：高管↔部门经理 ====================
        print("\n📋 创建 L2 合约（部门级）...")
        
        # L2-1: 总经理↔研发部经理
        l2_1_contract = {
            'contract_no': generate_contract_no('L2', current_year),
            'contract_type': 'L2',
            'year': current_year,
            'signer_name': '李四',
            'signer_title': '研发部经理',
            'counterpart_name': '张三',
            'counterpart_title': '总经理',
            'department_id': 1,
            'department_name': '研发部',
            'status': 'active',
            'sign_date': (datetime.now() - timedelta(days=25)).strftime('%Y-%m-%d'),
            'effective_date': f'{current_year}-01-01',
            'expiry_date': f'{current_year}-12-31',
            'remarks': '研发部年度目标责任状',
        }
        
        l2_1_id = create_contract(conn, l2_1_contract)
        contracts_created.append(('L2', l2_1_id))
        
        l2_1_items = [
            {
                'contract_id': l2_1_id,
                'sort_order': 1,
                'category': '业绩指标',
                'indicator_name': '新产品开发完成率',
                'indicator_description': '年度新产品开发计划完成率',
                'weight': 25,
                'unit': '%',
                'target_value': '100',
                'challenge_value': '110',
                'baseline_value': '90',
                'scoring_rule': '达成 100% 得 100 分，每超 5% 加 5 分，每低 5% 扣 10 分',
                'data_source': 'PLM 系统',
                'evaluation_method': '系统统计',
                'source_type': 'kpi',
                'source_id': kpis[5]['id'] if len(kpis) > 5 else None,
            },
            {
                'contract_id': l2_1_id,
                'sort_order': 2,
                'category': '业绩指标',
                'indicator_name': '研发项目预算控制率',
                'indicator_description': '研发项目实际支出与预算的比率',
                'weight': 20,
                'unit': '%',
                'target_value': '100',
                'challenge_value': '95',
                'baseline_value': '110',
                'scoring_rule': '控制在 100% 以内得 100 分，每超 5% 扣 10 分，每节约 5% 加 5 分',
                'data_source': '财务系统',
                'evaluation_method': '系统采集',
                'source_type': 'kpi',
                'source_id': kpis[6]['id'] if len(kpis) > 6 else None,
            },
            {
                'contract_id': l2_1_id,
                'sort_order': 3,
                'category': '管理指标',
                'indicator_name': '技术文档完整率',
                'indicator_description': '研发项目技术文档归档完整性',
                'weight': 20,
                'unit': '%',
                'target_value': '95',
                'challenge_value': '100',
                'baseline_value': '90',
                'scoring_rule': '达成 95% 得 100 分，每低 1% 扣 5 分',
                'data_source': '文档管理系统',
                'evaluation_method': '定期检查',
                'source_type': 'custom',
            },
            {
                'contract_id': l2_1_id,
                'sort_order': 4,
                'category': '能力指标',
                'indicator_name': '团队技术能力提升',
                'indicator_description': '团队技术培训完成率及技术分享次数',
                'weight': 20,
                'unit': '次',
                'target_value': '24',
                'challenge_value': '30',
                'baseline_value': '18',
                'scoring_rule': '完成 24 次培训/分享得 100 分，每多 2 次加 5 分',
                'data_source': '培训系统',
                'evaluation_method': '培训记录',
                'source_type': 'custom',
            },
            {
                'contract_id': l2_1_id,
                'sort_order': 5,
                'category': '态度指标',
                'indicator_name': '跨部门协作配合度',
                'indicator_description': '与其他部门协作配合的主动性和效果',
                'weight': 15,
                'unit': '分',
                'target_value': '90',
                'challenge_value': '95',
                'baseline_value': '80',
                'scoring_rule': '360 度评估平均分，90 分以上得 100 分',
                'data_source': '360 评估',
                'evaluation_method': '问卷调查',
                'source_type': 'custom',
            },
        ]
        
        for item in l2_1_items:
            create_item(conn, item)
            items_created += 1
        
        cursor.execute(
            "UPDATE performance_contracts SET total_weight = 100 WHERE id = ?",
            (l2_1_id,)
        )
        
        print(f"   ✓ L2-研发部合约创建成功 (ID: {l2_1_id}, 指标数：5)")
        
        # L2-2: 总经理↔销售部经理
        l2_2_contract = {
            'contract_no': generate_contract_no('L2', current_year),
            'contract_type': 'L2',
            'year': current_year,
            'signer_name': '王五',
            'signer_title': '销售部经理',
            'counterpart_name': '张三',
            'counterpart_title': '总经理',
            'department_id': 2,
            'department_name': '销售部',
            'status': 'active',
            'sign_date': (datetime.now() - timedelta(days=25)).strftime('%Y-%m-%d'),
            'effective_date': f'{current_year}-01-01',
            'expiry_date': f'{current_year}-12-31',
            'remarks': '销售部年度目标责任状',
        }
        
        l2_2_id = create_contract(conn, l2_2_contract)
        contracts_created.append(('L2', l2_2_id))
        
        l2_2_items = [
            {
                'contract_id': l2_2_id,
                'sort_order': 1,
                'category': '业绩指标',
                'indicator_name': '销售目标达成率',
                'indicator_description': '年度销售目标完成比例',
                'weight': 30,
                'unit': '%',
                'target_value': '100',
                'challenge_value': '120',
                'baseline_value': '85',
                'scoring_rule': '达成 100% 得 100 分，每超 5% 加 10 分，每低 5% 扣 15 分',
                'data_source': 'CRM 系统',
                'evaluation_method': '系统采集',
                'source_type': 'kpi',
                'source_id': kpis[7]['id'] if len(kpis) > 7 else None,
            },
            {
                'contract_id': l2_2_id,
                'sort_order': 2,
                'category': '业绩指标',
                'indicator_name': '新客户开发数量',
                'indicator_description': '年度新增有效客户数量',
                'weight': 25,
                'unit': '家',
                'target_value': '50',
                'challenge_value': '70',
                'baseline_value': '35',
                'scoring_rule': '完成 50 家得 100 分，每多 5 家加 5 分，每少 5 家扣 10 分',
                'data_source': 'CRM 系统',
                'evaluation_method': '系统统计',
                'source_type': 'kpi',
                'source_id': kpis[8]['id'] if len(kpis) > 8 else None,
            },
            {
                'contract_id': l2_2_id,
                'sort_order': 3,
                'category': '管理指标',
                'indicator_name': '销售回款率',
                'indicator_description': '销售回款占应收款比例',
                'weight': 20,
                'unit': '%',
                'target_value': '95',
                'challenge_value': '98',
                'baseline_value': '90',
                'scoring_rule': '达成 95% 得 100 分，每超 1% 加 2 分，每低 1% 扣 5 分',
                'data_source': '财务系统',
                'evaluation_method': '系统采集',
                'source_type': 'kpi',
                'source_id': kpis[9]['id'] if len(kpis) > 9 else None,
            },
            {
                'contract_id': l2_2_id,
                'sort_order': 4,
                'category': '能力指标',
                'indicator_name': '销售团队建设',
                'indicator_description': '销售人员培训及梯队建设',
                'weight': 15,
                'unit': '%',
                'target_value': '90',
                'challenge_value': '95',
                'baseline_value': '85',
                'scoring_rule': '培训计划完成率 90% 以上得 100 分',
                'data_source': 'HR 系统',
                'evaluation_method': '培训记录',
                'source_type': 'custom',
            },
            {
                'contract_id': l2_2_id,
                'sort_order': 5,
                'category': '态度指标',
                'indicator_name': '市场信息反馈及时性',
                'indicator_description': '市场动态和竞品信息反馈的及时性',
                'weight': 10,
                'unit': '分',
                'target_value': '90',
                'challenge_value': '95',
                'baseline_value': '80',
                'scoring_rule': '月度市场报告提交及时率，90% 以上得 100 分',
                'data_source': '市场报告',
                'evaluation_method': '管理层评估',
                'source_type': 'custom',
            },
        ]
        
        for item in l2_2_items:
            create_item(conn, item)
            items_created += 1
        
        cursor.execute(
            "UPDATE performance_contracts SET total_weight = 100 WHERE id = ?",
            (l2_2_id,)
        )
        
        print(f"   ✓ L2-销售部合约创建成功 (ID: {l2_2_id}, 指标数：5)")
        
        # ==================== L3 合约：部门经理↔员工 ====================
        print("\n📋 创建 L3 合约（个人级）...")
        
        # L3-1: 研发部经理↔高级工程师
        l3_1_contract = {
            'contract_no': generate_contract_no('L3', current_year),
            'contract_type': 'L3',
            'year': current_year,
            'signer_name': '赵六',
            'signer_title': '高级工程师',
            'counterpart_name': '李四',
            'counterpart_title': '研发部经理',
            'department_id': 1,
            'department_name': '研发部',
            'status': 'active',
            'sign_date': (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d'),
            'effective_date': f'{current_year}-01-01',
            'expiry_date': f'{current_year}-12-31',
            'remarks': '个人绩效合约',
        }
        
        l3_1_id = create_contract(conn, l3_1_contract)
        contracts_created.append(('L3', l3_1_id))
        
        l3_1_items = [
            {
                'contract_id': l3_1_id,
                'sort_order': 1,
                'category': '业绩指标',
                'indicator_name': '负责模块开发完成率',
                'indicator_description': '个人负责的开发模块按时完成率',
                'weight': 35,
                'unit': '%',
                'target_value': '100',
                'challenge_value': '105',
                'baseline_value': '95',
                'scoring_rule': '达成 100% 得 100 分，每超 5% 加 5 分，每低 5% 扣 10 分',
                'data_source': '项目管理工具',
                'evaluation_method': '系统统计',
                'source_type': 'work',
                'source_id': annual_works[0]['id'] if annual_works else None,
            },
            {
                'contract_id': l3_1_id,
                'sort_order': 2,
                'category': '业绩指标',
                'indicator_name': '代码质量指标',
                'indicator_description': '代码审查通过率及 Bug 率',
                'weight': 25,
                'unit': '%',
                'target_value': '95',
                'challenge_value': '98',
                'baseline_value': '90',
                'scoring_rule': '代码审查通过率 95% 以上且 Bug 率低于 2% 得 100 分',
                'data_source': '代码管理系统',
                'evaluation_method': '代码审查',
                'source_type': 'custom',
            },
            {
                'contract_id': l3_1_id,
                'sort_order': 3,
                'category': '能力指标',
                'indicator_name': '技术能力提升',
                'indicator_description': '新技术学习及应用情况',
                'weight': 25,
                'unit': '项',
                'target_value': '2',
                'challenge_value': '3',
                'baseline_value': '1',
                'scoring_rule': '掌握并应用 2 项新技术得 100 分',
                'data_source': '技术分享',
                'evaluation_method': '主管评估',
                'source_type': 'custom',
            },
            {
                'contract_id': l3_1_id,
                'sort_order': 4,
                'category': '态度指标',
                'indicator_name': '团队协作精神',
                'indicator_description': '团队合作意识和协作效果',
                'weight': 15,
                'unit': '分',
                'target_value': '90',
                'challenge_value': '95',
                'baseline_value': '85',
                'scoring_rule': '团队成员互评平均分 90 以上得 100 分',
                'data_source': '团队评估',
                'evaluation_method': '360 评估',
                'source_type': 'custom',
            },
        ]
        
        for item in l3_1_items:
            create_item(conn, item)
            items_created += 1
        
        cursor.execute(
            "UPDATE performance_contracts SET total_weight = 100 WHERE id = ?",
            (l3_1_id,)
        )
        
        print(f"   ✓ L3-工程师 1 合约创建成功 (ID: {l3_1_id}, 指标数：4)")
        
        # L3-2: 研发部经理↔工程师
        l3_2_contract = {
            'contract_no': generate_contract_no('L3', current_year),
            'contract_type': 'L3',
            'year': current_year,
            'signer_name': '钱七',
            'signer_title': '工程师',
            'counterpart_name': '李四',
            'counterpart_title': '研发部经理',
            'department_id': 1,
            'department_name': '研发部',
            'status': 'pending_sign',
            'sign_date': None,
            'effective_date': f'{current_year}-01-01',
            'expiry_date': f'{current_year}-12-31',
            'remarks': '个人绩效合约',
        }
        
        l3_2_id = create_contract(conn, l3_2_contract)
        contracts_created.append(('L3', l3_2_id))
        
        l3_2_items = [
            {
                'contract_id': l3_2_id,
                'sort_order': 1,
                'category': '业绩指标',
                'indicator_name': '任务完成及时率',
                'weight': 35,
                'unit': '%',
                'target_value': '95',
                'scoring_rule': '按时完成任务占比 95% 以上得 100 分',
                'data_source': '任务管理系统',
                'evaluation_method': '系统统计',
                'source_type': 'custom',
            },
            {
                'contract_id': l3_2_id,
                'sort_order': 2,
                'category': '业绩指标',
                'indicator_name': '工作质量',
                'weight': 30,
                'unit': '分',
                'target_value': '90',
                'scoring_rule': '主管评分 90 分以上得 100 分',
                'data_source': '主管评估',
                'evaluation_method': '主管评分',
                'source_type': 'custom',
            },
            {
                'contract_id': l3_2_id,
                'sort_order': 3,
                'category': '能力指标',
                'indicator_name': '学习成长',
                'weight': 20,
                'unit': '小时',
                'target_value': '40',
                'scoring_rule': '年度培训学习 40 小时以上得 100 分',
                'data_source': '培训系统',
                'evaluation_method': '培训记录',
                'source_type': 'custom',
            },
            {
                'contract_id': l3_2_id,
                'sort_order': 4,
                'category': '态度指标',
                'indicator_name': '工作积极性',
                'weight': 15,
                'unit': '分',
                'target_value': '90',
                'scoring_rule': '主管评估 90 分以上得 100 分',
                'data_source': '主管评估',
                'evaluation_method': '主管评分',
                'source_type': 'custom',
            },
        ]
        
        for item in l3_2_items:
            create_item(conn, item)
            items_created += 1
        
        cursor.execute(
            "UPDATE performance_contracts SET total_weight = 100 WHERE id = ?",
            (l3_2_id,)
        )
        
        print(f"   ✓ L3-工程师 2 合约创建成功 (ID: {l3_2_id}, 指标数：4)")
        
        # L3-3: 销售部经理↔销售代表
        l3_3_contract = {
            'contract_no': generate_contract_no('L3', current_year),
            'contract_type': 'L3',
            'year': current_year,
            'signer_name': '孙八',
            'signer_title': '销售代表',
            'counterpart_name': '王五',
            'counterpart_title': '销售部经理',
            'department_id': 2,
            'department_name': '销售部',
            'status': 'draft',
            'effective_date': f'{current_year}-01-01',
            'expiry_date': f'{current_year}-12-31',
            'remarks': '个人绩效合约 - 草稿',
        }
        
        l3_3_id = create_contract(conn, l3_3_contract)
        contracts_created.append(('L3', l3_3_id))
        
        l3_3_items = [
            {
                'contract_id': l3_3_id,
                'sort_order': 1,
                'category': '业绩指标',
                'indicator_name': '个人销售目标',
                'weight': 40,
                'unit': '万元',
                'target_value': '500',
                'challenge_value': '600',
                'scoring_rule': '完成 500 万得 100 分，每超 50 万加 10 分',
                'data_source': 'CRM 系统',
                'evaluation_method': '系统统计',
                'source_type': 'kpi',
                'source_id': kpis[10]['id'] if len(kpis) > 10 else None,
            },
            {
                'contract_id': l3_3_id,
                'sort_order': 2,
                'category': '业绩指标',
                'indicator_name': '新客户开发',
                'weight': 30,
                'unit': '家',
                'target_value': '10',
                'scoring_rule': '开发 10 家新客户得 100 分',
                'data_source': 'CRM 系统',
                'evaluation_method': '系统统计',
                'source_type': 'custom',
            },
            {
                'contract_id': l3_3_id,
                'sort_order': 3,
                'category': '能力指标',
                'indicator_name': '产品知识掌握',
                'weight': 15,
                'unit': '分',
                'target_value': '90',
                'scoring_rule': '产品知识考试 90 分以上得 100 分',
                'data_source': '培训考试',
                'evaluation_method': '考试评分',
                'source_type': 'custom',
            },
            {
                'contract_id': l3_3_id,
                'sort_order': 4,
                'category': '态度指标',
                'indicator_name': '客户服务态度',
                'weight': 15,
                'unit': '分',
                'target_value': '95',
                'scoring_rule': '客户评价 95 分以上得 100 分',
                'data_source': '客户反馈',
                'evaluation_method': '客户评价',
                'source_type': 'custom',
            },
        ]
        
        for item in l3_3_items:
            create_item(conn, item)
            items_created += 1
        
        cursor.execute(
            "UPDATE performance_contracts SET total_weight = 100 WHERE id = ?",
            (l3_3_id,)
        )
        
        print(f"   ✓ L3-销售代表合约创建成功 (ID: {l3_3_id}, 指标数：4)")
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("✅ 绩效合约种子数据创建完成！")
        print(f"   合约总数：{len(contracts_created)}")
        print(f"   指标条目总数：{items_created}")
        print("\n   合约分布:")
        for contract_type, contract_id in contracts_created:
            print(f"      - {contract_type} 合约 (ID: {contract_id})")
        print("=" * 60)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 创建失败：{str(e)}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    seed_performance_contracts()
