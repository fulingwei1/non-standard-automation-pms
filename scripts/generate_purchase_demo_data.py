# -*- coding: utf-8 -*-
"""
生成采购模块演示数据 - 简化版
"""

import sys
sys.path.insert(0, '/Users/flw/non-standard-automation-pm')

from sqlalchemy.orm import Session
from app.models.base import SessionLocal
from app.models.user import User, Role, UserRole
from app.models.purchase import PurchaseRequest, PurchaseRequestItem
from app.models.material import Material, BomHeader, BomItem, MaterialCategory

def create_purchase_manager(db: Session):
    """确保有采购经理角色"""
    role = db.query(Role).filter(Role.role_code == "PURCHASE_MANAGER").first()
    if not role:
        role = Role(role_code="PURCHASE_MANAGER", role_name="采购经理", description="负责采购订单审批")
        db.add(role)
        db.commit()
        db.refresh(role)
        print(f"✅ 创建角色：采购经理")
    
    user_role = db.query(UserRole).filter(UserRole.user_id == 1, UserRole.role_id == role.id).first()
    if not user_role:
        user_role = UserRole(user_id=1, role_id=role.id)
        db.add(user_role)
        db.commit()
        print(f"✅ 分配采购经理角色给 admin")
    return role

def create_materials(db: Session):
    """生成物料数据（带安全库存）"""
    # 先创建分类
    cat = db.query(MaterialCategory).filter(MaterialCategory.category_code == "ELECTRICAL").first()
    if not cat:
        cat = MaterialCategory(category_code="ELECTRICAL", category_name="电气件", level=1, is_active=True)
        db.add(cat)
        db.commit()
        db.refresh(cat)
    
    materials_data = [
        {"code": "MAT001", "name": "PLC 西门子 S7-1200", "safety_stock": 20, "stock": 5},
        {"code": "MAT002", "name": "伺服电机 750W", "safety_stock": 15, "stock": 3},
        {"code": "MAT003", "name": "气缸 SMC CDQ2", "safety_stock": 50, "stock": 10},
        {"code": "MAT004", "name": "电磁阀 SMC SY3000", "safety_stock": 40, "stock": 8},
        {"code": "MAT005", "name": "触摸屏 昆仑通态 7 寸", "safety_stock": 10, "stock": 2},
    ]
    
    created = []
    for mat in materials_data:
        existing = db.query(Material).filter(Material.material_code == mat["code"]).first()
        if existing:
            continue
        material = Material(
            material_code=mat["code"],
            material_name=mat["name"],
            category_id=cat.id,
            unit="个",
            safety_stock=mat["safety_stock"],
            current_stock=mat["stock"],
        )
        db.add(material)
        created.append(mat["code"])
    
    db.commit()
    print(f"✅ 创建 {len(created)} 个物料：{', '.join(created)}")
    return created

def create_purchase_requests(db: Session):
    """生成采购申请（待审批）"""
    from datetime import date
    materials = db.query(Material).limit(5).all()
    if not materials:
        print("⚠️ 没有物料，跳过采购申请")
        return
    
    pr = PurchaseRequest(
        request_code=f"PR{date.today().strftime('%Y%m%d')}001",
        project_id=1,
        status="SUBMITTED",
        created_by=1,
        submitted_by=1,
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)
    
    for mat in materials[:3]:
        item = PurchaseRequestItem(
            purchase_request_id=pr.id,
            material_id=mat.id,
            quantity=mat.safety_stock - mat.current_stock,
            unit=mat.unit,
            reason="安全库存补充",
        )
        db.add(item)
    
    db.commit()
    print(f"✅ 创建采购申请：{pr.request_code}（待审批）")
    return pr

def main():
    from datetime import date, timedelta
    print("=" * 60)
    print("生成采购模块演示数据")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        create_purchase_manager(db)
        create_materials(db)
        create_purchase_requests(db)
        print("=" * 60)
        print("✅ 演示数据生成完成！")
        print("=" * 60)
    finally:
        db.close()

if __name__ == "__main__":
    main()
