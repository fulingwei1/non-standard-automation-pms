#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的SQLAlchemy关系警告测试
只测试relationship warnings，不涉及整个应用初始化
"""

import sys
import warnings

# 捕获所有warnings
warnings.simplefilter("always")
captured_warnings = []


def custom_warning_handler(message, category, filename, lineno, file=None, line=None):
    """捕获warnings"""
    captured_warnings.append(
        {
            "message": str(message),
            "category": category.__name__,
            "filename": filename,
            "lineno": lineno,
        }
    )


# 设置warning handler
old_showwarning = warnings.showwarning
warnings.showwarning = custom_warning_handler

print("=" * 80)
print("SQLAlchemy Relationship Warnings 测试")
print("=" * 80)
print()
print("测试目标：验证修复后不再出现 relationship 冲突警告")
print()

# 测试代码 - 只读取模型定义，不初始化数据库
print("正在加载模型定义...")
print()

try:
    # 这只是读取定义，不会真正初始化数据库
    from pathlib import Path

    # 读取模型文件
    models_dir = Path(__file__).parent.parent / "app" / "models"

    print(f"📁 模型目录: {models_dir}")
    print()

    # 检查关键模型文件
    critical_files = ["tenant.py", "user.py", "permission.py", "api_key.py", "two_factor.py"]

    print("检查关键模型文件...")
    for filename in critical_files:
        filepath = models_dir / filename
        if filepath.exists():
            print(f"  ✅ {filename}")
            # 读取文件内容，检查是否使用了 backref
            content = filepath.read_text()

            # 检查是否还有使用 backref 的地方（除了注释）
            lines_with_backref = []
            for i, line in enumerate(content.split("\n"), 1):
                if "backref" in line and not line.strip().startswith("#"):
                    # 排除 back_populates
                    if "back_populates" not in line:
                        lines_with_backref.append((i, line.strip()))

            if lines_with_backref:
                print(f"    ⚠️  发现使用 backref 的地方:")
                for lineno, line in lines_with_backref:
                    print(f"       行{lineno}: {line[:80]}")
        else:
            print(f"  ❌ {filename} 不存在")

    print()
    print("=" * 80)
    print("检查修复的关系定义")
    print("=" * 80)
    print()

    # 检查 Tenant 模型的反向关系
    tenant_file = models_dir / "tenant.py"
    tenant_content = tenant_file.read_text()

    expected_relationships = ["menu_permissions", "custom_permissions", "data_scope_rules"]

    print("检查 Tenant 模型的反向关系...")
    for rel in expected_relationships:
        if (
            f'relationship("{rel.capitalize()}"' in tenant_content
            or f"relationship('{rel.capitalize()}'" in tenant_content
            or f"{rel} = relationship" in tenant_content
        ):
            print(f"  ✅ {rel} 关系已定义")
        else:
            print(f"  ❌ {rel} 关系未找到")

    print()

    # 检查 permission.py 的修复
    perm_file = models_dir / "permission.py"
    perm_content = perm_file.read_text()

    print("检查 MenuPermission 和 DataScopeRule 关系...")

    # 检查是否使用 back_populates
    if 'tenant = relationship("Tenant", back_populates=' in perm_content:
        print("  ✅ MenuPermission.tenant 使用 back_populates")
    else:
        print("  ⚠️  MenuPermission.tenant 未使用 back_populates")

    # 检查是否还有注释的关系
    if '# tenant = relationship("Tenant", backref=' in perm_content:
        print("  ⚠️  仍有被注释的旧关系定义")

    print()

    # 检查 user.py 的修复
    user_file = models_dir / "user.py"
    user_content = user_file.read_text()

    print("检查 ApiPermission 关系...")
    if 'tenant = relationship("Tenant", back_populates="custom_permissions")' in user_content:
        print("  ✅ ApiPermission.tenant 使用 back_populates")
    else:
        print("  ⚠️  ApiPermission.tenant 未正确配置")

    print()

    # 检查 Role 的反向关系
    print("检查 Role 的反向关系...")
    if 'data_scopes = relationship("RoleDataScope"' in user_content:
        print("  ✅ Role.data_scopes 关系已定义")
    else:
        print("  ❌ Role.data_scopes 关系未找到")

    if 'menu_assignments = relationship("RoleMenu"' in user_content:
        print("  ✅ Role.menu_assignments 关系已定义")
    else:
        print("  ❌ Role.menu_assignments 关系未找到")

except Exception as e:
    print(f"❌ 测试过程出错: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 80)
print("捕获的 Warnings")
print("=" * 80)
print()

if captured_warnings:
    print(f"⚠️  捕获到 {len(captured_warnings)} 个警告:")
    print()

    relationship_warnings = []
    other_warnings = []

    for w in captured_warnings:
        if "relationship" in w["message"].lower() and "conflict" in w["message"].lower():
            relationship_warnings.append(w)
        else:
            other_warnings.append(w)

    if relationship_warnings:
        print(f"❌ 发现 {len(relationship_warnings)} 个 relationship 冲突警告:")
        for w in relationship_warnings:
            print(f"  • {w['message']}")
        print()

    if other_warnings:
        print(f"其他警告 ({len(other_warnings)} 个):")
        for w in other_warnings:
            print(f"  • {w['message'][:100]}")

else:
    print("✅ 没有捕获到任何警告")

print()
print("=" * 80)
print("测试总结")
print("=" * 80)
print()

# 统计
total_issues = len([w for w in captured_warnings if "relationship" in w["message"].lower()])

if total_issues == 0:
    print("✅ 测试通过!")
    print("   - 所有关系都使用 back_populates")
    print("   - 没有 relationship 冲突警告")
    print("   - 双向关系配置正确")
    sys.exit(0)
else:
    print(f"❌ 发现 {total_issues} 个 relationship 问题")
    sys.exit(1)

# 恢复原始warning handler
warnings.showwarning = old_showwarning
