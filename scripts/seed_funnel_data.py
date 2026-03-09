#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
销售漏斗演示数据种子脚本
生成符合非标自动化行业特点的商机数据，用于漏斗分析

行业特点：
- 非标自动化：FCT、EOL、ICT、烧录等测试设备
- 客户行业：新能源汽车、动力电池、消费电子
- 项目金额：200-500万为主
- 销售周期：3-6个月
"""

import random
from datetime import date, datetime, timedelta

import sys
from pathlib import Path

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.sales.leads import Lead, Opportunity
from app.models.enums import LeadStatusEnum, OpportunityStageEnum

# ========== 配置 ==========

# 非标自动化行业典型客户
CUSTOMERS = [
    {"id": 1, "name": "宁德时代", "industry": "锂电池"},
    {"id": 2, "name": "比亚迪", "industry": "新能源汽车"},
    {"id": 3, "name": "中创新航", "industry": "锂电池"},
    {"id": 4, "name": "亿纬锂能", "industry": "锂电池"},
    {"id": 5, "name": "欣旺达", "industry": "消费电池"},
    {"id": 6, "name": "蜂巢能源", "industry": "锂电池"},
    {"id": 7, "name": "国轩高科", "industry": "锂电池"},
    {"id": 8, "name": "理想汽车", "industry": "新能源汽车"},
    {"id": 9, "name": "蔚来汽车", "industry": "新能源汽车"},
    {"id": 10, "name": "小鹏汽车", "industry": "新能源汽车"},
]

# 设备类型及典型金额范围（万元）
EQUIPMENT_TYPES = [
    {"type": "FCT", "name": "FCT功能测试设备", "min_amount": 150, "max_amount": 450},
    {"type": "EOL", "name": "EOL终检设备", "min_amount": 200, "max_amount": 500},
    {"type": "ICT", "name": "ICT在线测试设备", "min_amount": 180, "max_amount": 380},
    {"type": "HIPOT", "name": "耐压绝缘测试设备", "min_amount": 80, "max_amount": 200},
    {"type": "BURN", "name": "烧录设备", "min_amount": 100, "max_amount": 250},
    {"type": "ATE", "name": "自动化测试系统", "min_amount": 300, "max_amount": 600},
]

# 销售人员
SALES_OWNERS = [
    {"id": 1, "name": "张三"},
    {"id": 2, "name": "李四"},
    {"id": 3, "name": "王五"},
    {"id": 4, "name": "赵六"},
    {"id": 5, "name": "钱七"},
]

# 阶段转化概率（非标自动化行业特点：技术门槛高，转化率相对较低）
STAGE_CONVERSION_RATES = {
    OpportunityStageEnum.DISCOVERY: 0.55,      # 初步接触 → 需求挖掘 55%
    OpportunityStageEnum.QUALIFICATION: 0.60,  # 需求挖掘 → 方案介绍 60%
    OpportunityStageEnum.PROPOSAL: 0.50,       # 方案介绍 → 价格谈判 50%
    OpportunityStageEnum.NEGOTIATION: 0.65,    # 价格谈判 → 成交促成 65%
    OpportunityStageEnum.CLOSING: 0.80,        # 成交促成 → 赢单 80%
}

# 各阶段停留天数（非标自动化行业特点：决策周期长）
STAGE_DAYS = {
    OpportunityStageEnum.DISCOVERY: (5, 15),      # 5-15天
    OpportunityStageEnum.QUALIFICATION: (10, 25), # 10-25天
    OpportunityStageEnum.PROPOSAL: (15, 35),      # 15-35天
    OpportunityStageEnum.NEGOTIATION: (10, 30),   # 10-30天
    OpportunityStageEnum.CLOSING: (5, 15),        # 5-15天
}

# 阶段对应的成交概率
STAGE_PROBABILITY = {
    OpportunityStageEnum.DISCOVERY: 15,
    OpportunityStageEnum.QUALIFICATION: 35,
    OpportunityStageEnum.PROPOSAL: 55,
    OpportunityStageEnum.NEGOTIATION: 75,
    OpportunityStageEnum.CLOSING: 90,
    OpportunityStageEnum.WON: 100,
    OpportunityStageEnum.LOST: 0,
}


def generate_opp_code(index: int) -> str:
    """生成商机编码"""
    return f"OPP-2026-{index:04d}"


def generate_lead_code(index: int) -> str:
    """生成线索编码"""
    return f"LEAD-2026-{index:04d}"


def random_date_in_range(start_date: date, end_date: date) -> date:
    """在日期范围内随机生成一个日期"""
    delta = (end_date - start_date).days
    random_days = random.randint(0, delta)
    return start_date + timedelta(days=random_days)


def simulate_opportunity_progression(start_date: date) -> tuple:
    """
    模拟商机在漏斗中的进展
    返回: (当前阶段, 阶段进入日期, 预计成交日期)
    """
    current_date = start_date
    current_stage = OpportunityStageEnum.DISCOVERY

    # 按顺序模拟阶段转化
    stage_order = [
        OpportunityStageEnum.DISCOVERY,
        OpportunityStageEnum.QUALIFICATION,
        OpportunityStageEnum.PROPOSAL,
        OpportunityStageEnum.NEGOTIATION,
        OpportunityStageEnum.CLOSING,
    ]

    for i, stage in enumerate(stage_order):
        # 在当前阶段停留的天数
        min_days, max_days = STAGE_DAYS.get(stage, (5, 15))
        days_in_stage = random.randint(min_days, max_days)
        stage_exit_date = current_date + timedelta(days=days_in_stage)

        # 检查是否已经超过今天
        today = date.today()
        if stage_exit_date > today:
            # 商机还在这个阶段
            days_to_close = random.randint(30, 90)
            expected_close = today + timedelta(days=days_to_close)
            return (stage, current_date, expected_close)

        # 判断是否转化到下一阶段
        conversion_rate = STAGE_CONVERSION_RATES.get(stage, 0.5)
        if random.random() > conversion_rate:
            # 转化失败 - 输单
            return (OpportunityStageEnum.LOST, current_date, stage_exit_date)

        # 转化成功，进入下一阶段
        current_date = stage_exit_date
        if i < len(stage_order) - 1:
            current_stage = stage_order[i + 1]

    # 最后阶段的转化（成交促成 → 赢单/输单）
    if random.random() <= STAGE_CONVERSION_RATES[OpportunityStageEnum.CLOSING]:
        return (OpportunityStageEnum.WON, current_date, current_date)
    else:
        return (OpportunityStageEnum.LOST, current_date, current_date)


def create_sample_opportunities(session, count: int = 50):
    """创建示例商机数据"""
    print(f"🔄 生成 {count} 条商机数据...")

    opportunities = []
    # 统计各阶段数量
    stage_counts = {stage: 0 for stage in OpportunityStageEnum}

    for i in range(1, count + 1):
        # 随机选择客户和设备类型
        customer = random.choice(CUSTOMERS)
        equipment = random.choice(EQUIPMENT_TYPES)
        owner = random.choice(SALES_OWNERS)

        # 生成商机开始日期（过去3-6个月）
        start_date = random_date_in_range(
            date.today() - timedelta(days=180),
            date.today() - timedelta(days=30)
        )

        # 模拟商机进展
        current_stage, stage_date, expected_close = simulate_opportunity_progression(start_date)
        stage_counts[current_stage] += 1

        # 生成金额
        amount = random.randint(equipment["min_amount"], equipment["max_amount"]) * 10000

        # 创建商机记录
        opp = Opportunity(
            opp_code=generate_opp_code(i),
            customer_id=customer["id"],
            opp_name=f"{customer['name']}-{equipment['name']}项目",
            project_type="设备销售",
            equipment_type=equipment["type"],
            stage=current_stage,
            probability=STAGE_PROBABILITY.get(current_stage, 50),
            est_amount=amount,
            est_margin=random.uniform(0.18, 0.35),  # 18-35% 毛利率
            expected_close_date=expected_close,
            owner_id=owner["id"],
            created_at=datetime.combine(start_date, datetime.min.time()),
            updated_at=datetime.combine(stage_date, datetime.min.time()),
        )
        opportunities.append(opp)

    # 批量插入
    session.bulk_save_objects(opportunities)
    session.commit()

    # 打印统计
    print("\n📊 商机阶段分布:")
    stage_names = {
        OpportunityStageEnum.DISCOVERY: "初步接触",
        OpportunityStageEnum.QUALIFICATION: "需求挖掘",
        OpportunityStageEnum.PROPOSAL: "方案介绍",
        OpportunityStageEnum.NEGOTIATION: "价格谈判",
        OpportunityStageEnum.WON: "赢单",
        OpportunityStageEnum.LOST: "输单",
    }
    for stage, cnt in stage_counts.items():
        print(f"  • {stage_names.get(stage, stage.value)}: {cnt} 个")

    return opportunities


def create_sample_leads(session, count: int = 80):
    """创建示例线索数据"""
    print(f"🔄 生成 {count} 条线索数据...")

    leads = []
    # 统计各状态数量
    status_counts = {status: 0 for status in LeadStatusEnum}

    # 线索来源
    sources = ["展会", "官网", "老客户介绍", "主动拜访", "行业论坛", "招标信息"]

    for i in range(1, count + 1):
        # 随机选择客户
        customer = random.choice(CUSTOMERS)
        owner = random.choice(SALES_OWNERS)
        source = random.choice(sources)

        # 随机状态
        status_weights = [0.15, 0.25, 0.30, 0.20, 0.10]  # NEW, CONTACTED, QUALIFIED, CONVERTED, LOST
        status = random.choices(
            list(LeadStatusEnum),
            weights=status_weights
        )[0]
        status_counts[status] += 1

        # 生成创建日期
        created_date = random_date_in_range(
            date.today() - timedelta(days=120),
            date.today() - timedelta(days=5)
        )

        lead = Lead(
            lead_code=generate_lead_code(i),
            source=source,
            customer_name=customer["name"],
            industry=customer["industry"],
            contact_name=f"{customer['name']}采购部",
            contact_phone=f"1{random.randint(30, 99)}{random.randint(1000, 9999):04d}{random.randint(1000, 9999):04d}",
            demand_summary=f"{customer['name']}需要采购测试设备",
            owner_id=owner["id"],
            status=status,
            created_at=datetime.combine(created_date, datetime.min.time()),
        )
        leads.append(lead)

    # 批量插入
    session.bulk_save_objects(leads)
    session.commit()

    # 打印统计
    print("\n📊 线索状态分布:")
    status_names = {
        LeadStatusEnum.NEW: "新建",
        LeadStatusEnum.CONTACTED: "已联系",
        LeadStatusEnum.QUALIFIED: "已验证",
        LeadStatusEnum.CONVERTED: "已转化",
        LeadStatusEnum.LOST: "已丢失",
    }
    for status, cnt in status_counts.items():
        print(f"  • {status_names.get(status, status.value)}: {cnt} 个")

    return leads


def main():
    """主函数"""
    print("=" * 50)
    print("🚀 销售漏斗演示数据生成器")
    print("=" * 50)
    print()

    # 创建数据库连接
    print("📦 连接数据库...")
    engine = create_engine(str(settings.DATABASE_URL))
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 检查是否已有数据
        existing_opps = session.query(Opportunity).count()
        existing_leads = session.query(Lead).count()

        if existing_opps > 0 or existing_leads > 0:
            print(f"⚠️  数据库已有 {existing_leads} 条线索和 {existing_opps} 条商机")
            response = input("是否清空现有数据重新生成？(y/N): ")
            if response.lower() == 'y':
                print("🗑️  清空现有数据...")
                session.query(Opportunity).delete()
                session.query(Lead).delete()
                session.commit()
            else:
                print("✅ 保留现有数据，在此基础上追加")

        # 生成数据
        leads = create_sample_leads(session, count=80)
        opportunities = create_sample_opportunities(session, count=50)

        print()
        print("=" * 50)
        print("✅ 数据生成完成!")
        print(f"  • 线索: {len(leads)} 条")
        print(f"  • 商机: {len(opportunities)} 条")
        print("=" * 50)

        # 计算漏斗指标
        total_amount = sum(
            float(opp.est_amount or 0)
            for opp in opportunities
            if opp.stage not in [OpportunityStageEnum.LOST]
        )
        won_amount = sum(
            float(opp.est_amount or 0)
            for opp in opportunities
            if opp.stage == OpportunityStageEnum.WON
        )

        print()
        print("💰 Pipeline 统计:")
        print(f"  • Pipeline 总额: ¥{total_amount / 10000:.1f}万")
        print(f"  • 已赢单金额: ¥{won_amount / 10000:.1f}万")

    except Exception as e:
        session.rollback()
        print(f"❌ 错误: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
