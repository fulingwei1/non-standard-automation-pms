#!/usr/bin/env python3
"""
数据库表分析脚本
分析499个表的使用情况，找出重复、冗余和无用的表
"""
import sys
import sqlite3
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

def analyze_database():
    db_path = Path("data/app.db")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("="*70)
    print("📊 数据库表分析报告")
    print("="*70)
    print()
    
    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    all_tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
    
    print(f"总表数: {len(all_tables)}\n")
    
    # 1. 按前缀分组
    print("1️⃣  按业务模块分组:")
    print("-"*70)
    
    prefixes = defaultdict(list)
    for table in all_tables:
        # 提取前缀（第一个下划线之前）
        parts = table.split('_')
        if len(parts) > 1:
            prefix = parts[0]
            prefixes[prefix].append(table)
        else:
            prefixes['[单字]'].append(table)
    
    # 按表数量排序
    sorted_prefixes = sorted(prefixes.items(), key=lambda x: len(x[1]), reverse=True)
    
    for prefix, tables in sorted_prefixes[:30]:
        print(f"  {prefix:20s} - {len(tables):3d} 个表")
        if len(tables) <= 3:
            for t in tables:
                print(f"    └─ {t}")
    
    if len(sorted_prefixes) > 30:
        print(f"  ... 还有 {len(sorted_prefixes) - 30} 个分组")
    
    print()
    
    # 2. 检查空表
    print("2️⃣  检查空表:")
    print("-"*70)
    
    empty_tables = []
    for table in all_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count == 0:
                empty_tables.append(table)
        except:
            pass
    
    print(f"空表数量: {len(empty_tables)}/{len(all_tables)} ({len(empty_tables)/len(all_tables)*100:.1f}%)")
    
    if empty_tables:
        print(f"\n前20个空表:")
        for table in empty_tables[:20]:
            print(f"  • {table}")
        if len(empty_tables) > 20:
            print(f"  ... 还有 {len(empty_tables) - 20} 个")
    
    print()
    
    # 3. 检查相似表名
    print("3️⃣  检查相似/可能重复的表名:")
    print("-"*70)
    
    similar_groups = defaultdict(list)
    for table in all_tables:
        # 移除常见后缀
        base = table.replace('_items', '').replace('_item', '')
        base = base.replace('_records', '').replace('_record', '')
        base = base.replace('_logs', '').replace('_log', '')
        base = base.replace('_details', '').replace('_detail', '')
        similar_groups[base].append(table)
    
    # 找出有多个变体的
    duplicates = {k: v for k, v in similar_groups.items() if len(v) > 1}
    
    print(f"发现 {len(duplicates)} 组相似表名:\n")
    
    for base, tables in sorted(duplicates.items())[:20]:
        print(f"  {base}:")
        for t in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            count = cursor.fetchone()[0]
            print(f"    • {t} ({count} 条记录)")
    
    if len(duplicates) > 20:
        print(f"  ... 还有 {len(duplicates) - 20} 组")
    
    print()
    
    # 4. 检查视图（v_开头的表）
    print("4️⃣  检查视图表:")
    print("-"*70)
    
    views = [t for t in all_tables if t.startswith('v_')]
    print(f"视图数量: {len(views)}")
    for view in views:
        cursor.execute(f"SELECT COUNT(*) FROM {view}")
        count = cursor.fetchone()[0]
        print(f"  • {view} ({count} 条记录)")
    
    print()
    
    # 5. 按表大小分析
    print("5️⃣  按数据量分析:")
    print("-"*70)
    
    table_sizes = []
    for table in all_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_sizes.append((table, count))
        except:
            table_sizes.append((table, 0))
    
    # 排序
    table_sizes.sort(key=lambda x: x[1], reverse=True)
    
    print("数据最多的前10个表:")
    for table, count in table_sizes[:10]:
        print(f"  • {table:40s} - {count:,} 条记录")
    
    print()
    
    # 6. 统计摘要
    print("6️⃣  统计摘要:")
    print("-"*70)
    
    total_records = sum(count for _, count in table_sizes)
    non_empty = len([t for t in table_sizes if t[1] > 0])
    
    print(f"总表数:     {len(all_tables)}")
    print(f"非空表数:   {non_empty} ({non_empty/len(all_tables)*100:.1f}%)")
    print(f"空表数:     {len(empty_tables)} ({len(empty_tables)/len(all_tables)*100:.1f}%)")
    print(f"总记录数:   {total_records:,}")
    print(f"平均记录数: {total_records/len(all_tables):.1f}")
    print()
    
    # 7. 可能冗余的表
    print("7️⃣  可能冗余/无用的表:")
    print("-"*70)
    
    # 找出空表且有相似表名的
    potential_redundant = []
    for table in empty_tables:
        # 检查是否有相似的非空表
        base = table.replace('_items', '').replace('_records', '')
        for other in all_tables:
            if other != table and base in other:
                cursor.execute(f"SELECT COUNT(*) FROM {other}")
                if cursor.fetchone()[0] > 0:
                    potential_redundant.append((table, other))
                    break
    
    if potential_redundant:
        print(f"发现 {len(potential_redundant)} 个可能冗余的空表:\n")
        for empty, similar in potential_redundant[:15]:
            print(f"  • {empty} (空) - 可能被 {similar} 替代")
        if len(potential_redundant) > 15:
            print(f"  ... 还有 {len(potential_redundant) - 15} 个")
    else:
        print("未发现明显冗余的表")
    
    print()
    
    # 8. 建议
    print("8️⃣  优化建议:")
    print("-"*70)
    
    if len(empty_tables) > 100:
        print(f"⚠️  有 {len(empty_tables)} 个空表，建议:")
        print(f"   1. 确认这些表是否真的需要")
        print(f"   2. 考虑删除明显无用的空表")
        print(f"   3. 保留可能在未来使用的表")
    
    if len(duplicates) > 50:
        print(f"\n⚠️  有 {len(duplicates)} 组相似表名，建议:")
        print(f"   1. 检查是否有功能重复的表")
        print(f"   2. 合并或删除冗余的表")
        print(f"   3. 统一表命名规范")
    
    print()
    print("="*70)
    
    conn.close()
    
    # 生成清理建议
    with open("table_analysis_report.txt", "w") as f:
        f.write("数据库表分析报告\n")
        f.write("="*70 + "\n\n")
        f.write(f"总表数: {len(all_tables)}\n")
        f.write(f"非空表数: {non_empty}\n")
        f.write(f"空表数: {len(empty_tables)}\n")
        f.write(f"总记录数: {total_records:,}\n\n")
        
        f.write("所有空表列表:\n")
        f.write("-"*70 + "\n")
        for table in empty_tables:
            f.write(f"{table}\n")
    
    print(f"📄 详细报告已保存: table_analysis_report.txt")

if __name__ == "__main__":
    analyze_database()
