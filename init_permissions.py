#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API权限数据初始化工具

用法:
    python3 init_permissions.py          # 初始化所有权限
    python3 init_permissions.py --admin  # 只修复ADMIN权限
    python3 init_permissions.py --check  # 检查权限状态
"""

import sys
import os
import argparse

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

def check_permissions_status():
    """检查权限数据状态"""
    # 先导入所有模型（避免SQLAlchemy关系错误）
    import app.models  # noqa
    from app.models.base import SessionLocal
    from app.models.user import ApiPermission, RoleApiPermission, Role
    
    print("="*70)
    print("API权限数据状态检查")
    print("="*70)
    
    db = SessionLocal()
    try:
        # 检查API权限数量
        perm_count = db.query(ApiPermission).count()
        print(f"\n📊 API权限记录: {perm_count} 条")
        
        if perm_count == 0:
            print("   ⚠️  警告: 权限表为空，需要初始化！")
        elif perm_count < 20:
            print(f"   ⚠️  警告: 权限数量较少（< 20），可能不完整")
        else:
            print(f"   ✓ 权限数量正常")
        
        # 检查角色权限映射
        mapping_count = db.query(RoleApiPermission).count()
        print(f"\n📊 角色权限映射: {mapping_count} 条")
        
        if mapping_count == 0:
            print("   ⚠️  警告: 角色权限映射为空，需要初始化！")
        elif mapping_count < 50:
            print(f"   ⚠️  警告: 映射数量较少（< 50），可能不完整")
        else:
            print(f"   ✓ 映射数量正常")
        
        # 检查ADMIN角色权限
        admin_role = db.query(Role).filter(Role.role_code == "ADMIN").first()
        if admin_role:
            admin_perm_count = db.query(RoleApiPermission).filter(
                RoleApiPermission.role_id == admin_role.id
            ).count()
            print(f"\n📊 ADMIN角色权限: {admin_perm_count} 个")
            
            if admin_perm_count == 0:
                print("   ❌ 错误: ADMIN无任何权限，会导致403错误！")
            elif admin_perm_count < perm_count:
                print(f"   ⚠️  警告: ADMIN缺少 {perm_count - admin_perm_count} 个权限")
            else:
                print(f"   ✓ ADMIN拥有所有权限")
        else:
            print("\n   ❌ 错误: ADMIN角色不存在！")
        
        # 列出前10个权限
        if perm_count > 0:
            print("\n📋 权限示例（前10个）:")
            perms = db.query(ApiPermission).limit(10).all()
            for p in perms:
                print(f"   - {p.perm_code}: {p.perm_name}")
        
        print("\n" + "="*70)
        
        # 返回是否需要初始化
        return perm_count == 0 or mapping_count == 0 or (admin_role and admin_perm_count == 0)
        
    finally:
        db.close()


def init_all_permissions():
    """初始化所有权限数据"""
    import app.models  # noqa
    from app.models.base import SessionLocal
    from app.utils.init_permissions_data import init_api_permissions_data, ensure_admin_permissions
    
    print("="*70)
    print("API权限数据初始化")
    print("="*70)
    
    db = SessionLocal()
    try:
        print("\n步骤1: 初始化API权限和角色映射...")
        result = init_api_permissions_data(db)
        
        print(f"\n结果:")
        print(f"  ✓ 权限记录: 新建 {result['permissions_created']} 个，已存在 {result['permissions_existing']} 个")
        print(f"  ✓ 角色映射: 新建 {result['role_mappings_created']} 条，已存在 {result['role_mappings_existing']} 条")
        
        if result['errors']:
            print(f"\n  ❌ 错误: {', '.join(result['errors'])}")
            return False
        
        print("\n步骤2: 确保ADMIN角色拥有所有权限...")
        if ensure_admin_permissions(db):
            print("  ✓ ADMIN权限检查完成")
        else:
            print("  ❌ ADMIN权限检查失败")
            return False
        
        print("\n" + "="*70)
        print("✓ 初始化成功！")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def fix_admin_permissions():
    """只修复ADMIN权限"""
    import app.models  # noqa
    from app.models.base import SessionLocal
    from app.utils.init_permissions_data import ensure_admin_permissions
    
    print("="*70)
    print("修复ADMIN角色权限")
    print("="*70)
    
    db = SessionLocal()
    try:
        print("\n正在检查和修复ADMIN权限...")
        if ensure_admin_permissions(db):
            print("\n✓ ADMIN权限修复成功！")
            return True
        else:
            print("\n❌ ADMIN权限修复失败")
            return False
        
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="API权限数据初始化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 init_permissions.py              # 完整初始化
  python3 init_permissions.py --check      # 检查状态
  python3 init_permissions.py --admin      # 只修复ADMIN权限
  python3 init_permissions.py --auto       # 自动检查并按需初始化
        """
    )
    
    parser.add_argument(
        "--check", action="store_true",
        help="检查权限数据状态（不修改）"
    )
    parser.add_argument(
        "--admin", action="store_true",
        help="只修复ADMIN角色权限"
    )
    parser.add_argument(
        "--auto", action="store_true",
        help="自动检查并按需初始化"
    )
    
    args = parser.parse_args()
    
    if args.check:
        # 只检查状态
        needs_init = check_permissions_status()
        if needs_init:
            print("\n💡 建议执行: python3 init_permissions.py")
            sys.exit(1)
        else:
            print("\n✓ 权限数据状态正常")
            sys.exit(0)
    
    elif args.admin:
        # 只修复ADMIN权限
        success = fix_admin_permissions()
        sys.exit(0 if success else 1)
    
    elif args.auto:
        # 自动检查并按需初始化
        print("自动检查权限状态...\n")
        needs_init = check_permissions_status()
        
        if needs_init:
            print("\n需要初始化，开始执行...\n")
            success = init_all_permissions()
            sys.exit(0 if success else 1)
        else:
            print("\n✓ 权限数据已存在，无需初始化")
            sys.exit(0)
    
    else:
        # 默认: 完整初始化
        success = init_all_permissions()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
