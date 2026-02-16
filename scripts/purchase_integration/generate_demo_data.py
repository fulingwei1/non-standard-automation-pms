# -*- coding: utf-8 -*-
"""
演示数据生成脚本
生成采购订单、缺料预警、库存交易等演示数据
"""
import sys
import os
from decimal import Decimal
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.database import SessionLocal
from app.models.material import Material
from app.models.vendor import Vendor
from app.models.purchase import PurchaseRequest, PurchaseRequestItem, PurchaseOrder, PurchaseOrderItem
from app.models.shortage.alerts import ShortageAlert
from app.models.project import Project


def generate_purchase_requests(db, count=5):
    """生成采购申请演示数据"""
    print(f"  生成 {count} 个采购申请...")
    
    materials = db.query(Material).filter(Material.is_active == True).limit(10).all()
    projects = db.query(Project).filter(Project.is_active == True).limit(3).all()
    
    if not materials:
        print("    警告: 没有可用物料，跳过")
        return 0
    
    created = 0
    for i in range(count):
        project = random.choice(projects) if projects else None
        
        pr = PurchaseRequest(
            request_no=f"PR{datetime.utcnow().strftime('%Y%m%d')}{i+1:03d}",
            request_type=random.choice(["NORMAL", "SHORTAGE", "URGENT"]),
            project_id=project.id if project else None,
            status=random.choice(["DRAFT", "SUBMITTED", "APPROVED"]),
            remark=f"演示采购申请 {i+1}"
        )
        db.add(pr)
        db.flush()
        
        # 添加明细
        for j in range(random.randint(1, 3)):
            material = random.choice(materials)
            item = PurchaseRequestItem(
                request_id=pr.id,
                item_no=j+1,
                material_id=material.id,
                required_quantity=Decimal(str(random.randint(10, 100))),
                required_date=(datetime.utcnow() + timedelta(days=random.randint(7, 30))).date(),
                purpose="生产用料",
                urgency=random.choice(["NORMAL", "HIGH", "URGENT"])
            )
            db.add(item)
        
        created += 1
    
    db.commit()
    print(f"    ✅ 创建了 {created} 个采购申请")
    return created


def generate_purchase_orders(db, count=10):
    """生成采购订单演示数据"""
    print(f"  生成 {count} 个采购订单...")
    
    materials = db.query(Material).filter(Material.is_active == True).limit(10).all()
    suppliers = db.query(Vendor).filter(Vendor.is_active == True).all()
    projects = db.query(Project).filter(Project.is_active == True).limit(3).all()
    
    if not materials or not suppliers:
        print("    警告: 缺少物料或供应商数据，跳过")
        return 0
    
    created = 0
    for i in range(count):
        supplier = random.choice(suppliers)
        project = random.choice(projects) if projects else None
        
        po = PurchaseOrder(
            order_no=f"PO{datetime.utcnow().strftime('%Y%m%d')}{i+1:04d}",
            supplier_id=supplier.id,
            project_id=project.id if project else None,
            order_type=random.choice(["NORMAL", "URGENT"]),
            order_title=f"演示采购订单 {i+1}",
            order_date=datetime.utcnow().date(),
            required_date=(datetime.utcnow() + timedelta(days=random.randint(7, 30))).date(),
            status=random.choice(["DRAFT", "SUBMITTED", "APPROVED", "SENT", "CONFIRMED"]),
            payment_terms=supplier.payment_terms
        )
        db.add(po)
        db.flush()
        
        # 添加订单明细
        total_amount = Decimal("0")
        for j in range(random.randint(1, 5)):
            material = random.choice(materials)
            quantity = Decimal(str(random.randint(10, 100)))
            unit_price = material.standard_price or Decimal("100.00")
            amount = quantity * unit_price
            
            item = PurchaseOrderItem(
                order_id=po.id,
                item_no=j+1,
                material_id=material.id,
                material_code=material.material_code,
                material_name=material.material_name,
                specification=material.specification,
                unit=material.unit,
                quantity=quantity,
                unit_price=unit_price,
                amount=amount,
                required_date=po.required_date
            )
            db.add(item)
            total_amount += amount
        
        # 更新订单总额
        po.total_amount = total_amount
        po.tax_amount = total_amount * Decimal("0.13")
        po.amount_with_tax = total_amount + po.tax_amount
        
        created += 1
    
    db.commit()
    print(f"    ✅ 创建了 {created} 个采购订单")
    return created


def generate_shortage_alerts(db, count=8):
    """生成缺料预警演示数据"""
    print(f"  生成 {count} 个缺料预警...")
    
    # 查找库存低于安全库存的物料
    low_stock_materials = db.query(Material).filter(
        Material.current_stock < Material.safety_stock,
        Material.is_active == True
    ).all()
    
    projects = db.query(Project).filter(Project.is_active == True).limit(3).all()
    
    if not low_stock_materials:
        print("    警告: 没有低库存物料，跳过")
        return 0
    
    created = 0
    for material in low_stock_materials[:count]:
        project = random.choice(projects) if projects else None
        
        shortage_qty = material.safety_stock - material.current_stock
        
        alert = ShortageAlert(
            material_id=material.id,
            project_id=project.id if project else None,
            shortage_quantity=shortage_qty,
            alert_level="HIGH" if material.is_key_material else "MEDIUM",
            alert_type="LOW_STOCK",
            required_date=(datetime.utcnow() + timedelta(days=material.lead_time_days or 7)).date(),
            status="ACTIVE",
            description=f"{material.material_name} 库存低于安全库存"
        )
        db.add(alert)
        created += 1
    
    db.commit()
    print(f"    ✅ 创建了 {created} 个缺料预警")
    return created


def main():
    """生成演示数据"""
    
    print("=" * 80)
    print("生成演示数据")
    print("=" * 80)
    print()
    
    db = SessionLocal()
    
    try:
        # 生成采购申请
        print("1. 生成采购申请...")
        pr_count = generate_purchase_requests(db, count=5)
        print()
        
        # 生成采购订单
        print("2. 生成采购订单...")
        po_count = generate_purchase_orders(db, count=10)
        print()
        
        # 生成缺料预警
        print("3. 生成缺料预警...")
        alert_count = generate_shortage_alerts(db, count=8)
        print()
        
        # 汇总
        print("=" * 80)
        print("演示数据生成完成！")
        print("=" * 80)
        print(f"  采购申请: {pr_count}个")
        print(f"  采购订单: {po_count}个")
        print(f"  缺料预警: {alert_count}个")
        print("=" * 80)
        print()
        print("✅ 演示数据生成成功！")
        print("现在可以启动服务器测试系统功能。")
        print()
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
