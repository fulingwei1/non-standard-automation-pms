#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询前端首页13个账号的详细角色和权限信息
"""

import sys
sys.path.append('/Users/flw/non-standard-automation-pm')

from sqlalchemy import func
from app.models.base import SessionLocal
from app.models.user import User, Role, UserRole, ApiPermission, RoleApiPermission
import pandas as pd
from datetime import datetime

# 前端首页的13个账号
FRONTEND_ACCOUNTS = [
    'zhengrucai',    # 郑汝才
    'luoyixing',     # 骆奕兴
    'fulingwei',     # 符凌维
    'songkui',       # 宋魁
    'zhengqin',      # 郑琴
    'yaohong',       # 姚洪
    'changxiong',    # 常雄
    'gaoyong',       # 高勇
    'chenliang',     # 陈亮
    'tanzhangbin',   # 谭章斌
    'yuzhenhua',     # 于振华
    'wangjun',       # 王俊
    'wangzhihong',   # 王志红
]

def query_frontend_accounts():
    """查询前端账号的详细信息"""
    with SessionLocal() as db:
        print("=" * 100)
        print("🎯 前端首页快捷登录账号 - 角色与权限详细信息")
        print("=" * 100)
        print()
        
        results = []
        
        for username in FRONTEND_ACCOUNTS:
            # 查询用户基本信息
            user = db.query(User).filter(User.username == username).first()
            
            if not user:
                print(f"⚠️  用户 {username} 不存在")
                continue
            
            # 查询用户的角色
            user_roles = db.query(Role).join(UserRole).filter(
                UserRole.user_id == user.id
            ).all()
            
            # 查询角色的权限数量
            permissions_count = 0
            role_details = []
            
            for role in user_roles:
                # 统计该角色的权限数量
                perm_count = db.query(RoleApiPermission).filter(
                    RoleApiPermission.role_id == role.id
                ).count()
                
                permissions_count += perm_count
                
                role_details.append({
                    'role_code': role.role_code,
                    'role_name': role.role_name,
                    'data_scope': role.data_scope,
                    'permissions_count': perm_count,
                    'is_system': role.is_system,
                    'is_active': role.is_active
                })
            
            # 整理用户信息
            user_info = {
                'username': user.username,
                'real_name': user.real_name,
                'employee_no': user.employee_no,
                'department': user.department,
                'position': user.position,
                'is_superuser': user.is_superuser,
                'is_active': user.is_active,
                'roles_count': len(user_roles),
                'total_permissions': permissions_count,
                'roles': role_details,
                'last_login': user.last_login_at
            }
            
            results.append(user_info)
            
            # 打印单个用户信息
            print(f"📋 【{user.real_name}】 @{user.username}")
            print(f"   ├─ 工号: {user.employee_no or '无'}")
            print(f"   ├─ 部门: {user.department or '未知'}")
            print(f"   ├─ 职位: {user.position or '未知'}")
            print(f"   ├─ 状态: {'✅ 活跃' if user.is_active else '❌ 停用'}")
            print(f"   ├─ 超管: {'👑 是' if user.is_superuser else '否'}")
            print(f"   ├─ 角色数: {len(user_roles)} 个")
            print(f"   └─ 权限数: {permissions_count} 个")
            
            if role_details:
                print(f"   ")
                print(f"   🏷️  角色列表:")
                for idx, role in enumerate(role_details, 1):
                    status = '✅' if role['is_active'] else '❌'
                    system_badge = '🔧' if role['is_system'] else '📦'
                    print(f"      {idx}. {status} {system_badge} [{role['role_code']}] {role['role_name']}")
                    print(f"         ├─ 数据范围: {role['data_scope']}")
                    print(f"         └─ 权限数量: {role['permissions_count']} 个")
            
            if user.last_login_at:
                print(f"   🕐 最后登录: {user.last_login_at.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"   🕐 最后登录: 从未登录")
            
            print()
        
        # 生成统计摘要
        print("=" * 100)
        print("📊 统计摘要")
        print("=" * 100)
        
        if results:
            # 转换为DataFrame便于分析
            df = pd.DataFrame([{
                '姓名': r['real_name'],
                '用户名': r['username'],
                '部门': r['department'],
                '职位': r['position'],
                '超管': '是' if r['is_superuser'] else '否',
                '角色数': r['roles_count'],
                '权限数': r['total_permissions'],
                '状态': '活跃' if r['is_active'] else '停用'
            } for r in results])
            
            print(df.to_string(index=False))
            print()
            
            # 统计信息
            print(f"✅ 活跃账号: {sum(1 for r in results if r['is_active'])}/{len(results)}")
            print(f"👑 超级管理员: {sum(1 for r in results if r['is_superuser'])} 个")
            print(f"📊 平均角色数: {sum(r['roles_count'] for r in results) / len(results):.1f} 个/人")
            print(f"📊 平均权限数: {sum(r['total_permissions'] for r in results) / len(results):.0f} 个/人")
            print(f"🏢 涉及部门: {len(set(r['department'] for r in results if r['department']))} 个")
            
            # 部门分布
            dept_dist = {}
            for r in results:
                dept = r['department'] or '未知'
                dept_dist[dept] = dept_dist.get(dept, 0) + 1
            
            print()
            print("🏢 部门分布:")
            for dept, count in sorted(dept_dist.items(), key=lambda x: x[1], reverse=True):
                print(f"   {dept}: {count} 人")
            
            # 导出Excel
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_path = f'/Users/flw/non-standard-automation-pm/reports/前端账号详情_{timestamp}.xlsx'
            
            # 创建详细的Excel报告
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                # Sheet 1: 用户概览
                df.to_excel(writer, sheet_name='用户概览', index=False)
                
                # Sheet 2: 详细角色信息
                role_data = []
                for r in results:
                    for role in r['roles']:
                        role_data.append({
                            '姓名': r['real_name'],
                            '用户名': r['username'],
                            '角色编码': role['role_code'],
                            '角色名称': role['role_name'],
                            '数据范围': role['data_scope'],
                            '权限数量': role['permissions_count'],
                            '是否系统角色': '是' if role['is_system'] else '否',
                            '是否启用': '是' if role['is_active'] else '否'
                        })
                
                if role_data:
                    role_df = pd.DataFrame(role_data)
                    role_df.to_excel(writer, sheet_name='角色详情', index=False)
            
            print()
            print(f"📄 详细报告已导出: {excel_path}")
        
        return results

if __name__ == "__main__":
    try:
        results = query_frontend_accounts()
        print()
        print("✅ 查询完成!")
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()