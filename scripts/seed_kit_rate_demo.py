#!/usr/bin/env python3
"""
Seed demo data for kit-rate calculation:
customer -> project -> machine -> BOM -> materials -> purchase orders.
"""

import os
import sys
from datetime import date, timedelta
from decimal import Decimal

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from app.models.base import get_db_session
from app.models.material import BomHeader, BomItem, Material, MaterialCategory
from app.models.project import Customer, Machine, Project
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.vendor import Vendor


def get_or_create(db, model, defaults=None, **filters):
    instance = db.query(model).filter_by(**filters).first()
    if instance:
        return instance, False
    params = dict(defaults or {})
    params.update(filters)
    instance = model(**params)
    db.add(instance)
    db.flush()
    return instance, True


def main():
    today = date.today()
    planned_end = today + timedelta(days=45)

    customer_code = "CUST-KIT-001"
    project_code = "PRJ-KIT-001"
    machine_code = "MC-KIT-01"
    bom_no = "BOM-KIT-001"
    vendor_code = "VEND-KIT-001"
    po_no = "PO-KIT-001"

    with get_db_session() as db:
        customer, created = get_or_create(
            db,
            Customer,
            customer_code=customer_code,
            defaults={
                "customer_name": "Demo Industrial Co.",
                "short_name": "Demo Industrial",
                "contact_person": "Alex Chen",
                "contact_phone": "13800000001",
                "contact_email": "alex.chen@example.com",
                "industry": "Automation",
                "status": "ACTIVE",
            },
        )
        print(f"customer: {customer.customer_code} ({'created' if created else 'exists'})")

        vendor, created = get_or_create(
            db,
            Vendor,
            supplier_code=vendor_code,
            defaults={
                "supplier_name": "Demo Components Ltd.",
                "vendor_type": "MATERIAL",
                "supplier_level": "A",
                "status": "ACTIVE",
            },
        )
        print(f"vendor: {vendor.supplier_code} ({'created' if created else 'exists'})")

        project, created = get_or_create(
            db,
            Project,
            project_code=project_code,
            defaults={
                "project_name": "Auto Assembly Line A",
                "customer_id": customer.id,
                "customer_name": customer.customer_name,
                "customer_contact": customer.contact_person,
                "customer_phone": customer.contact_phone,
                "project_category": "RND",
                "stage": "S3",
                "health": "H2",
                "planned_start_date": today - timedelta(days=30),
                "planned_end_date": planned_end,
                "is_active": True,
            },
        )
        print(f"project: {project.project_code} ({'created' if created else 'exists'})")

        machine, created = get_or_create(
            db,
            Machine,
            project_id=project.id,
            machine_code=machine_code,
            defaults={
                "machine_name": "Assembly Station 1",
                "machine_no": 1,
                "machine_type": "ASSEMBLY",
                "stage": "S3",
                "planned_start_date": today - timedelta(days=25),
                "planned_end_date": planned_end,
            },
        )
        print(f"machine: {machine.machine_code} ({'created' if created else 'exists'})")

        categories = {
            "KIT-MECH": {"name": "Mechanical"},
            "KIT-ELEC": {"name": "Electrical"},
        }
        category_map = {}
        for code, data in categories.items():
            category, created = get_or_create(
                db,
                MaterialCategory,
                category_code=code,
                defaults={
                    "category_name": data["name"],
                    "is_active": True,
                },
            )
            category_map[code] = category
            print(f"category: {category.category_code} ({'created' if created else 'exists'})")

        materials_payload = [
            {
                "code": "MAT-KIT-001",
                "name": "Linear Actuator",
                "category": "KIT-MECH",
                "spec": "LA-200",
                "unit": "pcs",
                "price": Decimal("1200"),
                "stock": Decimal("0"),
                "key": True,
            },
            {
                "code": "MAT-KIT-002",
                "name": "PLC Controller",
                "category": "KIT-ELEC",
                "spec": "PLC-32IO",
                "unit": "pcs",
                "price": Decimal("3500"),
                "stock": Decimal("0"),
                "key": True,
            },
            {
                "code": "MAT-KIT-003",
                "name": "Servo Motor",
                "category": "KIT-MECH",
                "spec": "SM-750W",
                "unit": "pcs",
                "price": Decimal("800"),
                "stock": Decimal("0"),
                "key": False,
            },
            {
                "code": "MAT-KIT-004",
                "name": "Gearbox",
                "category": "KIT-MECH",
                "spec": "GB-120",
                "unit": "pcs",
                "price": Decimal("150"),
                "stock": Decimal("0"),
                "key": False,
            },
            {
                "code": "MAT-KIT-005",
                "name": "Proximity Sensor",
                "category": "KIT-ELEC",
                "spec": "PS-24V",
                "unit": "pcs",
                "price": Decimal("220"),
                "stock": Decimal("0"),
                "key": False,
            },
            {
                "code": "MAT-KIT-006",
                "name": "HMI Panel",
                "category": "KIT-ELEC",
                "spec": "HMI-7IN",
                "unit": "pcs",
                "price": Decimal("980"),
                "stock": Decimal("0"),
                "key": True,
            },
            {
                "code": "MAT-KIT-007",
                "name": "Cable Harness",
                "category": "KIT-ELEC",
                "spec": "CB-5M",
                "unit": "pcs",
                "price": Decimal("540"),
                "stock": Decimal("1"),
                "key": False,
            },
            {
                "code": "MAT-KIT-008",
                "name": "Pneumatic Valve",
                "category": "KIT-MECH",
                "spec": "PV-2WAY",
                "unit": "pcs",
                "price": Decimal("300"),
                "stock": Decimal("0"),
                "key": False,
            },
        ]

        material_map = {}
        for payload in materials_payload:
            material, created = get_or_create(
                db,
                Material,
                material_code=payload["code"],
                defaults={
                    "material_name": payload["name"],
                    "category_id": category_map[payload["category"]].id,
                    "specification": payload["spec"],
                    "unit": payload["unit"],
                    "standard_price": payload["price"],
                    "last_price": payload["price"],
                    "current_stock": payload["stock"],
                    "is_key_material": payload["key"],
                    "default_supplier_id": vendor.id,
                    "is_active": True,
                },
            )
            material_map[payload["code"]] = material
            print(f"material: {material.material_code} ({'created' if created else 'exists'})")

        bom, created = get_or_create(
            db,
            BomHeader,
            bom_no=bom_no,
            defaults={
                "bom_name": "Demo BOM - Assembly Station 1",
                "project_id": project.id,
                "machine_id": machine.id,
                "version": "1.0",
                "is_latest": True,
                "status": "APPROVED",
            },
        )
        print(f"bom: {bom.bom_no} ({'created' if created else 'exists'})")

        if bom.items.count() == 0:
            bom_items_payload = [
                {"code": "MAT-KIT-001", "qty": Decimal("4"), "price": Decimal("1200"), "received": Decimal("4"), "key": True},
                {"code": "MAT-KIT-002", "qty": Decimal("3"), "price": Decimal("3500"), "received": Decimal("1"), "key": True},
                {"code": "MAT-KIT-003", "qty": Decimal("5"), "price": Decimal("800"), "received": Decimal("0"), "key": False},
                {"code": "MAT-KIT-004", "qty": Decimal("6"), "price": Decimal("150"), "received": Decimal("0"), "key": False},
                {"code": "MAT-KIT-005", "qty": Decimal("2"), "price": Decimal("220"), "received": Decimal("2"), "key": False},
                {"code": "MAT-KIT-006", "qty": Decimal("1"), "price": Decimal("980"), "received": Decimal("1"), "key": True},
                {"code": "MAT-KIT-007", "qty": Decimal("2"), "price": Decimal("540"), "received": Decimal("0"), "key": False},
                {"code": "MAT-KIT-008", "qty": Decimal("4"), "price": Decimal("300"), "received": Decimal("0"), "key": False},
            ]

            total_amount = Decimal("0")
            for index, item in enumerate(bom_items_payload, start=1):
                material = material_map[item["code"]]
                amount = item["qty"] * item["price"]
                total_amount += amount
                db.add(
                    BomItem(
                        bom_id=bom.id,
                        item_no=index,
                        material_id=material.id,
                        material_code=material.material_code,
                        material_name=material.material_name,
                        specification=material.specification,
                        unit=material.unit,
                        quantity=item["qty"],
                        unit_price=item["price"],
                        amount=amount,
                        received_qty=item["received"],
                        required_date=planned_end,
                        is_key_item=item["key"],
                    )
                )

            bom.total_items = len(bom_items_payload)
            bom.total_amount = total_amount
            print(f"bom items: created {len(bom_items_payload)}")
        else:
            print(f"bom items: exists ({bom.items.count()})")

        purchase_order, created = get_or_create(
            db,
            PurchaseOrder,
            order_no=po_no,
            defaults={
                "supplier_id": vendor.id,
                "project_id": project.id,
                "order_type": "NORMAL",
                "order_title": "Kit Rate Demo Purchase",
                "order_date": today - timedelta(days=7),
                "required_date": today + timedelta(days=14),
                "promised_date": today + timedelta(days=10),
                "status": "ORDERED",
            },
        )
        print(f"purchase order: {purchase_order.order_no} ({'created' if created else 'exists'})")

        if purchase_order.items.count() == 0:
            po_items_payload = [
                {"code": "MAT-KIT-002", "qty": Decimal("1"), "price": Decimal("3500"), "received": Decimal("0")},
                {"code": "MAT-KIT-003", "qty": Decimal("2"), "price": Decimal("800"), "received": Decimal("0")},
            ]

            po_total = Decimal("0")
            for index, item in enumerate(po_items_payload, start=1):
                material = material_map[item["code"]]
                bom_item = (
                    db.query(BomItem)
                    .filter(BomItem.bom_id == bom.id)
                    .filter(BomItem.material_id == material.id)
                    .first()
                )
                amount = item["qty"] * item["price"]
                po_total += amount
                db.add(
                    PurchaseOrderItem(
                        order_id=purchase_order.id,
                        item_no=index,
                        material_id=material.id,
                        bom_item_id=bom_item.id if bom_item else None,
                        material_code=material.material_code,
                        material_name=material.material_name,
                        specification=material.specification,
                        unit=material.unit,
                        quantity=item["qty"],
                        unit_price=item["price"],
                        amount=amount,
                        received_qty=item["received"],
                        status="ORDERED",
                    )
                )

            purchase_order.total_amount = po_total
            purchase_order.amount_with_tax = po_total
            print(f"purchase order items: created {len(po_items_payload)}")
        else:
            print(f"purchase order items: exists ({purchase_order.items.count()})")

    print("done.")


if __name__ == "__main__":
    main()
