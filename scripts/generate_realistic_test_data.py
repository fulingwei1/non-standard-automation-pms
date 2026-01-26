#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成真实度高的测试数据脚本
从销售到项目到设备到物料到产品到发货的完整业务流程
包括产品分解给工程师的任务

使用方法:
    python3 scripts/generate_realistic_test_data.py
"""

import os
import random
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.acceptance import AcceptanceOrder, AcceptanceOrderItem
from app.models.base import get_db_session
from app.models.business_support import InvoiceRequest
from app.models.material import (
    BomHeader,
    BomItem,
    Material,
    MaterialCategory,
    MaterialSupplier,
)
from app.models.organization import Department, Employee
from app.models.progress import Task
from app.models.project import (
    Customer,
    Machine,
    Project,
    ProjectMilestone,
    ProjectPaymentPlan,
)
from app.models.purchase import GoodsReceipt, PurchaseOrder, PurchaseOrderItem
from app.models.sales import Contract, Invoice, Lead, Opportunity, Quote, QuoteItem
from app.models.user import Role, User, UserRole
from app.models.vendor import Vendor


def generate_customer_data(db):
    """生成客户数据"""
    print("生成客户数据...")

    customer = Customer(
        customer_code="CUST202501001",
        customer_name="深圳智行新能源汽车电子有限公司",
        short_name="智行新能源",
        customer_type="企业客户",
        industry="新能源汽车电子",
        scale="大型",
        address="深圳市龙华区观澜街道高新技术产业园A座15层",
        contact_person="王总",
        contact_phone="0755-88888888",
        contact_email="wang.zong@zhixingev.com",
        legal_person="王明",
        tax_no="91440300MA5F8K9X2L",
        bank_name="中国工商银行深圳分行",
        bank_account="4000021234567890123",
        credit_level="A",
        credit_limit=Decimal("5000000.00"),
        payment_terms="30%预付款，60%发货前，10%验收后",
        status="ACTIVE"
    )
    db.add(customer)
    db.flush()

    print(f"  ✓ 创建客户: {customer.customer_name} (ID: {customer.id})")
    return customer


def generate_users_data(db):
    """生成用户数据（如果不存在）"""
    print("检查用户数据...")

    # 检查或创建员工记录（User需要employee_id）

    # 销售
    sales_user = db.query(User).filter(User.username == "sales_zhang").first()
    if not sales_user:
        from app.core.security import get_password_hash

        # 先创建员工记录
        sales_emp = db.query(Employee).filter(Employee.employee_code == "EMP001").first()
        if not sales_emp:
            sales_emp = Employee(
                employee_code="EMP001",
                name="张销售",
                department="销售部",
                role="销售经理"
            )
            db.add(sales_emp)
            db.flush()

        sales_user = User(
            employee_id=sales_emp.id,
            username="sales_zhang",
            real_name="张销售",
            email="zhang.sales@company.com",
            password_hash=get_password_hash("sales123"),
            is_active=True
        )
        db.add(sales_user)
        db.flush()

    # 项目经理
    pm_user = db.query(User).filter(User.username == "pm_li").first()
    if not pm_user:
        from app.core.security import get_password_hash
        pm_emp = db.query(Employee).filter(Employee.employee_code == "EMP002").first()
        if not pm_emp:
            pm_emp = Employee(
                employee_code="EMP002",
                name="李项目经理",
                department="项目部",
                role="项目经理"
            )
            db.add(pm_emp)
            db.flush()

        pm_user = User(
            employee_id=pm_emp.id,
            username="pm_li",
            real_name="李项目经理",
            email="li.pm@company.com",
            password_hash=get_password_hash("pm123"),
            is_active=True
        )
        db.add(pm_user)
        db.flush()

    # 机械工程师
    mech_user = db.query(User).filter(User.username == "mech_wang").first()
    if not mech_user:
        from app.core.security import get_password_hash
        mech_emp = db.query(Employee).filter(Employee.employee_code == "EMP003").first()
        if not mech_emp:
            mech_emp = Employee(
                employee_code="EMP003",
                name="王机械工程师",
                department="技术部",
                role="机械工程师"
            )
            db.add(mech_emp)
            db.flush()

        mech_user = User(
            employee_id=mech_emp.id,
            username="mech_wang",
            real_name="王机械工程师",
            email="wang.mech@company.com",
            password_hash=get_password_hash("mech123"),
            is_active=True
        )
        db.add(mech_user)
        db.flush()

    # 电气工程师
    elec_user = db.query(User).filter(User.username == "elec_zhao").first()
    if not elec_user:
        from app.core.security import get_password_hash
        elec_emp = db.query(Employee).filter(Employee.employee_code == "EMP004").first()
        if not elec_emp:
            elec_emp = Employee(
                employee_code="EMP004",
                name="赵电气工程师",
                department="技术部",
                role="电气工程师"
            )
            db.add(elec_emp)
            db.flush()

        elec_user = User(
            employee_id=elec_emp.id,
            username="elec_zhao",
            real_name="赵电气工程师",
            email="zhao.elec@company.com",
            password_hash=get_password_hash("elec123"),
            is_active=True
        )
        db.add(elec_user)
        db.flush()

    # 软件工程师
    soft_user = db.query(User).filter(User.username == "soft_chen").first()
    if not soft_user:
        from app.core.security import get_password_hash
        soft_emp = db.query(Employee).filter(Employee.employee_code == "EMP005").first()
        if not soft_emp:
            soft_emp = Employee(
                employee_code="EMP005",
                name="陈软件工程师",
                department="技术部",
                role="软件工程师"
            )
            db.add(soft_emp)
            db.flush()

        soft_user = User(
            employee_id=soft_emp.id,
            username="soft_chen",
            real_name="陈软件工程师",
            email="chen.soft@company.com",
            password_hash=get_password_hash("soft123"),
            is_active=True
        )
        db.add(soft_user)
        db.flush()

    print(f"  ✓ 销售: {sales_user.real_name} (ID: {sales_user.id})")
    print(f"  ✓ 项目经理: {pm_user.real_name} (ID: {pm_user.id})")
    print(f"  ✓ 机械工程师: {mech_user.real_name} (ID: {mech_user.id})")
    print(f"  ✓ 电气工程师: {elec_user.real_name} (ID: {elec_user.id})")
    print(f"  ✓ 软件工程师: {soft_user.real_name} (ID: {soft_user.id})")

    return {
        "sales": sales_user,
        "pm": pm_user,
        "mech": mech_user,
        "elec": elec_user,
        "soft": soft_user
    }


def generate_sales_flow(db, customer, users):
    """生成销售流程数据：线索 → 商机 → 报价 → 合同"""
    print("\n生成销售流程数据...")

    # 1. 线索
    lead = Lead(
        lead_code="LD202501001",
        source="展会",
        customer_name=customer.customer_name,
        industry="新能源汽车电子",
        contact_name="王总",
        contact_phone="0755-88888888",
        demand_summary="需要BMS（电池管理系统）FCT功能测试设备，要求：\n"
                      "1. 支持8通道同时测试\n"
                      "2. 测试精度：电压±0.1%，电流±0.2%\n"
                      "3. 节拍要求：≤15秒/件\n"
                      "4. 支持CAN总线通信\n"
                      "5. 具备数据记录和追溯功能",
        owner_id=users["sales"].id,
        status="CONVERTED",
        created_at=datetime(2025, 1, 5, 10, 0, 0)
    )
    db.add(lead)
    db.flush()
    print(f"  ✓ 创建线索: {lead.lead_code}")

    # 2. 商机
    opportunity = Opportunity(
        opp_code="OPP202501001",
        lead_id=lead.id,
        customer_id=customer.id,
        opp_name="智行新能源BMS FCT测试设备项目",
        project_type="FIXED_PRICE",
        equipment_type="FCT",
        stage="PROPOSAL",
        est_amount=Decimal("2800000.00"),
        est_margin=Decimal("25.5"),
        budget_range="250-300万",
        decision_chain="技术总监 → 采购总监 → 总经理",
        delivery_window="2025年Q2",
        acceptance_basis="1. 通过客户FAT验收\n2. 满足技术规格要求\n3. 提供完整技术文档",
        score=85,
        risk_level="LOW",
        owner_id=users["sales"].id,
        gate_status="PASSED",
        gate_passed_at=datetime(2025, 1, 10, 14, 0, 0),
        created_at=datetime(2025, 1, 8, 9, 0, 0)
    )
    db.add(opportunity)
    db.flush()
    print(f"  ✓ 创建商机: {opportunity.opp_code}")

    # 3. 报价
    quote = Quote(
        quote_code="QT202501001",
        opportunity_id=opportunity.id,
        customer_id=customer.id,
        quote_name="智行新能源BMS FCT测试设备报价",
        quote_type="STANDARD",
        version_number=1,
        total_amount=Decimal("2800000.00"),
        tax_rate=Decimal("13.00"),
        tax_amount=Decimal("364000.00"),
        total_amount_with_tax=Decimal("3164000.00"),
        valid_until=date(2025, 2, 15),
        status="APPROVED",
        created_by=users["sales"].id,
        created_at=datetime(2025, 1, 12, 10, 0, 0)
    )
    db.add(quote)
    db.flush()

    # 报价明细
    quote_items = [
        {
            "item_name": "BMS FCT测试设备主机",
            "item_type": "EQUIPMENT",
            "specification": "8通道，精度±0.1%",
            "quantity": Decimal("1.00"),
            "unit_price": Decimal("1800000.00"),
            "amount": Decimal("1800000.00")
        },
        {
            "item_name": "测试治具",
            "item_type": "FIXTURE",
            "specification": "定制化，适配客户产品",
            "quantity": Decimal("8.00"),
            "unit_price": Decimal("50000.00"),
            "amount": Decimal("400000.00")
        },
        {
            "item_name": "上位机软件",
            "item_type": "SOFTWARE",
            "specification": "测试程序、数据管理",
            "quantity": Decimal("1.00"),
            "unit_price": Decimal("200000.00"),
            "amount": Decimal("200000.00")
        },
        {
            "item_name": "安装调试服务",
            "item_type": "SERVICE",
            "specification": "现场安装、调试、培训",
            "quantity": Decimal("1.00"),
            "unit_price": Decimal("200000.00"),
            "amount": Decimal("200000.00")
        },
        {
            "item_name": "质保服务",
            "item_type": "SERVICE",
            "specification": "1年质保，免费维护",
            "quantity": Decimal("1.00"),
            "unit_price": Decimal("200000.00"),
            "amount": Decimal("200000.00")
        }
    ]

    for item_data in quote_items:
        item = QuoteItem(
            quote_id=quote.id,
            item_name=item_data["item_name"],
            item_type=item_data["item_type"],
            specification=item_data["specification"],
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            amount=item_data["amount"]
        )
        db.add(item)
    db.flush()
    print(f"  ✓ 创建报价: {quote.quote_code} (含{len(quote_items)}项明细)")

    # 4. 合同
    contract = Contract(
        contract_code="CT202501001",
        opportunity_id=opportunity.id,
        quote_id=quote.id,
        customer_id=customer.id,
        contract_name="智行新能源BMS FCT测试设备采购合同",
        contract_type="SALES",
        total_amount=Decimal("2800000.00"),
        tax_rate=Decimal("13.00"),
        tax_amount=Decimal("364000.00"),
        total_amount_with_tax=Decimal("3164000.00"),
        currency="CNY",
        sign_date=date(2025, 1, 20),
        signer_name="王明",
        delivery_date=date(2025, 5, 30),
        payment_terms="30%预付款，60%发货前，10%验收后",
        status="SIGNED",
        owner_id=users["sales"].id,
        created_at=datetime(2025, 1, 20, 15, 0, 0)
    )
    db.add(contract)
    db.flush()

    # 合同明细（合同模型可能不包含明细表，使用备注记录）
    contract_items_summary = "\n".join([
        f"{i+1}. {item['item_name']} - {item['specification']} - 数量:{item['quantity']} - 金额:¥{item['amount']:,.2f}"
        for i, item in enumerate(quote_items)
    ])
    contract.remark = f"合同明细：\n{contract_items_summary}"
    print(f"  ✓ 创建合同: {contract.contract_code}")

    return {
        "lead": lead,
        "opportunity": opportunity,
        "quote": quote,
        "contract": contract
    }


def generate_project_data(db, customer, contract, users):
    """生成项目数据"""
    print("\n生成项目数据...")

    project = Project(
        project_code="PJ250120001",
        project_name="智行新能源BMS FCT测试设备项目",
        short_name="智行BMS测试",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        customer_contact="王总",
        customer_phone="0755-88888888",
        contract_no=contract.contract_code,
        project_type="FIXED_PRICE",
        product_category="FCT测试设备",
        industry="新能源汽车电子",
        project_category="销售",
        stage="S3",  # 采购备料阶段
        status="ST13",  # 采购备料中
        health="H1",  # 正常
        progress_pct=Decimal("25.00"),
        contract_date=date(2025, 1, 20),
        planned_start_date=date(2025, 1, 25),
        planned_end_date=date(2025, 5, 30),
        actual_start_date=date(2025, 1, 25),
        contract_amount=Decimal("2800000.00"),
        budget_amount=Decimal("2100000.00"),
        pm_id=users["pm"].id,
        pm_name=users["pm"].full_name,
        priority="HIGH",
        description="为智行新能源开发BMS FCT功能测试设备，支持8通道同时测试，"
                   "测试精度要求高，节拍≤15秒/件，具备完整的数据记录和追溯功能。",
        requirements="1. 支持8通道同时测试\n"
                     "2. 测试精度：电压±0.1%，电流±0.2%\n"
                     "3. 节拍要求：≤15秒/件\n"
                     "4. 支持CAN总线通信\n"
                     "5. 具备数据记录和追溯功能\n"
                     "6. 通过客户FAT验收",
        opportunity_id=contract.opportunity_id,
        contract_id=contract.id,
        created_at=datetime(2025, 1, 22, 9, 0, 0)
    )
    db.add(project)
    db.flush()
    print(f"  ✓ 创建项目: {project.project_code}")

    # 项目里程碑
    milestones_data = [
        {
            "milestone_name": "需求确认",
            "milestone_type": "REQUIREMENT_CONFIRMED",
            "planned_date": date(2025, 1, 30),
            "actual_date": date(2025, 1, 28),
            "status": "COMPLETED"
        },
        {
            "milestone_name": "方案设计完成",
            "milestone_type": "DESIGN_COMPLETED",
            "planned_date": date(2025, 2, 15),
            "actual_date": date(2025, 2, 12),
            "status": "COMPLETED"
        },
        {
            "milestone_name": "BOM发布",
            "milestone_type": "BOM_RELEASED",
            "planned_date": date(2025, 2, 20),
            "actual_date": date(2025, 2, 18),
            "status": "COMPLETED"
        },
        {
            "milestone_name": "物料到齐",
            "milestone_type": "MATERIAL_ARRIVED",
            "planned_date": date(2025, 3, 15),
            "actual_date": None,
            "status": "IN_PROGRESS"
        },
        {
            "milestone_name": "机械加工完成",
            "milestone_type": "MACHINING_COMPLETED",
            "planned_date": date(2025, 4, 10),
            "actual_date": None,
            "status": "PENDING"
        },
        {
            "milestone_name": "装配完成",
            "milestone_type": "ASSEMBLY_COMPLETED",
            "planned_date": date(2025, 4, 25),
            "actual_date": None,
            "status": "PENDING"
        },
        {
            "milestone_name": "调试完成",
            "milestone_type": "DEBUG_COMPLETED",
            "planned_date": date(2025, 5, 10),
            "actual_date": None,
            "status": "PENDING"
        },
        {
            "milestone_name": "FAT验收通过",
            "milestone_type": "FAT_PASS",
            "planned_date": date(2025, 5, 20),
            "actual_date": None,
            "status": "PENDING"
        },
        {
            "milestone_name": "发货",
            "milestone_type": "SHIPPED",
            "planned_date": date(2025, 5, 30),
            "actual_date": None,
            "status": "PENDING"
        }
    ]

    milestones = []
    for ms_data in milestones_data:
        milestone = ProjectMilestone(
            project_id=project.id,
            milestone_name=ms_data["milestone_name"],
            milestone_type=ms_data["milestone_type"],
            planned_date=ms_data["planned_date"],
            actual_date=ms_data["actual_date"],
            status=ms_data["status"]
        )
        db.add(milestone)
        milestones.append(milestone)
    db.flush()
    print(f"  ✓ 创建{len(milestones)}个里程碑")

    # 收款计划
    payment_plans_data = [
        {
            "payment_name": "预付款",
            "payment_type": "ADVANCE",
            "planned_amount": Decimal("840000.00"),  # 30%
            "planned_date": date(2025, 1, 25),
            "actual_date": date(2025, 1, 25),
            "status": "PAID"
        },
        {
            "payment_name": "发货前付款",
            "payment_type": "BEFORE_SHIPMENT",
            "planned_amount": Decimal("1680000.00"),  # 60%
            "planned_date": date(2025, 5, 25),
            "actual_date": None,
            "status": "PENDING"
        },
        {
            "payment_name": "验收后尾款",
            "payment_type": "ACCEPTANCE",
            "planned_amount": Decimal("280000.00"),  # 10%
            "planned_date": date(2025, 6, 15),
            "actual_date": None,
            "status": "PENDING"
        }
    ]

    for pp_data in payment_plans_data:
        payment_plan = ProjectPaymentPlan(
            project_id=project.id,
            contract_id=contract.id,
            payment_name=pp_data["payment_name"],
            payment_type=pp_data["payment_type"],
            planned_amount=pp_data["planned_amount"],
            planned_date=pp_data["planned_date"],
            actual_date=pp_data["actual_date"],
            status=pp_data["status"]
        )
        db.add(payment_plan)
    db.flush()
    print(f"  ✓ 创建{len(payment_plans_data)}个收款计划")

    return project


def generate_machine_data(db, project):
    """生成设备数据"""
    print("\n生成设备数据...")

    machine = Machine(
        project_id=project.id,
        machine_code="PN001",
        machine_name="智行BMS FCT测试设备-01",
        machine_type="FCT",
        equipment_type="FCT",
        stage="S3",  # 采购备料阶段
        status="ST13",
        health="H1",
        planned_start_date=date(2025, 1, 25),
        planned_end_date=date(2025, 5, 30),
        actual_start_date=date(2025, 1, 25),
        description="8通道BMS FCT功能测试设备，支持CAN总线通信，"
                   "测试精度：电压±0.1%，电流±0.2%，节拍≤15秒/件"
    )
    db.add(machine)
    db.flush()
    print(f"  ✓ 创建设备: {machine.machine_code}")

    return machine


def generate_material_data(db):
    """生成物料数据"""
    print("\n生成物料数据...")

    # 物料分类
    categories = {}
    category_data = [
        {"code": "CAT001", "name": "机械件", "parent": None},
        {"code": "CAT002", "name": "电气件", "parent": None},
        {"code": "CAT003", "name": "标准件", "parent": None},
        {"code": "CAT004", "name": "气动件", "parent": None},
        {"code": "CAT005", "name": "机加工件", "parent": "CAT001"},
        {"code": "CAT006", "name": "钣金件", "parent": "CAT001"},
    ]

    for cat_data in category_data:
        category = MaterialCategory(
            category_code=cat_data["code"],
            category_name=cat_data["name"],
            parent_id=categories.get(cat_data["parent"]) if cat_data["parent"] else None,
            level=1 if not cat_data["parent"] else 2,
            is_active=True
        )
        db.add(category)
        db.flush()
        categories[cat_data["code"]] = category.id

    # 供应商
    suppliers = {}
    supplier_data = [
        {
            "code": "SUP001",
            "name": "深圳精密机械加工有限公司",
            "type": "机加工",
            "contact": "李经理",
            "phone": "0755-12345678"
        },
        {
            "code": "SUP002",
            "name": "东莞电气元件供应商",
            "type": "电气",
            "contact": "张经理",
            "phone": "0769-87654321"
        },
        {
            "code": "SUP003",
            "name": "上海标准件贸易公司",
            "type": "标准件",
            "contact": "王经理",
            "phone": "021-11223344"
        }
    ]

    for sup_data in supplier_data:
        supplier = Vendor(
            supplier_code=sup_data["code"],
            supplier_name=sup_data["name"],
            supplier_type=sup_data["type"],
            vendor_type="MATERIAL",
            contact_person=sup_data["contact"],
            contact_phone=sup_data["phone"],
            status="ACTIVE"
        )
        db.add(supplier)
        db.flush()
        suppliers[sup_data["code"]] = supplier

    # 物料
    materials = {}
    material_data = [
        # 机械件
        {
            "code": "MAT001",
            "name": "设备底座",
            "category": "CAT005",
            "type": "MACHINING",
            "spec": "6061铝合金，800×600×50mm",
            "unit": "件",
            "price": Decimal("3500.00"),
            "supplier": "SUP001"
        },
        {
            "code": "MAT002",
            "name": "测试平台",
            "category": "CAT005",
            "type": "MACHINING",
            "spec": "45#钢，表面镀铬，1200×800×30mm",
            "unit": "件",
            "price": Decimal("5800.00"),
            "supplier": "SUP001"
        },
        {
            "code": "MAT003",
            "name": "设备外壳",
            "category": "CAT006",
            "type": "SHEET_METAL",
            "spec": "2mm冷轧钢板，喷塑",
            "unit": "套",
            "price": Decimal("4200.00"),
            "supplier": "SUP001"
        },
        # 电气件
        {
            "code": "MAT004",
            "name": "PLC控制器",
            "category": "CAT002",
            "type": "ELECTRICAL",
            "spec": "西门子S7-1200，CPU 1214C",
            "unit": "台",
            "price": Decimal("3500.00"),
            "supplier": "SUP002"
        },
        {
            "code": "MAT005",
            "name": "HMI触摸屏",
            "category": "CAT002",
            "type": "ELECTRICAL",
            "spec": "威纶通MT8102iE，10.1寸",
            "unit": "台",
            "price": Decimal("2800.00"),
            "supplier": "SUP002"
        },
        {
            "code": "MAT006",
            "name": "测试工装板",
            "category": "CAT002",
            "type": "ELECTRICAL",
            "spec": "8通道，定制化设计",
            "unit": "套",
            "price": Decimal("12000.00"),
            "supplier": "SUP002"
        },
        {
            "code": "MAT007",
            "name": "CAN总线模块",
            "category": "CAT002",
            "type": "ELECTRICAL",
            "spec": "CANopen协议，8通道",
            "unit": "套",
            "price": Decimal("4500.00"),
            "supplier": "SUP002"
        },
        {
            "code": "MAT008",
            "name": "电源模块",
            "category": "CAT002",
            "type": "ELECTRICAL",
            "spec": "24V/10A开关电源",
            "unit": "台",
            "price": Decimal("380.00"),
            "supplier": "SUP002"
        },
        # 标准件
        {
            "code": "MAT009",
            "name": "直线导轨",
            "category": "CAT003",
            "type": "STANDARD",
            "spec": "THK HRW21，长度1000mm",
            "unit": "根",
            "price": Decimal("1200.00"),
            "supplier": "SUP003"
        },
        {
            "code": "MAT010",
            "name": "伺服电机",
            "category": "CAT003",
            "type": "STANDARD",
            "spec": "安川SGMJV-08ADA6S，750W",
            "unit": "台",
            "price": Decimal("3200.00"),
            "supplier": "SUP003"
        },
        {
            "code": "MAT011",
            "name": "气缸",
            "category": "CAT004",
            "type": "PNEUMATIC",
            "spec": "SMC CDM2B25-50，双作用",
            "unit": "个",
            "price": Decimal("280.00"),
            "supplier": "SUP003"
        }
    ]

    for mat_data in material_data:
        material = Material(
            material_code=mat_data["code"],
            material_name=mat_data["name"],
            category_id=categories[mat_data["category"]],
            material_type=mat_data["type"],
            specification=mat_data["spec"],
            unit=mat_data["unit"],
            standard_price=mat_data["price"],
            last_price=mat_data["price"],
            default_supplier_id=suppliers[mat_data["supplier"]].id,
            is_active=True
        )
        db.add(material)
        db.flush()
        materials[mat_data["code"]] = material

        # 物料供应商关联
        mat_supplier = MaterialSupplier(
            material_id=material.id,
            supplier_id=suppliers[mat_data["supplier"]].id,
            is_default=True,
            price=mat_data["price"],
            lead_time_days=15
        )
        db.add(mat_supplier)

    db.flush()
    print(f"  ✓ 创建{len(materials)}个物料")

    return materials, suppliers


def generate_bom_data(db, project, machine, materials):
    """生成BOM数据"""
    print("\n生成BOM数据...")

    bom_header = BomHeader(
        project_id=project.id,
        machine_id=machine.id,
        bom_code=f"BOM-{machine.machine_code}",
        bom_name=f"{machine.machine_name}物料清单",
        version="V1.0",
        status="RELEASED",
        created_at=datetime(2025, 2, 18, 10, 0, 0)
    )
    db.add(bom_header)
    db.flush()

    # BOM明细
    bom_items_data = [
        {"material": "MAT001", "qty": 1, "level": 1, "remark": "设备底座"},
        {"material": "MAT002", "qty": 1, "level": 1, "remark": "测试平台"},
        {"material": "MAT003", "qty": 1, "level": 1, "remark": "设备外壳"},
        {"material": "MAT004", "qty": 1, "level": 1, "remark": "PLC控制器"},
        {"material": "MAT005", "qty": 1, "level": 1, "remark": "HMI触摸屏"},
        {"material": "MAT006", "qty": 1, "level": 1, "remark": "测试工装板（8通道）"},
        {"material": "MAT007", "qty": 1, "level": 1, "remark": "CAN总线模块"},
        {"material": "MAT008", "qty": 2, "level": 1, "remark": "电源模块"},
        {"material": "MAT009", "qty": 2, "level": 1, "remark": "直线导轨"},
        {"material": "MAT010", "qty": 1, "level": 1, "remark": "伺服电机"},
        {"material": "MAT011", "qty": 4, "level": 1, "remark": "气缸"}
    ]

    for item_data in bom_items_data:
        material = materials[item_data["material"]]
        bom_item = BomItem(
            bom_header_id=bom_header.id,
            material_id=material.id,
            material_code=material.material_code,
            material_name=material.material_name,
            specification=material.specification,
            quantity=Decimal(str(item_data["qty"])),
            unit=material.unit,
            unit_price=material.standard_price,
            total_price=material.standard_price * Decimal(str(item_data["qty"])),
            level=item_data["level"],
            remark=item_data["remark"]
        )
        db.add(bom_item)

    db.flush()
    print(f"  ✓ 创建BOM: {bom_header.bom_code} (含{len(bom_items_data)}项)")

    return bom_header


def generate_purchase_orders(db, bom_header, suppliers):
    """生成采购订单"""
    print("\n生成采购订单...")

    # 按供应商分组物料
    supplier_items = {}
    for item in bom_header.items:
        material = item.material
        supplier_id = material.default_supplier_id
        if supplier_id not in supplier_items:
            supplier_items[supplier_id] = []
        supplier_items[supplier_id].append(item)

    purchase_orders = []
    for supplier_id, items in supplier_items.items():
        supplier = next(s for s in suppliers.values() if s.id == supplier_id)

        po = PurchaseOrder(
            po_code=f"PO202502{len(purchase_orders)+1:03d}",
            supplier_id=supplier_id,
            project_id=bom_header.project_id,
            machine_id=bom_header.machine_id,
            bom_header_id=bom_header.id,
            total_amount=sum(item.total_price for item in items),
            status="CONFIRMED",
            order_date=date(2025, 2, 20),
            expected_delivery_date=date(2025, 3, 15),
            created_at=datetime(2025, 2, 20, 14, 0, 0)
        )
        db.add(po)
        db.flush()

        for item in items:
            po_item = PurchaseOrderItem(
                purchase_order_id=po.id,
                material_id=item.material_id,
                material_code=item.material_code,
                material_name=item.material_name,
                specification=item.specification,
                quantity=item.quantity,
                unit=item.unit,
                unit_price=item.unit_price,
                total_price=item.total_price
            )
            db.add(po_item)

        purchase_orders.append(po)
        print(f"  ✓ 创建采购订单: {po.po_code} (供应商: {supplier.supplier_name})")

    db.flush()
    return purchase_orders


def generate_tasks(db, project, machine, users):
    """生成工程师任务"""
    print("\n生成工程师任务...")

    tasks_data = [
        {
            "title": "设备底座和测试平台机械设计",
            "description": "完成设备底座（800×600×50mm，6061铝合金）和测试平台（1200×800×30mm，45#钢）的3D设计和2D工程图",
            "task_type": "DESIGN",
            "assignee": users["mech"],
            "priority": "HIGH",
            "due_date": date(2025, 2, 10),
            "status": "COMPLETED"
        },
        {
            "title": "设备外壳钣金设计",
            "description": "完成设备外壳的钣金设计，包括门板、侧板、顶板等，考虑散热和维修便利性",
            "task_type": "DESIGN",
            "assignee": users["mech"],
            "priority": "MEDIUM",
            "due_date": date(2025, 2, 15),
            "status": "COMPLETED"
        },
        {
            "title": "电气原理图设计",
            "description": "完成PLC、HMI、测试工装板、CAN总线模块、电源模块的电气原理图设计，包括接线图和端子图",
            "task_type": "DESIGN",
            "assignee": users["elec"],
            "priority": "HIGH",
            "due_date": date(2025, 2, 12),
            "status": "COMPLETED"
        },
        {
            "title": "测试工装板电路设计",
            "description": "设计8通道测试工装板电路，包括信号调理、CAN通信接口、保护电路等",
            "task_type": "DESIGN",
            "assignee": users["elec"],
            "priority": "HIGH",
            "due_date": date(2025, 2, 18),
            "status": "IN_PROGRESS"
        },
        {
            "title": "上位机软件架构设计",
            "description": "设计上位机软件架构，包括测试程序、数据管理、报表生成等模块",
            "task_type": "DESIGN",
            "assignee": users["soft"],
            "priority": "HIGH",
            "due_date": date(2025, 2, 15),
            "status": "COMPLETED"
        },
        {
            "title": "测试程序开发",
            "description": "开发BMS FCT测试程序，实现8通道同时测试，测试精度：电压±0.1%，电流±0.2%，节拍≤15秒/件",
            "task_type": "DEVELOPMENT",
            "assignee": users["soft"],
            "priority": "HIGH",
            "due_date": date(2025, 4, 30),
            "status": "IN_PROGRESS"
        },
        {
            "title": "CAN总线通信程序开发",
            "description": "开发CAN总线通信程序，实现与BMS设备的CANopen协议通信",
            "task_type": "DEVELOPMENT",
            "assignee": users["soft"],
            "priority": "HIGH",
            "due_date": date(2025, 4, 25),
            "status": "IN_PROGRESS"
        },
        {
            "title": "数据记录和追溯功能开发",
            "description": "开发数据记录和追溯功能，包括测试数据存储、查询、报表导出等",
            "task_type": "DEVELOPMENT",
            "assignee": users["soft"],
            "priority": "MEDIUM",
            "due_date": date(2025, 5, 5),
            "status": "PENDING"
        }
    ]

    tasks = []
    for task_data in tasks_data:
        task = Task(
            project_id=project.id,
            machine_id=machine.id,
            task_name=task_data["title"],
            stage=project.stage,
            status="DONE" if task_data["status"] == "COMPLETED" else "IN_PROGRESS" if task_data["status"] == "IN_PROGRESS" else "TODO",
            owner_id=task_data["assignee"].id,
            plan_start=date(2025, 2, 1),
            plan_end=task_data["due_date"],
            actual_start=date(2025, 2, 1) if task_data["status"] != "PENDING" else None,
            actual_end=task_data["due_date"] if task_data["status"] == "COMPLETED" else None,
            progress_percent=100 if task_data["status"] == "COMPLETED" else 50 if task_data["status"] == "IN_PROGRESS" else 0,
            block_reason=None
        )
        db.add(task)
        tasks.append(task)

    db.flush()
    print(f"  ✓ 创建{len(tasks)}个工程师任务")

    return tasks


def main():
    """主函数"""
    print("=" * 60)
    print("生成真实度高的测试数据")
    print("=" * 60)

    with get_db_session() as db:
        try:
            # 1. 生成用户
            users = generate_users_data(db)

            # 2. 生成客户
            customer = generate_customer_data(db)

            # 3. 生成销售流程
            sales_data = generate_sales_flow(db, customer, users)

            # 4. 生成项目
            project = generate_project_data(db, customer, sales_data["contract"], users)

            # 5. 生成设备
            machine = generate_machine_data(db, project)

            # 6. 生成物料
            materials, suppliers = generate_material_data(db)

            # 7. 生成BOM
            bom_header = generate_bom_data(db, project, machine, materials)

            # 8. 生成采购订单
            purchase_orders = generate_purchase_orders(db, bom_header, suppliers)

            # 9. 生成工程师任务
            tasks = generate_tasks(db, project, machine, users)

            db.commit()

            print("\n" + "=" * 60)
            print("数据生成完成！")
            print("=" * 60)
            print(f"\n生成的数据概览：")
            print(f"  - 客户: {customer.customer_name}")
            print(f"  - 项目: {project.project_code} - {project.project_name}")
            print(f"  - 设备: {machine.machine_code} - {machine.machine_name}")
            print(f"  - 合同: {sales_data['contract'].contract_code}")
            print(f"  - BOM: {bom_header.bom_code}")
            print(f"  - 采购订单: {len(purchase_orders)}个")
            print(f"  - 工程师任务: {len(tasks)}个")
            print(f"\n数据已保存到数据库！")

        except Exception as e:
            db.rollback()
            print(f"\n错误: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    main()
