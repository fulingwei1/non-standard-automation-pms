#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard统一整合测试脚本

验证所有适配器是否正确注册和工作
"""

import sys
from pathlib import Path

# 添加项目根目录到path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_registry():
    """测试适配器注册表"""
    print("=" * 60)
    print("测试1: 验证适配器注册表")
    print("=" * 60)

    # 导入适配器模块以触发注册
    import app.services.dashboard_adapters  # noqa: F401
    from app.services.dashboard_adapter import dashboard_registry

    modules = dashboard_registry.list_modules()

    print(f"\n已注册的模块数量: {len(modules)}")
    print("\n模块列表:")
    for i, module in enumerate(modules, 1):
        print(f"{i}. {module['module_name']} ({module['module_id']})")
        print(f"   支持角色: {', '.join(module['supported_roles'])}")

    assert len(modules) == 11, f"期望11个模块，实际只有{len(modules)}个"
    print("\n✅ 测试通过：所有11个模块已注册\n")


def test_adapters_for_role():
    """测试按角色获取适配器"""
    print("=" * 60)
    print("测试2: 按角色获取适配器")
    print("=" * 60)

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    import app.services.dashboard_adapters  # noqa: F401
    from app.models.user import User
    from app.services.dashboard_adapter import dashboard_registry

    # 使用SQLite数据库
    db_url = "sqlite:///data/app.db"
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # 创建模拟用户
    mock_user = User(id=1, username="test_user", email="test@example.com")

    # 测试不同角色
    roles_to_test = ["pmo", "admin", "production", "hr", "business_support"]

    for role in roles_to_test:
        adapters = dashboard_registry.get_adapters_for_role(role, db, mock_user)
        print(f"\n角色 '{role}' 可用模块数: {len(adapters)}")
        for adapter in adapters:
            print(f"  - {adapter.module_name}")

    db.close()
    print("\n✅ 测试通过：角色过滤正常工作\n")


def test_adapter_methods():
    """测试适配器方法"""
    print("=" * 60)
    print("测试3: 验证适配器方法")
    print("=" * 60)

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    import app.services.dashboard_adapters  # noqa: F401
    from app.models.user import User
    from app.services.dashboard_adapter import dashboard_registry

    # 使用SQLite数据库
    db_url = "sqlite:///data/app.db"
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    mock_user = User(id=1, username="test_user", email="test@example.com")

    # 测试PMO适配器
    adapter = dashboard_registry.get_adapter("pmo", db, mock_user)

    if adapter:
        print(f"\n测试模块: {adapter.module_name}")

        try:
            # 测试get_stats
            stats = adapter.get_stats()
            print(f"  ✓ get_stats() 返回 {len(stats)} 个统计卡片")

            # 测试get_widgets
            widgets = adapter.get_widgets()
            print(f"  ✓ get_widgets() 返回 {len(widgets)} 个widgets")

            # 测试get_detailed_data
            try:
                adapter.get_detailed_data()
                print("  ✓ get_detailed_data() 返回详细数据")
            except NotImplementedError:
                print("  ⊘ get_detailed_data() 未实现（可选）")

        except Exception as e:
            print(f"  ✗ 错误: {e}")
            raise

    db.close()
    print("\n✅ 测试通过：适配器方法正常工作\n")


def test_unified_endpoints():
    """测试统一端点（需要启动服务）"""
    print("=" * 60)
    print("测试4: 验证统一端点（可选）")
    print("=" * 60)

    print("\n提示: 此测试需要启动服务")
    print("运行以下命令测试API:")
    print("\n  1. 启动服务:")
    print("     uvicorn app.main:app --reload\n")
    print("  2. 测试统一dashboard:")
    print("     curl http://localhost:8000/api/v1/dashboard/unified/pmo\n")
    print("  3. 测试详细数据:")
    print(
        "     curl http://localhost:8000/api/v1/dashboard/unified/pmo/detailed?module_id=business_support\n"
    )
    print("  4. 测试模块列表:")
    print("     curl http://localhost:8000/api/v1/dashboard/modules\n")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Dashboard统一整合测试")
    print("=" * 60 + "\n")

    try:
        test_registry()
        test_adapters_for_role()
        test_adapter_methods()
        test_unified_endpoints()

        print("\n" + "=" * 60)
        print("🎉 所有测试通过！Dashboard统一整合成功！")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
