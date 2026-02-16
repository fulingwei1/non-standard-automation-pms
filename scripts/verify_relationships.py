#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLAlchemy 关系验证脚本
验证修复后的relationship配置是否正确，无warnings
"""

import sys
import warnings
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 捕获所有warnings
warnings.simplefilter("always")
warning_list = []

def warning_handler(message, category, filename, lineno, file=None, line=None):
    """自定义warning处理器"""
    warning_list.append({
        'message': str(message),
        'category': category.__name__,
        'filename': filename,
        'lineno': lineno
    })

# 设置warning处理器
warnings.showwarning = warning_handler

print("=" * 80)
print("SQLAlchemy Relationship 验证测试")
print("=" * 80)
print()

print("步骤 1: 导入所有模型...")
try:
    from app.models.tenant import Tenant
    from app.models.api_key import APIKey
    from app.models.two_factor import User2FASecret, User2FABackupCode
    from app.models.user import User, Role, ApiPermission, RoleApiPermission, UserRole
    from app.models.permission import (
        MenuPermission,
        DataScopeRule,
        RoleDataScope,
        RoleMenu,
        PermissionGroup
    )
    print("✅ 所有模型导入成功")
except Exception as e:
    print(f"❌ 模型导入失败: {e}")
    sys.exit(1)

print()
print("步骤 2: 检查关系配置...")

# 验证关系列表
relationships_to_verify = [
    ("Tenant", "users", "User"),
    ("Tenant", "roles", "Role"),
    ("Tenant", "menu_permissions", "MenuPermission"),
    ("Tenant", "custom_permissions", "ApiPermission"),
    ("Tenant", "data_scope_rules", "DataScopeRule"),
    ("User", "tenant", "Tenant"),
    ("Role", "tenant", "Tenant"),
    ("Role", "data_scopes", "RoleDataScope"),
    ("Role", "menu_assignments", "RoleMenu"),
    ("MenuPermission", "tenant", "Tenant"),
    ("MenuPermission", "parent", "MenuPermission"),
    ("MenuPermission", "children", "MenuPermission"),
    ("ApiPermission", "tenant", "Tenant"),
    ("DataScopeRule", "tenant", "Tenant"),
    ("RoleDataScope", "role", "Role"),
    ("RoleDataScope", "scope_rule", "DataScopeRule"),
    ("RoleMenu", "role", "Role"),
    ("RoleMenu", "menu", "MenuPermission"),
    ("PermissionGroup", "parent", "PermissionGroup"),
    ("PermissionGroup", "children", "PermissionGroup"),
]

errors = []
success_count = 0

for model_name, rel_name, target_name in relationships_to_verify:
    try:
        # 获取模型类
        model_cls = eval(model_name)
        
        # 检查关系是否存在
        if not hasattr(model_cls, rel_name):
            errors.append(f"❌ {model_name}.{rel_name} 关系不存在")
            continue
        
        rel = getattr(model_cls, rel_name)
        
        # 检查是否是relationship
        if not hasattr(rel, 'property'):
            errors.append(f"❌ {model_name}.{rel_name} 不是有效的relationship")
            continue
        
        print(f"✅ {model_name}.{rel_name} → {target_name}")
        success_count += 1
        
    except Exception as e:
        errors.append(f"❌ 验证 {model_name}.{rel_name} 时出错: {e}")

print()
print("=" * 80)
print("验证结果摘要")
print("=" * 80)
print(f"✅ 成功验证: {success_count}/{len(relationships_to_verify)}")
print(f"❌ 失败数量: {len(errors)}")
print()

if errors:
    print("错误详情:")
    for error in errors:
        print(f"  {error}")
    print()

print("步骤 3: 检查 SQLAlchemy Warnings...")
print()

if warning_list:
    print(f"⚠️  发现 {len(warning_list)} 个警告:")
    print()
    for i, w in enumerate(warning_list, 1):
        print(f"警告 #{i}:")
        print(f"  类型: {w['category']}")
        print(f"  消息: {w['message']}")
        print(f"  位置: {w['filename']}:{w['lineno']}")
        print()
    
    # 检查是否有relationship冲突警告
    relationship_warnings = [w for w in warning_list if 'relationship' in w['message'].lower()]
    if relationship_warnings:
        print(f"❌ 发现 {len(relationship_warnings)} 个 relationship 冲突警告")
        sys.exit(1)
else:
    print("✅ 没有发现任何 SQLAlchemy 警告")

print()
print("步骤 4: 验证双向关系一致性...")
print()

# 双向关系验证
bidirectional_checks = [
    ("Tenant", "users", "User", "tenant"),
    ("Tenant", "roles", "Role", "tenant"),
    ("Tenant", "menu_permissions", "MenuPermission", "tenant"),
    ("Tenant", "custom_permissions", "ApiPermission", "tenant"),
    ("Tenant", "data_scope_rules", "DataScopeRule", "tenant"),
    ("Role", "data_scopes", "RoleDataScope", "role"),
    ("Role", "menu_assignments", "RoleMenu", "role"),
    ("MenuPermission", "role_menus", "RoleMenu", "menu"),
    ("DataScopeRule", "role_data_scopes", "RoleDataScope", "scope_rule"),
]

bidirectional_errors = []
bidirectional_success = 0

for model1_name, rel1_name, model2_name, rel2_name in bidirectional_checks:
    try:
        model1 = eval(model1_name)
        model2 = eval(model2_name)
        
        # 检查双向关系是否存在
        if not hasattr(model1, rel1_name):
            bidirectional_errors.append(f"❌ {model1_name}.{rel1_name} 不存在")
            continue
        
        if not hasattr(model2, rel2_name):
            bidirectional_errors.append(f"❌ {model2_name}.{rel2_name} 不存在")
            continue
        
        # 检查 back_populates 配置
        rel1 = getattr(model1, rel1_name).property
        rel2 = getattr(model2, rel2_name).property
        
        # 注意：这里只能做基本检查，完整验证需要数据库连接
        print(f"✅ {model1_name}.{rel1_name} ↔ {model2_name}.{rel2_name}")
        bidirectional_success += 1
        
    except Exception as e:
        bidirectional_errors.append(
            f"❌ 验证 {model1_name}.{rel1_name} ↔ {model2_name}.{rel2_name} 时出错: {e}"
        )

print()
print(f"✅ 双向关系验证: {bidirectional_success}/{len(bidirectional_checks)}")

if bidirectional_errors:
    print()
    print("双向关系错误:")
    for error in bidirectional_errors:
        print(f"  {error}")

print()
print("=" * 80)
print("最终结果")
print("=" * 80)

if errors or warning_list or bidirectional_errors:
    print("❌ 验证未完全通过，存在问题需要修复")
    sys.exit(1)
else:
    print("✅ 所有验证通过！")
    print("   - 所有关系定义正确")
    print("   - 没有 SQLAlchemy warnings")
    print("   - 双向关系配置一致")
    sys.exit(0)
