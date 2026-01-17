#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成立项管理演示数据
"""

import os
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from random import choice, randint

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.base import get_db_session
from app.models.pmo import PmoProjectInitiation
from app.models.user import User

# 项目类型
PROJECT_TYPES = ['NEW', 'UPGRADE', 'MAINTAIN']
PROJECT_LEVELS = ['A', 'B', 'C']
STATUSES = ['DRAFT', 'SUBMITTED', 'REVIEWING', 'APPROVED', 'REJECTED']
TECHNICAL_DIFFICULTIES = ['LOW', 'MEDIUM', 'HIGH']

# 客户名称列表
CUSTOMER_NAMES = [
    '华为技术有限公司',
    '比亚迪股份有限公司',
    '宁德时代新能源科技股份有限公司',
    '小米科技有限责任公司',
    'OPPO广东移动通信有限公司',
    'vivo移动通信有限公司',
    '联想（北京）有限公司',
    '京东方科技集团股份有限公司',
    '中芯国际集成电路制造有限公司',
    '紫光展锐（上海）科技有限公司',
]

# 项目名称模板
PROJECT_NAME_TEMPLATES = [
    '{customer}自动化测试设备',
    '{customer}ICT测试系统',
    '{customer}FCT测试平台',
    '{customer}EOL测试线体',
    '{customer}视觉检测设备',
    '{customer}自动化组装线',
    '{customer}烧录设备',
    '{customer}老化测试系统',
]


def generate_initiation_no(db, today_str):
    """生成立项申请编号：INIT-yymmdd-xxx"""
    max_init = (
        db.query(PmoProjectInitiation)
        .filter(PmoProjectInitiation.application_no.like(f"INIT-{today_str}-%"))
        .order_by(PmoProjectInitiation.application_no.desc())
        .first()
    )
    if max_init:
        seq = int(max_init.application_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"INIT-{today_str}-{seq:03d}"


def generate_initiations(db, count=10):
    """生成立项申请数据"""
    # 获取用户列表
    users = db.query(User).filter(User.is_active == True).limit(20).all()
    if not users:
        print("❌ 错误：数据库中没有活跃用户，请先初始化用户数据")
        return []

    print(f"✓ 找到 {len(users)} 个用户")

    today = datetime.now()
    today_str = today.strftime("%y%m%d")

    # 先查询今天已有的记录，确定起始序号
    existing_today = (
        db.query(PmoProjectInitiation)
        .filter(PmoProjectInitiation.application_no.like(f"INIT-{today_str}-%"))
        .order_by(PmoProjectInitiation.application_no.desc())
        .first()
    )
    if existing_today:
        start_seq = int(existing_today.application_no.split("-")[-1]) + 1
    else:
        start_seq = 1

    initiations = []

    for i in range(count):
        # 随机选择申请人和状态
        applicant = choice(users)
        status = choice(STATUSES)

        # 根据状态设置时间
        if status == 'DRAFT':
            apply_time = today - timedelta(days=randint(1, 30))
        elif status == 'SUBMITTED':
            apply_time = today - timedelta(days=randint(1, 20))
        elif status == 'REVIEWING':
            apply_time = today - timedelta(days=randint(5, 15))
        elif status in ['APPROVED', 'REJECTED']:
            apply_time = today - timedelta(days=randint(10, 30))
        else:
            apply_time = today - timedelta(days=randint(1, 30))

        # 随机选择客户和项目名称
        customer_name = choice(CUSTOMER_NAMES)
        project_name_template = choice(PROJECT_NAME_TEMPLATES)
        project_name = project_name_template.format(customer=customer_name)

        # 生成合同金额（10万到500万之间）
        contract_amount = Decimal(randint(100000, 5000000))

        # 生成日期
        required_start_date = date.today() + timedelta(days=randint(30, 90))
        required_end_date = required_start_date + timedelta(days=randint(90, 180))

        # 生成立项申请编号
        seq = start_seq + i
        application_no = f"INIT-{today_str}-{seq:03d}"

        initiation = PmoProjectInitiation(
            application_no=application_no,
            project_name=project_name,
            project_type=choice(PROJECT_TYPES),
            project_level=choice(PROJECT_LEVELS),
            customer_name=customer_name,
            contract_no=f"CT{randint(20240001, 20249999)}" if randint(0, 1) else None,
            contract_amount=contract_amount if randint(0, 1) else None,
            required_start_date=required_start_date,
            required_end_date=required_end_date,
            requirement_summary=f"{project_name}的需求概述，包括测试要求、产能要求、质量标准等。",
            technical_difficulty=choice(TECHNICAL_DIFFICULTIES),
            estimated_hours=randint(500, 5000),
            resource_requirements=f"需要{randint(2, 5)}名机械工程师、{randint(1, 3)}名电气工程师、{randint(1, 2)}名软件工程师。",
            risk_assessment=f"技术风险：{choice(['低', '中', '高'])}；进度风险：{choice(['低', '中', '高'])}；质量风险：{choice(['低', '中', '高'])}。",
            applicant_id=applicant.id,
            applicant_name=applicant.real_name or applicant.username,
            apply_time=apply_time,
            status=status,
        )

        # 如果是已审批状态，设置审批信息
        if status == 'APPROVED':
            approver = choice(users)
            initiation.approved_by = approver.id
            initiation.approved_at = apply_time + timedelta(days=randint(1, 7))
            initiation.review_result = "项目符合公司战略方向，技术方案可行，批准立项。"
            initiation.approved_level = choice(PROJECT_LEVELS)
        elif status == 'REJECTED':
            approver = choice(users)
            initiation.approved_by = approver.id
            initiation.approved_at = apply_time + timedelta(days=randint(1, 7))
            initiation.review_result = "项目风险较高，资源需求超出当前能力，暂不批准。"

        db.add(initiation)
        initiations.append(initiation)

        print(f"  ✓ 创建立项申请: {application_no} - {project_name} (状态: {status})")

    return initiations


def main():
    """主函数"""
    print("=" * 60)
    print("生成立项管理演示数据")
    print("=" * 60)

    with get_db_session() as db:
        try:
            # 检查是否已有数据
            existing_count = db.query(PmoProjectInitiation).count()
            if existing_count > 0:
                print(f"\n⚠️  数据库中已有 {existing_count} 条立项申请数据")
                response = input("是否继续生成新数据？(y/n): ")
                if response.lower() != 'y':
                    print("已取消")
                    return

            # 生成数据
            print("\n开始生成立项申请数据...")
            initiations = generate_initiations(db, count=15)

            db.commit()

            print("\n" + "=" * 60)
            print("数据生成完成！")
            print("=" * 60)
            print(f"\n生成的数据概览：")
            print(f"  - 立项申请: {len(initiations)} 个")

            # 按状态统计
            status_stats = {}
            for init in initiations:
                status = init.status
                if status not in status_stats:
                    status_stats[status] = 0
                status_stats[status] += 1

            print(f"\n各状态数量：")
            for status, count in status_stats.items():
                status_name = {
                    'DRAFT': '草稿',
                    'SUBMITTED': '已提交',
                    'REVIEWING': '评审中',
                    'APPROVED': '已通过',
                    'REJECTED': '已驳回',
                }.get(status, status)
                print(f"  - {status_name}: {count} 个")

            print(f"\n数据已保存到数据库！")

        except Exception as e:
            db.rollback()
            print(f"\n❌ 错误：{e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
