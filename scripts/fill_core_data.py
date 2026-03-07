#!/usr/bin/env python3
"""
快速数据填充脚本 - 直接操作 SQLite
填充核心表数据，让前端页面不再空白
"""

import sqlite3
import random
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"

def fill_core_data():
    print(f"🚀 开始填充数据到: {DB_PATH}")
    
    if not DB_PATH.exists():
        print(f"❌ 数据库不存在: {DB_PATH}")
        return 1
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    try:
        # ========== 1. 填充客户 ==========
        cur.execute("SELECT COUNT(*) FROM customers")
        if cur.fetchone()[0] <= 5:
            customers = [
                ("CUST001", "比亚迪股份有限公司", "比亚迪", "新能源汽车", "深圳", "A"),
                ("CUST002", "宁德时代新能源科技股份有限公司", "宁德时代", "动力电池", "宁德", "A"),
                ("CUST003", "小米科技有限责任公司", "小米", "消费电子", "北京", "A"),
                ("CUST004", "华为技术有限公司", "华为", "通信设备", "深圳", "A"),
                ("CUST005", "吉利汽车集团有限公司", "吉利汽车", "新能源汽车", "杭州", "A"),
                ("CUST006", "长城汽车股份有限公司", "长城汽车", "新能源汽车", "保定", "A"),
                ("CUST007", "理想汽车科技有限公司", "理想汽车", "新能源汽车", "北京", "A"),
                ("CUST008", "蔚来汽车科技有限公司", "蔚来汽车", "新能源汽车", "上海", "A"),
                ("CUST009", "小鹏汽车科技有限公司", "小鹏汽车", "新能源汽车", "广州", "B"),
                ("CUST010", "中创新航科技股份有限公司", "中创新航", "动力电池", "常州", "A"),
            ]
            for i, (code, name, short_name, industry, city, level) in enumerate(customers, 1):
                cur.execute("""
                    INSERT OR IGNORE INTO customers (id, customer_code, customer_name, short_name, 
                        industry, address, credit_level, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', datetime('now'))
                """, (i, code, name, short_name, industry, city, level))
            print(f"✅ 填充了 {len(customers)} 个客户")
        else:
            print("✓ 客户数据已存在")
        
        # ========== 2. 填充员工 ==========
        cur.execute("SELECT COUNT(*) FROM employees")
        if cur.fetchone()[0] <= 5:
            employees = [
                ("EMP001", "张工", "机械部", "机械工程师"),
                ("EMP002", "李工", "机械部", "机械工程师"),
                ("EMP003", "王工", "电气部", "电气工程师"),
                ("EMP004", "赵工", "电气部", "电气工程师"),
                ("EMP005", "孙工", "软件部", "软件工程师"),
                ("EMP006", "周工", "软件部", "软件工程师"),
                ("EMP007", "刘经理", "PMO", "项目经理"),
                ("EMP008", "陈总监", "销售部", "销售总监"),
            ]
            for i, (code, name, dept, role) in enumerate(employees, 1):
                cur.execute("""
                    INSERT OR IGNORE INTO employees (id, employee_code, name, department, role, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (i, code, name, dept, role))
            print(f"✅ 填充了 {len(employees)} 个员工")
        else:
            print("✓ 员工数据已存在")
        
        # ========== 3. 填充项目 ==========
        cur.execute("SELECT COUNT(*) FROM projects")
        if cur.fetchone()[0] <= 3:
            projects = [
                ("PRJ2026001", "比亚迪电池测试线项目", 1, "S4", "ST04", "INSPECTION", "AUTO", 2500000),
                ("PRJ2026002", "宁德时代FCT测试设备", 2, "S3", "ST03", "INSPECTION", "AUTO", 1800000),
                ("PRJ2026003", "小米视觉检测系统", 3, "S2", "ST02", "INSPECTION", "3C", 950000),
                ("PRJ2026004", "华为通信模块烧录线", 4, "S9", "ST09", "ASSEMBLY_LINE", "3C", 3200000),
                ("PRJ2026005", "吉利EOL测试项目", 5, "S4", "ST04", "INSPECTION", "AUTO", 1600000),
            ]
            for i, (code, name, customer_id, stage, status, product_category, industry, amount) in enumerate(projects, 1):
                cur.execute("""
                    INSERT OR IGNORE INTO projects (id, project_code, project_name, customer_id, stage, status, 
                        product_category, industry, contract_amount, health, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (i, code, name, customer_id, stage, status, product_category, industry, amount, 
                      random.choice(['H1', 'H2', 'H3'])))
            print(f"✅ 填充了 {len(projects)} 个项目")
        else:
            print("✓ 项目数据已存在")
        
        # ========== 4. 填充任务 ==========
        cur.execute("SELECT COUNT(*) FROM tasks")
        if cur.fetchone()[0] <= 10:
            task_names = ["机械设计", "电气设计", "PLC编程", "视觉调试", "机械装配", "电气接线", "整机调试", "客户验收"]
            stages = ["设计", "采购", "装配", "调试", "验收"]
            statuses = ["TODO", "DOING", "DONE"]
            
            task_id = 1
            for project_id in range(1, 6):
                for task_name in task_names:
                    status = random.choice(statuses)
                    progress = 0 if status == "TODO" else (100 if status == "DONE" else random.randint(30, 80))
                    
                    cur.execute("""
                        INSERT OR IGNORE INTO tasks (id, project_id, task_name, stage, status, 
                            progress_percent, plan_start, plan_end, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, date('now', '-10 days'), date('now', '+20 days'), datetime('now'))
                    """, (task_id, project_id, f"{task_name}-{project_id}", random.choice(stages), status, progress))
                    task_id += 1
            print(f"✅ 填充了 {task_id-1} 个任务")
        else:
            print("✓ 任务数据已存在")
        
        # ========== 5. 填充物料 ==========
        cur.execute("SELECT COUNT(*) FROM materials")
        if cur.fetchone()[0] <= 5:
            materials = [
                ("MAT001", "标准气缸", "SMC", "气动元件", "个", 150.00),
                ("MAT002", "伺服电机", "三菱", "电机", "台", 2800.00),
                ("MAT003", "PLC控制器", "西门子", "控制器", "台", 5200.00),
                ("MAT004", "工业相机", "Basler", "视觉", "个", 8500.00),
                ("MAT005", "传感器", "欧姆龙", "传感器", "个", 320.00),
                ("MAT006", "触摸屏", "威纶通", "人机界面", "个", 1200.00),
                ("MAT007", "电磁阀", "SMC", "气动元件", "个", 180.00),
                ("MAT008", "直线导轨", "上银", "机械标准件", "套", 450.00),
            ]
            for i, (code, name, brand, category, unit, price) in enumerate(materials, 1):
                cur.execute("""
                    INSERT OR IGNORE INTO materials (id, material_code, material_name, brand, 
                        category_l1, unit, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                """, (i, code, name, brand, category, unit))
            print(f"✅ 填充了 {len(materials)} 个物料")
        else:
            print("✓ 物料数据已存在")
        
        conn.commit()
        
        # ========== 统计 ==========
        print("\n✨ 数据填充完成!")
        print("\n📊 当前数据概况:")
        
        tables = [
            ("customers", "客户"),
            ("employees", "员工"),
            ("projects", "项目"),
            ("tasks", "任务"),
            ("materials", "物料"),
        ]
        
        for table, name in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"  {name}: {count} 条")
            except Exception as e:
                print(f"  {name}: 查询失败")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    exit(fill_core_data())
