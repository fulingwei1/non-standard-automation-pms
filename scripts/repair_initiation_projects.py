#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
立项申请项目修复脚本

用于修复已批准但未创建项目的立项申请。

使用方法:
1. 基础模式 - 查看需要修复的立项申请:
   python scripts/repair_initiation_projects.py

2. 交互模式 - 逐个选择项目经理并创建项目:
   python scripts/repair_initiation_projects.py --interactive

3. 自动模式 - 使用默认项目经理批量创建:
   python scripts/repair_initiation_projects.py --auto --pm-id <项目经理ID>
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.pmo import PmoProjectInitiation
from app.models.project import Customer, Project
from app.models.user import User
from app.utils.project_utils import init_project_stages


def get_db_session():
    """获取数据库会话"""
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return SessionLocal()


def get_pending_initiations(db):
    """
    获取需要修复的立项申请

    Returns:
        list: 已批准但未创建项目的立项申请列表
    """
    initiations = (
        db.query(PmoProjectInitiation)
        .filter(
            PmoProjectInitiation.status == "APPROVED", PmoProjectInitiation.project_id.is_(None)
        )
        .all()
    )

    return initiations


def get_available_pms(db):
    """
    获取可用的项目经理列表

    Returns:
        list: 用户列表（可以选择作为项目经理）
    """
    # 获取所有用户，实际项目中可能需要根据角色过滤
    users = db.query(User).filter(User.is_active == True).order_by(User.real_name).all()

    return users


def create_project_from_initiation(db, initiation, pm_id):
    """
    从立项申请创建项目

    Args:
        db: 数据库会话
        initiation: 立项申请对象
        pm_id: 项目经理ID

    Returns:
        Project: 创建的项目对象，如果失败返回 None
    """
    try:
        # 生成项目编码
        today = date.today()
        project_code = f"PJ{today.strftime('%y%m%d')}{initiation.id:03d}"

        # 检查项目编码是否已存在
        existing = db.query(Project).filter(Project.project_code == project_code).first()
        if existing:
            project_code = f"PJ{today.strftime('%y%m%d')}{initiation.id:04d}"

        # 查找或创建客户
        customer = (
            db.query(Customer).filter(Customer.customer_name == initiation.customer_name).first()
        )
        customer_id = customer.id if customer else None

        # 获取项目经理信息
        pm = db.query(User).filter(User.id == pm_id).first()
        if not pm:
            print(f"  ❌ 错误: 找不到ID为 {pm_id} 的用户")
            return None

        # 创建项目
        project = Project(
            project_code=project_code,
            project_name=initiation.project_name,
            customer_id=customer_id,
            customer_name=initiation.customer_name,
            contract_no=initiation.contract_no,
            contract_amount=initiation.contract_amount or Decimal("0"),
            contract_date=initiation.required_start_date,
            planned_start_date=initiation.required_start_date,
            planned_end_date=initiation.required_end_date,
            pm_id=pm_id,
            pm_name=pm.real_name or pm.username,
            project_type=initiation.project_type,
            stage="S1",
            status="ST01",
            health="H1",
        )

        db.add(project)
        db.flush()

        # 初始化项目阶段
        init_project_stages(db, project.id)

        # 关联立项申请和项目
        initiation.project_id = project.id

        db.commit()

        return project

    except Exception as e:
        db.rollback()
        print(f"  ❌ 创建项目失败: {e}")
        return None


def display_initiations(initiations):
    """显示立项申请列表"""
    if not initiations:
        print("\n✅ 没有需要修复的立项申请")
        return

    print(f"\n{'='*100}")
    print(f"找到 {len(initiations)} 个已批准但未创建项目的立项申请:")
    print(f"{'='*100}\n")

    for idx, init in enumerate(initiations, 1):
        print(f"{idx}. [{init.id}] {init.project_name}")
        print(f"   客户: {init.customer_name}")
        print(f"   合同金额: {init.contract_amount or 'N/A'}")
        print(f"   申请时间: {init.apply_date or init.created_at}")
        print(f"   审批时间: {init.approved_at or 'N/A'}")
        print(f"   当前项目经理: {init.approved_pm_id or '未指定'}")
        print()


def interactive_mode(db, initiations, pms):
    """交互模式：逐个选择项目经理并创建项目"""
    if not initiations:
        print("\n✅ 没有需要修复的立项申请")
        return

    print(f"\n{'='*100}")
    print("交互模式：逐个选择项目经理")
    print(f"{'='*100}\n")

    success_count = 0

    for idx, initiation in enumerate(initiations, 1):
        print(f"\n[{idx}/{len(initiations)}] 处理立项申请: {initiation.project_name}")

        # 显示可用项目经理
        print("\n可用的项目经理:")
        pm_map = {}
        for p_idx, pm in enumerate(pms[:20], 1):  # 只显示前20个
            pm_map[p_idx] = pm.id
            print(f"  {p_idx}. {pm.real_name or pm.username} (ID: {pm.id})")

        # 获取用户输入
        while True:
            try:
                choice = input(
                    f"\n请选择项目经理 (1-{len(pm_map)}, 或跳过输入 s, 退出输入 q): "
                ).strip()

                if choice.lower() == "q":
                    print("退出修复流程")
                    return
                elif choice.lower() == "s":
                    print("跳过此立项申请")
                    break

                pm_idx = int(choice)
                if pm_idx not in pm_map:
                    print(f"❌ 无效的选择，请输入 1-{len(pm_map)}")
                    continue

                pm_id = pm_map[pm_idx]
                pm = next(p for p in pms if p.id == pm_id)

                # 创建项目
                print("\n正在创建项目...")
                project = create_project_from_initiation(db, initiation, pm_id)

                if project:
                    print("  ✅ 项目创建成功!")
                    print(f"     项目编码: {project.project_code}")
                    print(f"     项目ID: {project.id}")
                    print(f"     项目经理: {pm.real_name or pm.username}")
                    success_count += 1
                else:
                    print("  ❌ 项目创建失败")

                break

            except ValueError:
                print("❌ 无效的输入")
            except KeyboardInterrupt:
                print("\n\n用户中断")
                return

    print(f"\n{'='*100}")
    print(f"修复完成！成功创建 {success_count}/{len(initiations)} 个项目")
    print(f"{'='*100}")


def auto_mode(db, initiations, pm_id):
    """自动模式：使用指定的项目经理批量创建项目"""
    if not initiations:
        print("\n✅ 没有需要修复的立项申请")
        return

    # 验证项目经理
    pm = db.query(User).filter(User.id == pm_id).first()
    if not pm:
        print(f"❌ 错误: 找不到ID为 {pm_id} 的用户")
        return

    print(f"\n{'='*100}")
    print(f"自动模式：使用项目经理 {pm.real_name or pm.username} (ID: {pm_id}) 批量创建项目")
    print(f"{'='*100}\n")

    success_count = 0
    failed_count = 0

    for idx, initiation in enumerate(initiations, 1):
        print(f"[{idx}/{len(initiations)}] {initiation.project_name}... ", end="", flush=True)

        project = create_project_from_initiation(db, initiation, pm_id)

        if project:
            print(f"✅ 成功 ({project.project_code})")
            success_count += 1
        else:
            print("❌ 失败")
            failed_count += 1

    print(f"\n{'='*100}")
    print(f"批量创建完成！成功: {success_count}, 失败: {failed_count}, 总计: {len(initiations)}")
    print(f"{'='*100}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="立项申请项目修复脚本")
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="交互模式：逐个选择项目经理并创建项目"
    )
    parser.add_argument(
        "--auto", "-a", action="store_true", help="自动模式：使用指定项目经理批量创建"
    )
    parser.add_argument("--pm-id", type=int, help="自动模式下使用的项目经理ID")

    args = parser.parse_args()

    # 获取数据库会话
    db = get_db_session()

    try:
        # 获取需要修复的立项申请
        initiations = get_pending_initiations(db)

        # 显示立项申请列表
        display_initiations(initiations)

        if not initiations:
            return

        # 根据模式执行修复
        if args.interactive:
            # 交互模式
            pms = get_available_pms(db)
            interactive_mode(db, initiations, pms)
        elif args.auto:
            # 自动模式
            if not args.pm_id:
                print("❌ 自动模式需要指定 --pm-id 参数")
                print("\n示例: python scripts/repair_initiation_projects.py --auto --pm-id 1")
                return
            auto_mode(db, initiations, args.pm_id)
        else:
            # 仅查看模式
            print("\n💡 提示:")
            print("  - 使用 --interactive 进入交互模式逐个选择项目经理")
            print("  - 使用 --auto --pm-id <ID> 使用指定项目经理批量创建")

    finally:
        db.close()


if __name__ == "__main__":
    main()
