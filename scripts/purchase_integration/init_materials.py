# -*- coding: utf-8 -*-
"""
物料数据初始化脚本
"""
from decimal import Decimal
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.material import Material, MaterialCategory


def init_material_categories(db: Session):
    """初始化物料分类"""
    
    categories_data = [
        {"code": "RAW_METAL", "name": "原材料-金属", "level": 1, "parent": None},
        {"code": "RAW_PLASTIC", "name": "原材料-塑料", "level": 1, "parent": None},
        {"code": "RAW_RUBBER", "name": "原材料-橡胶", "level": 1, "parent": None},
        {"code": "MOTOR", "name": "电机", "level": 1, "parent": None},
        {"code": "BEARING", "name": "轴承", "level": 1, "parent": None},
        {"code": "SENSOR", "name": "传感器", "level": 1, "parent": None},
        {"code": "FASTENER", "name": "紧固件", "level": 1, "parent": None},
        {"code": "HYDRAULIC", "name": "液压气动", "level": 1, "parent": None},
        {"code": "ELECTRONIC", "name": "电子元器件", "level": 1, "parent": None},
        {"code": "SEMI_FINISHED", "name": "半成品", "level": 1, "parent": None}
    ]
    
    category_map = {}
    
    for cat_data in categories_data:
        existing = db.query(MaterialCategory).filter(
            MaterialCategory.category_code == cat_data["code"]
        ).first()
        
        if existing:
            category_map[cat_data["code"]] = existing
            print(f"  分类已存在: {cat_data['name']}")
        else:
            category = MaterialCategory(
                category_code=cat_data["code"],
                category_name=cat_data["name"],
                level=cat_data["level"],
                is_active=True
            )
            db.add(category)
            db.flush()
            category_map[cat_data["code"]] = category
            print(f"  创建分类: {cat_data['name']}")
    
    db.commit()
    return category_map


def init_materials(db: Session):
    """初始化物料数据"""
    
    # 先初始化分类
    categories = init_material_categories(db)
    
    materials_data = [
        # 金属材料
        {
            "code": "M_STEEL_304_1.5",
            "name": "不锈钢板 304",
            "category": "RAW_METAL",
            "spec": "1.5mm*1220*2440",
            "unit": "张",
            "type": "RAW_MATERIAL",
            "brand": "宝钢",
            "price": Decimal("350.00"),
            "safety_stock": Decimal("50"),
            "current_stock": Decimal("80"),
            "lead_time": 7,
            "min_qty": Decimal("10"),
            "is_key": True
        },
        {
            "code": "M_ALUMINUM_6061_50",
            "name": "铝合金型材 6061",
            "category": "RAW_METAL",
            "spec": "50*50*3mm",
            "unit": "米",
            "type": "RAW_MATERIAL",
            "brand": "南山铝业",
            "price": Decimal("45.50"),
            "safety_stock": Decimal("200"),
            "current_stock": Decimal("350"),
            "lead_time": 5,
            "min_qty": Decimal("50"),
            "is_key": False
        },
        {
            "code": "M_STEEL_Q235_3",
            "name": "碳钢板 Q235",
            "category": "RAW_METAL",
            "spec": "3mm*1500*6000",
            "unit": "张",
            "type": "RAW_MATERIAL",
            "brand": "鞍钢",
            "price": Decimal("280.00"),
            "safety_stock": Decimal("30"),
            "current_stock": Decimal("45"),
            "lead_time": 7,
            "min_qty": Decimal("5"),
            "is_key": True
        },
        
        # 电机
        {
            "code": "M_MOTOR_AC220_0.75KW",
            "name": "三相异步电机",
            "category": "MOTOR",
            "spec": "AC220V 0.75KW 1400rpm",
            "unit": "台",
            "type": "PURCHASED_PART",
            "brand": "ABB",
            "price": Decimal("680.00"),
            "safety_stock": Decimal("10"),
            "current_stock": Decimal("15"),
            "lead_time": 10,
            "min_qty": Decimal("5"),
            "is_key": True
        },
        {
            "code": "M_MOTOR_AC380_1.5KW",
            "name": "三相异步电机",
            "category": "MOTOR",
            "spec": "AC380V 1.5KW 1450rpm",
            "unit": "台",
            "type": "PURCHASED_PART",
            "brand": "西门子",
            "price": Decimal("1200.00"),
            "safety_stock": Decimal("5"),
            "current_stock": Decimal("8"),
            "lead_time": 15,
            "min_qty": Decimal("2"),
            "is_key": True
        },
        {
            "code": "M_STEPPER_MOTOR_57",
            "name": "步进电机",
            "category": "MOTOR",
            "spec": "57步进 1.8度 2相",
            "unit": "台",
            "type": "PURCHASED_PART",
            "brand": "雷赛",
            "price": Decimal("180.00"),
            "safety_stock": Decimal("20"),
            "current_stock": Decimal("35"),
            "lead_time": 7,
            "min_qty": Decimal("10"),
            "is_key": False
        },
        
        # 轴承
        {
            "code": "M_BEARING_6205",
            "name": "深沟球轴承",
            "category": "BEARING",
            "spec": "6205-2RS",
            "unit": "个",
            "type": "PURCHASED_PART",
            "brand": "SKF",
            "price": Decimal("25.00"),
            "safety_stock": Decimal("100"),
            "current_stock": Decimal("150"),
            "lead_time": 5,
            "min_qty": Decimal("50"),
            "is_key": False
        },
        {
            "code": "M_BEARING_6305",
            "name": "深沟球轴承",
            "category": "BEARING",
            "spec": "6305-ZZ",
            "unit": "个",
            "type": "PURCHASED_PART",
            "brand": "NSK",
            "price": Decimal("35.00"),
            "safety_stock": Decimal("80"),
            "current_stock": Decimal("120"),
            "lead_time": 5,
            "min_qty": Decimal("40"),
            "is_key": False
        },
        
        # 传感器
        {
            "code": "M_SENSOR_PROX_M18",
            "name": "接近传感器",
            "category": "SENSOR",
            "spec": "M18 NPN NO DC10-30V",
            "unit": "个",
            "type": "PURCHASED_PART",
            "brand": "欧姆龙",
            "price": Decimal("85.00"),
            "safety_stock": Decimal("30"),
            "current_stock": Decimal("45"),
            "lead_time": 7,
            "min_qty": Decimal("10"),
            "is_key": True
        },
        {
            "code": "M_SENSOR_PHOTO_E3Z",
            "name": "光电传感器",
            "category": "SENSOR",
            "spec": "E3Z-D87 反射型 2m",
            "unit": "个",
            "type": "PURCHASED_PART",
            "brand": "欧姆龙",
            "price": Decimal("120.00"),
            "safety_stock": Decimal("20"),
            "current_stock": Decimal("28"),
            "lead_time": 7,
            "min_qty": Decimal("10"),
            "is_key": True
        },
        
        # 紧固件
        {
            "code": "M_BOLT_M8_30",
            "name": "六角螺栓",
            "category": "FASTENER",
            "spec": "M8*30 8.8级",
            "unit": "个",
            "type": "PURCHASED_PART",
            "brand": "标准件",
            "price": Decimal("0.15"),
            "safety_stock": Decimal("1000"),
            "current_stock": Decimal("2500"),
            "lead_time": 3,
            "min_qty": Decimal("500"),
            "is_key": False
        },
        {
            "code": "M_NUT_M8",
            "name": "六角螺母",
            "category": "FASTENER",
            "spec": "M8 8级",
            "unit": "个",
            "type": "PURCHASED_PART",
            "brand": "标准件",
            "price": Decimal("0.08"),
            "safety_stock": Decimal("1000"),
            "current_stock": Decimal("3000"),
            "lead_time": 3,
            "min_qty": Decimal("500"),
            "is_key": False
        },
        
        # 液压气动
        {
            "code": "M_CYLINDER_MAL25_100",
            "name": "气缸",
            "category": "HYDRAULIC",
            "spec": "MAL25*100 双作用",
            "unit": "个",
            "type": "PURCHASED_PART",
            "brand": "SMC",
            "price": Decimal("280.00"),
            "safety_stock": Decimal("10"),
            "current_stock": Decimal("12"),
            "lead_time": 10,
            "min_qty": Decimal("5"),
            "is_key": True
        },
        {
            "code": "M_VALVE_SY5120",
            "name": "电磁阀",
            "category": "HYDRAULIC",
            "spec": "SY5120-5LZD DC24V",
            "unit": "个",
            "type": "PURCHASED_PART",
            "brand": "SMC",
            "price": Decimal("380.00"),
            "safety_stock": Decimal("15"),
            "current_stock": Decimal("18"),
            "lead_time": 10,
            "min_qty": Decimal("5"),
            "is_key": True
        },
        
        # 电子元器件
        {
            "code": "M_PLC_FX3U_32MT",
            "name": "PLC",
            "category": "ELECTRONIC",
            "spec": "FX3U-32MT/ESS",
            "unit": "台",
            "type": "PURCHASED_PART",
            "brand": "三菱",
            "price": Decimal("2800.00"),
            "safety_stock": Decimal("3"),
            "current_stock": Decimal("5"),
            "lead_time": 15,
            "min_qty": Decimal("1"),
            "is_key": True
        },
        {
            "code": "M_HMI_7INCH",
            "name": "触摸屏",
            "category": "ELECTRONIC",
            "spec": "7寸彩色触摸屏",
            "unit": "台",
            "type": "PURCHASED_PART",
            "brand": "威纶通",
            "price": Decimal("1200.00"),
            "safety_stock": Decimal("5"),
            "current_stock": Decimal("6"),
            "lead_time": 10,
            "min_qty": Decimal("2"),
            "is_key": True
        }
    ]
    
    created_count = 0
    updated_count = 0
    
    for mat_data in materials_data:
        category_code = mat_data["category"]
        category = categories.get(category_code)
        
        if not category:
            print(f"  警告: 分类 {category_code} 不存在，跳过物料 {mat_data['name']}")
            continue
        
        existing = db.query(Material).filter(
            Material.material_code == mat_data["code"]
        ).first()
        
        if existing:
            # 更新现有物料
            existing.material_name = mat_data["name"]
            existing.category_id = category.id
            existing.specification = mat_data["spec"]
            existing.unit = mat_data["unit"]
            existing.material_type = mat_data["type"]
            existing.brand = mat_data["brand"]
            existing.standard_price = mat_data["price"]
            existing.safety_stock = mat_data["safety_stock"]
            existing.current_stock = mat_data["current_stock"]
            existing.lead_time_days = mat_data["lead_time"]
            existing.min_order_qty = mat_data["min_qty"]
            existing.is_key_material = mat_data["is_key"]
            updated_count += 1
            print(f"  更新物料: {mat_data['name']}")
        else:
            # 创建新物料
            material = Material(
                material_code=mat_data["code"],
                material_name=mat_data["name"],
                category_id=category.id,
                specification=mat_data["spec"],
                unit=mat_data["unit"],
                material_type=mat_data["type"],
                brand=mat_data["brand"],
                standard_price=mat_data["price"],
                safety_stock=mat_data["safety_stock"],
                current_stock=mat_data["current_stock"],
                lead_time_days=mat_data["lead_time"],
                min_order_qty=mat_data["min_qty"],
                is_key_material=mat_data["is_key"],
                is_active=True
            )
            db.add(material)
            created_count += 1
            print(f"  创建物料: {mat_data['name']}")
    
    db.commit()
    
    print(f"\n✅ 物料数据初始化完成")
    print(f"   新创建: {created_count}个")
    print(f"   已更新: {updated_count}个")
    print(f"   总计: {created_count + updated_count}个物料")
    
    return created_count + updated_count


if __name__ == "__main__":
    db = SessionLocal()
    try:
        count = init_materials(db)
        print(f"\n初始化了 {count} 个物料")
    finally:
        db.close()
