#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超级管理员数据修复脚本
Team 4: 统一超级管理员判断标准

功能：
1. 检测不一致的用户数据
2. 修复 is_superuser 和 tenant_id 的数据一致性
3. 生成修复报告
"""

import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

def get_db_engine():
    """获取数据库引擎"""
    return create_engine(settings.DATABASE_URL)

def check_inconsistent_users(session):
    """检查不一致的用户数据"""
    print("\n" + "="*80)
    print("步骤 1: 检查数据不一致的用户")
    print("="*80)
    
    # 类型1: is_superuser=TRUE 但 tenant_id 不为空
    query_type1 = text("""
        SELECT id, username, is_superuser, tenant_id, email, real_name
        FROM users
        WHERE is_superuser = TRUE AND tenant_id IS NOT NULL
    """)
    
    result_type1 = session.execute(query_type1).fetchall()
    
    print(f"\n类型1: is_superuser=TRUE 但 tenant_id 不为空 ({len(result_type1)} 条记录)")
    if result_type1:
        print("-" * 80)
        print(f"{'ID':<6} {'用户名':<20} {'is_superuser':<15} {'tenant_id':<12} {'邮箱':<25}")
        print("-" * 80)
        for row in result_type1:
            print(f"{row[0]:<6} {row[1]:<20} {row[2]!s:<15} {row[3]!s:<12} {row[4] or 'N/A':<25}")
    
    # 类型2: is_superuser=FALSE 但 tenant_id 为空
    query_type2 = text("""
        SELECT id, username, is_superuser, tenant_id, email, real_name
        FROM users
        WHERE is_superuser = FALSE AND tenant_id IS NULL
    """)
    
    result_type2 = session.execute(query_type2).fetchall()
    
    print(f"\n类型2: is_superuser=FALSE 但 tenant_id 为空 ({len(result_type2)} 条记录)")
    if result_type2:
        print("-" * 80)
        print(f"{'ID':<6} {'用户名':<20} {'is_superuser':<15} {'tenant_id':<12} {'邮箱':<25}")
        print("-" * 80)
        for row in result_type2:
            print(f"{row[0]:<6} {row[1]:<20} {row[2]!s:<15} {row[3]!s:<12} {row[4] or 'N/A':<25}")
    
    return len(result_type1) + len(result_type2), result_type1, result_type2

def fix_inconsistent_users(session, dry_run=True):
    """修复不一致的用户数据
    
    Args:
        session: 数据库会话
        dry_run: 是否为演练模式（不实际修改数据）
    """
    print("\n" + "="*80)
    print(f"步骤 2: 修复数据不一致 ({'演练模式' if dry_run else '实际执行'})")
    print("="*80)
    
    # 修复策略1: 将 is_superuser=TRUE 但有 tenant_id 的用户降级为普通用户
    print("\n策略1: 将 is_superuser=TRUE 但有 tenant_id 的用户降级为普通用户")
    fix_query1 = text("""
        UPDATE users 
        SET is_superuser = FALSE 
        WHERE is_superuser = TRUE AND tenant_id IS NOT NULL
    """)
    
    if not dry_run:
        result1 = session.execute(fix_query1)
        print(f"✓ 已修复 {result1.rowcount} 条记录")
    else:
        # 计算将要修复的记录数
        count_query1 = text("""
            SELECT COUNT(*) FROM users 
            WHERE is_superuser = TRUE AND tenant_id IS NOT NULL
        """)
        count1 = session.execute(count_query1).scalar()
        print(f"→ 将修复 {count1} 条记录 (演练)")
    
    # 修复策略2: 将 tenant_id 为空但 is_superuser=FALSE 的用户设置为超级管理员
    # 注意：这个策略需要谨慎，可能需要人工确认
    print("\n策略2: 将 tenant_id 为空但 is_superuser=FALSE 的用户设置为超级管理员")
    print("警告: 此操作会提升用户权限，请谨慎确认！")
    
    fix_query2 = text("""
        UPDATE users 
        SET is_superuser = TRUE 
        WHERE tenant_id IS NULL AND is_superuser = FALSE
    """)
    
    if not dry_run:
        # 在实际执行前再次确认
        confirm = input("是否确认执行策略2？这将提升用户权限 (yes/no): ")
        if confirm.lower() == 'yes':
            result2 = session.execute(fix_query2)
            print(f"✓ 已修复 {result2.rowcount} 条记录")
        else:
            print("✗ 已跳过策略2")
    else:
        count_query2 = text("""
            SELECT COUNT(*) FROM users 
            WHERE tenant_id IS NULL AND is_superuser = FALSE
        """)
        count2 = session.execute(count_query2).scalar()
        print(f"→ 将修复 {count2} 条记录 (演练，需确认)")

def verify_fix(session):
    """验证修复结果"""
    print("\n" + "="*80)
    print("步骤 3: 验证修复结果")
    print("="*80)
    
    # 检查是否还有不一致的记录
    verify_query = text("""
        SELECT COUNT(*) FROM users 
        WHERE (is_superuser = TRUE AND tenant_id IS NOT NULL)
           OR (is_superuser = FALSE AND tenant_id IS NULL)
    """)
    
    inconsistent_count = session.execute(verify_query).scalar()
    
    if inconsistent_count == 0:
        print("\n✓ 所有用户数据已一致！")
    else:
        print(f"\n✗ 仍有 {inconsistent_count} 条不一致的记录")
    
    # 统计超级管理员和普通用户数量
    stats_query = text("""
        SELECT 
            COUNT(*) FILTER (WHERE is_superuser = TRUE AND tenant_id IS NULL) as superuser_count,
            COUNT(*) FILTER (WHERE is_superuser = FALSE AND tenant_id IS NOT NULL) as tenant_user_count,
            COUNT(*) as total_count
        FROM users
    """)
    
    stats = session.execute(stats_query).fetchone()
    
    print("\n当前用户统计:")
    print(f"  - 超级管理员 (is_superuser=TRUE & tenant_id=NULL): {stats[0]}")
    print(f"  - 租户用户 (is_superuser=FALSE & tenant_id IS NOT NULL): {stats[1]}")
    print(f"  - 用户总数: {stats[2]}")
    
    return inconsistent_count == 0

def generate_report(session, report_path):
    """生成修复报告"""
    print("\n" + "="*80)
    print("步骤 4: 生成修复报告")
    print("="*80)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 获取当前统计数据
    stats_query = text("""
        SELECT 
            COUNT(*) FILTER (WHERE is_superuser = TRUE AND tenant_id IS NULL) as superuser_count,
            COUNT(*) FILTER (WHERE is_superuser = FALSE AND tenant_id IS NOT NULL) as tenant_user_count,
            COUNT(*) FILTER (WHERE (is_superuser = TRUE AND tenant_id IS NOT NULL) 
                               OR (is_superuser = FALSE AND tenant_id IS NULL)) as inconsistent_count,
            COUNT(*) as total_count
        FROM users
    """)
    
    stats = session.execute(stats_query).fetchone()
    
    report_content = f"""
# 超级管理员数据修复报告
**生成时间**: {timestamp}
**执行脚本**: scripts/fix_superuser_data.py

## 修复目标
统一超级管理员判断标准，确保数据一致性：
- 超级管理员：`is_superuser = TRUE` AND `tenant_id IS NULL`
- 租户用户：`is_superuser = FALSE` AND `tenant_id IS NOT NULL`

## 当前状态

| 用户类型 | 数量 |
|---------|------|
| 超级管理员 (is_superuser=TRUE & tenant_id=NULL) | {stats[0]} |
| 租户用户 (is_superuser=FALSE & tenant_id IS NOT NULL) | {stats[1]} |
| 不一致记录 | {stats[2]} |
| 用户总数 | {stats[3]} |

## 修复策略

### 策略1: 降级不一致的超级管理员
将 `is_superuser=TRUE` 但 `tenant_id IS NOT NULL` 的用户降级为普通用户。

```sql
UPDATE users 
SET is_superuser = FALSE 
WHERE is_superuser = TRUE AND tenant_id IS NOT NULL;
```

### 策略2: 提升无租户的用户（需人工确认）
将 `tenant_id IS NULL` 但 `is_superuser=FALSE` 的用户设置为超级管理员。

⚠️ **警告**: 此操作会提升用户权限，建议人工审核后再执行。

```sql
UPDATE users 
SET is_superuser = TRUE 
WHERE tenant_id IS NULL AND is_superuser = FALSE;
```

## 验证方法

执行以下 SQL 查询，结果应为 0：

```sql
SELECT COUNT(*) FROM users 
WHERE (is_superuser = TRUE AND tenant_id IS NOT NULL)
   OR (is_superuser = FALSE AND tenant_id IS NULL);
```

## 后续步骤

1. ✅ 添加数据库约束 (`migrations/fix_superuser_constraints.sql`)
2. ✅ 使用统一判断函数 `is_superuser(user)` 替代 `user.tenant_id is None`
3. ✅ 在用户创建/更新时添加验证逻辑
4. ✅ 定期检查数据一致性

## 相关文件

- 数据库约束: `migrations/fix_superuser_constraints.sql`
- 统一判断函数: `app/core/auth.py::is_superuser()`
- 验证函数: `app/core/auth.py::validate_user_tenant_consistency()`
- 设计规范: `docs/超级管理员设计规范.md`
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n✓ 修复报告已生成: {report_path}")
    return report_path

def main():
    """主函数"""
    print("="*80)
    print("超级管理员数据修复脚本")
    print("Team 4: 统一超级管理员判断标准")
    print("="*80)
    
    # 解析命令行参数
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == '--apply':
        dry_run = False
    
    if dry_run:
        print("\n模式: 演练模式 (不会实际修改数据)")
        print("要实际执行修复，请使用: python scripts/fix_superuser_data.py --apply")
    else:
        print("\n模式: 实际执行 (将修改数据)")
        confirm = input("是否确认执行数据修复？(yes/no): ")
        if confirm.lower() != 'yes':
            print("已取消执行")
            return
    
    # 创建数据库会话
    engine = get_db_engine()
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # 步骤1: 检查不一致的数据
        total_inconsistent, type1, type2 = check_inconsistent_users(session)
        
        if total_inconsistent == 0:
            print("\n✓ 未发现数据不一致，无需修复！")
            # 仍然生成报告
            report_path = project_root / "data" / f"superuser_fix_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            generate_report(session, report_path)
            return
        
        # 步骤2: 修复不一致的数据
        fix_inconsistent_users(session, dry_run)
        
        if not dry_run:
            # 提交事务
            session.commit()
            print("\n✓ 数据修复已提交")
        
        # 步骤3: 验证修复结果
        verify_fix(session)
        
        # 步骤4: 生成报告
        report_path = project_root / "data" / f"superuser_fix_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        generate_report(session, report_path)
        
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        if not dry_run:
            session.rollback()
            print("已回滚事务")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()
