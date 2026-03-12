# -*- coding: utf-8 -*-
"""
技术参数模板模型

为不同行业/测试类型提供标准化技术参数模板，支持快速创建技术方案并估算成本
"""

from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class IndustryEnum(str, Enum):
    """行业分类枚举 - 非标自动化测试设备常见行业"""

    AUTOMOTIVE_ELECTRONICS = "AUTOMOTIVE_ELECTRONICS"  # 汽车电子
    CONSUMER_ELECTRONICS = "CONSUMER_ELECTRONICS"  # 消费电子
    MEDICAL_DEVICE = "MEDICAL_DEVICE"  # 医疗器械
    NEW_ENERGY = "NEW_ENERGY"  # 新能源（电池、光伏等）
    SEMICONDUCTOR = "SEMICONDUCTOR"  # 半导体
    AEROSPACE = "AEROSPACE"  # 航空航天
    COMMUNICATION = "COMMUNICATION"  # 通信设备
    HOME_APPLIANCE = "HOME_APPLIANCE"  # 家用电器
    INDUSTRIAL_CONTROL = "INDUSTRIAL_CONTROL"  # 工业控制
    OTHER = "OTHER"  # 其他


class TestTypeEnum(str, Enum):
    """测试类型枚举 - 非标自动化测试设备常见测试类型"""

    FUNCTIONAL_TEST = "FUNCTIONAL_TEST"  # 功能测试
    AGING_TEST = "AGING_TEST"  # 老化测试
    AIR_TIGHTNESS_TEST = "AIR_TIGHTNESS_TEST"  # 气密测试
    ELECTRICAL_TEST = "ELECTRICAL_TEST"  # 电气测试
    BURN_IN_TEST = "BURN_IN_TEST"  # 烧录测试
    AOI_TEST = "AOI_TEST"  # AOI 光学检测
    PRESSURE_TEST = "PRESSURE_TEST"  # 耐压测试
    ENVIRONMENTAL_TEST = "ENVIRONMENTAL_TEST"  # 环境测试（高温、低温、湿热）
    VIBRATION_TEST = "VIBRATION_TEST"  # 振动测试
    EMC_TEST = "EMC_TEST"  # 电磁兼容测试
    SAFETY_TEST = "SAFETY_TEST"  # 安规测试
    PERFORMANCE_TEST = "PERFORMANCE_TEST"  # 性能测试
    DURABILITY_TEST = "DURABILITY_TEST"  # 耐久性测试
    COMPREHENSIVE_TEST = "COMPREHENSIVE_TEST"  # 综合测试
    OTHER = "OTHER"  # 其他


class CostCategoryEnum(str, Enum):
    """成本类别枚举"""

    MECHANICAL = "MECHANICAL"  # 机械结构（机架、工装、气缸等）
    ELECTRICAL = "ELECTRICAL"  # 电气元件（PLC、传感器、线缆等）
    SOFTWARE = "SOFTWARE"  # 软件开发（测试程序、上位机等）
    OUTSOURCE = "OUTSOURCE"  # 外协加工（钣金、机加工等）
    LABOR = "LABOR"  # 人工成本


class TechnicalParameterTemplate(Base, TimestampMixin):
    """
    技术参数模板

    为不同行业/测试类型提供标准化技术参数模板，用于：
    1. 快速创建技术方案
    2. 基于模板参数估算成本
    3. 提供行业最佳实践参考
    """

    __tablename__ = "technical_parameter_templates"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    name = Column(String(200), nullable=False, comment="模板名称")
    code = Column(String(50), unique=True, nullable=False, comment="模板编码")

    # 分类信息
    industry = Column(String(50), nullable=False, comment="行业分类")
    test_type = Column(String(50), nullable=False, comment="测试类型")
    description = Column(Text, comment="模板描述")

    # 技术参数模板 - JSON 格式
    # 结构示例：
    # {
    #   "test_station_count": {"label": "测试工位数", "type": "number", "default": 4, "unit": "个"},
    #   "cycle_time": {"label": "节拍时间", "type": "number", "default": 30, "unit": "秒"},
    #   "accuracy": {"label": "测试精度", "type": "number", "default": 0.01, "unit": "%"},
    #   "power_supply": {"label": "电源要求", "type": "select", "options": ["AC220V", "AC380V"], "default": "AC220V"},
    #   "air_pressure": {"label": "气源要求", "type": "number", "default": 0.6, "unit": "MPa"},
    #   "communication": {"label": "通讯协议", "type": "multiselect", "options": ["MODBUS", "PROFINET", "ETHERNET/IP"]},
    # }
    parameters = Column(JSON, comment="技术参数模板（JSON格式）")

    # 成本估算因子 - JSON 格式
    # 结构示例：
    # {
    #   "base_cost": 50000,  // 基础成本（元）
    #   "factors": {
    #     "test_station_count": {"type": "linear", "coefficient": 8000},  // 每增加一个工位增加8000元
    #     "cycle_time": {"type": "inverse", "coefficient": 5000, "base": 30},  // 节拍越短成本越高
    #     "accuracy": {"type": "exponential", "coefficient": 10000, "base": 0.1},  // 精度越高成本指数增长
    #   },
    #   "category_ratios": {  // 成本类别默认占比
    #     "MECHANICAL": 0.35,
    #     "ELECTRICAL": 0.30,
    #     "SOFTWARE": 0.15,
    #     "OUTSOURCE": 0.10,
    #     "LABOR": 0.10
    #   }
    # }
    cost_factors = Column(JSON, comment="成本估算因子（JSON格式）")

    # 典型工时估算 - JSON 格式
    # {
    #   "design_hours": 80,      // 方案设计工时
    #   "assembly_hours": 120,   // 组装工时
    #   "debug_hours": 60,       // 调试工时
    #   "installation_hours": 40, // 现场安装工时
    #   "training_hours": 16     // 培训工时
    # }
    typical_labor_hours = Column(JSON, comment="典型工时估算（JSON格式）")

    # 附件和参考资料
    reference_docs = Column(JSON, comment="参考文档列表（JSON格式）")
    sample_images = Column(JSON, comment="示例图片列表（JSON格式）")

    # 使用统计
    use_count = Column(Integer, default=0, comment="使用次数")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 创建人
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")

    # 关系
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index("idx_tech_template_code", "code"),
        Index("idx_tech_template_industry", "industry"),
        Index("idx_tech_template_test_type", "test_type"),
        Index("idx_tech_template_industry_test_type", "industry", "test_type"),
        Index("idx_tech_template_is_active", "is_active"),
        {"comment": "技术参数模板表"},
    )

    def __repr__(self):
        return f"<TechnicalParameterTemplate {self.code}: {self.name}>"
