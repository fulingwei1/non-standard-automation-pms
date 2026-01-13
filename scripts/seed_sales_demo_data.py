#!/usr/bin/env python3
"""
Seed demo data for the sales module so sales engineers can see quotes & contracts.

Creates/updates:
  * Customers for重点客户
  * Opportunities owned by zhang_sales
  * Quotes + versions + items
  * Contracts + deliverables linked to the quotes
"""

from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, Tuple

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.models.base import get_db_session
from app.models.project import Customer
from app.models.sales import (
    Opportunity,
    Quote,
    QuoteVersion,
    QuoteItem,
    Contract,
    ContractDeliverable,
)
from app.models.user import User


def d(value: str | float | int) -> Decimal:
    """Quick helper to keep Decimal precision."""
    return Decimal(str(value))


TODAY = date.today()
NOW = datetime.now()


CUSTOMERS = [
    {
        "customer_code": "CUS-ROBOTEC",
        "customer_name": "罗博智能科技",
        "short_name": "罗博智造",
        "customer_type": "MANUFACTURING",
        "industry": "汽车电子",
        "scale": "大型",
        "address": "苏州市工业园区科创大道88号",
        "contact_person": "李慧",
        "contact_phone": "13812340987",
        "contact_email": "lihui@robotec.cn",
        "legal_person": "陈卫东",
        "tax_no": "91320594MA1234567Q",
        "bank_name": "中国银行苏州分行",
        "bank_account": "445566778899",
        "credit_level": "A",
        "credit_limit": d("8000000"),
        "payment_terms": "NET45",
    },
    {
        "customer_code": "CUS-MEDILAB",
        "customer_name": "华信医药实验室",
        "short_name": "华信医药",
        "customer_type": "PHARMA",
        "industry": "生物医药",
        "scale": "中型",
        "address": "上海市浦东新区张江科创园88号",
        "contact_person": "周晨",
        "contact_phone": "13901881234",
        "contact_email": "zhouchen@huaxinlab.com",
        "legal_person": "林慕白",
        "tax_no": "91310115MA1K99876J",
        "bank_name": "招商银行上海科创支行",
        "bank_account": "621488778899",
        "credit_level": "A-",
        "credit_limit": d("5000000"),
        "payment_terms": "NET60",
    },
    {
        "customer_code": "CUS-SMARTLINK",
        "customer_name": "东华智能装备",
        "short_name": "东华智能",
        "customer_type": "DISCRETE",
        "industry": "消费电子",
        "scale": "大型",
        "address": "深圳市宝安区智能制造城A8",
        "contact_person": "陈研",
        "contact_phone": "13751118866",
        "contact_email": "chenyan@smartlink.com",
        "remark": "3C制造头部客户",
    },
    {
        "customer_code": "CUS-PV-BLUE",
        "customer_name": "蓝晶光伏系统",
        "short_name": "蓝晶光伏",
        "customer_type": "ENERGY",
        "industry": "新能源",
        "scale": "大型",
        "address": "杭州市余杭区未来科技城88号",
        "contact_person": "刘航",
        "contact_phone": "13671880099",
        "contact_email": "liuhang@bluepv.com",
        "remark": "TOP10光伏客户，聚焦海外项目",
    },
]


SALES_BUNDLES = [
    {
        "customer_code": "CUS-ROBOTEC",
        "opportunity": {
            "opp_code": "OPP-RBT-2409",
            "opp_name": "新能源汽车电芯装配与测试线",
            "project_type": "整线交付",
            "equipment_type": "Pack测试线",
            "stage": "NEGOTIATION",
            "est_amount": d("3850000"),
            "est_margin": d("23.5"),
            "budget_range": "300-400万",
            "decision_chain": "制造副总 + 采购总监 + PMO",
            "delivery_window": "2024Q4",
            "acceptance_basis": "整线CT≤18s，CPK≥1.33，安全互锁100%通过",
            "score": 82,
            "risk_level": "MEDIUM",
            "gate_status": "PASS",
        },
        "quote": {
            "quote_code": "Q-RBT-001",
            "status": "APPROVED",
            "valid_until_days": 45,
        },
        "version": {
            "version_no": "V1.0",
            "total_price": d("3850000"),
            "cost_total": d("2950000"),
            "gross_margin": d("23.4"),
            "lead_time_days": 90,
            "delivery_offset_days": 100,
            "risk_terms": "含核心供应商交付约束、整线联调窗口、现场改造界面说明。",
            "cost_breakdown_complete": True,
            "margin_warning": False,
            "approved": True,
        },
        "items": [
            {
                "item_type": "MODULE",
                "item_name": "Pack装配 & 功能验证段",
                "qty": d("1"),
                "unit_price": d("1850000"),
                "cost": d("1420000"),
                "lead_time_days": 82,
                "remark": "含高压测试、安全互锁",
                "cost_category": "EQUIPMENT",
                "cost_source": "TEMPLATE",
                "specification": "4工位并行 + 自动下料",
                "unit": "套",
            },
            {
                "item_type": "MODULE",
                "item_name": "Pack耐压 / 绝缘测试段",
                "qty": d("1"),
                "unit_price": d("980000"),
                "cost": d("720000"),
                "lead_time_days": 75,
                "remark": "含轨道与快换治具",
                "cost_category": "EQUIPMENT",
                "cost_source": "HISTORY",
                "specification": "耐压 5kV，绝缘 2000MΩ",
                "unit": "套",
            },
            {
                "item_type": "LABOR",
                "item_name": "调试与交付保障",
                "qty": d("280"),
                "unit_price": d("650"),
                "cost": d("420"),
                "lead_time_days": 45,
                "remark": "调试 + 驻场验收",
                "cost_category": "LABOR",
                "cost_source": "MANUAL",
                "specification": "两班制，含现场培训",
                "unit": "小时",
            },
        ],
        "contract": {
            "contract_code": "HT-RBT-001",
            "status": "SIGNED",
            "contract_amount": d("3850000"),
            "signed_offset_days": -7,
            "payment_terms_summary": "30%预付款 + 60% FAT后 + 10% SAT验收后",
            "acceptance_summary": "FAT/SAT一次通过，性能指标满足3σ要求。",
            "project_id": 9,
            "deliverables": [
                {
                    "deliverable_name": "整线设计与SOW定版",
                    "deliverable_type": "DOCUMENT",
                    "required_for_payment": True,
                    "template_ref": "SOW-RBT",
                },
                {
                    "deliverable_name": "整线联调与FAT报告",
                    "deliverable_type": "REPORT",
                    "required_for_payment": True,
                    "template_ref": "FAT-ROBOTEC",
                },
            ],
        },
    },
    {
        "customer_code": "CUS-MEDILAB",
        "opportunity": {
            "opp_code": "OPP-LAB-2410",
            "opp_name": "细胞制备自动灌装单元",
            "project_type": "高洁净装备",
            "equipment_type": "无菌灌装岛",
            "stage": "PROPOSAL",
            "est_amount": d("2480000"),
            "est_margin": d("19.8"),
            "budget_range": "200-300万",
            "decision_chain": "运营副总 + 质量主管 + 财务BP",
            "delivery_window": "2025Q1",
            "acceptance_basis": "灌装精度 ≤±1%，GMP/FDA 验证通过。",
            "score": 76,
            "risk_level": "LOW",
            "gate_status": "PENDING",
        },
        "quote": {
            "quote_code": "Q-LAB-014",
            "status": "IN_REVIEW",
            "valid_until_days": 30,
        },
        "version": {
            "version_no": "V0.9",
            "total_price": d("2480000"),
            "cost_total": d("1985000"),
            "gross_margin": d("20.0"),
            "lead_time_days": 70,
            "delivery_offset_days": 85,
            "risk_terms": "洁净度验证与第三方认证费用由客户承担，关键部件延误触发ECO流程。",
            "cost_breakdown_complete": True,
            "margin_warning": False,
            "approved": False,
        },
        "items": [
            {
                "item_type": "MODULE",
                "item_name": "无菌灌装主岛",
                "qty": d("1"),
                "unit_price": d("1380000"),
                "cost": d("1090000"),
                "lead_time_days": 60,
                "remark": "含CIP/SIP模块",
                "cost_category": "EQUIPMENT",
                "cost_source": "TEMPLATE",
                "specification": "10ml灌装×4工位",
                "unit": "套",
            },
            {
                "item_type": "MODULE",
                "item_name": "隔离器与传递舱",
                "qty": d("1"),
                "unit_price": d("620000"),
                "cost": d("470000"),
                "lead_time_days": 68,
                "remark": "RABS + 气闸联锁",
                "cost_category": "EQUIPMENT",
                "cost_source": "HISTORY",
                "specification": "ISO5/7区联动",
                "unit": "套",
            },
            {
                "item_type": "LABOR",
                "item_name": "验证与调试服务",
                "qty": d("220"),
                "unit_price": d("550"),
                "cost": d("360"),
                "lead_time_days": 40,
                "remark": "含IQ/OQ/PQ文档",
                "cost_category": "LABOR",
                "cost_source": "MANUAL",
                "specification": "项目团队+质量顾问",
                "unit": "小时",
            },
        ],
        "contract": {
            "contract_code": "HT-LAB-014",
            "status": "IN_REVIEW",
            "contract_amount": d("2480000"),
            "signed_offset_days": None,
            "payment_terms_summary": "20%预付款 + 70% 发货前 + 10% PQ验收后",
            "acceptance_summary": "通过GMP/FDA双体系审核后触发最终回款。",
            "project_id": None,
            "deliverables": [
                {
                    "deliverable_name": "验证方案与报告",
                    "deliverable_type": "REPORT",
                    "required_for_payment": True,
                    "template_ref": "PQ-TEMPLATE",
                },
                {
                    "deliverable_name": "灌装配方与Batch Record",
                    "deliverable_type": "DOCUMENT",
                    "required_for_payment": False,
                    "template_ref": "BR-SAMPLE",
                },
            ],
        },
    },
    {
        "customer_code": "CUS-ROBOTEC",
        "opportunity": {  # 共享同一个核心商机，演示多版本/多合同
            "opp_code": "OPP-RBT-2409",
            "opp_name": "新能源汽车电芯装配与测试线",
            "project_type": "整线交付",
            "equipment_type": "Pack测试线",
            "stage": "NEGOTIATION",
            "est_amount": d("4100000"),
            "est_margin": d("24.0"),
            "budget_range": "300-450万",
            "decision_chain": "制造副总 + 采购总监 + PMO",
            "delivery_window": "2025Q1",
            "acceptance_basis": "整线CT≤18s，CPK≥1.33，安全互锁100%通过",
            "score": 84,
            "risk_level": "MEDIUM",
            "gate_status": "PASS",
        },
        "quote": {
            "quote_code": "Q-DEMO-003",
            "status": "IN_REVIEW",
            "valid_until_days": 45,
        },
        "version": {
            "version_no": "V1",
            "total_price": d("2990000"),
            "cost_total": d("2150000"),
            "gross_margin": d("28.0"),
            "lead_time_days": 85,
            "delivery_offset_days": 60,
            "risk_terms": "演示数据 - 快速打样，交付窗口需锁定治具排产。",
            "cost_breakdown_complete": True,
            "margin_warning": False,
            "approved": False,
        },
        "items": [
            {
                "item_type": "MODULE",
                "item_name": "演示单元A",
                "qty": d("1"),
                "unit_price": d("1200000"),
                "cost": d("800000"),
                "lead_time_days": 60,
                "remark": "含快换治具与视觉检测",
                "cost_category": "EQUIPMENT",
                "cost_source": "CUSTOM",
                "specification": "双工位激光 + 视觉检测",
                "unit": "套",
            },
            {
                "item_type": "MODULE",
                "item_name": "Pack全线MES集成",
                "qty": d("1"),
                "unit_price": d("650000"),
                "cost": d("420000"),
                "lead_time_days": 55,
                "remark": "含WMS接口/能源看板",
                "cost_category": "SOFTWARE",
                "cost_source": "HISTORY",
                "specification": "MES+WMS+能源监控接口",
                "unit": "套",
            },
            {
                "item_type": "LABOR",
                "item_name": "实施与驻场调试",
                "qty": d("150"),
                "unit_price": d("550"),
                "cost": d("360"),
                "lead_time_days": 30,
                "remark": "快速联调+培训",
                "cost_category": "LABOR",
                "cost_source": "MANUAL",
                "specification": "项目团队+客户共创",
                "unit": "小时",
            },
        ],
        "contract": {
            "contract_code": "HT-DEMO-003",
            "status": "IN_REVIEW",
            "contract_amount": d("2990000"),
            "signed_offset_days": 0,
            "payment_terms_summary": "40%预付款 + 50% 预验收 + 10% 终验",
            "acceptance_summary": "演示数据合同，关注治具验收与联调报告。",
            "project_id": None,
            "deliverables": [
                {
                    "deliverable_name": "工装治具确认",
                    "deliverable_type": "CHECKLIST",
                    "required_for_payment": True,
                    "template_ref": "DEMO-SOW",
                },
                {
                    "deliverable_name": "上线联调报告",
                    "deliverable_type": "REPORT",
                    "required_for_payment": True,
                    "template_ref": "DEMO-FAT",
                },
            ],
        },
    },
    {
        "customer_code": "CUS-SMARTLINK",
        "opportunity": {
            "opp_code": "OPP-SMT-2501",
            "opp_name": "高速SMT产线AOI整机升级",
            "project_type": "线体改造",
            "equipment_type": "AOI & 测试",
            "stage": "PROPOSAL",
            "est_amount": d("1850000"),
            "est_margin": d("22.0"),
            "budget_range": "150-200万",
            "decision_chain": "制造副总 + 设备部 + 财务BP",
            "delivery_window": "2025Q2",
            "acceptance_basis": "CT≤0.8s/板，缺陷检出率≥99.5%",
            "score": 74,
            "risk_level": "LOW",
            "gate_status": "PASS",
        },
        "quote": {
            "quote_code": "Q-SMT-005",
            "status": "DRAFT",
            "valid_until_days": 35,
        },
        "version": {
            "version_no": "V0.5",
            "total_price": d("1850000"),
            "cost_total": d("1440000"),
            "gross_margin": d("22.1"),
            "lead_time_days": 65,
            "delivery_offset_days": 70,
            "risk_terms": "接口改造需锁定夜间停线窗口；SMEMA协议对接责任界面已标注。",
            "cost_breakdown_complete": True,
            "margin_warning": False,
            "approved": False,
        },
        "items": [
            {
                "item_type": "MODULE",
                "item_name": "高速AOI整机",
                "qty": d("2"),
                "unit_price": d("520000"),
                "cost": d("390000"),
                "lead_time_days": 55,
                "remark": "含多角度视觉与AI算法",
                "cost_category": "EQUIPMENT",
                "cost_source": "SUPPLIER",
                "specification": "四相机+AI缺陷识别",
                "unit": "台",
            },
            {
                "item_type": "MODULE",
                "item_name": "在线测试治具与缓存段",
                "qty": d("1"),
                "unit_price": d("420000"),
                "cost": d("315000"),
                "lead_time_days": 60,
                "remark": "含SMEMA接口、缓存轨道",
                "cost_category": "EQUIPMENT",
                "cost_source": "TEMPLATE",
                "specification": "双轨缓存+自动分拣",
                "unit": "套",
            },
            {
                "item_type": "LABOR",
                "item_name": "驻场调试与算法训练",
                "qty": d("200"),
                "unit_price": d("450"),
                "cost": d("320"),
                "lead_time_days": 30,
                "remark": "算法训练+夜间切线",
                "cost_category": "LABOR",
                "cost_source": "MANUAL",
                "specification": "昼夜两班+远程监控",
                "unit": "小时",
            },
        ],
        "contract": {
            "contract_code": "HT-SMT-005",
            "status": "DRAFT",
            "contract_amount": d("1850000"),
            "signed_offset_days": None,
            "payment_terms_summary": "20%预付款 + 70% 调试完成 + 10% 终验",
            "acceptance_summary": "AOI良率对比验证+产线节拍测试完成后验收。",
            "project_id": None,
            "deliverables": [
                {
                    "deliverable_name": "算法训练报告",
                    "deliverable_type": "REPORT",
                    "required_for_payment": True,
                    "template_ref": "AOI-TRAIN",
                },
                {
                    "deliverable_name": "节拍/良率验证记录",
                    "deliverable_type": "CHECKLIST",
                    "required_for_payment": True,
                    "template_ref": "SMT-VERIFY",
                },
            ],
        },
    },
    {
        "customer_code": "CUS-PV-BLUE",
        "opportunity": {
            "opp_code": "OPP-PV-2502",
            "opp_name": "海外储能集装箱EPC",
            "project_type": "交钥匙工程",
            "equipment_type": "储能系统",
            "stage": "NEGOTIATION",
            "est_amount": d("5280000"),
            "est_margin": d("18.5"),
            "budget_range": "500-550万",
            "decision_chain": "国际事业部总监 + 财务 + 风控",
            "delivery_window": "2025Q3",
            "acceptance_basis": "UL9540A认证+整柜FAT/SAT",
            "score": 78,
            "risk_level": "MEDIUM",
            "gate_status": "PASS",
        },
        "quote": {
            "quote_code": "Q-PV-022",
            "status": "APPROVED",
            "valid_until_days": 60,
        },
        "version": {
            "version_no": "V1.2",
            "total_price": d("5280000"),
            "cost_total": d("4300000"),
            "gross_margin": d("18.5"),
            "lead_time_days": 120,
            "delivery_offset_days": 140,
            "risk_terms": "海外港口物流风险由客户承担；火灾抑制选择Novec系统需预付。",
            "cost_breakdown_complete": True,
            "margin_warning": True,
            "approved": True,
        },
        "items": [
            {
                "item_type": "MODULE",
                "item_name": "2.5MWh储能集装箱",
                "qty": d("2"),
                "unit_price": d("1800000"),
                "cost": d("1500000"),
                "lead_time_days": 110,
                "remark": "含BMS/EMS",
                "cost_category": "EQUIPMENT",
                "cost_source": "SUPPLIER",
                "specification": "液冷+消防一体化",
                "unit": "套",
            },
            {
                "item_type": "MODULE",
                "item_name": "消防与监控系统",
                "qty": d("2"),
                "unit_price": d("260000"),
                "cost": d("190000"),
                "lead_time_days": 75,
                "remark": "Novec+高清监控",
                "cost_category": "EQUIPMENT",
                "cost_source": "HISTORY",
                "specification": "UL9540A认证",
                "unit": "套",
            },
            {
                "item_type": "LABOR",
                "item_name": "海外EPC施工与调试",
                "qty": d("420"),
                "unit_price": d("520"),
                "cost": d("360"),
                "lead_time_days": 120,
                "remark": "含境外签证与驻场",
                "cost_category": "LABOR",
                "cost_source": "MANUAL",
                "specification": "驻场EPC团队",
                "unit": "小时",
            },
        ],
        "contract": {
            "contract_code": "HT-PV-022",
            "status": "ACTIVE",
            "contract_amount": d("5280000"),
            "signed_offset_days": -20,
            "payment_terms_summary": "30%预付款 + 50% FAT后 + 20% SAT后",
            "acceptance_summary": "通过UL9540A+当地电力公司验收后转入运维。",
            "project_id": 10,
            "deliverables": [
                {
                    "deliverable_name": "国际物流计划",
                    "deliverable_type": "DOCUMENT",
                    "required_for_payment": False,
                    "template_ref": "PV-LOG",
                },
                {
                    "deliverable_name": "海外FAT/SAT报告",
                    "deliverable_type": "REPORT",
                    "required_for_payment": True,
                    "template_ref": "PV-FAT",
                },
            ],
        },
    },
]


def ensure_customer(db, owner: User, payload: Dict) -> Tuple[Customer, bool]:
    customer = db.query(Customer).filter_by(customer_code=payload["customer_code"]).first()
    if customer:
        print(f"✓ 客户已存在: {customer.customer_code}")
        return customer, False

    customer = Customer(**payload, created_by=owner.id)
    db.add(customer)
    db.flush()
    print(f"＋ 创建客户: {customer.customer_code} - {customer.customer_name}")
    return customer, True


def upsert_opportunity(db, owner: User, customer: Customer, payload: Dict) -> Opportunity:
    opportunity = db.query(Opportunity).filter_by(opp_code=payload["opp_code"]).first()
    fields = {
        "customer_id": customer.id,
        "opp_name": payload["opp_name"],
        "project_type": payload["project_type"],
        "equipment_type": payload["equipment_type"],
        "stage": payload["stage"],
        "est_amount": payload["est_amount"],
        "est_margin": payload["est_margin"],
        "budget_range": payload["budget_range"],
        "decision_chain": payload["decision_chain"],
        "delivery_window": payload["delivery_window"],
        "acceptance_basis": payload["acceptance_basis"],
        "score": payload["score"],
        "risk_level": payload["risk_level"],
        "owner_id": owner.id,
        "gate_status": payload["gate_status"],
        "gate_passed_at": NOW if payload["gate_status"] == "PASS" else None,
    }

    if opportunity:
        for key, value in fields.items():
            setattr(opportunity, key, value)
        print(f"✓ 更新商机: {opportunity.opp_code}")
        return opportunity

    opportunity = Opportunity(
        opp_code=payload["opp_code"],
        **fields,
    )
    db.add(opportunity)
    db.flush()
    print(f"＋ 创建商机: {opportunity.opp_code} - {opportunity.opp_name}")
    return opportunity


def upsert_quote_bundle(db, owner: User, bundle: Dict, customer: Customer):
    opportunity = upsert_opportunity(db, owner, customer, bundle["opportunity"])

    quote = db.query(Quote).filter_by(quote_code=bundle["quote"]["quote_code"]).first()
    valid_until = TODAY + timedelta(days=bundle["quote"]["valid_until_days"])
    if quote:
        quote.opportunity_id = opportunity.id
        quote.customer_id = customer.id
        quote.status = bundle["quote"]["status"]
        quote.valid_until = valid_until
        quote.owner_id = owner.id
        print(f"✓ 更新报价: {quote.quote_code}")
    else:
        quote = Quote(
            quote_code=bundle["quote"]["quote_code"],
            opportunity_id=opportunity.id,
            customer_id=customer.id,
            status=bundle["quote"]["status"],
            valid_until=valid_until,
            owner_id=owner.id,
        )
        db.add(quote)
        db.flush()
        print(f"＋ 创建报价: {quote.quote_code}")

    version_payload = bundle["version"]
    version = (
        db.query(QuoteVersion)
        .filter(QuoteVersion.quote_id == quote.id, QuoteVersion.version_no == version_payload["version_no"])
        .first()
    )
    delivery_date = TODAY + timedelta(days=version_payload["delivery_offset_days"])
    version_fields = {
        "total_price": version_payload["total_price"],
        "cost_total": version_payload["cost_total"],
        "gross_margin": version_payload["gross_margin"],
        "lead_time_days": version_payload["lead_time_days"],
        "delivery_date": delivery_date,
        "risk_terms": version_payload["risk_terms"],
        "cost_breakdown_complete": version_payload.get("cost_breakdown_complete", True),
        "margin_warning": version_payload.get("margin_warning", False),
        "created_by": owner.id,
        "approved_by": 1 if version_payload.get("approved") else None,
        "approved_at": NOW if version_payload.get("approved") else None,
    }

    if version:
        for key, value in version_fields.items():
            setattr(version, key, value)
        print(f"  ↻ 更新版本: {quote.quote_code}-{version.version_no}")
    else:
        version = QuoteVersion(
            quote_id=quote.id,
            version_no=version_payload["version_no"],
            **version_fields,
        )
        db.add(version)
        db.flush()
        print(f"  ＋ 创建版本: {quote.quote_code}-{version.version_no}")

    quote.current_version_id = version.id

    # Recreate items each run to ensure demo数据一致
    for existing in list(version.items):
        db.delete(existing)
    db.flush()

    for item_payload in bundle["items"]:
        item = QuoteItem(
            quote_version_id=version.id,
            item_name=item_payload["item_name"],
            item_type=item_payload["item_type"],
            qty=item_payload["qty"],
            unit_price=item_payload["unit_price"],
            cost=item_payload["cost"],
            lead_time_days=item_payload["lead_time_days"],
            remark=item_payload["remark"],
            cost_category=item_payload["cost_category"],
            cost_source=item_payload["cost_source"],
            specification=item_payload["specification"],
            unit=item_payload["unit"],
        )
        db.add(item)
        print(f"    ＋ 添加明细: {item.item_name}")

    contract_payload = bundle["contract"]
    contract = db.query(Contract).filter_by(contract_code=contract_payload["contract_code"]).first()
    signed_date = (
        TODAY + timedelta(days=contract_payload["signed_offset_days"])
        if isinstance(contract_payload.get("signed_offset_days"), (int, float))
        else None
    )
    contract_fields = {
        "opportunity_id": opportunity.id,
        "quote_version_id": version.id,
        "customer_id": customer.id,
        "project_id": contract_payload.get("project_id"),
        "contract_amount": contract_payload["contract_amount"],
        "signed_date": signed_date,
        "status": contract_payload["status"],
        "payment_terms_summary": contract_payload["payment_terms_summary"],
        "acceptance_summary": contract_payload["acceptance_summary"],
        "owner_id": owner.id,
    }

    if contract:
        for key, value in contract_fields.items():
            setattr(contract, key, value)
        print(f"  ↻ 更新合同: {contract.contract_code}")
    else:
        contract = Contract(
            contract_code=contract_payload["contract_code"],
            **contract_fields,
        )
        db.add(contract)
        db.flush()
        print(f"  ＋ 创建合同: {contract.contract_code}")

    deliverable_lookup = {d.deliverable_name: d for d in contract.deliverables}
    for deliverable in contract_payload["deliverables"]:
        instance = deliverable_lookup.get(deliverable["deliverable_name"])
        if instance:
            instance.deliverable_type = deliverable["deliverable_type"]
            instance.required_for_payment = deliverable["required_for_payment"]
            instance.template_ref = deliverable["template_ref"]
            print(f"    ↻ 更新交付物: {instance.deliverable_name}")
        else:
            instance = ContractDeliverable(
                contract_id=contract.id,
                **deliverable,
            )
            db.add(instance)
            print(f"    ＋ 添加交付物: {instance.deliverable_name}")


def main():
    with get_db_session() as db:
        owner = db.query(User).filter_by(username="zhang_sales").first()
        if not owner:
            raise SystemExit("用户 zhang_sales 不存在，请先创建销售工程师账户。")

        customer_map: Dict[str, Customer] = {}
        for payload in CUSTOMERS:
            customer, _created = ensure_customer(db, owner, payload)
            customer_map[payload["customer_code"]] = customer

        for bundle in SALES_BUNDLES:
            customer = customer_map[bundle["customer_code"]]
            upsert_quote_bundle(db, owner, bundle, customer)

        print("\n✅ 销售演示数据准备完成，可使用 zhang_sales / Password123! 登录查看。")


if __name__ == "__main__":
    main()
