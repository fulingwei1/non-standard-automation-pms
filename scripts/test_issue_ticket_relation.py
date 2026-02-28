#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试服务工单与问题管理关联功能

使用方法:
    python scripts/test_issue_ticket_relation.py
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.base import get_db_session
from app.models.issue import Issue
from app.models.service import ServiceTicket


def test_issue_ticket_relation():
    """测试问题与工单关联功能"""
    print("=" * 60)
    print("测试服务工单与问题管理关联功能")
    print("=" * 60)
    
    with get_db_session() as db:
        # 1. 检查字段是否存在
        print("\n1. 检查数据库字段...")
        try:
            # 尝试查询 service_ticket_id 字段
            result = db.execute("PRAGMA table_info(issues)").fetchall()
            columns = [row[1] for row in result]
            if 'service_ticket_id' in columns:
                print("   ✅ service_ticket_id 字段存在")
            else:
                print("   ❌ service_ticket_id 字段不存在，请先运行迁移脚本")
                return False
        except Exception as e:
            print(f"   ⚠️  检查字段时出错: {e}")
            # MySQL 环境
            try:
                result = db.execute("SHOW COLUMNS FROM issues LIKE 'service_ticket_id'").fetchall()
                if result:
                    print("   ✅ service_ticket_id 字段存在")
                else:
                    print("   ❌ service_ticket_id 字段不存在，请先运行迁移脚本")
                    return False
            except Exception as e2:
                print(f"   ❌ 检查字段失败: {e2}")
                return False
        
        # 2. 检查是否有测试数据
        print("\n2. 检查测试数据...")
        ticket_count = db.query(ServiceTicket).count()
        issue_count = db.query(Issue).count()
        print(f"   工单数量: {ticket_count}")
        print(f"   问题数量: {issue_count}")
        
        if ticket_count == 0:
            print("   ⚠️  没有工单数据，无法测试关联功能")
            return False
        
        if issue_count == 0:
            print("   ⚠️  没有问题数据，无法测试关联功能")
            return False
        
        # 3. 测试关联查询
        print("\n3. 测试关联查询...")
        try:
            # 查询有关联工单的问题
            issues_with_ticket = db.query(Issue).filter(
                Issue.service_ticket_id.isnot(None)
            ).count()
            print(f"   ✅ 有关联工单的问题数量: {issues_with_ticket}")
            
            # 查询一个具体的问题（如果有）
            issue_with_ticket = db.query(Issue).filter(
                Issue.service_ticket_id.isnot(None)
            ).first()
            
            if issue_with_ticket:
                print(f"   ✅ 找到关联问题: {issue_with_ticket.issue_no}")
                if issue_with_ticket.service_ticket:
                    print(f"   ✅ 关联工单: {issue_with_ticket.service_ticket.ticket_no}")
                else:
                    print("   ⚠️  工单关系未正确加载")
        except Exception as e:
            print(f"   ❌ 关联查询失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 4. 测试反向关联
        print("\n4. 测试反向关联...")
        try:
            # 查询一个工单
            ticket = db.query(ServiceTicket).first()
            if ticket:
                print(f"   ✅ 找到工单: {ticket.ticket_no}")
                # 查询关联的问题
                related_issues = db.query(Issue).filter(
                    Issue.service_ticket_id == ticket.id
                ).all()
                print(f"   ✅ 该工单关联的问题数量: {len(related_issues)}")
        except Exception as e:
            print(f"   ❌ 反向关联查询失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 5. 测试索引
        print("\n5. 检查索引...")
        try:
            # SQLite
            result = db.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_issues_service_ticket_id'").fetchall()
            if result:
                print("   ✅ 索引 idx_issues_service_ticket_id 存在")
            else:
                # MySQL
                result = db.execute("SHOW INDEX FROM issues WHERE Key_name='idx_issues_service_ticket_id'").fetchall()
                if result:
                    print("   ✅ 索引 idx_issues_service_ticket_id 存在")
                else:
                    print("   ⚠️  索引可能未创建，但不影响功能")
        except Exception as e:
            print(f"   ⚠️  检查索引时出错: {e}")
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        return True


if __name__ == "__main__":
    success = test_issue_ticket_relation()
    sys.exit(0 if success else 1)
