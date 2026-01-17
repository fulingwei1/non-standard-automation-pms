#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试权限API端点
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.base import get_db_session
from app.models.user import Permission


def test_permission_query():
    """测试权限查询"""
    try:
        with get_db_session() as db:
            # 直接查询
            perms = db.query(Permission).limit(5).all()
            print(f'✅ 查询成功，找到 {len(perms)} 条权限')

            if perms:
                p = perms[0]
                print(f'\n第一条权限信息:')
                print(f'  ID: {p.id}')
                try:
                    print(f'  权限编码: {p.permission_code}')
                except AttributeError as e:
                    print(f'  ❌ 无法访问permission_code: {e}')
                    # 尝试直接访问数据库字段
                    print(f'  尝试访问perm_code: {getattr(p, "perm_code", "不存在")}')

                try:
                    print(f'  权限名称: {p.permission_name}')
                except AttributeError as e:
                    print(f'  ❌ 无法访问permission_name: {e}')
                    print(f'  尝试访问perm_name: {getattr(p, "perm_name", "不存在")}')

                print(f'  模块: {p.module}')
                print(f'  操作: {p.action}')

                # 检查所有属性
                print(f'\n所有属性:')
                attrs = [attr for attr in dir(p) if not attr.startswith('_')]
                for attr in attrs[:10]:
                    print(f'    {attr}')
    except Exception as e:
        print(f'❌ 查询失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_permission_query()
