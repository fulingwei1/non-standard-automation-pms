# -*- coding: utf-8 -*-
"""
工程师绩效评价模块 - 枚举定义
"""
from enum import Enum


class EngineerJobTypeEnum(str, Enum):
    """工程师岗位类型"""
    MECHANICAL = 'mechanical'    # 机械工程师
    TEST = 'test'                # 测试工程师
    ELECTRICAL = 'electrical'    # 电气工程师
    SOLUTION = 'solution'        # 方案工程师（售前技术支持）


class EngineerJobLevelEnum(str, Enum):
    """工程师职级"""
    JUNIOR = 'junior'            # 初级
    INTERMEDIATE = 'intermediate'  # 中级
    SENIOR = 'senior'            # 高级
    EXPERT = 'expert'            # 资深/专家


class ContributionTypeEnum(str, Enum):
    """知识贡献类型"""
    DOCUMENT = 'document'        # 技术文档
    TEMPLATE = 'template'        # 标准模板
    MODULE = 'module'            # 代码/功能模块
    TRAINING = 'training'        # 培训分享
    PATENT = 'patent'            # 专利
    STANDARD = 'standard'        # 标准规范


class ContributionStatusEnum(str, Enum):
    """知识贡献状态"""
    DRAFT = 'draft'              # 草稿
    PENDING = 'pending'          # 待审核
    APPROVED = 'approved'        # 已通过
    REJECTED = 'rejected'        # 已拒绝


class ReviewResultEnum(str, Enum):
    """评审结果"""
    PASSED = 'passed'            # 通过
    REJECTED = 'rejected'        # 驳回
    CONDITIONAL = 'conditional'  # 有条件通过


class IssueSeverityEnum(str, Enum):
    """问题严重程度"""
    CRITICAL = 'critical'        # 致命
    MAJOR = 'major'              # 严重
    NORMAL = 'normal'            # 一般
    MINOR = 'minor'              # 轻微


class IssueStatusEnum(str, Enum):
    """问题状态"""
    OPEN = 'open'                # 待处理
    IN_PROGRESS = 'in_progress'  # 处理中
    RESOLVED = 'resolved'        # 已解决
    CLOSED = 'closed'            # 已关闭


class BugFoundStageEnum(str, Enum):
    """Bug发现阶段"""
    INTERNAL_DEBUG = 'internal_debug'    # 内部调试
    SITE_DEBUG = 'site_debug'            # 现场调试
    ACCEPTANCE = 'acceptance'            # 客户验收
    PRODUCTION = 'production'            # 售后运行


class PlcBrandEnum(str, Enum):
    """PLC品牌"""
    SIEMENS = 'siemens'          # 西门子
    MITSUBISHI = 'mitsubishi'    # 三菱
    OMRON = 'omron'              # 欧姆龙
    BECKHOFF = 'beckhoff'        # 倍福
    INOVANCE = 'inovance'        # 汇川
    DELTA = 'delta'              # 台达


class DrawingTypeEnum(str, Enum):
    """电气图纸类型"""
    SCHEMATIC = 'schematic'      # 原理图
    LAYOUT = 'layout'            # 布局图
    WIRING = 'wiring'            # 接线图
    TERMINAL = 'terminal'        # 端子图
    PANEL = 'panel'              # 柜体图


class CodeModuleCategoryEnum(str, Enum):
    """代码模块分类"""
    COMMUNICATION = 'communication'  # 通讯模块
    DATA = 'data'                    # 数据处理
    UI = 'ui'                        # 界面组件
    DRIVER = 'driver'                # 硬件驱动
    UTILITY = 'utility'              # 工具类


class PlcModuleCategoryEnum(str, Enum):
    """PLC模块分类"""
    MOTION = 'motion'            # 运动控制
    IO = 'io'                    # IO处理
    COMMUNICATION = 'communication'  # 通讯
    DATA = 'data'                # 数据处理
    ALARM = 'alarm'              # 报警处理
    PROCESS = 'process'          # 工艺流程
