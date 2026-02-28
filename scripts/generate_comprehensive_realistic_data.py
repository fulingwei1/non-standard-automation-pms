#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成全面、真实度高的测试数据脚本
包含：销售线索、技术评估、失败案例、项目、生产、预警异常等完整数据

使用方法:
    python3 scripts/generate_comprehensive_realistic_data.py
"""

import json
import os
import random
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 注意：WorkOrder.material_id外键引用错误，需要修复模型定义
# 临时解决方案：不设置material_id字段
from app.models.alert import AlertRecord, AlertRule, ExceptionEvent
from app.models.base import get_db_session
from app.models.organization import Employee
from app.models.production import (
    ProcessDict,
    ProductionPlan,
    Worker,
    WorkOrder,
    WorkReport,
    Workshop,
)
from app.models.project import (
    Customer,
    Machine,
    Project,
    ProjectMilestone,
    ProjectPaymentPlan,
)
from app.models.sales import (
    FailureCase,
    Lead,
    LeadRequirementDetail,
    Opportunity,
    Quote,
    QuoteItem,
    QuoteVersion,
    TechnicalAssessment,
)
from app.models.user import User

# ==================== 数据模板 ====================

CUSTOMER_TEMPLATES = [
    {
        "name": "深圳智行新能源汽车电子有限公司",
        "short_name": "智行新能源",
        "type": "企业客户",
        "industry": "新能源汽车电子",
        "scale": "大型",
        "address": "深圳市龙华区观澜街道高新技术产业园A座15层",
        "contact": "王总",
        "phone": "0755-88888888",
        "email": "wang.zong@zhixingev.com",
        "credit_level": "A",
        "credit_limit": 5000000
    },
    {
        "name": "东莞华强精密电子科技有限公司",
        "short_name": "华强精密",
        "type": "企业客户",
        "industry": "消费电子",
        "scale": "中型",
        "address": "东莞市松山湖科技产业园区科技路88号",
        "contact": "李经理",
        "phone": "0769-12345678",
        "email": "li.manager@hqprecision.com",
        "credit_level": "B",
        "credit_limit": 2000000
    },
    {
        "name": "苏州博世汽车零部件有限公司",
        "short_name": "博世汽车",
        "type": "企业客户",
        "industry": "汽车零部件",
        "scale": "大型",
        "address": "苏州市工业园区星海街200号",
        "contact": "张总监",
        "phone": "0512-87654321",
        "email": "zhang.director@bosch.com",
        "credit_level": "A",
        "credit_limit": 8000000
    },
    {
        "name": "上海联影医疗科技有限公司",
        "short_name": "联影医疗",
        "type": "企业客户",
        "industry": "医疗器械",
        "scale": "大型",
        "address": "上海市嘉定区嘉定工业区叶城路1288号",
        "contact": "陈总",
        "phone": "021-65432100",
        "email": "chen.zong@united-imaging.com",
        "credit_level": "A",
        "credit_limit": 10000000
    },
    {
        "name": "北京小米通讯技术有限公司",
        "short_name": "小米通讯",
        "type": "企业客户",
        "industry": "消费电子",
        "scale": "大型",
        "address": "北京市海淀区安宁庄东路小米科技园",
        "contact": "刘经理",
        "phone": "010-88888888",
        "email": "liu.manager@xiaomi.com",
        "credit_level": "A",
        "credit_limit": 15000000
    }
]

INDUSTRIES = ["新能源汽车电子", "消费电子", "汽车零部件", "医疗器械", "通信设备", "工业自动化"]
EQUIPMENT_TYPES = ["ICT", "FCT", "EOL", "烧录", "老化", "视觉检测", "自动化组装"]
PROJECT_STAGES = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"]
HEALTH_STATUSES = ["H1", "H2", "H3", "H4"]


def generate_customers(db, count=10):
    """生成客户数据"""
    print(f"\n生成 {count} 个客户...")
    customers = []

    # 扩展客户模板
    extended_templates = CUSTOMER_TEMPLATES + [
        {
            "name": "广州比亚迪汽车工业有限公司",
            "short_name": "比亚迪",
            "type": "企业客户",
            "industry": "新能源汽车",
            "scale": "大型",
            "address": "广州市番禺区石楼镇莲花山工业区",
            "contact": "刘总",
            "phone": "020-34567890",
            "email": "liu.zong@byd.com",
            "credit_level": "A",
            "credit_limit": 20000000
        },
        {
            "name": "深圳华为技术有限公司",
            "short_name": "华为",
            "type": "企业客户",
            "industry": "通信设备",
            "scale": "大型",
            "address": "深圳市龙岗区坂田华为基地",
            "contact": "陈经理",
            "phone": "0755-28780808",
            "email": "chen.manager@huawei.com",
            "credit_level": "A",
            "credit_limit": 50000000
        },
        {
            "name": "苏州汇川技术股份有限公司",
            "short_name": "汇川技术",
            "type": "企业客户",
            "industry": "工业自动化",
            "scale": "大型",
            "address": "苏州市吴中区越溪街道天鹅荡路5号",
            "contact": "周总",
            "phone": "0512-66666666",
            "email": "zhou.zong@invt.com",
            "credit_level": "A",
            "credit_limit": 15000000
        },
        {
            "name": "上海ABB工程有限公司",
            "short_name": "ABB",
            "type": "企业客户",
            "industry": "工业自动化",
            "scale": "大型",
            "address": "上海市浦东新区外高桥保税区富特东三路76号",
            "contact": "John Smith",
            "phone": "021-28912345",
            "email": "john.smith@abb.com",
            "credit_level": "A",
            "credit_limit": 30000000
        },
        {
            "name": "北京京东方科技集团股份有限公司",
            "short_name": "京东方",
            "type": "企业客户",
            "industry": "消费电子",
            "scale": "大型",
            "address": "北京市朝阳区酒仙桥路10号",
            "contact": "王经理",
            "phone": "010-64318888",
            "email": "wang.manager@boe.com",
            "credit_level": "A",
            "credit_limit": 25000000
        }
    ]

    for i, template in enumerate(extended_templates[:count]):
        customer_code = f"CUST2025{i+1:03d}"
        # 检查是否已存在
        existing = db.query(Customer).filter(Customer.customer_code == customer_code).first()
        if existing:
            print(f"  ⊙ 客户已存在: {existing.customer_name} ({customer_code})")
            customers.append(existing)
            continue

        customer = Customer(
            customer_code=customer_code,
            customer_name=template["name"],
            short_name=template["short_name"],
            customer_type=template["type"],
            industry=template["industry"],
            scale=template["scale"],
            address=template["address"],
            contact_person=template["contact"],
            contact_phone=template["phone"],
            contact_email=template["email"],
            legal_person=template["contact"],
            tax_no=f"91440300MA5F8K9X{i+1}L",
            bank_name="中国工商银行",
            bank_account=f"4000021234567890{i+1:03d}",
            credit_level=template["credit_level"],
            credit_limit=Decimal(str(template["credit_limit"])),
            payment_terms="30%预付款，60%发货前，10%验收后",
            status="ACTIVE"
        )
        db.add(customer)
        db.flush()
        customers.append(customer)
        print(f"  ✓ {customer.customer_name} ({customer.customer_code})")

    return customers


def generate_failure_cases(db, users):
    """生成失败案例数据"""
    print("\n生成失败案例数据...")

    failure_cases_data = [
        {
            "case_code": "FC2024-001",
            "project_name": "某新能源电池包EOL测试设备项目",
            "industry": "新能源汽车电子",
            "product_types": json.dumps(["电池包", "BMS"]),
            "processes": json.dumps(["EOL测试", "功能测试"]),
            "takt_time_s": 45,
            "annual_volume": 50000,
            "budget_status": "预算不足",
            "customer_project_status": "项目延期",
            "spec_status": "需求不明确",
            "price_sensitivity": "高",
            "delivery_months": 3,
            "failure_tags": json.dumps(["需求变更频繁", "预算不足", "交付周期过短", "技术难度低估"]),
            "core_failure_reason": "客户需求在项目执行过程中频繁变更，且预算不足导致无法满足所有变更需求。同时交付周期过短，技术难度被低估，最终项目延期严重，客户满意度低。",
            "early_warning_signals": json.dumps([
                "需求文档不完整",
                "客户多次提出变更",
                "预算与需求不匹配",
                "交付周期过短"
            ]),
            "final_result": "项目延期3个月，客户满意度低，尾款回收困难",
            "lesson_learned": "1. 必须要求客户提供完整的需求文档并冻结需求；2. 预算不足的项目需要谨慎评估；3. 交付周期过短的项目风险高，需要充分评估技术难度；4. 需求变更必须走正式变更流程。",
            "keywords": json.dumps(["需求变更", "预算不足", "交付周期", "技术难度", "EOL测试"])
        },
        {
            "case_code": "FC2024-002",
            "project_name": "某消费电子主板ICT测试设备项目",
            "industry": "消费电子",
            "product_types": json.dumps(["主板", "PCBA"]),
            "processes": json.dumps(["ICT测试", "在线测试"]),
            "takt_time_s": 8,
            "annual_volume": 200000,
            "budget_status": "预算充足",
            "customer_project_status": "项目正常",
            "spec_status": "规范明确",
            "price_sensitivity": "中",
            "delivery_months": 4,
            "failure_tags": json.dumps(["节拍要求过高", "测试覆盖率不足", "误判率高"]),
            "core_failure_reason": "客户要求的节拍时间过短（8秒），导致测试覆盖率不足，误判率高。设备在客户现场运行后，误判率超过5%，客户不满意。",
            "early_warning_signals": json.dumps([
                "节拍要求极短",
                "测试覆盖率要求高",
                "误判率要求严格"
            ]),
            "final_result": "设备验收不通过，需要返工，项目亏损",
            "lesson_learned": "1. 节拍时间过短的项目需要充分评估技术可行性；2. 测试覆盖率与节拍时间存在矛盾，需要平衡；3. 误判率要求严格的项目需要充分验证；4. 需要在报价阶段明确技术边界。",
            "keywords": json.dumps(["节拍时间", "测试覆盖率", "误判率", "ICT测试", "技术边界"])
        },
        {
            "case_code": "FC2024-003",
            "project_name": "某汽车零部件视觉检测设备项目",
            "industry": "汽车零部件",
            "product_types": json.dumps(["汽车零部件", "精密零件"]),
            "processes": json.dumps(["视觉检测", "尺寸检测"]),
            "takt_time_s": 12,
            "annual_volume": 100000,
            "budget_status": "预算充足",
            "customer_project_status": "项目正常",
            "spec_status": "规范明确",
            "price_sensitivity": "低",
            "delivery_months": 5,
            "failure_tags": json.dumps(["检测精度要求过高", "现场环境复杂", "光源干扰"]),
            "core_failure_reason": "客户要求的检测精度过高（±0.01mm），现场环境复杂，存在光源干扰。设备在客户现场无法达到要求的检测精度，需要多次调试。",
            "early_warning_signals": json.dumps([
                "检测精度要求极高",
                "现场环境复杂",
                "存在光源干扰"
            ]),
            "final_result": "设备调试周期延长2个月，项目成本超支",
            "lesson_learned": "1. 检测精度要求过高的项目需要充分评估现场环境；2. 现场环境复杂需要提前调研；3. 光源干扰问题需要在设计阶段考虑；4. 需要预留足够的调试时间。",
            "keywords": json.dumps(["检测精度", "现场环境", "光源干扰", "视觉检测", "调试周期"])
        }
    ]

    failure_cases = []
    for case_data in failure_cases_data:
        # 检查是否已存在
        existing = db.query(FailureCase).filter(FailureCase.case_code == case_data["case_code"]).first()
        if existing:
            print(f"  ⊙ 失败案例已存在: {existing.case_code}")
            failure_cases.append(existing)
            continue

        case = FailureCase(
            case_code=case_data["case_code"],
            project_name=case_data["project_name"],
            industry=case_data["industry"],
            product_types=case_data["product_types"],
            processes=case_data["processes"],
            takt_time_s=case_data["takt_time_s"],
            annual_volume=case_data["annual_volume"],
            budget_status=case_data["budget_status"],
            customer_project_status=case_data["customer_project_status"],
            spec_status=case_data["spec_status"],
            price_sensitivity=case_data["price_sensitivity"],
            delivery_months=case_data["delivery_months"],
            failure_tags=case_data["failure_tags"],
            core_failure_reason=case_data["core_failure_reason"],
            early_warning_signals=case_data["early_warning_signals"],
            final_result=case_data["final_result"],
            lesson_learned=case_data["lesson_learned"],
            keywords=case_data["keywords"],
            created_by=(users.get("pm") or users.get("sales") or (list(users.values())[0] if users else None)).id if users else None
        )
        db.add(case)
        db.flush()
        failure_cases.append(case)
        print(f"  ✓ {case.case_code} - {case.project_name}")

    return failure_cases


def generate_leads_with_assessments(db, customers, users):
    """生成销售线索和技术评估数据"""
    print("\n生成销售线索和技术评估数据...")

    # 扩展线索数据
    leads_data = [
        {
            "lead_code": "LD202501001",
            "source": "展会",
            "customer": customers[0],
            "industry": "新能源汽车电子",
            "contact": "王总",
            "phone": "0755-88888888",
            "demand": "需要BMS（电池管理系统）FCT功能测试设备，要求：\n1. 支持8通道同时测试\n2. 测试精度：电压±0.1%，电流±0.2%\n3. 节拍要求：≤15秒/件\n4. 支持CAN总线通信\n5. 具备数据记录和追溯功能",
            "stage": "ASSESSING",
            "assessment_status": "IN_PROGRESS",
            "completeness": 75
        },
        {
            "lead_code": "LD202501002",
            "source": "官网咨询",
            "customer": customers[1],
            "industry": "消费电子",
            "contact": "李经理",
            "phone": "0769-12345678",
            "demand": "需要主板ICT测试设备，要求：\n1. 支持双工位并行测试\n2. 节拍要求：≤8秒/件\n3. 测试覆盖率≥95%\n4. 误判率≤2%\n5. 支持条码追溯",
            "stage": "NEW",
            "assessment_status": "PENDING",
            "completeness": 50
        },
        {
            "lead_code": "LD202501003",
            "source": "老客户推荐",
            "customer": customers[2],
            "industry": "汽车零部件",
            "contact": "张总监",
            "phone": "0512-87654321",
            "demand": "需要汽车零部件视觉检测设备，要求：\n1. 检测精度：±0.01mm\n2. 节拍要求：≤12秒/件\n3. 支持多种规格产品检测\n4. 具备缺陷分类功能\n5. 数据上传MES系统",
            "stage": "ASSESSING",
            "assessment_status": "IN_PROGRESS",
            "completeness": 80
        },
        {
            "lead_code": "LD202501004",
            "source": "电话咨询",
            "customer": customers[3] if len(customers) > 3 else customers[0],
            "industry": "医疗器械",
            "contact": "陈总",
            "phone": "021-65432100",
            "demand": "需要医疗设备功能测试设备，要求：\n1. 支持多通道并行测试\n2. 测试精度：±0.05%\n3. 节拍要求：≤20秒/件\n4. 符合医疗设备标准\n5. 具备完整测试报告",
            "stage": "NEW",
            "assessment_status": "PENDING",
            "completeness": 60
        },
        {
            "lead_code": "LD202501005",
            "source": "展会",
            "customer": customers[4] if len(customers) > 4 else customers[1],
            "industry": "消费电子",
            "contact": "刘经理",
            "phone": "010-88888888",
            "demand": "需要手机主板ICT测试设备，要求：\n1. 支持4工位并行测试\n2. 节拍要求：≤6秒/件\n3. 测试覆盖率≥98%\n4. 误判率≤1%\n5. 支持自动化上下料",
            "stage": "ASSESSING",
            "assessment_status": "IN_PROGRESS",
            "completeness": 85
        }
    ]

    leads = []
    assessments = []

    for lead_data in leads_data:
        # 检查是否已存在
        existing = db.query(Lead).filter(Lead.lead_code == lead_data["lead_code"]).first()
        if existing:
            print(f"  ⊙ 线索已存在: {existing.lead_code}")
            leads.append(existing)
            continue

        # 创建线索
        lead = Lead(
            lead_code=lead_data["lead_code"],
            source=lead_data["source"],
            customer_name=lead_data["customer"].customer_name,
            industry=lead_data["industry"],
            contact_name=lead_data["contact"],
            contact_phone=lead_data["phone"],
            demand_summary=lead_data["demand"],
            owner_id=users["sales"].id,
            status=lead_data["stage"],
            assessment_status=lead_data["assessment_status"],
            completeness=lead_data["completeness"],
            assignee_id=users.get("presale", users.get("pm")).id,
            created_at=datetime.now() - timedelta(days=random.randint(1, 30))
        )
        db.add(lead)
        db.flush()

        # 创建需求详情
        req_detail = LeadRequirementDetail(
            lead_id=lead.id,
            customer_factory_location=f"{lead_data['customer'].address}",
            target_object_type="BMS" if "BMS" in lead_data["demand"] else "主板" if "主板" in lead_data["demand"] else "汽车零部件",
            application_scenario="生产线测试",
            delivery_mode="现场安装",
            expected_delivery_date=datetime.now() + timedelta(days=120),
            requirement_maturity=3 if lead_data["completeness"] >= 70 else 2,
            has_sow=lead_data["completeness"] >= 70,
            has_interface_doc=lead_data["completeness"] >= 60,
            has_drawing_doc=lead_data["completeness"] >= 50,
            cycle_time_seconds=Decimal("15") if "15秒" in lead_data["demand"] else Decimal("8") if "8秒" in lead_data["demand"] else Decimal("12"),
            workstation_count=8 if "8通道" in lead_data["demand"] else 2 if "双工位" in lead_data["demand"] else 1,
            yield_target=Decimal("98.0"),
            retest_allowed=True,
            retest_max_count=2,
            traceability_type="条码追溯",
            data_retention_period=365,
            test_scope=json.dumps(["功能测试", "性能测试", "可靠性测试"]),
            acceptance_method="FAT验收",
            acceptance_basis="满足技术规格要求，通过客户验收测试",
            interface_types=json.dumps(["CAN总线", "RS232", "以太网"]),
            communication_protocols=json.dumps(["CANopen", "Modbus TCP"]),
            power_supply=json.dumps({"voltage": "220V", "power": "5KW"}),
            environment=json.dumps({"temperature": "20-30℃", "humidity": "40-60%"}),
            requirement_version="V1.0",
            is_frozen=False
        )
        db.add(req_detail)
        db.flush()

        lead.requirement_detail_id = req_detail.id

        # 如果评估状态为进行中，创建技术评估
        if lead_data["assessment_status"] == "IN_PROGRESS":
            assessment = TechnicalAssessment(
                source_type="LEAD",
                source_id=lead.id,
                evaluator_id=users.get("presale", users.get("pm")).id,
                status="IN_PROGRESS",
                total_score=random.randint(30, 80),
                dimension_scores=json.dumps({
                    "technology": random.randint(5, 20),
                    "business": random.randint(5, 20),
                    "resource": random.randint(5, 20),
                    "delivery": random.randint(5, 20),
                    "customer": random.randint(5, 20)
                }),
                veto_triggered=False,
                decision="PENDING",
                risks=json.dumps([
                    "需求可能变更",
                    "交付周期紧张",
                    "技术难度较高"
                ]),
                evaluated_at=None
            )
            db.add(assessment)
            db.flush()

            lead.assessment_id = assessment.id
            assessments.append(assessment)

        leads.append(lead)
        print(f"  ✓ {lead.lead_code} - {lead.customer_name} (完整度: {lead.completeness}%)")

    db.flush()
    return leads, assessments


def generate_opportunities_and_projects(db, customers, leads, users):
    """生成商机和项目数据"""
    print("\n生成商机和项目数据...")

    opportunities = []
    projects = []

    # 从线索转换为商机（至少80%的线索转为商机）
    leads_to_convert = leads[:int(len(leads) * 0.8)] if len(leads) > 3 else leads
    for i, lead in enumerate(leads_to_convert):
        customer = customers[i % len(customers)]
        opp_code = f"OPP202501{i+1:03d}"

        # 检查商机是否已存在
        existing_opp = db.query(Opportunity).filter(Opportunity.opp_code == opp_code).first()
        if existing_opp:
            print(f"  ⊙ 商机已存在: {existing_opp.opp_code}")
            opportunities.append(existing_opp)
            # 检查是否有对应的项目
            existing_project = db.query(Project).filter(Project.opportunity_id == existing_opp.id).first()
            if existing_project:
                projects.append(existing_project)
            continue

        # 创建商机
        opp = Opportunity(
            opp_code=opp_code,
            lead_id=lead.id,
            customer_id=customer.id,
            opp_name=f"{customer.short_name}{random.choice(['BMS', '主板', '视觉检测'])}测试设备项目",
            project_type="FIXED_PRICE",
            equipment_type=random.choice(EQUIPMENT_TYPES),
            stage="PROPOSAL",
            est_amount=Decimal(str(random.randint(1500000, 5000000))),
            est_margin=Decimal(str(random.uniform(20, 35))),
            budget_range=f"{random.randint(150, 300)}-{random.randint(300, 500)}万",
            decision_chain="技术总监 → 采购总监 → 总经理",
            delivery_window=f"2025年Q{random.randint(2, 4)}",
            acceptance_basis="1. 通过客户FAT验收\n2. 满足技术规格要求\n3. 提供完整技术文档",
            score=random.randint(60, 90),
            risk_level=random.choice(["LOW", "MEDIUM", "HIGH"]),
            owner_id=users["sales"].id,
            gate_status="PASSED",
            gate_passed_at=datetime.now() - timedelta(days=random.randint(1, 10)),
            created_at=datetime.now() - timedelta(days=random.randint(5, 20))
        )
        db.add(opp)
        db.flush()
        opportunities.append(opp)

        # 为商机创建报价（70%概率）
        if random.random() > 0.3:
                quote = Quote(
                    quote_code=f"QT{opp.opp_code}",
                    opportunity_id=opp.id,
                    customer_id=customer.id,
                    status="APPROVED",
                    valid_until=date.today() + timedelta(days=30),
                    owner_id=users["sales"].id,
                    created_at=datetime.now() - timedelta(days=random.randint(1, 10))
                )
                db.add(quote)
                db.flush()

                # 创建报价版本
                quote_version = QuoteVersion(
                    quote_id=quote.id,
                    version_no="V1.0",
                    total_price=opp.est_amount,
                    cost_total=opp.est_amount * Decimal("0.75"),
                    gross_margin=Decimal("25.0"),
                    lead_time_days=120,
                    delivery_date=date.today() + timedelta(days=120),
                    created_by=users["sales"].id
                )
                db.add(quote_version)
                db.flush()

                # 创建报价明细
                quote_items = [
                    {"name": "测试设备主机", "type": "EQUIPMENT", "qty": 1, "price": opp.est_amount * Decimal("0.6")},
                    {"name": "测试治具", "type": "FIXTURE", "qty": 4, "price": opp.est_amount * Decimal("0.2")},
                    {"name": "软件系统", "type": "SOFTWARE", "qty": 1, "price": opp.est_amount * Decimal("0.15")},
                    {"name": "安装调试", "type": "SERVICE", "qty": 1, "price": opp.est_amount * Decimal("0.05")}
                ]

                for item_data in quote_items:
                    item = QuoteItem(
                        quote_version_id=quote_version.id,
                        item_name=item_data["name"],
                        item_type=item_data["type"],
                        qty=Decimal(str(item_data["qty"])),
                        unit_price=item_data["price"] / Decimal(str(item_data["qty"])),
                        cost=item_data["price"] * Decimal("0.8")  # 成本约为价格的80%
                    )
                    db.add(item)
                db.flush()
                quote.current_version_id = quote_version.id

        # 创建项目（如果商机已签单）
        if random.random() > 0.2:  # 80%概率签单
            stage = random.choice(["S2", "S3", "S4", "S5", "S6"])
            health = random.choice(["H1", "H2", "H3"])
            project_code = f"PJ2501{i+1:03d}"

            # 检查项目是否已存在
            existing_project = db.query(Project).filter(Project.project_code == project_code).first()
            if existing_project:
                print(f"  ⊙ 项目已存在: {existing_project.project_code}")
                projects.append(existing_project)
                continue

            project = Project(
                project_code=project_code,
                project_name=opp.opp_name,
                short_name=f"{customer.short_name}测试项目",
                customer_id=customer.id,
                customer_name=customer.customer_name,
                customer_contact=customer.contact_person,
                customer_phone=customer.contact_phone,
                contract_no=f"CT202501{i+1:03d}",
                project_type="FIXED_PRICE",
                product_category=opp.equipment_type,
                industry=customer.industry,
                project_category="销售",
                stage=stage,
                status=f"ST{random.randint(10, 30)}",
                health=health,
                progress_pct=Decimal(str(random.randint(10, 80))),
                contract_date=date.today() - timedelta(days=random.randint(10, 60)),
                planned_start_date=date.today() - timedelta(days=random.randint(5, 30)),
                planned_end_date=date.today() + timedelta(days=random.randint(60, 180)),
                actual_start_date=date.today() - timedelta(days=random.randint(0, 20)) if stage != "S2" else None,
                contract_amount=opp.est_amount,
                budget_amount=opp.est_amount * Decimal("0.75"),
                actual_cost=opp.est_amount * Decimal(str(random.uniform(0.3, 0.6))),
                pm_id=users["pm"].id,
                pm_name=users["pm"].real_name,
                priority=random.choice(["NORMAL", "HIGH", "URGENT"]),
                description=lead.demand_summary,
                requirements=lead.demand_summary,
                opportunity_id=opp.id,
                created_at=datetime.now() - timedelta(days=random.randint(5, 30))
            )
            db.add(project)
            db.flush()
            projects.append(project)

            # 创建设备
            machine = Machine(
                project_id=project.id,
                machine_code=f"PN{i+1:03d}",
                machine_name=f"{project.short_name}-01",
                machine_type=opp.equipment_type,
                stage=stage,
                status=project.status,
                health=health,
                progress_pct=project.progress_pct,
                planned_start_date=project.planned_start_date,
                planned_end_date=project.planned_end_date,
                actual_start_date=project.actual_start_date
            )
            db.add(machine)
            db.flush()

            # 创建项目里程碑
            milestone_templates = [
                {"name": "需求确认", "type": "REQUIREMENT_CONFIRMED", "days_offset": 5, "status": "COMPLETED"},
                {"name": "方案设计完成", "type": "DESIGN_COMPLETED", "days_offset": 20, "status": "COMPLETED" if stage != "S2" else "PENDING"},
                {"name": "BOM发布", "type": "BOM_RELEASED", "days_offset": 30, "status": "COMPLETED" if stage in ["S3", "S4", "S5", "S6"] else "PENDING"},
                {"name": "物料到齐", "type": "MATERIAL_ARRIVED", "days_offset": 60, "status": "COMPLETED" if stage in ["S4", "S5", "S6"] else "PENDING"},
                {"name": "机械加工完成", "type": "MACHINING_COMPLETED", "days_offset": 90, "status": "COMPLETED" if stage in ["S5", "S6"] else "PENDING"},
                {"name": "装配完成", "type": "ASSEMBLY_COMPLETED", "days_offset": 120, "status": "COMPLETED" if stage == "S6" else "PENDING"},
                {"name": "调试完成", "type": "DEBUG_COMPLETED", "days_offset": 150, "status": "PENDING"},
                {"name": "FAT验收通过", "type": "FAT_PASS", "days_offset": 180, "status": "PENDING"},
                {"name": "发货", "type": "SHIPPED", "days_offset": 200, "status": "PENDING"}
            ]

            for ms_template in milestone_templates:
                planned_date = project.planned_start_date + timedelta(days=ms_template["days_offset"])
                milestone = ProjectMilestone(
                    project_id=project.id,
                    milestone_code=f"{project.project_code}-{ms_template['type']}",
                    milestone_name=ms_template["name"],
                    milestone_type=ms_template["type"],
                    planned_date=planned_date,
                    actual_date=planned_date if ms_template["status"] == "COMPLETED" else None,
                    status=ms_template["status"],
                    is_key=ms_template["type"] in ["FAT_PASS", "SHIPPED"]
                )
                db.add(milestone)
            db.flush()

            # 创建收款计划
            payment_plans = [
                {"name": "预付款", "type": "ADVANCE", "ratio": Decimal("0.30"), "days": 0},
                {"name": "发货前付款", "type": "BEFORE_SHIPMENT", "ratio": Decimal("0.60"), "days": 180},
                {"name": "验收后尾款", "type": "ACCEPTANCE", "ratio": Decimal("0.10"), "days": 210}
            ]

            for pp_data in payment_plans:
                payment_plan = ProjectPaymentPlan(
                    project_id=project.id,
                    payment_no=payment_plans.index(pp_data) + 1,
                    payment_name=pp_data["name"],
                    payment_type=pp_data["type"],
                    payment_ratio=pp_data["ratio"] * 100,
                    planned_amount=project.contract_amount * pp_data["ratio"],
                    planned_date=project.planned_start_date + timedelta(days=pp_data["days"]),
                    status="PAID" if pp_data["type"] == "ADVANCE" else "PENDING"
                )
                db.add(payment_plan)
            db.flush()

            print(f"  ✓ 商机: {opp.opp_code} → 项目: {project.project_code} (阶段: {stage}, 健康度: {health})")
        else:
            print(f"  ✓ 商机: {opp.opp_code} (未签单)")

    db.flush()
    return opportunities, projects


def generate_production_data(db, projects, users):
    """生成生产数据"""
    print("\n生成生产数据...")

    # 创建车间
    workshops_data = [
        {"code": "WS001", "name": "机加车间", "type": "MACHINING"},
        {"code": "WS002", "name": "装配车间", "type": "ASSEMBLY"},
        {"code": "WS003", "name": "调试车间", "type": "DEBUGGING"}
    ]

    workshops = []
    for ws_data in workshops_data:
        # 检查是否已存在
        existing = db.query(Workshop).filter(Workshop.workshop_code == ws_data["code"]).first()
        if existing:
            workshops.append(existing)
            continue

        workshop = Workshop(
            workshop_code=ws_data["code"],
            workshop_name=ws_data["name"],
            workshop_type=ws_data["type"],
            manager_id=users["pm"].id,
            location=f"工厂{ws_data['name']}",
            capacity_hours=Decimal("160.00"),
            is_active=True
        )
        db.add(workshop)
        db.flush()
        workshops.append(workshop)

    # 创建工序字典
    processes_data = [
        {"code": "PROC001", "name": "铣削加工", "type": "MACHINING", "hours": Decimal("2.5")},
        {"code": "PROC002", "name": "车削加工", "type": "MACHINING", "hours": Decimal("1.5")},
        {"code": "PROC003", "name": "装配", "type": "ASSEMBLY", "hours": Decimal("4.0")},
        {"code": "PROC004", "name": "调试", "type": "DEBUGGING", "hours": Decimal("8.0")}
    ]

    processes = []
    for proc_data in processes_data:
        # 检查是否已存在
        existing = db.query(ProcessDict).filter(ProcessDict.process_code == proc_data["code"]).first()
        if existing:
            processes.append(existing)
            continue

        process = ProcessDict(
            process_code=proc_data["code"],
            process_name=proc_data["name"],
            process_type=proc_data["type"],
            standard_hours=proc_data["hours"],
            is_active=True
        )
        db.add(process)
        db.flush()
        processes.append(process)

    # 创建工人
    workers = []
    for i in range(5):
        worker_no = f"WK{i+1:03d}"
        # 检查是否已存在
        existing = db.query(Worker).filter(Worker.worker_no == worker_no).first()
        if existing:
            workers.append(existing)
            continue

        worker = Worker(
            worker_no=worker_no,
            worker_name=f"工人{i+1}",
            workshop_id=workshops[i % len(workshops)].id,
            position="操作工",
            skill_level=random.choice(["JUNIOR", "INTERMEDIATE", "SENIOR"]),
            phone=f"1380013800{i}",
            entry_date=date.today() - timedelta(days=random.randint(100, 1000)),
            status="ACTIVE",
            hourly_rate=Decimal(str(random.randint(25, 50))),
            is_active=True
        )
        db.add(worker)
        db.flush()
        workers.append(worker)

    # 为项目创建生产计划和工单
    work_orders = []
    for project in projects:
        # 为所有项目创建生产数据，根据阶段调整
        if project.stage in ["S3", "S4", "S5", "S6"]:  # 从采购备料开始
            # 创建生产计划
            plan = ProductionPlan(
                plan_no=f"PLAN{project.project_code}",
                plan_name=f"{project.project_name}生产计划",
                plan_type="WORKSHOP",
                project_id=project.id,
                workshop_id=workshops[0].id,
                plan_start_date=project.planned_start_date,
                plan_end_date=project.planned_end_date,
                status="EXECUTING",
                progress=random.randint(30, 80),
                created_by=users["pm"].id
            )
            db.add(plan)
            db.flush()

            # 创建工单（根据项目阶段创建不同数量的工单）
            proc_count = 2 if project.stage in ["S3", "S4"] else 3 if project.stage == "S5" else 1
            for j, proc in enumerate(processes[:proc_count]):  # 每个项目多个工单
                wo = WorkOrder(
                    work_order_no=f"WO{project.project_code}-{j+1:02d}",
                    task_name=f"{project.short_name}-{proc.process_name}",
                    task_type=proc.process_type,
                    project_id=project.id,
                    production_plan_id=plan.id,
                    process_id=proc.id,
                    workshop_id=workshops[j % len(workshops)].id,
                    # material_id=None,  # 不设置material_id避免外键问题
                    material_name=f"{project.short_name}物料-{j+1}",
                    specification=f"规格{j+1}",
                    plan_qty=random.randint(1, 5),
                    completed_qty=random.randint(0, 3),
                    qualified_qty=random.randint(0, 2),
                    standard_hours=proc.standard_hours,
                    actual_hours=proc.standard_hours * Decimal(str(random.uniform(0.5, 1.2))),
                    plan_start_date=project.planned_start_date + timedelta(days=j*5),
                    plan_end_date=project.planned_start_date + timedelta(days=(j+1)*5),
                    assigned_to=workers[j % len(workers)].id,
                    assigned_at=datetime.now() - timedelta(days=random.randint(1, 10)),
                    assigned_by=users["pm"].id,
                    status=random.choice(["ASSIGNED", "STARTED", "COMPLETED"]),
                    priority=random.choice(["NORMAL", "HIGH"]),
                    progress=random.randint(0, 100),
                    created_by=users["pm"].id
                )
                db.add(wo)
                db.flush()
                work_orders.append(wo)

                # 为工单创建报工记录
                if wo.status in ["STARTED", "COMPLETED"]:
                    # 开工报工
                    start_report = WorkReport(
                        report_no=f"WR{wo.work_order_no}-START",
                        work_order_id=wo.id,
                        worker_id=wo.assigned_to,
                        report_type="START",
                        report_time=wo.assigned_at or datetime.now() - timedelta(days=random.randint(1, 5)),
                        progress_percent=0,
                        work_hours=Decimal("0"),
                        status="APPROVED"
                    )
                    db.add(start_report)

                    # 如果已完成，添加完工报工
                    if wo.status == "COMPLETED":
                        complete_report = WorkReport(
                            report_no=f"WR{wo.work_order_no}-COMPLETE",
                            work_order_id=wo.id,
                            worker_id=wo.assigned_to,
                            report_type="COMPLETE",
                            report_time=wo.actual_end_time or datetime.now() - timedelta(days=random.randint(0, 2)),
                            progress_percent=100,
                            work_hours=wo.actual_hours,
                            completed_qty=wo.completed_qty,
                            qualified_qty=wo.qualified_qty,
                            defect_qty=max(0, wo.completed_qty - wo.qualified_qty) if wo.completed_qty else 0,
                            status="APPROVED"
                        )
                        db.add(complete_report)

    db.flush()
    print(f"  ✓ 创建 {len(workshops)} 个车间, {len(processes)} 个工序, {len(workers)} 个工人, {len(work_orders)} 个工单")

    db.flush()
    return workshops, processes, workers, work_orders


def generate_alert_and_exception_data(db, projects, users):
    """生成预警和异常数据"""
    print("\n生成预警和异常数据...")

    # 创建预警规则
    alert_rules = []
    rule_templates = [
        {
            "rule_code": "RULE001",
            "rule_name": "项目进度延期预警",
            "rule_type": "PROJECT_PROGRESS",
            "target_type": "PROJECT",
            "alert_level": "WARNING",
            "threshold_value": "7"
        },
        {
            "rule_code": "RULE002",
            "rule_name": "项目成本超支预警",
            "rule_type": "PROJECT_COST",
            "target_type": "PROJECT",
            "alert_level": "WARNING",
            "threshold_value": "10"
        },
        {
            "rule_code": "RULE003",
            "rule_name": "项目健康度下降预警",
            "rule_type": "PROJECT_HEALTH",
            "target_type": "PROJECT",
            "alert_level": "CRITICAL",
            "threshold_value": "H3"
        }
    ]

    for rule_data in rule_templates:
        # 检查是否已存在
        existing = db.query(AlertRule).filter(AlertRule.rule_code == rule_data["rule_code"]).first()
        if existing:
            alert_rules.append(existing)
            continue

        rule = AlertRule(
            rule_code=rule_data["rule_code"],
            rule_name=rule_data["rule_name"],
            rule_type=rule_data["rule_type"],
            target_type=rule_data["target_type"],
            condition_type="THRESHOLD",
            condition_operator=">=",
            threshold_value=rule_data["threshold_value"],
            alert_level=rule_data["alert_level"],
            is_enabled=True,
            is_system=True,
            created_by=users["pm"].id
        )
        db.add(rule)
        db.flush()
        alert_rules.append(rule)

    # 为项目创建预警记录
    alert_records = []
    for project in projects:
        # 根据项目健康度决定预警数量
        alert_probability = 0.3 if project.health == "H1" else 0.6 if project.health == "H2" else 0.9
        if random.random() < alert_probability:  # 根据健康度调整预警概率
            alert = AlertRecord(
                alert_no=f"ALT{project.project_code}{random.randint(1, 99)}",
                rule_id=alert_rules[0].id,
                target_type="PROJECT",
                target_id=project.id,
                target_no=project.project_code,
                target_name=project.project_name,
                project_id=project.id,
                alert_level=random.choice(["WARNING", "CRITICAL"]),
                alert_title=f"{project.project_name}进度延期预警",
                alert_content=f"项目{project.project_code}预计延期{random.randint(3, 10)}天，请及时处理。",
                triggered_at=datetime.now() - timedelta(days=random.randint(1, 5)),
                trigger_value=str(project.progress_pct),
                threshold_value="70",
                status=random.choice(["PENDING", "ACKNOWLEDGED", "RESOLVED"])
            )
            db.add(alert)
            db.flush()
            alert_records.append(alert)

    # 创建异常事件
    exceptions = []
    for project in projects:
        # 根据项目健康度决定异常数量
        exception_probability = 0.2 if project.health == "H1" else 0.5 if project.health == "H2" else 0.8
        if random.random() < exception_probability:  # 根据健康度调整异常概率
            exception = ExceptionEvent(
                event_no=f"EXC{project.project_code}{random.randint(1, 99)}",
                source_type="PROJECT",
                source_id=project.id,
                project_id=project.id,
                event_type=random.choice(["MATERIAL", "QUALITY", "PROCESS", "EQUIPMENT"]),
                severity=random.choice(["MINOR", "MAJOR", "CRITICAL"]),
                event_title=f"{project.project_name}物料异常",
                event_description="关键物料供应商交期延误，影响项目进度。",
                discovered_at=datetime.now() - timedelta(days=random.randint(1, 10)),
                discovered_by=users["pm"].id,
                impact_scope="PROJECT",
                impact_description="项目进度可能延期3-5天",
                schedule_impact=random.randint(3, 7),
                cost_impact=Decimal(str(random.randint(5000, 50000))),
                status=random.choice(["OPEN", "HANDLING", "RESOLVED"]),
                responsible_dept="采购部",
                responsible_user_id=users["pm"].id,
                due_date=date.today() + timedelta(days=random.randint(1, 7)),
                is_overdue=random.random() > 0.7
            )
            db.add(exception)
            db.flush()
            exceptions.append(exception)

    print(f"  ✓ 创建 {len(alert_rules)} 个预警规则, {len(alert_records)} 个预警记录, {len(exceptions)} 个异常事件")

    db.flush()
    return alert_rules, alert_records, exceptions


def generate_users_if_needed(db):
    """生成用户数据（如果不存在）"""
    print("\n检查用户数据...")

    users = {}
    user_templates = [
        {"username": "sales_zhang", "real_name": "张销售", "role": "销售", "dept": "销售部"},
        {"username": "pm_li", "real_name": "李项目经理", "role": "项目经理", "dept": "项目部"},
        {"username": "presale_wang", "real_name": "王售前工程师", "role": "售前工程师", "dept": "技术部"},
        {"username": "mech_wang", "real_name": "王机械工程师", "role": "机械工程师", "dept": "技术部"},
        {"username": "elec_zhao", "real_name": "赵电气工程师", "role": "电气工程师", "dept": "技术部"}
    ]

    from app.core.security import get_password_hash

    for user_template in user_templates:
        user = db.query(User).filter(User.username == user_template["username"]).first()
        if not user:
            # 先创建员工记录
            emp = db.query(Employee).filter(Employee.employee_code == f"EMP{user_template['username'][-1].upper()}").first()
            if not emp:
                emp = Employee(
                    employee_code=f"EMP{user_template['username'][-1].upper()}",
                    name=user_template["real_name"],
                    department=user_template["dept"],
                    role=user_template["role"],
                    is_active=True
                )
                db.add(emp)
                db.flush()

            user = User(
                employee_id=emp.id,
                username=user_template["username"],
                real_name=user_template["real_name"],
                email=f"{user_template['username']}@company.com",
                password_hash=get_password_hash("123456"),
                is_active=True
            )
            db.add(user)
            db.flush()

        # 统一使用英文key
        role_key_map = {
            "销售": "sales",
            "项目经理": "pm",
            "售前工程师": "presale",
            "机械工程师": "mech",
            "电气工程师": "elec"
        }
        key = role_key_map.get(user_template["role"], user_template["role"].lower())
        users[key] = user
        print(f"  ✓ {user.real_name} ({user.username})")

    db.flush()
    return users


def main():
    """主函数"""
    print("=" * 80)
    print("生成全面、真实度高的测试数据")
    print("=" * 80)

    with get_db_session() as db:
        try:
            # 1. 生成用户
            users = generate_users_if_needed(db)

            # 2. 生成客户
            customers = generate_customers(db, count=5)

            # 3. 生成失败案例
            failure_cases = generate_failure_cases(db, users)

            # 4. 生成销售线索和技术评估
            leads, assessments = generate_leads_with_assessments(db, customers, users)

            # 5. 生成商机和项目
            opportunities, projects = generate_opportunities_and_projects(db, customers, leads, users)

            # 6. 生成生产数据
            workshops, processes, workers, work_orders = generate_production_data(db, projects, users)

            # 7. 生成预警和异常数据
            alert_rules, alert_records, exceptions = generate_alert_and_exception_data(db, projects, users)

            db.commit()

            print("\n" + "=" * 80)
            print("数据生成完成！")
            print("=" * 80)
            print(f"\n生成的数据概览：")
            print(f"  - 客户: {len(customers)} 个")
            print(f"  - 失败案例: {len(failure_cases)} 个")
            print(f"  - 销售线索: {len(leads)} 个")
            print(f"  - 技术评估: {len(assessments)} 个")
            print(f"  - 商机: {len(opportunities)} 个")
            print(f"  - 项目: {len(projects)} 个")
            print(f"  - 车间: {len(workshops)} 个")
            print(f"  - 工序: {len(processes)} 个")
            print(f"  - 工人: {len(workers)} 个")
            print(f"  - 工单: {len(work_orders)} 个")
            print(f"  - 预警规则: {len(alert_rules)} 个")
            print(f"  - 预警记录: {len(alert_records)} 个")
            print(f"  - 异常事件: {len(exceptions)} 个")
            print(f"\n数据已保存到数据库！")

        except Exception as e:
            db.rollback()
            print(f"\n错误: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    main()
