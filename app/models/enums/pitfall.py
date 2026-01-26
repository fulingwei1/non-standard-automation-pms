# -*- coding: utf-8 -*-
"""
踩坑库枚举定义
"""

from enum import Enum


class PitfallStage(str, Enum):
    """踩坑发生阶段"""
    S1 = "S1"  # 需求进入
    S2 = "S2"  # 方案设计
    S3 = "S3"  # 采购备料
    S4 = "S4"  # 加工制造
    S5 = "S5"  # 装配调试
    S6 = "S6"  # 出厂验收
    S7 = "S7"  # 包装发运
    S8 = "S8"  # 现场安装
    S9 = "S9"  # 质保结项


class PitfallEquipmentType(str, Enum):
    """设备类型"""
    ICT = "ICT"          # ICT测试设备
    FCT = "FCT"          # FCT测试设备
    EOL = "EOL"          # EOL测试设备
    BURNING = "BURNING"  # 烧录设备
    AGING = "AGING"      # 老化设备
    VISION = "VISION"    # 视觉检测设备
    ASSEMBLY = "ASSEMBLY"  # 自动化组装线
    OTHER = "OTHER"      # 其他


class PitfallProblemType(str, Enum):
    """问题类型"""
    TECHNICAL = "TECHNICAL"    # 技术问题
    SUPPLIER = "SUPPLIER"      # 供应商问题
    COMMUNICATION = "COMMUNICATION"  # 沟通问题
    SCHEDULE = "SCHEDULE"      # 进度问题
    COST = "COST"              # 成本问题
    QUALITY = "QUALITY"        # 质量问题
    OTHER = "OTHER"            # 其他


class PitfallSourceType(str, Enum):
    """踩坑来源"""
    REALTIME = "REALTIME"      # 实时录入
    STAGE_END = "STAGE_END"    # 阶段结束录入
    REVIEW = "REVIEW"          # 复盘导入
    ECN = "ECN"                # ECN关联
    ISSUE = "ISSUE"            # Issue关联


class PitfallStatus(str, Enum):
    """踩坑状态"""
    DRAFT = "DRAFT"            # 草稿
    PUBLISHED = "PUBLISHED"    # 已发布
    ARCHIVED = "ARCHIVED"      # 已归档


class PitfallSensitiveReason(str, Enum):
    """敏感原因"""
    CUSTOMER = "CUSTOMER"      # 涉及客户信息
    COST = "COST"              # 涉及成本/报价
    SUPPLIER = "SUPPLIER"      # 涉及供应商问题
    OTHER = "OTHER"            # 其他


class RecommendationTriggerType(str, Enum):
    """推荐触发类型"""
    PROJECT_CREATE = "PROJECT_CREATE"  # 项目创建
    STAGE_CHANGE = "STAGE_CHANGE"      # 阶段切换
    KEYWORD = "KEYWORD"                # 关键字触发
    MANUAL = "MANUAL"                  # 手动搜索
