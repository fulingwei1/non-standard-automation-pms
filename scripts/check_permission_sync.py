#!/usr/bin/env python3
"""
权限配置同步检查工具
检查前端和后端的权限配置是否一致
"""

import re
import json
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent

def extract_frontend_roles():
    """从前端 roleConfig.js 中提取财务权限角色"""
    frontend_file = ROOT_DIR / "frontend/src/lib/roleConfig.js"
    
    if not frontend_file.exists():
        return []
    
    content = frontend_file.read_text(encoding='utf-8')
    
    # 查找 hasFinanceAccess 函数
    pattern = r'hasFinanceAccess\([^)]*\)\s*\{[^}]*allowedRoles\s*=\s*\[(.*?)\];'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        return []
    
    roles_str = match.group(1)
    # 提取所有角色（去除引号和注释）
    roles = []
    for line in roles_str.split('\n'):
        line = line.strip()
        if not line or line.startswith('//'):
            continue
        # 提取引号中的内容
        role_matches = re.findall(r"['\"]([^'\"]+)['\"]", line)
        roles.extend(role_matches)
    
    return sorted(set(roles))

def extract_backend_roles():
    """从后端 security.py 中提取财务权限角色"""
    backend_file = ROOT_DIR / "app/core/security.py"
    
    if not backend_file.exists():
        return []
    
    content = backend_file.read_text(encoding='utf-8')
    
    # 查找 has_finance_access 函数
    pattern = r'finance_roles\s*=\s*\[(.*?)\]'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        return []
    
    roles_str = match.group(1)
    # 提取所有角色（去除引号和注释）
    roles = []
    for line in roles_str.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        # 提取引号中的内容
        role_matches = re.findall(r"['\"]([^'\"]+)['\"]", line)
        roles.extend(role_matches)
    
    return sorted(set(roles))

def check_sync():
    """检查前后端权限配置是否同步"""
    frontend_roles = extract_frontend_roles()
    backend_roles = extract_backend_roles()
    
    print("=" * 60)
    print("权限配置同步检查")
    print("=" * 60)
    print()
    
    print(f"前端角色数量: {len(frontend_roles)}")
    print(f"后端角色数量: {len(backend_roles)}")
    print()
    
    # 找出差异
    only_frontend = set(frontend_roles) - set(backend_roles)
    only_backend = set(backend_roles) - set(frontend_roles)
    common = set(frontend_roles) & set(backend_roles)
    
    if only_frontend:
        print("⚠️  仅在前端配置的角色:")
        for role in sorted(only_frontend):
            print(f"  - {role}")
        print()
    
    if only_backend:
        print("⚠️  仅在后端配置的角色:")
        for role in sorted(only_backend):
            print(f"  - {role}")
        print()
    
    if not only_frontend and not only_backend:
        print("✅ 前后端权限配置完全同步！")
        print()
        print("共同角色列表:")
        for role in sorted(common):
            print(f"  - {role}")
    else:
        print("❌ 前后端权限配置不一致！")
        print()
        print("建议:")
        if only_frontend:
            print("  1. 在后端 security.py 中添加以下角色:")
            for role in sorted(only_frontend):
                print(f"     '{role}',")
        if only_backend:
            print("  2. 在前端 roleConfig.js 中添加以下角色:")
            for role in sorted(only_backend):
                print(f"     '{role}',")
    
    print()
    print("=" * 60)
    
    return len(only_frontend) == 0 and len(only_backend) == 0

if __name__ == "__main__":
    is_synced = check_sync()
    exit(0 if is_synced else 1)
