# -*- coding: utf-8 -*-
"""
供应商数据初始化脚本
"""
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.vendor import Vendor


def init_suppliers(db: Session):
    """初始化供应商数据"""
    
    suppliers_data = [
        {
            "vendor_code": "SUP_METAL_001",
            "vendor_name": "上海金属材料有限公司",
            "vendor_type": "SUPPLIER",
            "contact_person": "张经理",
            "contact_phone": "021-12345678",
            "email": "zhang@metalsupply.com",
            "address": "上海市浦东新区XX路123号",
            "credit_rating": "A",
            "payment_terms": "月结30天",
            "is_active": True,
            "remark": "主要供应不锈钢板材"
        },
        {
            "vendor_code": "SUP_ALUMINUM_002",
            "vendor_name": "广东铝材供应商",
            "vendor_type": "SUPPLIER",
            "contact_person": "李总",
            "contact_phone": "0755-87654321",
            "email": "li@aluminum.com",
            "address": "广东省深圳市宝安区XX路456号",
            "credit_rating": "B+",
            "payment_terms": "货到付款",
            "is_active": True,
            "remark": "铝合金型材专业供应商"
        },
        {
            "vendor_code": "SUP_MOTOR_003",
            "vendor_name": "江苏电机制造厂",
            "vendor_type": "SUPPLIER",
            "contact_person": "王工",
            "contact_phone": "025-11112222",
            "email": "wang@motor.com",
            "address": "江苏省南京市江宁区XX路789号",
            "credit_rating": "A+",
            "payment_terms": "月结60天",
            "is_active": True,
            "remark": "各类电机供应，质量可靠"
        },
        {
            "vendor_code": "SUP_BEARING_004",
            "vendor_name": "浙江轴承有限公司",
            "vendor_type": "SUPPLIER",
            "contact_person": "赵总",
            "contact_phone": "0571-88888888",
            "email": "zhao@bearing.com",
            "address": "浙江省杭州市XX区XX路321号",
            "credit_rating": "A",
            "payment_terms": "月结45天",
            "is_active": True,
            "remark": "进口和国产轴承供应"
        },
        {
            "vendor_code": "SUP_ELECTRONIC_005",
            "vendor_name": "深圳电子元器件商行",
            "vendor_type": "SUPPLIER",
            "contact_person": "孙经理",
            "contact_phone": "0755-66666666",
            "email": "sun@electronics.com",
            "address": "广东省深圳市福田区XX路654号",
            "credit_rating": "B",
            "payment_terms": "款到发货",
            "is_active": True,
            "remark": "各类电子元器件"
        },
        {
            "vendor_code": "SUP_FASTENER_006",
            "vendor_name": "上海标准件批发中心",
            "vendor_type": "SUPPLIER",
            "contact_person": "周总",
            "contact_phone": "021-55555555",
            "email": "zhou@fastener.com",
            "address": "上海市松江区XX路987号",
            "credit_rating": "B+",
            "payment_terms": "月结30天",
            "is_active": True,
            "remark": "各类标准件紧固件"
        },
        {
            "vendor_code": "SUP_PLASTIC_007",
            "vendor_name": "江苏塑料制品厂",
            "vendor_type": "SUPPLIER",
            "contact_person": "吴经理",
            "contact_phone": "0512-77777777",
            "email": "wu@plastic.com",
            "address": "江苏省苏州市XX区XX路147号",
            "credit_rating": "A-",
            "payment_terms": "月结30天",
            "is_active": True,
            "remark": "工程塑料和塑料制品"
        },
        {
            "vendor_code": "SUP_RUBBER_008",
            "vendor_name": "广州橡胶密封件公司",
            "vendor_type": "SUPPLIER",
            "contact_person": "郑总",
            "contact_phone": "020-99999999",
            "email": "zheng@rubber.com",
            "address": "广东省广州市白云区XX路258号",
            "credit_rating": "B+",
            "payment_terms": "货到付款",
            "is_active": True,
            "remark": "各类橡胶密封件"
        },
        {
            "vendor_code": "SUP_HYDRAULIC_009",
            "vendor_name": "山东液压气动设备厂",
            "vendor_type": "SUPPLIER",
            "contact_person": "冯工",
            "contact_phone": "0531-44444444",
            "email": "feng@hydraulic.com",
            "address": "山东省济南市XX区XX路369号",
            "credit_rating": "A",
            "payment_terms": "月结45天",
            "is_active": True,
            "remark": "液压气动元件"
        },
        {
            "vendor_code": "SUP_SENSOR_010",
            "vendor_name": "北京传感器技术公司",
            "vendor_type": "SUPPLIER",
            "contact_person": "陈工",
            "contact_phone": "010-33333333",
            "email": "chen@sensor.com",
            "address": "北京市海淀区XX路753号",
            "credit_rating": "A+",
            "payment_terms": "月结60天",
            "is_active": True,
            "remark": "各类工业传感器"
        }
    ]
    
    created_count = 0
    updated_count = 0
    
    for supplier_data in suppliers_data:
        existing = db.query(Vendor).filter(
            Vendor.vendor_code == supplier_data["vendor_code"]
        ).first()
        
        if existing:
            # 更新现有供应商
            for key, value in supplier_data.items():
                setattr(existing, key, value)
            updated_count += 1
            print(f"  更新供应商: {supplier_data['vendor_name']}")
        else:
            # 创建新供应商
            supplier = Vendor(**supplier_data)
            db.add(supplier)
            created_count += 1
            print(f"  创建供应商: {supplier_data['vendor_name']}")
    
    db.commit()
    
    print(f"\n✅ 供应商数据初始化完成")
    print(f"   新创建: {created_count}个")
    print(f"   已更新: {updated_count}个")
    print(f"   总计: {created_count + updated_count}个供应商")
    
    return created_count + updated_count


if __name__ == "__main__":
    db = SessionLocal()
    try:
        count = init_suppliers(db)
        print(f"\n初始化了 {count} 个供应商")
    finally:
        db.close()
