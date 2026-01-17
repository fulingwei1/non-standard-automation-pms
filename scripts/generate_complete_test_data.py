#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成完整测试数据脚本
生成S1-S9各个阶段的项目，包含所有模块的完整数据

使用方法:
    python3 scripts/generate_complete_test_data.py
"""

import json
import os
import random
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.acceptance import AcceptanceOrder, AcceptanceOrderItem
from app.models.base import get_db_session
from app.models.material import Material, MaterialCategory, MaterialSupplier, Supplier
from app.models.organization import Department, Employee
from app.models.progress import Task
from app.models.project import (
    Customer,
    Machine,
    Project,
    ProjectCost,
    ProjectDocument,
    ProjectMember,
    ProjectMilestone,
    ProjectPaymentPlan,
)
from app.models.purchase import GoodsReceipt, PurchaseOrder, PurchaseOrderItem
from app.models.sales import (
    Contract,
    Invoice,
    Lead,
    Opportunity,
    Quote,
    QuoteItem,
    QuoteVersion,
)
from app.models.user import User

# 物料分类数据
MATERIAL_CATEGORIES = [
    {"code": "ME", "name": "机械件", "children": [
        {"code": "ME01", "name": "机加工件"},
        {"code": "ME02", "name": "钣金件"},
        {"code": "ME03", "name": "标准件"},
    ]},
    {"code": "EL", "name": "电气件", "children": [
        {"code": "EL01", "name": "传感器"},
        {"code": "EL02", "name": "电机"},
        {"code": "EL03", "name": "控制器"},
        {"code": "EL04", "name": "线缆"},
    ]},
    {"code": "PN", "name": "气动件", "children": [
        {"code": "PN01", "name": "气缸"},
        {"code": "PN02", "name": "电磁阀"},
        {"code": "PN03", "name": "接头"},
    ]},
    {"code": "ST", "name": "标准件", "children": [
        {"code": "ST01", "name": "螺丝"},
        {"code": "ST02", "name": "轴承"},
        {"code": "ST03", "name": "导轨"},
    ]},
]

# 物料模板数据
MATERIAL_TEMPLATES = {
    "ME01": [
        {"name": "底板", "spec": "500x300x20mm", "price": 150.00},
        {"name": "侧板", "spec": "400x200x10mm", "price": 80.00},
        {"name": "顶板", "spec": "500x300x15mm", "price": 120.00},
    ],
    "EL01": [
        {"name": "压力传感器", "spec": "0-10bar", "price": 350.00},
        {"name": "温度传感器", "spec": "-20~80℃", "price": 280.00},
        {"name": "位置传感器", "spec": "M18", "price": 150.00},
    ],
    "EL02": [
        {"name": "步进电机", "spec": "57步进", "price": 450.00},
        {"name": "伺服电机", "spec": "750W", "price": 1200.00},
    ],
    "PN01": [
        {"name": "气缸", "spec": "SC50x100", "price": 280.00},
        {"name": "气缸", "spec": "SC32x50", "price": 180.00},
    ],
    "ST01": [
        {"name": "内六角螺丝", "spec": "M6x20", "price": 0.50},
        {"name": "内六角螺丝", "spec": "M8x30", "price": 0.80},
    ],
}

# 供应商数据
SUPPLIERS = [
    {"name": "深圳精密机械加工有限公司", "type": "机加工", "rating": 4.5},
    {"name": "东莞电气元件供应商", "type": "电气", "rating": 4.3},
    {"name": "苏州气动元件有限公司", "type": "气动", "rating": 4.6},
    {"name": "上海标准件批发商", "type": "标准件", "rating": 4.2},
    {"name": "广州钣金加工厂", "type": "钣金", "rating": 4.4},
]

# 项目阶段配置
STAGE_CONFIGS = [
    {"stage": "S1", "status": "ST01", "health": "H1", "progress": 5, "count": 2},
    {"stage": "S2", "status": "ST05", "health": "H1", "progress": 15, "count": 2},
    {"stage": "S3", "status": "ST13", "health": "H1", "progress": 30, "count": 2},
    {"stage": "S4", "status": "ST16", "health": "H1", "progress": 50, "count": 2},
    {"stage": "S5", "status": "ST20", "health": "H1", "progress": 70, "count": 2},
    {"stage": "S6", "status": "ST23", "health": "H1", "progress": 85, "count": 1},
    {"stage": "S7", "status": "ST25", "health": "H1", "progress": 90, "count": 1},
    {"stage": "S8", "status": "ST27", "health": "H1", "progress": 95, "count": 1},
    {"stage": "S9", "status": "ST30", "health": "H4", "progress": 100, "count": 1},
]

EQUIPMENT_TYPES = ["ICT", "FCT", "EOL", "AGING", "VISION", "ASSEMBLY", "BURN_IN"]
INDUSTRIES = ["新能源汽车电子", "消费电子", "半导体", "通信设备", "工业自动化"]
CUSTOMER_NAMES = [
    "深圳智行新能源汽车电子有限公司",
    "东莞华强电子科技有限公司",
    "苏州精密测试设备有限公司",
    "上海半导体测试技术有限公司",
    "北京智能装备制造有限公司",
    "广州自动化系统集成有限公司",
    "杭州视觉检测技术有限公司",
    "成都工业自动化设备有限公司",
    "武汉电子测试设备有限公司",
    "西安智能制造科技有限公司"
]


def get_or_create_users(db):
    """获取或创建用户"""
    users = {}
    user_configs = [
        {"username": "sales_zhang", "name": "张销售", "dept": "销售部", "role": "销售经理"},
        {"username": "pm_li", "name": "李项目经理", "dept": "项目部", "role": "项目经理"},
        {"username": "mech_wang", "name": "王机械工程师", "dept": "技术部", "role": "机械工程师"},
        {"username": "elec_zhao", "name": "赵电气工程师", "dept": "技术部", "role": "电气工程师"},
        {"username": "soft_chen", "name": "陈软件工程师", "dept": "技术部", "role": "软件工程师"},
        {"username": "purchase_zhou", "name": "周采购", "dept": "采购部", "role": "采购专员"},
        {"username": "finance_qian", "name": "钱财务", "dept": "财务部", "role": "财务专员"},
    ]

    for config in user_configs:
        user = db.query(User).filter(User.username == config["username"]).first()
        if not user:
            from app.core.security import get_password_hash
            emp = db.query(Employee).filter(Employee.employee_code == config["username"].upper().replace("_", "")).first()
            if not emp:
                emp = Employee(
                    employee_code=config["username"].upper().replace("_", ""),
                    name=config["name"],
                    department=config["dept"],
                    role=config["role"]
                )
                db.add(emp)
                db.flush()

            user = User(
                employee_id=emp.id,
                username=config["username"],
                real_name=config["name"],
                email=f"{config['username']}@company.com",
                password_hash=get_password_hash("123456"),
                is_active=True
            )
            db.add(user)
            db.flush()

        users[config["username"].split("_")[0]] = user

    return users


def create_material_categories(db):
    """创建物料分类"""
    print("\n创建物料分类...")
    categories = {}

    for cat_data in MATERIAL_CATEGORIES:
        # 检查是否已存在
        parent = db.query(MaterialCategory).filter(MaterialCategory.category_code == cat_data["code"]).first()
        if not parent:
            parent = MaterialCategory(
                category_code=cat_data["code"],
                category_name=cat_data["name"],
                level=1,
                full_path=cat_data["name"],
                is_active=True
            )
            db.add(parent)
            db.flush()
        categories[cat_data["code"]] = parent

        for child_data in cat_data.get("children", []):
            # 检查是否已存在
            child = db.query(MaterialCategory).filter(MaterialCategory.category_code == child_data["code"]).first()
            if not child:
                child = MaterialCategory(
                    category_code=child_data["code"],
                    category_name=child_data["name"],
                    parent_id=parent.id,
                    level=2,
                    full_path=f"{cat_data['name']}/{child_data['name']}",
                    is_active=True
                )
                db.add(child)
                db.flush()
            categories[child_data["code"]] = child

    print(f"  ✓ 已准备 {len(categories)} 个物料分类")
    return categories


def create_suppliers(db):
    """创建供应商"""
    print("\n创建供应商...")
    suppliers = []

    for idx, sup_data in enumerate(SUPPLIERS, 1):
        supplier_code = f"SUP{idx:03d}"
        # 检查是否已存在
        supplier = db.query(Supplier).filter(Supplier.supplier_code == supplier_code).first()
        if supplier:
            suppliers.append(supplier)
            continue

        # 只使用数据库表中存在的字段
        supplier = Supplier(
            supplier_code=f"SUP{idx:03d}",
            supplier_name=sup_data["name"],
            supplier_short_name=sup_data["name"][:6],
            supplier_type=sup_data["type"],
            contact_person=f"联系人{idx}",
            contact_phone=f"0755-8888{idx:04d}",
            contact_email=f"contact{idx}@supplier.com",
            address=f"深圳市南山区供应商{idx}号",
            quality_rating=Decimal(str(sup_data["rating"])),
            delivery_rating=Decimal(str(sup_data["rating"])),
            service_rating=Decimal(str(sup_data["rating"])),
            overall_rating=Decimal(str(sup_data["rating"])),
            supplier_level="A" if sup_data["rating"] >= 4.5 else "B",
            status="ACTIVE",
            cooperation_start=date.today() - timedelta(days=365),
            payment_terms="月结30天"
        )
        db.add(supplier)
        db.flush()
        suppliers.append(supplier)

    print(f"  ✓ 创建了 {len(suppliers)} 个供应商")
    return suppliers


def create_materials(db, categories, suppliers):
    """创建物料"""
    print("\n创建物料...")
    materials = []
    material_idx = 1

    for cat_code, category in categories.items():
        if cat_code in MATERIAL_TEMPLATES:
            for mat_data in MATERIAL_TEMPLATES[cat_code]:
                material_code = f"MAT{material_idx:05d}"
                # 检查是否已存在
                existing = db.query(Material).filter(Material.material_code == material_code).first()
                if existing:
                    materials.append(existing)
                    material_idx += 1
                    continue

                material = Material(
                    material_code=material_code,
                    material_name=mat_data["name"],
                    category_id=category.id,
                    specification=mat_data["spec"],
                    unit="件",
                    material_type="PURCHASE",
                    source_type="PURCHASE",
                    standard_price=Decimal(str(mat_data["price"])),
                    last_price=Decimal(str(mat_data["price"])),
                    currency="CNY",
                    lead_time_days=random.randint(7, 30),
                    min_order_qty=Decimal("1.00"),
                    default_supplier_id=suppliers[random.randint(0, len(suppliers)-1)].id if suppliers else None,
                    is_active=True
                )
                db.add(material)
                db.flush()
                materials.append(material)
                material_idx += 1

    print(f"  ✓ 创建了 {len(materials)} 个物料")
    return materials


def create_customer(db, index):
    """创建客户"""
    customer_name = CUSTOMER_NAMES[index % len(CUSTOMER_NAMES)]
    customer_code = f"CUST{250100 + index:03d}"

    existing = db.query(Customer).filter(Customer.customer_code == customer_code).first()
    if existing:
        return existing

    customer = Customer(
        customer_code=customer_code,
        customer_name=customer_name,
        short_name=customer_name[:6],
        customer_type="企业客户",
        industry=INDUSTRIES[index % len(INDUSTRIES)],
        scale="大型" if index % 3 == 0 else "中型",
        address=f"深圳市南山区科技园{index}号",
        contact_person=f"王总{index}",
        contact_phone=f"0755-8888{index:04d}",
        contact_email=f"contact{index}@customer.com",
        credit_level="A" if index % 2 == 0 else "B",
        credit_limit=Decimal("5000000.00"),
        payment_terms="30%预付款，60%发货前，10%验收后",
        status="ACTIVE"
    )
    db.add(customer)
    db.flush()
    return customer


def create_sales_flow(db, customer, users, project_index):
    """创建销售流程"""
    lead_code = f"LD{250100 + project_index:03d}"
    # 检查是否已存在
    existing_lead = db.query(Lead).filter(Lead.lead_code == lead_code).first()
    if existing_lead:
        # 如果已存在，返回关联的合同
        existing_contract = db.query(Contract).filter(Contract.opportunity_id == existing_lead.id).first()
        if existing_contract:
            return existing_contract

    lead = Lead(
        lead_code=lead_code,
        source="展会" if project_index % 2 == 0 else "网络",
        customer_name=customer.customer_name,
        industry=customer.industry,
        contact_name=customer.contact_person,
        contact_phone=customer.contact_phone,
        demand_summary=f"需要{EQUIPMENT_TYPES[project_index % len(EQUIPMENT_TYPES)]}测试设备",
        owner_id=users["sales"].id,
        status="CONVERTED"
    )
    db.add(lead)
    db.flush()

    opp_code = f"OPP{250100 + project_index:03d}"
    existing_opp = db.query(Opportunity).filter(Opportunity.opp_code == opp_code).first()
    if existing_opp:
        opportunity = existing_opp
    else:
        opportunity = Opportunity(
        opp_code=opp_code,
        lead_id=lead.id,
        customer_id=customer.id,
        opp_name=f"{customer.short_name}{EQUIPMENT_TYPES[project_index % len(EQUIPMENT_TYPES)]}测试设备项目",
        project_type="FIXED_PRICE",
        equipment_type=EQUIPMENT_TYPES[project_index % len(EQUIPMENT_TYPES)],
        stage="WON",
        est_amount=Decimal("2000000.00") + Decimal(str(project_index * 100000)),
        owner_id=users["sales"].id,
        gate_status="PASSED"
        )
        db.add(opportunity)
        db.flush()

    quote_code = f"QT{250100 + project_index:03d}"
    existing_quote = db.query(Quote).filter(Quote.quote_code == quote_code).first()
    if existing_quote:
        quote = existing_quote
    else:
        quote = Quote(
        quote_code=quote_code,
        opportunity_id=opportunity.id,
        customer_id=customer.id,
        status="APPROVED",
        owner_id=users["sales"].id
        )
        db.add(quote)
        db.flush()

    if not existing_quote:
        quote_version = QuoteVersion(
        quote_id=quote.id,
        version_no="V1.0",
        total_price=opportunity.est_amount,
        cost_total=opportunity.est_amount * Decimal("0.75"),
        gross_margin=Decimal("25.00"),
        lead_time_days=120,
        delivery_date=date.today() + timedelta(days=120),
        created_by=users["sales"].id
        )
        db.add(quote_version)
        db.flush()
        quote.current_version_id = quote_version.id
        db.flush()
    else:
        quote_version = quote.current_version

    contract_code = f"CT{250100 + project_index:03d}"
    existing_contract = db.query(Contract).filter(Contract.contract_code == contract_code).first()
    if existing_contract:
        return existing_contract

    contract = Contract(
        contract_code=contract_code,
        opportunity_id=opportunity.id,
        quote_version_id=quote_version.id,
        customer_id=customer.id,
        contract_amount=opportunity.est_amount,
        signed_date=date.today() - timedelta(days=180 - project_index * 10),
        status="SIGNED",
        payment_terms_summary="30%预付款，60%发货前，10%验收后",
        owner_id=users["sales"].id
    )
    db.add(contract)
    db.flush()

    return contract


def create_bom(db, project, machine, materials, suppliers):
    """创建BOM（使用bom_versions表）"""
    from sqlalchemy import text

    bom_name = f"{project.short_name}BOM"
    version_no = "V1.0"

    # 计算总金额和物料数量（确保有足够的物料）
    if len(materials) < 5:
        return None, []
    selected_materials = random.sample(materials, min(random.randint(5, 15), len(materials)))
    total_amount = Decimal("0.00")
    total_items = len(selected_materials)

    for material in selected_materials:
        qty = Decimal(str(random.randint(1, 10)))
        unit_price = material.standard_price or Decimal("100.00")
        total_amount += qty * unit_price

    # 创建BOM版本（使用原始SQL，因为模型可能不匹配）
    from sqlalchemy import text
    bom_version_sql = text("""
        INSERT INTO bom_versions (project_id, machine_id, version_no, version_name, status, is_current, total_items, total_amount, created_at, updated_at)
        VALUES (:project_id, :machine_id, :version_no, :version_name, :status, :is_current, :total_items, :total_amount, :created_at, :updated_at)
    """)

    from sqlalchemy import text

    # 使用数据库会话的连接
    try:
        from app.models.base import get_engine
        engine = get_engine()
        conn = engine.connect()
        result = conn.execute(
            bom_version_sql,
            {
                "project_id": project.id, "machine_id": machine.id, "version_no": version_no,
                "version_name": bom_name, "status": "RELEASED", "is_current": True,
                "total_items": total_items, "total_amount": float(total_amount),
                "created_at": datetime.now(), "updated_at": datetime.now()
            }
        )
        bom_version_id = result.lastrowid

        # 创建BOM明细
        bom_item_sql = text("""
            INSERT INTO bom_items (bom_version_id, material_id, item_no, material_code, material_name, specification, unit, quantity, unit_price, amount, source_type, supplier_id, required_date, level, created_at, updated_at)
            VALUES (:bom_version_id, :material_id, :item_no, :material_code, :material_name, :specification, :unit, :quantity, :unit_price, :amount, :source_type, :supplier_id, :required_date, :level, :created_at, :updated_at)
        """)

        item_no = 1
        for material in selected_materials:
            qty = Decimal(str(random.randint(1, 10)))
            unit_price = material.standard_price or Decimal("100.00")
            amount = qty * unit_price

            conn.execute(
                bom_item_sql,
                {
                    "bom_version_id": bom_version_id, "material_id": material.id, "item_no": str(item_no),
                    "material_code": material.material_code, "material_name": material.material_name,
                    "specification": material.specification or "", "unit": material.unit,
                    "quantity": float(qty), "unit_price": float(unit_price), "amount": float(amount),
                    "source_type": "PURCHASE", "supplier_id": material.default_supplier_id,
                    "required_date": project.planned_start_date + timedelta(days=30),
                    "level": 1, "created_at": datetime.now(), "updated_at": datetime.now()
                }
            )
            item_no += 1

        conn.commit()
        conn.close()
    except Exception as e:
        import traceback
        print(f"    警告: BOM创建失败: {e}")
        traceback.print_exc()
        bom_version_id = None
        # 不抛出异常，返回None让上层处理

    # 返回一个简单的对象用于后续使用
    class BomVersionObj:
        def __init__(self, id):
            self.id = id

    if bom_version_id is None:
        # 如果BOM创建失败，返回None和空列表
        return None, []

    return BomVersionObj(bom_version_id), selected_materials


def create_purchase_orders(db, project, bom_materials, suppliers, users):
    """创建采购订单"""
    if not bom_materials:
        return []

    # 按供应商分组物料
    supplier_items = {}
    for material in bom_materials:
        if material.default_supplier_id:
            if material.default_supplier_id not in supplier_items:
                supplier_items[material.default_supplier_id] = []
            supplier_items[material.default_supplier_id].append(material)

    if not supplier_items:
        return []

    purchase_orders = []
    for supplier_id, items in supplier_items.items():
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            continue

        order_no = f"PO{project.project_code}{len(purchase_orders)+1:02d}"
        # 计算总金额
        total_amount = Decimal("0.00")
        for material in items:
            qty = Decimal(str(random.randint(1, 10)))
            unit_price = material.standard_price or Decimal("100.00")
            total_amount += qty * unit_price

        po = PurchaseOrder(
            order_no=order_no,
            supplier_id=supplier_id,
            project_id=project.id,
            order_title=f"{project.short_name}物料采购",
            total_amount=total_amount * Decimal("1.13"),
            tax_rate=Decimal("13.00"),
            tax_amount=total_amount * Decimal("0.13"),
            amount_with_tax=total_amount * Decimal("1.13"),
            order_date=project.planned_start_date + timedelta(days=5),
            required_date=project.planned_start_date + timedelta(days=45),
            status="APPROVED" if project.stage in ["S3", "S4", "S5"] else "DRAFT",
            payment_terms="月结30天",
            payment_status="UNPAID",
            created_by=users["purchase"].id
        )
        db.add(po)
        db.flush()

        # 创建采购订单明细
        for idx, material in enumerate(items, 1):
            qty = Decimal(str(random.randint(1, 10)))
            unit_price = material.standard_price or Decimal("100.00")
            amount = qty * unit_price

            poi = PurchaseOrderItem(
                order_id=po.id,
                item_no=idx,
                material_id=material.id,
                material_code=material.material_code,
                material_name=material.material_name,
                specification=material.specification,
                unit=material.unit,
                quantity=qty,
                unit_price=unit_price,
                amount=amount,
                tax_rate=Decimal("13.00"),
                tax_amount=amount * Decimal("0.13"),
                amount_with_tax=amount * Decimal("1.13"),
                required_date=project.planned_start_date + timedelta(days=30),
                status="PENDING" if project.stage == "S3" else "RECEIVED"
            )
            db.add(poi)

        purchase_orders.append(po)

    db.flush()
    return purchase_orders


def create_acceptance_orders(db, project, machine, users, stage_config):
    """创建验收单"""
    if project.stage not in ["S6", "S7", "S8", "S9"]:
        return None

    acceptance_type = "FAT" if project.stage == "S6" else "SAT"
    order_no = f"ACC-{project.project_code}-{acceptance_type}"

    acceptance = AcceptanceOrder(
        order_no=order_no,
        project_id=project.id,
        machine_id=machine.id,
        acceptance_type=acceptance_type,
        planned_date=project.planned_end_date - timedelta(days=10),
        actual_start_date=datetime.combine(project.planned_end_date - timedelta(days=5), datetime.min.time()) if project.stage in ["S7", "S8", "S9"] else None,
        actual_end_date=datetime.combine(project.planned_end_date - timedelta(days=3), datetime.min.time()) if project.stage in ["S7", "S8", "S9"] else None,
        status="COMPLETED" if project.stage in ["S7", "S8", "S9"] else "DRAFT",
        overall_result="PASSED" if project.stage in ["S7", "S8", "S9"] else None
    )
    db.add(acceptance)
    db.flush()

    # 创建验收项
    items = [
        {"name": "功能测试", "result": "PASSED" if project.stage in ["S7", "S8", "S9"] else None},
        {"name": "性能测试", "result": "PASSED" if project.stage in ["S7", "S8", "S9"] else None},
        {"name": "外观检查", "result": "PASSED" if project.stage in ["S7", "S8", "S9"] else None},
    ]

    for idx, item_data in enumerate(items, 1):
        item = AcceptanceOrderItem(
            order_id=acceptance.id,
            category_code="FUNCTIONAL",
            category_name="功能测试",
            item_code=f"ITEM{idx:03d}",
            item_name=item_data["name"],
            sort_order=idx,
            result_status=item_data["result"] if item_data["result"] else "PENDING"
        )
        db.add(item)

    db.flush()
    return acceptance


def create_invoices(db, project, contract, payment_plans, users):
    """创建发票"""
    if project.stage not in ["S7", "S8", "S9"]:
        return []

    invoices = []
    for plan in payment_plans:
        if plan.status == "PAID" or project.stage in ["S7", "S8", "S9"]:
            invoice = Invoice(
                invoice_code=f"INV-{project.project_code}-{plan.payment_no}",
                contract_id=contract.id,
                project_id=project.id,
                invoice_type="NORMAL",
                amount=plan.planned_amount,
                tax_rate=Decimal("13.00"),
                tax_amount=plan.planned_amount * Decimal("0.13"),
                total_amount=plan.planned_amount * Decimal("1.13"),
                issue_date=plan.actual_date or date.today(),
                status="ISSUED"
            )
            db.add(invoice)
            invoices.append(invoice)

    db.flush()
    return invoices


def create_project_members(db, project, users):
    """创建项目成员"""
    members = []
    roles = [
        {"user": "pm", "role_code": "PM", "is_lead": True},
        {"user": "mech", "role_code": "MECH", "is_lead": False},
        {"user": "elec", "role_code": "ELEC", "is_lead": False},
        {"user": "soft", "role_code": "SOFT", "is_lead": False},
    ]

    for role_data in roles:
        if role_data["user"] in users:
            # 检查是否已存在
            existing_member = db.query(ProjectMember).filter(
                ProjectMember.project_id == project.id,
                ProjectMember.user_id == users[role_data["user"]].id,
                ProjectMember.role_code == role_data["role_code"]
            ).first()
            if existing_member:
                members.append(existing_member)
                continue

            member = ProjectMember(
                project_id=project.id,
                user_id=users[role_data["user"]].id,
                role_code=role_data["role_code"],
                is_lead=role_data["is_lead"],
                start_date=project.planned_start_date,
                allocation_pct=Decimal("100.00"),
                is_active=True
            )
            db.add(member)
            members.append(member)

    db.flush()
    return members


def create_project_documents(db, project, stage_config):
    """创建项目文档"""
    docs = []
    doc_types = ["需求文档", "设计方案", "BOM清单", "测试报告"]

    for idx, doc_type in enumerate(doc_types, 1):
        if (stage_config["stage"] == "S1" and doc_type == "需求文档") or \
           (stage_config["stage"] == "S2" and doc_type == "设计方案") or \
           (stage_config["stage"] == "S3" and doc_type == "BOM清单") or \
           (stage_config["stage"] in ["S6", "S7", "S8", "S9"] and doc_type == "测试报告"):

            doc = ProjectDocument(
                project_id=project.id,
                doc_name=f"{project.short_name}-{doc_type}",
                doc_type=doc_type,
                file_path=f"/docs/{project.project_code}/{doc_type}.pdf",
                file_name=f"{doc_type}.pdf",
                version="V1.0",
                status="APPROVED" if stage_config["stage"] not in ["S1", "S2"] else "DRAFT"
            )
            db.add(doc)
            docs.append(doc)

    db.flush()
    return docs


def create_project_costs(db, project, stage_config):
    """创建项目成本"""
    costs = []
    cost_configs = [
        {"type": "MATERIAL", "category": "物料成本", "ratio": 0.40},
        {"type": "LABOR", "category": "人工成本", "ratio": 0.30},
        {"type": "OUTSOURCE", "category": "外协成本", "ratio": 0.20},
        {"type": "OTHER", "category": "其他成本", "ratio": 0.10},
    ]

    budget_total = project.budget_amount or Decimal("1000000.00")

    for cost_data in cost_configs:
        amount = budget_total * Decimal(str(cost_data["ratio"])) * Decimal(str(stage_config["progress"] / 100))

        cost = ProjectCost(
            project_id=project.id,
            cost_type=cost_data["type"],
            cost_category=cost_data["category"],
            amount=amount,
            cost_date=project.planned_start_date + timedelta(days=stage_config["progress"] * 2)
        )
        db.add(cost)
        costs.append(cost)

    db.flush()
    return costs


def create_project(db, customer, contract, users, stage_config, project_index, materials, suppliers):
    """创建完整项目"""
    project_code = f"PJ{250100 + project_index:03d}"
    # 检查是否已存在
    existing_project = db.query(Project).filter(Project.project_code == project_code).first()
    if existing_project:
        # 如果项目已存在，检查并补充创建缺失的关联数据
        machine = db.query(Machine).filter(Machine.project_id == existing_project.id).first()
        if machine:
            try:
                # 检查并创建BOM（如果不存在）
                from sqlalchemy import text

                from app.models.base import get_engine
                engine = get_engine()
                conn = engine.connect()
                bom_check = text("SELECT COUNT(*) FROM bom_versions WHERE project_id = :pid")
                bom_count = conn.execute(bom_check, {"pid": existing_project.id}).scalar()
                conn.close()

                if bom_count == 0 and existing_project.stage in ["S3", "S4", "S5", "S6", "S7", "S8", "S9"]:
                    bom, bom_materials = create_bom(db, existing_project, machine, materials, suppliers)
                    if bom_materials:
                        create_purchase_orders(db, existing_project, bom_materials, suppliers, users)

                # 检查并创建其他关联数据
                member_count = db.query(ProjectMember).filter(ProjectMember.project_id == existing_project.id).count()
                if member_count == 0:
                    create_project_members(db, existing_project, users)

                doc_count = db.query(ProjectDocument).filter(ProjectDocument.project_id == existing_project.id).count()
                if doc_count == 0:
                    create_project_documents(db, existing_project, stage_config)

                cost_count = db.query(ProjectCost).filter(ProjectCost.project_id == existing_project.id).count()
                if cost_count == 0:
                    create_project_costs(db, existing_project, stage_config)

                # 验收单和发票（根据阶段）
                if existing_project.stage in ["S6", "S7", "S8", "S9"]:
                    acc_count = db.query(AcceptanceOrder).filter(AcceptanceOrder.project_id == existing_project.id).count()
                    if acc_count == 0:
                        create_acceptance_orders(db, existing_project, machine, users, stage_config)

                    if existing_project.stage in ["S7", "S8", "S9"]:
                        payment_plans = db.query(ProjectPaymentPlan).filter(ProjectPaymentPlan.project_id == existing_project.id).all()
                        inv_count = db.query(Invoice).filter(Invoice.project_id == existing_project.id).count()
                        if inv_count == 0 and payment_plans:
                            create_invoices(db, existing_project, contract, payment_plans, users)

                db.commit()
            except Exception as e2:
                db.rollback()
                print(f"    警告: 补充项目 {existing_project.project_code} 关联数据失败: {e2}")

        return existing_project

    base_date = date.today() - timedelta(days=180 - project_index * 10)
    equipment_type = EQUIPMENT_TYPES[project_index % len(EQUIPMENT_TYPES)]

    project_name = f"{customer.short_name}{equipment_type}测试设备项目"

    planned_start = base_date
    planned_end = base_date + timedelta(days=120)
    actual_start = planned_start

    project = Project(
        project_code=project_code,
        project_name=project_name,
        short_name=f"{customer.short_name[:4]}{equipment_type}",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        customer_contact=customer.contact_person,
        customer_phone=customer.contact_phone,
        contract_no=contract.contract_code,
        project_type="FIXED_PRICE",
        product_category=f"{equipment_type}测试设备",
        industry=customer.industry,
        stage=stage_config["stage"],
        status=stage_config["status"],
        health=stage_config["health"],
        progress_pct=Decimal(str(stage_config["progress"])),
        contract_date=contract.signed_date,
        planned_start_date=planned_start,
        planned_end_date=planned_end,
        actual_start_date=actual_start,
        contract_amount=contract.contract_amount,
        budget_amount=contract.contract_amount * Decimal("0.75"),
        pm_id=users["pm"].id,
        pm_name=users["pm"].real_name,
        priority="HIGH" if project_index % 3 == 0 else "NORMAL",
        description=f"{equipment_type}测试设备项目，阶段：{stage_config['stage']}",
        requirements=f"需要开发{equipment_type}测试设备，满足客户测试需求",
        opportunity_id=contract.opportunity_id,
        contract_id=contract.id
    )
    db.add(project)
    db.flush()

    # 创建里程碑
    milestones_config = {
        "S1": [{"name": "需求确认", "type": "REQUIREMENT_CONFIRMED", "date_offset": 5, "status": "COMPLETED"}],
        "S2": [
            {"name": "需求确认", "type": "REQUIREMENT_CONFIRMED", "date_offset": 5, "status": "COMPLETED"},
            {"name": "方案设计完成", "type": "DESIGN_COMPLETED", "date_offset": 20, "status": "COMPLETED"}
        ],
        "S3": [
            {"name": "BOM发布", "type": "BOM_RELEASED", "date_offset": 30, "status": "COMPLETED"},
            {"name": "物料到齐", "type": "MATERIAL_ARRIVED", "date_offset": 45, "status": "IN_PROGRESS"}
        ],
        "S4": [
            {"name": "物料到齐", "type": "MATERIAL_ARRIVED", "date_offset": 45, "status": "COMPLETED"},
            {"name": "机械加工完成", "type": "MACHINING_COMPLETED", "date_offset": 75, "status": "IN_PROGRESS"}
        ],
        "S5": [
            {"name": "机械加工完成", "type": "MACHINING_COMPLETED", "date_offset": 75, "status": "COMPLETED"},
            {"name": "装配完成", "type": "ASSEMBLY_COMPLETED", "date_offset": 90, "status": "COMPLETED"},
            {"name": "调试完成", "type": "DEBUG_COMPLETED", "date_offset": 105, "status": "IN_PROGRESS"}
        ],
        "S6": [
            {"name": "调试完成", "type": "DEBUG_COMPLETED", "date_offset": 105, "status": "COMPLETED"},
            {"name": "FAT验收通过", "type": "FAT_PASS", "date_offset": 130, "status": "PENDING"}
        ],
        "S7": [
            {"name": "FAT验收通过", "type": "FAT_PASS", "date_offset": 130, "status": "COMPLETED"},
            {"name": "发货", "type": "SHIPPED", "date_offset": 145, "status": "PENDING"}
        ],
        "S8": [
            {"name": "发货", "type": "SHIPPED", "date_offset": 145, "status": "COMPLETED"},
            {"name": "SAT验收通过", "type": "SAT_PASS", "date_offset": 160, "status": "IN_PROGRESS"}
        ],
        "S9": [
            {"name": "SAT验收通过", "type": "SAT_PASS", "date_offset": 160, "status": "COMPLETED"},
            {"name": "终验收通过", "type": "FINAL_ACCEPTANCE", "date_offset": 180, "status": "COMPLETED"}
        ]
    }

    milestones_data = milestones_config.get(stage_config["stage"], [])
    for ms_data in milestones_data:
        planned_date = base_date + timedelta(days=ms_data["date_offset"])
        actual_date = planned_date if ms_data["status"] == "COMPLETED" else None

        milestone = ProjectMilestone(
            project_id=project.id,
            milestone_code=f"MS-{project.project_code}-{ms_data['type']}",
            milestone_name=ms_data["name"],
            milestone_type=ms_data["type"],
            planned_date=planned_date,
            actual_date=actual_date,
            reminder_days=7,
            status=ms_data["status"],
            is_key=(ms_data["type"] in ["FAT_PASS", "SAT_PASS", "FINAL_ACCEPTANCE"])
        )
        db.add(milestone)

    # 创建收款计划
    payment_plans = []
    plans = [
        {"payment_name": "预付款", "payment_type": "ADVANCE", "amount": contract.contract_amount * Decimal("0.30"), "date_offset": 0, "status": "PAID"},
        {"payment_name": "发货前付款", "payment_type": "BEFORE_SHIPMENT", "amount": contract.contract_amount * Decimal("0.60"), "date_offset": 145, "status": "PENDING"},
        {"payment_name": "验收后尾款", "payment_type": "ACCEPTANCE", "amount": contract.contract_amount * Decimal("0.10"), "date_offset": 180, "status": "PENDING"}
    ]

    for idx, plan_data in enumerate(plans, 1):
        planned_date = base_date + timedelta(days=plan_data["date_offset"])
        actual_date = planned_date if plan_data["status"] == "PAID" else None

        payment_plan = ProjectPaymentPlan(
            project_id=project.id,
            contract_id=contract.id,
            payment_no=idx,
            payment_name=plan_data["payment_name"],
            payment_type=plan_data["payment_type"],
            planned_amount=plan_data["amount"],
            planned_date=planned_date,
            actual_date=actual_date,
            status=plan_data["status"]
        )
        db.add(payment_plan)
        payment_plans.append(payment_plan)

    # 创建设备
    machine = Machine(
        project_id=project.id,
        machine_code=f"PN{project.id:03d}",
        machine_name=f"{project.short_name}-01",
        machine_type=equipment_type,
        specification=f"{equipment_type}测试设备，满足客户测试需求",
        stage=stage_config["stage"],
        status=stage_config["status"],
        health=stage_config["health"],
        planned_start_date=project.planned_start_date,
        planned_end_date=project.planned_end_date,
        actual_start_date=project.actual_start_date
    )
    db.add(machine)
    db.flush()

    # 创建BOM（只在S3及以后阶段创建）
    bom = None
    bom_materials = []
    if project.stage in ["S3", "S4", "S5", "S6", "S7", "S8", "S9"]:
        try:
            bom, bom_materials = create_bom(db, project, machine, materials, suppliers)
            if bom is None or not bom_materials:
                print(f"    警告: 项目 {project.project_code} BOM创建返回空数据")
        except Exception as e:
            import traceback
            print(f"    警告: 项目 {project.project_code} BOM创建失败: {e}")
            traceback.print_exc()
            bom_materials = []

    # 创建采购订单（只在S3及以后阶段创建，使用BOM物料）
    purchase_orders = []
    if project.stage in ["S3", "S4", "S5", "S6", "S7", "S8", "S9"]:
        try:
            # 如果没有BOM物料，使用所有有供应商的物料
            if not bom_materials:
                bom_materials = [m for m in materials if m.default_supplier_id]
            if bom_materials:
                purchase_orders = create_purchase_orders(db, project, bom_materials, suppliers, users)
        except Exception as e:
            import traceback
            print(f"    警告: 项目 {project.project_code} 采购订单创建失败: {e}")
            traceback.print_exc()

    # 创建验收单
    try:
        acceptance = create_acceptance_orders(db, project, machine, users, stage_config)
    except Exception as e:
        import traceback
        print(f"    警告: 项目 {project.project_code} 验收单创建失败: {e}")
        traceback.print_exc()
        acceptance = None

    # 创建发票
    try:
        invoices = create_invoices(db, project, contract, payment_plans, users)
    except Exception as e:
        import traceback
        print(f"    警告: 项目 {project.project_code} 发票创建失败: {e}")
        traceback.print_exc()
        invoices = []

    # 创建项目成员
    try:
        members = create_project_members(db, project, users)
    except Exception as e:
        import traceback
        print(f"    警告: 项目 {project.project_code} 项目成员创建失败: {e}")
        traceback.print_exc()
        members = []

    # 创建项目文档
    try:
        docs = create_project_documents(db, project, stage_config)
    except Exception as e:
        import traceback
        print(f"    警告: 项目 {project.project_code} 项目文档创建失败: {e}")
        traceback.print_exc()
        docs = []

    # 创建项目成本
    try:
        costs = create_project_costs(db, project, stage_config)
    except Exception as e:
        import traceback
        print(f"    警告: 项目 {project.project_code} 项目成本创建失败: {e}")
        traceback.print_exc()
        costs = []

    # 创建任务
    tasks_config = {
        "S1": [{"name": "需求调研", "assignee": "pm", "days": 3, "status": "DONE"}],
        "S2": [
            {"name": "方案设计", "assignee": "mech", "days": 15, "status": "DONE"},
            {"name": "电气方案设计", "assignee": "elec", "days": 15, "status": "IN_PROGRESS"}
        ],
        "S3": [
            {"name": "BOM设计", "assignee": "mech", "days": 10, "status": "DONE"},
            {"name": "物料采购", "assignee": "purchase", "days": 20, "status": "IN_PROGRESS"}
        ],
        "S4": [
            {"name": "机械加工", "assignee": "mech", "days": 30, "status": "IN_PROGRESS"},
            {"name": "钣金加工", "assignee": "mech", "days": 25, "status": "IN_PROGRESS"}
        ],
        "S5": [
            {"name": "机械装配", "assignee": "mech", "days": 15, "status": "DONE"},
            {"name": "电气接线", "assignee": "elec", "days": 10, "status": "DONE"},
            {"name": "程序调试", "assignee": "soft", "days": 15, "status": "IN_PROGRESS"}
        ],
        "S6": [
            {"name": "功能测试", "assignee": "soft", "days": 10, "status": "DONE"},
            {"name": "FAT验收准备", "assignee": "pm", "days": 5, "status": "IN_PROGRESS"}
        ],
        "S7": [
            {"name": "FAT验收", "assignee": "pm", "days": 5, "status": "DONE"},
            {"name": "包装准备", "assignee": "pm", "days": 3, "status": "IN_PROGRESS"}
        ],
        "S8": [
            {"name": "设备发货", "assignee": "pm", "days": 1, "status": "DONE"},
            {"name": "现场安装", "assignee": "elec", "days": 10, "status": "IN_PROGRESS"}
        ],
        "S9": [
            {"name": "SAT验收", "assignee": "pm", "days": 5, "status": "DONE"},
            {"name": "项目结项", "assignee": "pm", "days": 1, "status": "DONE"}
        ]
    }

    tasks_data = tasks_config.get(stage_config["stage"], [])
    user_map = {"pm": users["pm"], "mech": users["mech"], "elec": users["elec"], "soft": users["soft"], "purchase": users["purchase"]}

    for task_data in tasks_data:
        if task_data["assignee"] not in user_map:
            continue
        plan_start = base_date
        plan_end = base_date + timedelta(days=task_data["days"])
        actual_end = plan_end if task_data["status"] == "DONE" else None

        task = Task(
            project_id=project.id,
            machine_id=machine.id,
            milestone_id=None,
            task_name=task_data["name"],
            stage=stage_config["stage"],
            status=task_data["status"],
            owner_id=user_map[task_data["assignee"]].id,
            plan_start=plan_start,
            plan_end=plan_end,
            actual_start=plan_start,
            actual_end=actual_end,
            progress_percent=100 if task_data["status"] == "DONE" else 50
        )
        db.add(task)

    db.flush()

    return project


def main():
    """主函数"""
    print("=" * 60)
    print("生成完整测试数据")
    print("=" * 60)

    with get_db_session() as db:
        try:
            # 1. 准备用户
            print("\n1. 准备用户数据...")
            users = get_or_create_users(db)
            print(f"   ✓ 已准备 {len(users)} 个用户")

            # 2. 创建物料分类
            categories = create_material_categories(db)

            # 3. 创建供应商
            suppliers = create_suppliers(db)

            # 4. 创建物料
            materials = create_materials(db, categories, suppliers)

            # 5. 生成各个阶段的项目
            project_index = 0
            all_projects = []

            for stage_config in STAGE_CONFIGS:
                print(f"\n生成 {stage_config['stage']} 阶段项目...")

                for i in range(stage_config["count"]):
                    project_index += 1

                    # 创建客户
                    customer = create_customer(db, project_index)

                    # 创建销售流程
                    contract = create_sales_flow(db, customer, users, project_index)

                    # 创建项目（包含所有关联数据）
                    project = create_project(db, customer, contract, users, stage_config, project_index, materials, suppliers)
                    all_projects.append(project)

                    print(f"   ✓ 创建项目: {project.project_code} - {project.project_name} "
                          f"(阶段: {project.stage}, 进度: {project.progress_pct}%)")

            db.commit()

            print("\n" + "=" * 60)
            print("数据生成完成！")
            print("=" * 60)
            print(f"\n生成的数据概览：")
            print(f"  物料分类: {len(categories)} 个")
            print(f"  供应商: {len(suppliers)} 个")
            print(f"  物料: {len(materials)} 个")
            print(f"  项目: {len(all_projects)} 个")

            # 按阶段统计
            stage_stats = {}
            for project in all_projects:
                stage = project.stage
                if stage not in stage_stats:
                    stage_stats[stage] = 0
                stage_stats[stage] += 1

            print(f"\n各阶段项目数量：")
            for stage in ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"]:
                count = stage_stats.get(stage, 0)
                print(f"  {stage}: {count} 个项目")

            print(f"\n数据已保存到数据库！")
            print(f"现在可以在项目看板查看完整的数据展示。")

        except Exception as e:
            db.rollback()
            print(f"\n错误: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    main()
