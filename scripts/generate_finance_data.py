#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成完整的融资数据脚本
包括：投资方、融资轮次、融资记录、股权结构、融资用途

使用方法:
    python3 scripts/generate_finance_data.py
"""

import os
import random
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.base import get_db_session
from app.models.finance import (
    EquityStructure,
    FundingRecord,
    FundingRound,
    FundingUsage,
    Investor,
)
from app.models.user import User

# 投资方数据模板
INVESTOR_TEMPLATES = [
    {
        "code": "INV001",
        "name": "深创投",
        "type": "VC",
        "legal_name": "深圳市创新投资集团有限公司",
        "region": "深圳",
        "investment_focus": "智能制造、新能源、人工智能",
        "investment_stage": "A轮-C轮",
        "typical_ticket_size": 50000000,
        "is_lead_investor": True,
    },
    {
        "code": "INV002",
        "name": "红杉资本中国基金",
        "type": "PE",
        "legal_name": "红杉资本中国基金",
        "region": "北京",
        "investment_focus": "科技、消费、医疗健康",
        "investment_stage": "B轮-D轮",
        "typical_ticket_size": 100000000,
        "is_lead_investor": True,
    },
    {
        "code": "INV003",
        "name": "IDG资本",
        "type": "VC",
        "legal_name": "IDG资本",
        "region": "北京",
        "investment_focus": "TMT、消费、医疗",
        "investment_stage": "A轮-C轮",
        "typical_ticket_size": 80000000,
        "is_lead_investor": True,
    },
    {
        "code": "INV004",
        "name": "真格基金",
        "type": "VC",
        "legal_name": "真格基金",
        "region": "北京",
        "investment_focus": "早期科技创业",
        "investment_stage": "种子轮-A轮",
        "typical_ticket_size": 10000000,
        "is_lead_investor": False,
    },
    {
        "code": "INV005",
        "name": "经纬中国",
        "type": "VC",
        "legal_name": "经纬中国",
        "region": "上海",
        "investment_focus": "企业服务、消费、医疗",
        "investment_stage": "A轮-C轮",
        "typical_ticket_size": 60000000,
        "is_lead_investor": True,
    },
    {
        "code": "INV006",
        "name": "高瓴资本",
        "type": "PE",
        "legal_name": "高瓴资本管理有限公司",
        "region": "北京",
        "investment_focus": "消费、医疗、企业服务",
        "investment_stage": "B轮-IPO",
        "typical_ticket_size": 200000000,
        "is_lead_investor": True,
    },
    {
        "code": "INV007",
        "name": "腾讯投资",
        "type": "STRATEGIC",
        "legal_name": "深圳市腾讯计算机系统有限公司",
        "region": "深圳",
        "investment_focus": "互联网、科技、游戏",
        "investment_stage": "A轮-IPO",
        "typical_ticket_size": 150000000,
        "is_lead_investor": True,
    },
    {
        "code": "INV008",
        "name": "阿里巴巴创业投资",
        "type": "STRATEGIC",
        "legal_name": "阿里巴巴（中国）网络技术有限公司",
        "region": "杭州",
        "investment_focus": "电商、云计算、物流",
        "investment_stage": "A轮-IPO",
        "typical_ticket_size": 120000000,
        "is_lead_investor": True,
    },
    {
        "code": "INV009",
        "name": "天使投资人-张总",
        "type": "ANGEL",
        "legal_name": "个人",
        "region": "深圳",
        "investment_focus": "早期科技项目",
        "investment_stage": "种子轮",
        "typical_ticket_size": 2000000,
        "is_lead_investor": False,
    },
    {
        "code": "INV010",
        "name": "天使投资人-李总",
        "type": "ANGEL",
        "legal_name": "个人",
        "region": "北京",
        "investment_focus": "智能制造",
        "investment_stage": "种子轮-A轮",
        "typical_ticket_size": 3000000,
        "is_lead_investor": False,
    },
]

# 融资轮次配置
FUNDING_ROUNDS_CONFIG = [
    {
        "code": "ROUND_SEED",
        "name": "种子轮",
        "type": "SEED",
        "order": 1,
        "target_amount": 5000000,
        "valuation_pre": 20000000,
        "valuation_post": 25000000,
        "launch_date": date(2020, 3, 1),
        "closing_date": date(2020, 6, 15),
        "status": "CLOSED",
    },
    {
        "code": "ROUND_A",
        "name": "A轮",
        "type": "A",
        "order": 2,
        "target_amount": 30000000,
        "valuation_pre": 80000000,
        "valuation_post": 110000000,
        "launch_date": date(2021, 1, 1),
        "closing_date": date(2021, 5, 20),
        "status": "CLOSED",
    },
    {
        "code": "ROUND_B",
        "name": "B轮",
        "type": "B",
        "order": 3,
        "target_amount": 80000000,
        "valuation_pre": 300000000,
        "valuation_post": 380000000,
        "launch_date": date(2022, 3, 1),
        "closing_date": date(2022, 8, 30),
        "status": "CLOSED",
    },
    {
        "code": "ROUND_C",
        "name": "C轮",
        "type": "C",
        "order": 4,
        "target_amount": 150000000,
        "valuation_pre": 800000000,
        "valuation_post": 950000000,
        "launch_date": date(2023, 6, 1),
        "closing_date": date(2023, 12, 15),
        "status": "CLOSED",
    },
    {
        "code": "ROUND_D",
        "name": "D轮",
        "type": "D",
        "order": 5,
        "target_amount": 300000000,
        "valuation_pre": 2000000000,
        "valuation_post": 2300000000,
        "launch_date": date(2024, 9, 1),
        "expected_closing_date": date(2025, 3, 31),
        "status": "IN_PROGRESS",
    },
]

# 融资用途分类
USAGE_CATEGORIES = [
    {"category": "R&D", "items": [
        {"item": "研发团队扩充", "percentage": 35},
        {"item": "核心技术研发", "percentage": 20},
        {"item": "产品迭代升级", "percentage": 10},
    ]},
    {"category": "MARKETING", "items": [
        {"item": "品牌推广", "percentage": 15},
        {"item": "市场拓展", "percentage": 8},
        {"item": "渠道建设", "percentage": 5},
    ]},
    {"category": "OPERATIONS", "items": [
        {"item": "运营团队", "percentage": 4},
        {"item": "日常运营", "percentage": 2},
    ]},
    {"category": "EQUIPMENT", "items": [
        {"item": "生产设备采购", "percentage": 3},
        {"item": "测试设备", "percentage": 1},
    ]},
]


def generate_investors(db):
    """生成投资方数据"""
    print("生成投资方数据...")
    investors = []

    for template in INVESTOR_TEMPLATES:
        # 检查是否已存在
        existing = db.query(Investor).filter(Investor.investor_code == template["code"]).first()
        if existing:
            investors.append(existing)
            continue

        investor = Investor(
            investor_code=template["code"],
            investor_name=template["name"],
            investor_type=template["type"],
            legal_name=template.get("legal_name", template["name"]),
            region=template.get("region", "深圳"),
            country="中国",
            contact_person=f"{template['name']}投资经理",
            contact_phone=f"138{random.randint(10000000, 99999999)}",
            contact_email=f"contact@{template['code'].lower()}.com",
            website=f"https://www.{template['code'].lower()}.com",
            investment_focus=template.get("investment_focus", ""),
            investment_stage=template.get("investment_stage", ""),
            typical_ticket_size=Decimal(str(template.get("typical_ticket_size", 0))),
            is_lead_investor=template.get("is_lead_investor", False),
            is_active=True,
            description=f"{template['name']}是一家专注于{template.get('investment_focus', '科技')}领域的投资机构",
        )
        db.add(investor)
        investors.append(investor)

    db.commit()
    print(f"✓ 已生成 {len(investors)} 个投资方")
    return investors


def generate_funding_rounds(db, investors, users):
    """生成融资轮次数据"""
    print("生成融资轮次数据...")
    funding_rounds = []

    # 获取财务或高管用户作为负责人
    finance_users = [u for u in users if u.real_name and ("财务" in u.real_name or "总" in u.real_name or "CEO" in u.real_name)]
    if not finance_users:
        finance_users = users[:3]

    for i, config in enumerate(FUNDING_ROUNDS_CONFIG):
        # 检查是否已存在
        existing = db.query(FundingRound).filter(FundingRound.round_code == config["code"]).first()
        if existing:
            funding_rounds.append(existing)
            continue
        # 选择领投方
        if config["type"] == "SEED":
            lead_investor = next((inv for inv in investors if inv.investor_type == "ANGEL"), investors[0])
        elif config["type"] == "A":
            lead_investor = next((inv for inv in investors if inv.investor_type == "VC" and "真格" in inv.investor_name), investors[1])
        elif config["type"] == "B":
            lead_investor = next((inv for inv in investors if inv.investor_type == "VC" and "深创投" in inv.investor_name), investors[2])
        elif config["type"] == "C":
            lead_investor = next((inv for inv in investors if inv.investor_type == "PE"), investors[5])
        else:
            lead_investor = next((inv for inv in investors if inv.investor_type == "PE" and "高瓴" in inv.investor_name), investors[5])

        responsible_person = finance_users[i % len(finance_users)]

        funding_round = FundingRound(
            round_code=config["code"],
            round_name=config["name"],
            round_type=config["type"],
            round_order=config["order"],
            target_amount=Decimal(str(config["target_amount"])),
            actual_amount=Decimal(str(float(config["target_amount"]) * 0.95)),  # 实际金额略低于目标
            currency="CNY",
            valuation_pre=Decimal(str(config.get("valuation_pre", 0))),
            valuation_post=Decimal(str(config.get("valuation_post", 0))),
            launch_date=config.get("launch_date"),
            closing_date=config.get("closing_date"),
            expected_closing_date=config.get("expected_closing_date"),
            status=config["status"],
            lead_investor_id=lead_investor.id,
            lead_investor_name=lead_investor.investor_name,
            responsible_person_id=responsible_person.id,
            responsible_person_name=responsible_person.real_name or responsible_person.username,
            description=f"{config['name']}融资，目标金额{config['target_amount']/10000}万元",
        )
        db.add(funding_round)
        funding_rounds.append(funding_round)

    db.commit()
    print(f"✓ 已生成 {len(funding_rounds)} 个融资轮次")
    return funding_rounds


def generate_funding_records(db, funding_rounds, investors):
    """生成融资记录数据"""
    print("生成融资记录数据...")
    records = []
    record_counter = 1

    for round_obj in funding_rounds:
        # 每个轮次有3-6个投资方
        num_investors = random.randint(3, 6)

        # 选择投资方（包括领投方）
        selected_investors = [round_obj.lead_investor]
        available_investors = [inv for inv in investors if inv.id != round_obj.lead_investor_id]
        selected_investors.extend(random.sample(available_investors, min(num_investors - 1, len(available_investors))))

        # 计算总金额和分配
        total_amount = float(round_obj.actual_amount)
        lead_amount = total_amount * 0.5  # 领投方占50%
        other_amount = total_amount * 0.5 / (len(selected_investors) - 1)  # 其他投资方平分剩余50%

        for idx, investor in enumerate(selected_investors):
            if idx == 0:  # 领投方
                amount = Decimal(str(lead_amount))
            else:
                amount = Decimal(str(other_amount))

            # 计算持股比例（简化计算）
            if round_obj.valuation_post > 0:
                share_percentage = Decimal(str((float(amount) / float(round_obj.valuation_post)) * 100))
            else:
                share_percentage = Decimal("0")

            # 生成记录编码
            record_code = f"FR{record_counter:06d}"
            record_counter += 1

            # 付款日期
            if round_obj.closing_date:
                payment_date = round_obj.closing_date + timedelta(days=random.randint(0, 30))
                actual_payment_date = payment_date + timedelta(days=random.randint(0, 15))
            else:
                payment_date = None
                actual_payment_date = None

            record = FundingRecord(
                record_code=record_code,
                funding_round_id=round_obj.id,
                investor_id=investor.id,
                investment_amount=amount,
                currency="CNY",
                share_percentage=share_percentage,
                share_count=Decimal(str(float(amount) / 1.0)),  # 简化计算
                price_per_share=Decimal("1.0"),
                commitment_date=round_obj.launch_date,
                payment_date=payment_date,
                actual_payment_date=actual_payment_date,
                payment_method="WIRE",
                payment_status="COMPLETED" if round_obj.status == "CLOSED" else "PENDING",
                paid_amount=amount if round_obj.status == "CLOSED" else Decimal("0"),
                remaining_amount=Decimal("0") if round_obj.status == "CLOSED" else amount,
                contract_no=f"CONTRACT-{round_obj.round_code}-{investor.investor_code}",
                contract_date=round_obj.launch_date + timedelta(days=random.randint(10, 30)) if round_obj.launch_date else None,
                status="PAID" if round_obj.status == "CLOSED" else "COMMITTED",
                description=f"{investor.investor_name}参与{round_obj.round_name}投资",
            )
            db.add(record)
            records.append(record)

    db.commit()
    print(f"✓ 已生成 {len(records)} 条融资记录")
    return records


def generate_equity_structures(db, funding_rounds, investors):
    """生成股权结构数据"""
    print("生成股权结构数据...")
    structures = []

    # 创始人股权（初始）
    founder_shares = {
        "创始人A": 40.0,
        "创始人B": 30.0,
        "创始人C": 20.0,
        "员工期权池": 10.0,
    }

    for round_obj in funding_rounds:
        # 获取该轮次的所有投资方记录
        round_records = db.query(FundingRecord).filter(
            FundingRecord.funding_round_id == round_obj.id
        ).all()

        # 计算投资方总持股比例
        investor_total_percentage = sum(float(record.share_percentage or 0) for record in round_records)

        # 创始人剩余股权（按比例稀释）
        remaining_founder_share = 100.0 - investor_total_percentage

        # 生成创始人股权结构
        for founder_name, original_share in founder_shares.items():
            # 按比例稀释
            diluted_share = (original_share / 100.0) * remaining_founder_share

            structure = EquityStructure(
                funding_round_id=round_obj.id,
                investor_id=None,
                shareholder_name=founder_name,
                shareholder_type="FOUNDER" if "创始人" in founder_name else "EMPLOYEE",
                share_percentage=Decimal(str(diluted_share)),
                share_count=Decimal(str(diluted_share * 1000000)),  # 简化计算
                share_class="COMMON",
                effective_date=round_obj.closing_date or round_obj.launch_date or date.today(),
                description=f"{founder_name}在{round_obj.round_name}后的持股比例",
            )
            db.add(structure)
            structures.append(structure)

        # 生成投资方股权结构
        for record in round_records:
            investor = db.query(Investor).filter(Investor.id == record.investor_id).first()
            if investor:
                structure = EquityStructure(
                    funding_round_id=round_obj.id,
                    investor_id=investor.id,
                    shareholder_name=investor.investor_name,
                    shareholder_type="INVESTOR",
                    share_percentage=record.share_percentage,
                    share_count=record.share_count,
                    share_class="PREFERRED",
                    effective_date=round_obj.closing_date or round_obj.launch_date or date.today(),
                    description=f"{investor.investor_name}在{round_obj.round_name}后的持股比例",
                )
                db.add(structure)
                structures.append(structure)

    db.commit()
    print(f"✓ 已生成 {len(structures)} 条股权结构记录")
    return structures


def generate_funding_usages(db, funding_rounds, users):
    """生成融资用途数据"""
    print("生成融资用途数据...")
    usages = []

    # 获取各部门负责人
    dept_users = users[:10]  # 使用前10个用户作为各部门负责人

    for round_obj in funding_rounds:
        total_planned = 0
        usage_items = []

        # 根据轮次类型调整用途分配
        if round_obj.round_type == "SEED":
            # 种子轮主要用于研发
            categories = [USAGE_CATEGORIES[0]]  # R&D
        elif round_obj.round_type == "A":
            # A轮：研发+市场
            categories = [USAGE_CATEGORIES[0], USAGE_CATEGORIES[1]]  # R&D + MARKETING
        else:
            # B轮及以上：全部分类
            categories = USAGE_CATEGORIES

        for category_config in categories:
            for item_config in category_config["items"]:
                # 计算计划金额
                percentage = item_config["percentage"] / 100.0
                planned_amount = float(round_obj.actual_amount) * percentage
                total_planned += planned_amount

                # 实际金额（已完成轮次有实际数据）
                if round_obj.status == "CLOSED":
                    actual_amount = planned_amount * random.uniform(0.8, 1.1)
                    status = random.choice(["COMPLETED", "IN_PROGRESS"])
                else:
                    actual_amount = planned_amount * random.uniform(0.1, 0.5)
                    status = "IN_PROGRESS"

                # 时间安排
                if round_obj.closing_date:
                    planned_start_date = round_obj.closing_date + timedelta(days=random.randint(0, 30))
                    planned_end_date = planned_start_date + timedelta(days=random.randint(90, 365))

                    if status == "COMPLETED":
                        actual_start_date = planned_start_date + timedelta(days=random.randint(0, 15))
                        actual_end_date = actual_start_date + timedelta(days=random.randint(60, 300))
                    else:
                        actual_start_date = planned_start_date + timedelta(days=random.randint(0, 15))
                        actual_end_date = None
                else:
                    planned_start_date = None
                    planned_end_date = None
                    actual_start_date = None
                    actual_end_date = None

                responsible_person = dept_users[len(usages) % len(dept_users)]

                usage = FundingUsage(
                    funding_round_id=round_obj.id,
                    usage_category=category_config["category"],
                    usage_item=item_config["item"],
                    planned_amount=Decimal(str(planned_amount)),
                    actual_amount=Decimal(str(actual_amount)),
                    percentage=Decimal(str(item_config["percentage"])),
                    planned_start_date=planned_start_date,
                    planned_end_date=planned_end_date,
                    actual_start_date=actual_start_date,
                    actual_end_date=actual_end_date,
                    status=status,
                    responsible_person_id=responsible_person.id,
                    responsible_person_name=responsible_person.real_name or responsible_person.username,
                    description=f"{round_obj.round_name}资金用于{item_config['item']}",
                )
                db.add(usage)
                usages.append(usage)

    db.commit()
    print(f"✓ 已生成 {len(usages)} 条融资用途记录")
    return usages


def main():
    """主函数"""
    print("=" * 60)
    print("开始生成融资数据")
    print("=" * 60)

    with get_db_session() as db:
        # 获取现有用户
        users = db.query(User).limit(20).all()
        if not users:
            print("❌ 错误：数据库中暂无用户数据，请先运行用户初始化脚本")
            return

        print(f"✓ 找到 {len(users)} 个用户")

        # 1. 生成投资方
        investors = generate_investors(db)

        # 2. 生成融资轮次
        funding_rounds = generate_funding_rounds(db, investors, users)

        # 3. 生成融资记录
        funding_records = generate_funding_records(db, funding_rounds, investors)

        # 4. 生成股权结构
        equity_structures = generate_equity_structures(db, funding_rounds, investors)

        # 5. 生成融资用途
        funding_usages = generate_funding_usages(db, funding_rounds, users)

        print("=" * 60)
        print("融资数据生成完成！")
        print("=" * 60)
        print(f"投资方: {len(investors)} 个")
        print(f"融资轮次: {len(funding_rounds)} 个")
        print(f"融资记录: {len(funding_records)} 条")
        print(f"股权结构: {len(equity_structures)} 条")
        print(f"融资用途: {len(funding_usages)} 条")
        print("=" * 60)


if __name__ == "__main__":
    main()
