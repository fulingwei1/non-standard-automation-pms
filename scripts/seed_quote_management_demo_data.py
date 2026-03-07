#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为报价管理页面补充可展示的非标自动化行业演示数据。

用途：
- 给“当前没有任何报价数据”的活跃用户各补 1 条报价
- 同时补齐关联的商机、报价版本、报价明细
- 数据场景聚焦非标自动化（机器人上下料、视觉检测、输送线集成等）

运行方式：
    python scripts/seed_quote_management_demo_data.py
    python scripts/seed_quote_management_demo_data.py --limit 20
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from itertools import cycle
from pathlib import Path
import sys
from typing import Iterable, List

from sqlalchemy import func

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.models.base import SessionLocal
from app.models.project.customer import Customer
from app.models.sales.leads import Opportunity
from app.models.sales.quotes import Quote, QuoteItem, QuoteVersion
from app.models.user import User


@dataclass(frozen=True)
class ItemTemplate:
    item_type: str
    item_name: str
    qty: Decimal
    unit_price: Decimal
    cost: Decimal
    lead_time_days: int
    remark: str
    unit: str = "套"
    cost_category: str = "设备成本"


@dataclass(frozen=True)
class ScenarioTemplate:
    project_type: str
    equipment_type: str
    opportunity_suffix: str
    risk_terms: str
    lead_time_days: int
    items: List[ItemTemplate]


SCENARIOS: List[ScenarioTemplate] = [
    ScenarioTemplate(
        project_type="AUTOMATION_RETROFIT",
        equipment_type="机器人上下料",
        opportunity_suffix="电芯装配线机器人上下料改造",
        risk_terms="需客户提前完成地基加固与安全围栏验收。",
        lead_time_days=52,
        items=[
            ItemTemplate("EQUIPMENT", "六轴机器人单元", Decimal("2"), Decimal("185000"), Decimal("142000"), 35, "含末端夹具"),
            ItemTemplate("ELECTRIC", "电控柜与PLC程序", Decimal("1"), Decimal("98000"), Decimal("72000"), 28, "含远程调试"),
            ItemTemplate("SERVICE", "现场安装与联调", Decimal("1"), Decimal("76000"), Decimal("51000"), 14, "驻场2周"),
        ],
    ),
    ScenarioTemplate(
        project_type="VISION_STATION",
        equipment_type="视觉检测工站",
        opportunity_suffix="动力电池壳体视觉检测工站",
        risk_terms="光照条件与节拍目标需在预验收前锁定。",
        lead_time_days=45,
        items=[
            ItemTemplate("EQUIPMENT", "视觉检测工站主体", Decimal("1"), Decimal("268000"), Decimal("205000"), 30, "含机架"),
            ItemTemplate("SOFTWARE", "视觉算法与标定服务", Decimal("1"), Decimal("122000"), Decimal("86000"), 26, "含缺陷样本训练"),
            ItemTemplate("SERVICE", "产线对接与试运行", Decimal("1"), Decimal("54000"), Decimal("36000"), 12, "含MES接口"),
        ],
    ),
    ScenarioTemplate(
        project_type="CONVEYOR_INTEGRATION",
        equipment_type="输送线集成",
        opportunity_suffix="PACK段输送线与缓存系统集成",
        risk_terms="现场电缆桥架改造由甲方负责，乙方提供指导。",
        lead_time_days=60,
        items=[
            ItemTemplate("EQUIPMENT", "输送线与缓存模组", Decimal("1"), Decimal("335000"), Decimal("258000"), 40, "含防护结构"),
            ItemTemplate("ELECTRIC", "多站点I/O与伺服包", Decimal("1"), Decimal("148000"), Decimal("111000"), 30, "含现场布线"),
            ItemTemplate("SERVICE", "交付培训与验收支持", Decimal("1"), Decimal("62000"), Decimal("43000"), 16, "双班次培训"),
        ],
    ),
    ScenarioTemplate(
        project_type="MES_INTEGRATION",
        equipment_type="MES接口改造",
        opportunity_suffix="产线MES追溯与报工接口改造",
        risk_terms="第三方MES接口文档需在项目启动后一周内提供。",
        lead_time_days=34,
        items=[
            ItemTemplate("SOFTWARE", "MES接口开发包", Decimal("1"), Decimal("116000"), Decimal("78000"), 20, "含API网关"),
            ItemTemplate("SOFTWARE", "数据追溯与看板模块", Decimal("1"), Decimal("92000"), Decimal("64000"), 18, "含权限模型"),
            ItemTemplate("SERVICE", "上线验证与运维移交", Decimal("1"), Decimal("38000"), Decimal("25000"), 8, "含运维手册"),
        ],
    ),
    ScenarioTemplate(
        project_type="ELECTRIC_REBUILD",
        equipment_type="电控柜改造",
        opportunity_suffix="老旧产线电控柜升级与安全回路改造",
        risk_terms="停线窗口需连续不少于72小时。",
        lead_time_days=41,
        items=[
            ItemTemplate("ELECTRIC", "主控柜与I/O扩展柜", Decimal("2"), Decimal("86000"), Decimal("61000"), 24, "含防呆端子"),
            ItemTemplate("ELECTRIC", "安全回路与急停系统", Decimal("1"), Decimal("74000"), Decimal("52000"), 18, "SIL2方案"),
            ItemTemplate("SERVICE", "现场切换与夜间调试", Decimal("1"), Decimal("49000"), Decimal("32000"), 10, "含夜班支持"),
        ],
    ),
]

CUSTOMER_SEEDS = [
    ("NSA-CUST-001", "华东精密智造股份有限公司", "华东精密"),
    ("NSA-CUST-002", "苏州新越自动化科技有限公司", "苏州新越"),
    ("NSA-CUST-003", "宁波锐联工业装备有限公司", "宁波锐联"),
    ("NSA-CUST-004", "合肥智擎新能源设备有限公司", "合肥智擎"),
    ("NSA-CUST-005", "东莞领航智能产线有限公司", "东莞领航"),
    ("NSA-CUST-006", "常州先达机器视觉有限公司", "常州先达"),
    ("NSA-CUST-007", "嘉兴云虎机器人系统有限公司", "嘉兴云虎"),
    ("NSA-CUST-008", "无锡迈拓柔性制造有限公司", "无锡迈拓"),
]

QUOTE_STATUS_CYCLE = [
    "DRAFT",
    "IN_REVIEW",
    "APPROVED",
    "SENT",
    "ACCEPTED",
    "CONVERTED",
    "REJECTED",
    "EXPIRED",
]

OPPORTUNITY_STAGE_CYCLE = [
    "DISCOVERY",
    "QUALIFICATION",
    "PROPOSAL",
    "NEGOTIATION",
]


def to_decimal(value: Decimal) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def ensure_demo_customers(db, owner_candidates: List[User]) -> tuple[List[Customer], int]:
    customers: List[Customer] = []
    owners = cycle(owner_candidates or [None])
    created_count = 0

    for code, name, short_name in CUSTOMER_SEEDS:
        existing = db.query(Customer).filter(Customer.customer_code == code).first()
        if existing:
            customers.append(existing)
            continue

        owner = next(owners)
        customer = Customer(
            customer_code=code,
            customer_name=name,
            short_name=short_name,
            customer_type="制造企业",
            industry="非标自动化",
            scale="中大型",
            contact_person="项目采购经理",
            contact_phone="400-800-2026",
            address="中国华东区域",
            status="ACTIVE",
            payment_terms="30%预付款+60%发货前+10%验收",
            created_by=owner.id if owner else None,
            sales_owner_id=owner.id if owner else None,
            remark="非标自动化行业演示客户数据",
        )
        db.add(customer)
        db.flush()
        customers.append(customer)
        created_count += 1

    return customers, created_count


def calculate_totals(items: Iterable[ItemTemplate]) -> tuple[Decimal, Decimal, Decimal]:
    total_price = sum((item.qty * item.unit_price for item in items), Decimal("0"))
    total_cost = sum((item.qty * item.cost for item in items), Decimal("0"))
    if total_price <= 0:
        margin = Decimal("0")
    else:
        margin = (total_price - total_cost) / total_price * Decimal("100")
    return to_decimal(total_price), to_decimal(total_cost), to_decimal(margin)


def seed_quotes_for_users(limit: int | None = None) -> None:
    db = SessionLocal()
    try:
        active_users = (
            db.query(User)
            .filter(User.is_active.is_(True))
            .order_by(User.id.asc())
            .all()
        )
        if not active_users:
            print("未找到活跃用户，已跳过。")
            return

        existing_owner_ids = {
            owner_id
            for (owner_id,) in db.query(Quote.owner_id).distinct().all()
            if owner_id is not None
        }
        target_users = [user for user in active_users if user.id not in existing_owner_ids]
        if limit is not None:
            target_users = target_users[:limit]

        if not target_users:
            print("所有活跃用户都已有报价数据，无需补充。")
            return

        customers, created_customer_count = ensure_demo_customers(db, active_users[:8])
        customer_cycle = cycle(customers)
        scenario_cycle = cycle(SCENARIOS)
        quote_status_cycle = cycle(QUOTE_STATUS_CYCLE)
        stage_cycle = cycle(OPPORTUNITY_STAGE_CYCLE)

        next_opp_seq = (db.query(func.max(Opportunity.id)).scalar() or 0) + 1
        next_quote_seq = (db.query(func.max(Quote.id)).scalar() or 0) + 1
        today_tag = date.today().strftime("%m%d")

        created_opportunities = 0
        created_quotes = 0
        created_versions = 0
        created_items = 0

        for index, user in enumerate(target_users, start=1):
            customer = next(customer_cycle)
            scenario = next(scenario_cycle)
            status = next(quote_status_cycle)
            stage = next(stage_cycle)

            opp_code = f"NSOP{today_tag}{next_opp_seq:05d}"[:20]
            quote_code = f"NSQT{today_tag}{next_quote_seq:05d}"[:20]
            next_opp_seq += 1
            next_quote_seq += 1

            total_price, total_cost, gross_margin = calculate_totals(scenario.items)
            valid_until = date.today() + timedelta(days=30 + (index % 30))
            if status == "EXPIRED":
                valid_until = date.today() - timedelta(days=3 + (index % 7))

            opportunity = Opportunity(
                opp_code=opp_code,
                customer_id=customer.id,
                opp_name=f"{customer.short_name}-{scenario.opportunity_suffix}",
                project_type=scenario.project_type,
                equipment_type=scenario.equipment_type,
                stage=stage,
                probability=55 + (index % 35),
                est_amount=total_price,
                est_margin=gross_margin,
                expected_close_date=date.today() + timedelta(days=40 + (index % 45)),
                owner_id=user.id,
                updated_by=user.id,
                gate_status="PENDING",
            )
            db.add(opportunity)
            db.flush()
            created_opportunities += 1

            quote = Quote(
                quote_code=quote_code,
                opportunity_id=opportunity.id,
                customer_id=customer.id,
                status=status,
                valid_until=valid_until,
                delivery_date=date.today() + timedelta(days=scenario.lead_time_days),
                owner_id=user.id,
            )
            db.add(quote)
            db.flush()
            created_quotes += 1

            version = QuoteVersion(
                quote_id=quote.id,
                version_no="V1",
                total_price=total_price,
                cost_total=total_cost,
                gross_margin=gross_margin,
                lead_time_days=scenario.lead_time_days,
                risk_terms=scenario.risk_terms,
                delivery_date=date.today() + timedelta(days=scenario.lead_time_days),
                created_by=user.id,
            )
            db.add(version)
            db.flush()
            created_versions += 1

            for item in scenario.items:
                db.add(
                    QuoteItem(
                        quote_version_id=version.id,
                        item_type=item.item_type,
                        item_name=item.item_name,
                        qty=item.qty,
                        unit_price=item.unit_price,
                        cost=item.cost,
                        lead_time_days=item.lead_time_days,
                        remark=item.remark,
                        unit=item.unit,
                        cost_category=item.cost_category,
                        cost_source="MANUAL",
                    )
                )
                created_items += 1

            quote.current_version_id = version.id

        db.commit()
        print("报价管理演示数据写入完成：")
        print(f"- 目标用户（原无报价）: {len(target_users)}")
        print(f"- 新增客户: {created_customer_count}")
        print(f"- 新增商机: {created_opportunities}")
        print(f"- 新增报价: {created_quotes}")
        print(f"- 新增报价版本: {created_versions}")
        print(f"- 新增报价明细: {created_items}")
        print("已可在“报价管理”页面按当前登录用户看到数据。")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def parse_args():
    parser = argparse.ArgumentParser(description="补充报价管理演示数据")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="仅处理前 N 个无报价活跃用户（默认处理全部）",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    seed_quotes_for_users(limit=args.limit)
