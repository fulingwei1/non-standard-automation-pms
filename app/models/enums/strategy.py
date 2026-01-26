# -*- coding: utf-8 -*-
"""
战略管理相关枚举
"""
from enum import Enum


class StrategyStatusEnum(str, Enum):
    """战略状态"""
    DRAFT = "DRAFT"           # 草稿
    ACTIVE = "ACTIVE"         # 生效中
    ARCHIVED = "ARCHIVED"     # 已归档


class BSCDimensionEnum(str, Enum):
    """BSC平衡计分卡四维度"""
    FINANCIAL = "FINANCIAL"         # 财务维度
    CUSTOMER = "CUSTOMER"           # 客户维度
    INTERNAL = "INTERNAL"           # 内部运营维度
    LEARNING = "LEARNING"           # 学习与成长维度


class IPOOCTypeEnum(str, Enum):
    """IPOOC指标类型"""
    INPUT = "INPUT"           # 输入型指标
    PROCESS = "PROCESS"       # 过程型指标
    OUTPUT = "OUTPUT"         # 输出型指标
    OUTCOME = "OUTCOME"       # 结果型指标


class VOCSourceEnum(str, Enum):
    """VOC声音来源"""
    SHAREHOLDER = "SHAREHOLDER"     # 股东之声
    CUSTOMER = "CUSTOMER"           # 客户之声
    EMPLOYEE = "EMPLOYEE"           # 员工之声
    COMPLIANCE = "COMPLIANCE"       # 监管之声


class CSFDerivationMethodEnum(str, Enum):
    """CSF导出方法"""
    FOUR_PARAM = "FOUR_PARAM"           # 四维参数法（财务维度）
    FIVE_SOURCE = "FIVE_SOURCE"         # 五大源法（客户维度）
    VALUE_CHAIN = "VALUE_CHAIN"         # 价值链法（内部运营）
    INTANGIBLE = "INTANGIBLE"           # 无形资产法（学习成长）


class WorkStatusEnum(str, Enum):
    """工作状态"""
    NOT_STARTED = "NOT_STARTED"     # 未开始
    IN_PROGRESS = "IN_PROGRESS"     # 进行中
    COMPLETED = "COMPLETED"         # 已完成
    DELAYED = "DELAYED"             # 已延期
    CANCELLED = "CANCELLED"         # 已取消


class StrategyEventTypeEnum(str, Enum):
    """战略事件类型"""
    ANNUAL_PLANNING = "ANNUAL_PLANNING"         # 年度战略规划
    QUARTERLY_REVIEW = "QUARTERLY_REVIEW"       # 季度审视会
    MONTHLY_TRACKING = "MONTHLY_TRACKING"       # 月度跟踪会
    KPI_COLLECTION = "KPI_COLLECTION"           # KPI采集
    DECOMPOSITION = "DECOMPOSITION"             # 目标分解
    ASSESSMENT = "ASSESSMENT"                   # 考核评估


class DataSourceTypeEnum(str, Enum):
    """数据源类型"""
    MANUAL = "MANUAL"           # 手动录入
    AUTO = "AUTO"               # 自动采集
    FORMULA = "FORMULA"         # 公式计算


class HealthLevelEnum(str, Enum):
    """健康度等级"""
    EXCELLENT = "EXCELLENT"     # 优秀 >= 90%
    GOOD = "GOOD"               # 良好 >= 70%
    WARNING = "WARNING"         # 警示 >= 50%
    DANGER = "DANGER"           # 危险 < 50%


class ObjectiveLevelEnum(str, Enum):
    """目标分解层级"""
    COMPANY = "COMPANY"         # 公司级
    DEPARTMENT = "DEPARTMENT"   # 部门级
    PERSONAL = "PERSONAL"       # 个人级


class StrategyReviewTypeEnum(str, Enum):
    """审视类型"""
    ANNUAL = "ANNUAL"           # 年度审视
    QUARTERLY = "QUARTERLY"     # 季度审视
    MONTHLY = "MONTHLY"         # 月度审视
    SPECIAL = "SPECIAL"         # 专项审视
