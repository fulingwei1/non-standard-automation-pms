#!/usr/bin/env python3
"""清除演示数据 - 保留系统预置数据(admin用户、权限定义等)"""
import sqlite3, sys, os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "app.db")

# 演示数据ID范围 (seed_demo_data.py 插入的)
DEMO_RANGES = {
    'customer_satisfactions': 'id BETWEEN 1 AND 100',
    'payments': 'id BETWEEN 1 AND 100',
    'invoices': 'id BETWEEN 1 AND 100',
    'service_tickets': 'id BETWEEN 1 AND 100',
    'delivery_orders': 'id BETWEEN 1 AND 100',
    'work_order': 'id BETWEEN 1 AND 100',
    'production_plan': 'id BETWEEN 1 AND 100',
    'worker': 'id BETWEEN 1 AND 100',
    'workshop': 'id BETWEEN 1 AND 100',
    'purchase_orders': 'id BETWEEN 1 AND 100',
    'materials': 'id BETWEEN 1 AND 100',
    'projects': 'id BETWEEN 1 AND 100',
    'contracts': 'id BETWEEN 1 AND 100',
    'quotes': 'id BETWEEN 1 AND 100',
    'opportunities': 'id BETWEEN 1 AND 100',
    'leads': 'id BETWEEN 1 AND 100',
    'customers': 'id BETWEEN 1 AND 100',
    'user_roles': 'user_id BETWEEN 2 AND 100',  # 保留admin(id=1)的角色
    'users': 'id BETWEEN 2 AND 100',             # 保留admin(id=1)
    'employees': 'id BETWEEN 2 AND 100',
    'departments': 'id BETWEEN 1 AND 100',
    'roles': "role_code LIKE 'ROLE_%' AND is_system != 1",  # 只删非系统角色
    'positions': 'id BETWEEN 1 AND 100',
}

def main():
    if '--yes' not in sys.argv:
        print("⚠️  这将清除所有演示数据！")
        print("   保留: admin用户、系统权限定义、API权限、菜单权限")
        print(f"   数据库: {DB_PATH}")
        ans = input("\n确认清除? (yes/no): ")
        if ans.lower() != 'yes':
            print("已取消")
            return

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")
    c = conn.cursor()

    total = 0
    for table, condition in DEMO_RANGES.items():
        try:
            before = c.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            c.execute(f"DELETE FROM {table} WHERE {condition}")
            after = c.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            deleted = before - after
            if deleted > 0:
                print(f"  🗑  {table}: 删除 {deleted} 条 (剩余 {after})")
                total += deleted
        except Exception as e:
            print(f"  ⚠️  {table}: {e}")

    conn.commit()
    conn.close()
    print(f"\n✅ 清除完成，共删除 {total} 条演示数据")

if __name__ == '__main__':
    main()
