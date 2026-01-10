#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查待删除角色的使用情况
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.models.base import get_db_session

# 待删除的角色ID
roles_to_delete = [26, 62, 63, 64, 65, 74, 75, 76, 77, 79, 80]

with get_db_session() as session:
    print("检查待删除角色的使用情况:")
    print("=" * 60)
    
    for role_id in roles_to_delete:
        # 获取角色信息
        role_result = session.execute(text("""
            SELECT role_code, role_name FROM roles WHERE id = :role_id
        """), {"role_id": role_id})
        role = role_result.fetchone()
        
        if not role:
            continue
        
        print(f"\n角色 ID {role_id}: {role.role_code} - {role.role_name}")
        
        # 检查用户角色关联
        user_roles_result = session.execute(text("""
            SELECT COUNT(*) FROM user_roles WHERE role_id = :role_id
        """), {"role_id": role_id})
        user_roles_count = user_roles_result.scalar()
        print(f"  用户角色关联: {user_roles_count} 条")
        
        if user_roles_count > 0:
            user_roles = session.execute(text("""
                SELECT user_id FROM user_roles WHERE role_id = :role_id
            """), {"role_id": role_id})
            user_ids = [row[0] for row in user_roles]
            print(f"    涉及用户ID: {user_ids}")
        
        # 检查角色权限关联
        permissions_result = session.execute(text("""
            SELECT COUNT(*) FROM role_permissions WHERE role_id = :role_id
        """), {"role_id": role_id})
        permissions_count = permissions_result.scalar()
        print(f"  角色权限关联: {permissions_count} 条")
        
        # 检查用户角色分配
        try:
            assignments_result = session.execute(text("""
                SELECT COUNT(*) FROM user_role_assignments WHERE role_id = :role_id
            """), {"role_id": role_id})
            assignments_count = assignments_result.scalar()
            print(f"  用户角色分配: {assignments_count} 条")
        except:
            print(f"  用户角色分配: 表不存在或查询失败")
        
        # 检查时薪配置
        try:
            hourly_rate_result = session.execute(text("""
                SELECT COUNT(*) FROM hourly_rates WHERE role_id = :role_id
            """), {"role_id": role_id})
            hourly_rate_count = hourly_rate_result.scalar()
            print(f"  时薪配置: {hourly_rate_count} 条")
            if hourly_rate_count > 0:
                hourly_rates = session.execute(text("""
                    SELECT id, config_type, role_id FROM hourly_rates WHERE role_id = :role_id
                """), {"role_id": role_id})
                for hr in hourly_rates:
                    print(f"    配置ID {hr[0]}: {hr[1]}")
        except Exception as e:
            print(f"  时薪配置: 表不存在或查询失败 ({e})")
