# -*- coding: utf-8 -*-
"""
优势产品管理模型

管理公司优势产品（宣传册产品），用于：
1. 销售线索填写时优先选择
2. 中标率预测模型的产品因子计算
3. AI秒出方案的产品匹配
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin

# ==================== 行业分类 ====================

class Industry(Base, TimestampMixin):
    """行业分类表

    定义公司服务的各个行业，用于：
    1. 销售线索行业归类
    2. 优势产品与行业匹配
    3. 方案模板与行业关联
    """

    __tablename__ = "industries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, comment="行业编码")
    name = Column(String(100), nullable=False, comment="行业名称")
    parent_id = Column(Integer, ForeignKey("industries.id"), comment="父级行业ID（支持多级分类）")
    description = Column(Text, comment="行业描述")
    typical_products = Column(Text, comment="典型产品类型（JSON Array）")
    typical_tests = Column(Text, comment="典型测试类型（JSON Array）")
    market_size = Column(String(50), comment="市场规模评估：LARGE/MEDIUM/SMALL")
    growth_potential = Column(String(50), comment="增长潜力：HIGH/MEDIUM/LOW")
    company_experience = Column(String(50), comment="公司经验：EXPERT/EXPERIENCED/LEARNING/NEW")
    sort_order = Column(Integer, default=0, comment="排序序号")
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 关系
    children = relationship("Industry", backref="parent", remote_side=[id])
    category_mappings = relationship("IndustryCategoryMapping", back_populates="industry", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_industry_code", "code"),
        Index("idx_industry_parent", "parent_id"),
        Index("idx_industry_active", "is_active"),
    )

    def __repr__(self):
        return f"<Industry {self.code}: {self.name}>"


class IndustryCategoryMapping(Base, TimestampMixin):
    """行业-产品类别映射表

    定义每个行业适用哪些优势产品类别，以及匹配度
    """

    __tablename__ = "industry_category_mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    industry_id = Column(Integer, ForeignKey("industries.id"), nullable=False, comment="行业ID")
    category_id = Column(Integer, ForeignKey("advantage_product_categories.id"), nullable=False, comment="产品类别ID")
    match_score = Column(Integer, default=100, comment="匹配度分数（0-100），100表示最匹配")
    is_primary = Column(Boolean, default=False, comment="是否主要适用类别")
    typical_scenarios = Column(Text, comment="典型应用场景（JSON Array）")

    # 关系
    industry = relationship("Industry", back_populates="category_mappings")
    category = relationship("AdvantageProductCategory", back_populates="industry_mappings")

    __table_args__ = (
        Index("idx_ind_cat_mapping_industry", "industry_id"),
        Index("idx_ind_cat_mapping_category", "category_id"),
        Index("idx_ind_cat_mapping_primary", "is_primary"),
    )

    def __repr__(self):
        return f"<IndustryCategoryMapping industry={self.industry_id} category={self.category_id}>"


class AdvantageProductCategory(Base, TimestampMixin):
    """优势产品类别

    如：白色家电、汽车电子、新能源、半导体、电动工具、自动化线体、其他设备、教育实训
    """

    __tablename__ = "advantage_product_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, comment="类别编码")
    name = Column(String(100), nullable=False, comment="类别名称")
    description = Column(Text, comment="类别描述")
    test_types = Column(Text, comment="适用测试类型（JSON Array）：ICT/FCT/EOL/老化/视觉等")
    typical_ct_range = Column(String(50), comment="典型节拍范围：如10-30秒")
    automation_levels = Column(Text, comment="支持的自动化程度（JSON Array）")
    sort_order = Column(Integer, default=0, comment="排序序号")
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 关系
    products = relationship("AdvantageProduct", back_populates="category", lazy="dynamic")
    industry_mappings = relationship("IndustryCategoryMapping", back_populates="category", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_adv_category_code", "code"),
        Index("idx_adv_category_active", "is_active"),
    )

    def __repr__(self):
        return f"<AdvantageProductCategory {self.code}: {self.name}>"


class AdvantageProduct(Base, TimestampMixin):
    """优势产品

    公司优势产品/宣传册产品，用于销售线索评估和AI方案生成
    """

    __tablename__ = "advantage_products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_code = Column(String(50), unique=True, nullable=False, comment="产品编码（如KC2701）")
    product_name = Column(String(200), nullable=False, comment="产品名称")
    category_id = Column(Integer, ForeignKey("advantage_product_categories.id"), comment="所属类别")
    series_code = Column(String(50), comment="产品系列编码（如KC2700）")
    description = Column(Text, comment="产品描述")

    # 技术参数（用于AI方案生成）
    test_types = Column(Text, comment="支持的测试类型（JSON Array）")
    typical_ct_seconds = Column(Integer, comment="典型节拍时间（秒）")
    max_throughput_uph = Column(Integer, comment="最大产能（UPH）")
    automation_level = Column(String(50), comment="自动化程度：MANUAL/SEMI_AUTO/FULL_AUTO")
    rail_type = Column(String(50), comment="轨道类型：SINGLE/DUAL/MULTI")
    workstation_count = Column(Integer, comment="工位数量")

    # 适用场景
    applicable_products = Column(Text, comment="适用产品类型（JSON Array）")
    applicable_interfaces = Column(Text, comment="支持的接口类型（JSON Array）")
    special_features = Column(Text, comment="特殊功能（JSON Array）：如3D SPI、视觉检测等")

    # 商务信息
    reference_price_min = Column(Numeric(14, 2), comment="参考价格下限")
    reference_price_max = Column(Numeric(14, 2), comment="参考价格上限")
    typical_lead_time_days = Column(Integer, comment="典型交期（天）")

    # 匹配权重
    match_keywords = Column(Text, comment="匹配关键词（JSON Array），用于AI智能推荐")
    priority_score = Column(Integer, default=50, comment="优先推荐分数（0-100），越高越优先推荐")

    is_active = Column(Boolean, default=True, comment="是否启用")

    # 关系
    category = relationship("AdvantageProductCategory", back_populates="products")

    __table_args__ = (
        Index("idx_adv_product_code", "product_code"),
        Index("idx_adv_product_category", "category_id"),
        Index("idx_adv_product_series", "series_code"),
        Index("idx_adv_product_active", "is_active"),
    )

    def __repr__(self):
        return f"<AdvantageProduct {self.product_code}: {self.product_name}>"


# 默认类别配置（用于初始化）
DEFAULT_CATEGORIES = [
    {"code": "HOME_APPLIANCE", "name": "白色家电", "sort_order": 1},
    {"code": "AUTOMOTIVE", "name": "汽车电子", "sort_order": 2},
    {"code": "NEW_ENERGY", "name": "新能源", "sort_order": 3},
    {"code": "SEMICONDUCTOR", "name": "半导体", "sort_order": 4},
    {"code": "POWER_TOOL", "name": "电动工具", "sort_order": 5},
    {"code": "AUTOMATION_LINE", "name": "自动化线体", "sort_order": 6},
    {"code": "OTHER_EQUIPMENT", "name": "其他设备", "sort_order": 7},
    {"code": "EDUCATION", "name": "教育实训", "sort_order": 8},
]

# 类别名称到编码的映射（用于 Excel 导入）
CATEGORY_NAME_TO_CODE = {cat["name"]: cat["code"] for cat in DEFAULT_CATEGORIES}


# ==================== 新产品请求 ====================

class NewProductRequest(Base, TimestampMixin):
    """新产品请求表

    当销售选择的产品不在优势产品列表中时，需要填写此表
    用于：
    1. 评估新产品开发价值
    2. 积累市场需求数据
    3. 后续可能转为优势产品
    """

    __tablename__ = "new_product_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, comment="关联线索ID")

    # 产品信息
    product_name = Column(String(200), nullable=False, comment="产品名称")
    product_type = Column(String(100), comment="产品类型")
    industry_id = Column(Integer, ForeignKey("industries.id"), comment="建议归属行业")
    category_id = Column(Integer, ForeignKey("advantage_product_categories.id"), comment="建议归属类别")

    # 需求描述
    test_requirements = Column(Text, comment="测试需求描述")
    capacity_requirements = Column(Text, comment="产能需求")
    special_requirements = Column(Text, comment="特殊要求")

    # 市场信息
    market_potential = Column(String(50), comment="市场潜力评估：HIGH/MEDIUM/LOW")
    similar_customers = Column(Text, comment="有类似需求的其他客户（JSON Array）")
    estimated_annual_demand = Column(Integer, comment="预估年需求量")

    # 审核状态
    review_status = Column(String(20), default="PENDING", comment="审核状态：PENDING/APPROVED/REJECTED/CONVERTED")
    reviewer_id = Column(Integer, ForeignKey("users.id"), comment="审核人ID")
    reviewed_at = Column(DateTime, comment="审核时间")
    review_comment = Column(Text, comment="审核意见")

    # 转化为优势产品
    converted_product_id = Column(Integer, ForeignKey("advantage_products.id"), comment="转化后的优势产品ID")

    # 关系
    industry = relationship("Industry", foreign_keys=[industry_id])
    category = relationship("AdvantageProductCategory", foreign_keys=[category_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    converted_product = relationship("AdvantageProduct", foreign_keys=[converted_product_id])

    __table_args__ = (
        Index("idx_new_product_lead", "lead_id"),
        Index("idx_new_product_status", "review_status"),
        Index("idx_new_product_industry", "industry_id"),
    )

    def __repr__(self):
        return f"<NewProductRequest {self.id}: {self.product_name}>"


# ==================== 默认行业配置 ====================

DEFAULT_INDUSTRIES = [
    # 一级行业
    {"code": "3C_ELECTRONICS", "name": "3C电子", "sort_order": 1, "market_size": "LARGE", "growth_potential": "MEDIUM", "company_experience": "EXPERT"},
    {"code": "AUTOMOTIVE", "name": "汽车电子", "sort_order": 2, "market_size": "LARGE", "growth_potential": "HIGH", "company_experience": "EXPERT"},
    {"code": "NEW_ENERGY", "name": "新能源", "sort_order": 3, "market_size": "LARGE", "growth_potential": "HIGH", "company_experience": "EXPERIENCED"},
    {"code": "HOME_APPLIANCE", "name": "家电", "sort_order": 4, "market_size": "LARGE", "growth_potential": "LOW", "company_experience": "EXPERT"},
    {"code": "MEDICAL_DEVICE", "name": "医疗器械", "sort_order": 5, "market_size": "MEDIUM", "growth_potential": "HIGH", "company_experience": "LEARNING"},
    {"code": "INDUSTRIAL_CONTROL", "name": "工业控制", "sort_order": 6, "market_size": "MEDIUM", "growth_potential": "MEDIUM", "company_experience": "EXPERIENCED"},
    {"code": "SEMICONDUCTOR", "name": "半导体", "sort_order": 7, "market_size": "LARGE", "growth_potential": "HIGH", "company_experience": "EXPERIENCED"},
    {"code": "COMMUNICATION", "name": "通信设备", "sort_order": 8, "market_size": "LARGE", "growth_potential": "MEDIUM", "company_experience": "EXPERIENCED"},
    {"code": "POWER_TOOLS", "name": "电动工具", "sort_order": 9, "market_size": "MEDIUM", "growth_potential": "MEDIUM", "company_experience": "EXPERT"},
    {"code": "LIGHTING", "name": "照明", "sort_order": 10, "market_size": "MEDIUM", "growth_potential": "LOW", "company_experience": "EXPERIENCED"},
    {"code": "AEROSPACE", "name": "航空航天", "sort_order": 11, "market_size": "MEDIUM", "growth_potential": "HIGH", "company_experience": "LEARNING"},
    {"code": "MILITARY", "name": "军工", "sort_order": 12, "market_size": "MEDIUM", "growth_potential": "MEDIUM", "company_experience": "LEARNING"},
    {"code": "EDUCATION", "name": "教育科研", "sort_order": 13, "market_size": "SMALL", "growth_potential": "MEDIUM", "company_experience": "EXPERIENCED"},
    {"code": "OTHER", "name": "其他行业", "sort_order": 99, "market_size": "SMALL", "growth_potential": "LOW", "company_experience": "LEARNING"},
]

# 二级行业（子行业）
DEFAULT_SUB_INDUSTRIES = [
    # 3C电子子行业
    {"code": "MOBILE_PHONE", "name": "手机", "parent_code": "3C_ELECTRONICS", "typical_products": '["手机主板", "摄像头模组", "触摸屏", "电池"]'},
    {"code": "TABLET", "name": "平板电脑", "parent_code": "3C_ELECTRONICS", "typical_products": '["主板", "显示屏", "电池包"]'},
    {"code": "LAPTOP", "name": "笔记本电脑", "parent_code": "3C_ELECTRONICS", "typical_products": '["主板", "键盘", "电源适配器"]'},
    {"code": "WEARABLE", "name": "可穿戴设备", "parent_code": "3C_ELECTRONICS", "typical_products": '["智能手表", "TWS耳机", "手环"]'},
    {"code": "CHARGER", "name": "充电器/适配器", "parent_code": "3C_ELECTRONICS", "typical_products": '["充电器", "适配器", "充电宝"]'},

    # 汽车电子子行业
    {"code": "AUTO_ECU", "name": "ECU/控制器", "parent_code": "AUTOMOTIVE", "typical_products": '["域控制器", "BMS", "MCU", "VCU"]'},
    {"code": "AUTO_SENSOR", "name": "汽车传感器", "parent_code": "AUTOMOTIVE", "typical_products": '["毫米波雷达", "激光雷达", "摄像头"]'},
    {"code": "AUTO_MOTOR", "name": "汽车电机", "parent_code": "AUTOMOTIVE", "typical_products": '["驱动电机", "转向电机", "车窗电机"]'},
    {"code": "AUTO_LIGHTING", "name": "汽车车灯", "parent_code": "AUTOMOTIVE", "typical_products": '["LED大灯", "尾灯", "转向灯"]'},
    {"code": "AUTO_CHARGING", "name": "汽车充电", "parent_code": "AUTOMOTIVE", "typical_products": '["OBC", "DC-DC", "充电桩"]'},

    # 新能源子行业
    {"code": "BATTERY_PACK", "name": "动力电池", "parent_code": "NEW_ENERGY", "typical_products": '["电芯", "模组", "PACK"]'},
    {"code": "ENERGY_STORAGE", "name": "储能系统", "parent_code": "NEW_ENERGY", "typical_products": '["储能电池", "BMS", "PCS"]'},
    {"code": "PV_INVERTER", "name": "光伏逆变", "parent_code": "NEW_ENERGY", "typical_products": '["逆变器", "优化器", "汇流箱"]'},
    {"code": "CHARGING_PILE", "name": "充电桩", "parent_code": "NEW_ENERGY", "typical_products": '["直流桩", "交流桩", "充电模块"]'},

    # 家电子行业
    {"code": "WHITE_APPLIANCE", "name": "白色家电", "parent_code": "HOME_APPLIANCE", "typical_products": '["空调", "冰箱", "洗衣机"]'},
    {"code": "SMALL_APPLIANCE", "name": "小家电", "parent_code": "HOME_APPLIANCE", "typical_products": '["电饭煲", "吸尘器", "破壁机"]'},
    {"code": "KITCHEN_APPLIANCE", "name": "厨房电器", "parent_code": "HOME_APPLIANCE", "typical_products": '["油烟机", "燃气灶", "消毒柜"]'},

    # 医疗器械子行业
    {"code": "MEDICAL_MONITOR", "name": "监护设备", "parent_code": "MEDICAL_DEVICE", "typical_products": '["血压计", "血糖仪", "心电监护"]'},
    {"code": "MEDICAL_IMAGING", "name": "影像设备", "parent_code": "MEDICAL_DEVICE", "typical_products": '["CT", "MRI", "超声"]'},
    {"code": "IVD", "name": "体外诊断", "parent_code": "MEDICAL_DEVICE", "typical_products": '["生化分析仪", "免疫分析仪"]'},

    # 工业控制子行业
    {"code": "PLC_DCS", "name": "PLC/DCS", "parent_code": "INDUSTRIAL_CONTROL", "typical_products": '["PLC", "DCS", "PAC"]'},
    {"code": "SERVO_DRIVE", "name": "伺服驱动", "parent_code": "INDUSTRIAL_CONTROL", "typical_products": '["伺服驱动器", "伺服电机"]'},
    {"code": "FREQUENCY_CONVERTER", "name": "变频器", "parent_code": "INDUSTRIAL_CONTROL", "typical_products": '["通用变频器", "专用变频器"]'},
]

# 行业-产品类别映射配置
DEFAULT_INDUSTRY_CATEGORY_MAPPINGS = [
    # 3C电子 -> 白色家电测试设备（历史原因，类别名称沿用）
    {"industry_code": "3C_ELECTRONICS", "category_code": "HOME_APPLIANCE", "match_score": 100, "is_primary": True},
    {"industry_code": "MOBILE_PHONE", "category_code": "HOME_APPLIANCE", "match_score": 100, "is_primary": True},
    {"industry_code": "CHARGER", "category_code": "HOME_APPLIANCE", "match_score": 100, "is_primary": True},

    # 汽车电子
    {"industry_code": "AUTOMOTIVE", "category_code": "AUTOMOTIVE", "match_score": 100, "is_primary": True},
    {"industry_code": "AUTO_ECU", "category_code": "AUTOMOTIVE", "match_score": 100, "is_primary": True},
    {"industry_code": "AUTO_SENSOR", "category_code": "AUTOMOTIVE", "match_score": 90, "is_primary": True},
    {"industry_code": "AUTO_MOTOR", "category_code": "AUTOMOTIVE", "match_score": 80, "is_primary": False},
    {"industry_code": "AUTO_CHARGING", "category_code": "NEW_ENERGY", "match_score": 90, "is_primary": True},

    # 新能源
    {"industry_code": "NEW_ENERGY", "category_code": "NEW_ENERGY", "match_score": 100, "is_primary": True},
    {"industry_code": "BATTERY_PACK", "category_code": "NEW_ENERGY", "match_score": 100, "is_primary": True},
    {"industry_code": "ENERGY_STORAGE", "category_code": "NEW_ENERGY", "match_score": 95, "is_primary": True},
    {"industry_code": "PV_INVERTER", "category_code": "NEW_ENERGY", "match_score": 85, "is_primary": True},
    {"industry_code": "CHARGING_PILE", "category_code": "NEW_ENERGY", "match_score": 90, "is_primary": True},

    # 家电
    {"industry_code": "HOME_APPLIANCE", "category_code": "HOME_APPLIANCE", "match_score": 100, "is_primary": True},
    {"industry_code": "WHITE_APPLIANCE", "category_code": "HOME_APPLIANCE", "match_score": 100, "is_primary": True},
    {"industry_code": "SMALL_APPLIANCE", "category_code": "HOME_APPLIANCE", "match_score": 95, "is_primary": True},

    # 半导体
    {"industry_code": "SEMICONDUCTOR", "category_code": "SEMICONDUCTOR", "match_score": 100, "is_primary": True},

    # 电动工具
    {"industry_code": "POWER_TOOLS", "category_code": "POWER_TOOLS", "match_score": 100, "is_primary": True},

    # 教育
    {"industry_code": "EDUCATION", "category_code": "EDUCATION", "match_score": 100, "is_primary": True},
]
