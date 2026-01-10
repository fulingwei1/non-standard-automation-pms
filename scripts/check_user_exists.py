#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查用户是否存在
"""
import sys
sys.path.insert(0, '/Users/flw/non-standard-automation-pm')

from app.models.base import get_db_session
from app.models.user import User
from app.models.organization import Employee

def check_user(username: str):
    """检查用户是否存在"""
    with get_db_session() as db:
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            print(f"❌ 用户 '{username}' 不存在于数据库中")
            print("\n可能的原因：")
            print("1. 该员工尚未开通系统账号")
            print("2. 用户名拼写错误")
            print("3. 需要通过员工同步服务创建账号")
            return
        
        print(f"✅ 用户 '{username}' 存在于数据库中")
        print(f"\n用户信息：")
        print(f"  - ID: {user.id}")
        print(f"  - 用户名: {user.username}")
        print(f"  - 真实姓名: {user.real_name}")
        print(f"  - 工号: {user.employee_no}")
        print(f"  - 部门: {user.department}")
        print(f"  - 职位: {user.position}")
        print(f"  - 是否激活: {user.is_active}")
        print(f"  - 是否超级管理员: {user.is_superuser}")
        print(f"  - 最后登录时间: {user.last_login_at}")
        
        # 查询关联的员工信息
        if user.employee_id:
            employee = db.query(Employee).filter(Employee.id == user.employee_id).first()
            if employee:
                print(f"\n关联的员工信息：")
                print(f"  - 员工ID: {employee.id}")
                print(f"  - 员工编码: {employee.employee_code}")
                print(f"  - 员工姓名: {employee.name}")
                print(f"  - 部门: {employee.department}")
                print(f"  - 角色: {employee.role}")
        
        print(f"\n💡 提示：")
        print(f"  如果登录时显示'密码错误'，说明用户存在但密码不正确。")
        print(f"  请联系管理员重置密码。")

if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "fulingwei"
    check_user(username)
