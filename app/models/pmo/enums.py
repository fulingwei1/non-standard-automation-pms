# -*- coding: utf-8 -*-
"""
PMO模型 - 枚举定义
"""
from enum import Enum


class ProjectLevelEnum(str, Enum):
    """项目级别"""
    A = 'A'  # A级项目(重点)
    B = 'B'  # B级项目(一般)
    C = 'C'  # C级项目(简单)


class ProjectPhaseEnum(str, Enum):
    """项目阶段"""
    INITIATION = 'INITIATION'  # 立项阶段
    DESIGN = 'DESIGN'          # 设计阶段
    PRODUCTION = 'PRODUCTION'  # 生产阶段
    DELIVERY = 'DELIVERY'      # 交付阶段
    CLOSURE = 'CLOSURE'        # 结项阶段


class InitiationStatusEnum(str, Enum):
    """立项申请状态"""
    DRAFT = 'DRAFT'          # 草稿
    SUBMITTED = 'SUBMITTED'  # 已提交
    REVIEWING = 'REVIEWING'  # 评审中
    APPROVED = 'APPROVED'    # 已批准
    REJECTED = 'REJECTED'    # 已驳回


class PhaseStatusEnum(str, Enum):
    """阶段状态"""
    PENDING = 'PENDING'        # 未开始
    IN_PROGRESS = 'IN_PROGRESS'  # 进行中
    COMPLETED = 'COMPLETED'    # 已完成
    SKIPPED = 'SKIPPED'        # 已跳过


class MilestoneStatusEnum(str, Enum):
    """里程碑状态"""
    PENDING = 'PENDING'        # 待完成
    IN_PROGRESS = 'IN_PROGRESS'  # 进行中
    COMPLETED = 'COMPLETED'    # 已完成
    DELAYED = 'DELAYED'        # 已延期
    CANCELLED = 'CANCELLED'    # 已取消


class ChangeTypeEnum(str, Enum):
    """变更类型"""
    SCOPE = 'SCOPE'          # 范围变更
    SCHEDULE = 'SCHEDULE'    # 进度变更
    COST = 'COST'            # 成本变更
    RESOURCE = 'RESOURCE'    # 资源变更
    REQUIREMENT = 'REQUIREMENT'  # 需求变更
    OTHER = 'OTHER'          # 其他变更


class ChangeLevelEnum(str, Enum):
    """变更级别"""
    MINOR = 'MINOR'      # 小变更
    MAJOR = 'MAJOR'      # 重大变更
    CRITICAL = 'CRITICAL'  # 关键变更


class ChangeStatusEnum(str, Enum):
    """变更状态"""
    DRAFT = 'DRAFT'          # 草稿
    SUBMITTED = 'SUBMITTED'  # 已提交
    REVIEWING = 'REVIEWING'  # 评审中
    APPROVED = 'APPROVED'    # 已批准
    REJECTED = 'REJECTED'    # 已驳回
    CANCELLED = 'CANCELLED'  # 已取消


class RiskCategoryEnum(str, Enum):
    """风险类别"""
    TECHNICAL = 'TECHNICAL'  # 技术风险
    SCHEDULE = 'SCHEDULE'    # 进度风险
    COST = 'COST'            # 成本风险
    RESOURCE = 'RESOURCE'    # 资源风险
    EXTERNAL = 'EXTERNAL'    # 外部风险
    OTHER = 'OTHER'          # 其他风险


class RiskLevelEnum(str, Enum):
    """风险等级"""
    LOW = 'LOW'          # 低
    MEDIUM = 'MEDIUM'    # 中
    HIGH = 'HIGH'        # 高
    CRITICAL = 'CRITICAL'  # 严重


class RiskStatusEnum(str, Enum):
    """风险状态"""
    IDENTIFIED = 'IDENTIFIED'  # 已识别
    ANALYZING = 'ANALYZING'    # 分析中
    RESPONDING = 'RESPONDING'  # 应对中
    MONITORING = 'MONITORING'  # 监控中
    CLOSED = 'CLOSED'          # 已关闭


class MeetingTypeEnum(str, Enum):
    """会议类型"""
    KICKOFF = 'KICKOFF'              # 启动会
    WEEKLY = 'WEEKLY'                # 周例会
    MILESTONE_REVIEW = 'MILESTONE_REVIEW'  # 里程碑评审
    CHANGE_REVIEW = 'CHANGE_REVIEW'  # 变更评审
    RISK_REVIEW = 'RISK_REVIEW'      # 风险评审
    CLOSURE = 'CLOSURE'              # 结项会
    OTHER = 'OTHER'                  # 其他


class ResourceAllocationStatusEnum(str, Enum):
    """资源分配状态"""
    PLANNED = 'PLANNED'      # 已计划
    ACTIVE = 'ACTIVE'        # 生效中
    COMPLETED = 'COMPLETED'  # 已完成
    RELEASED = 'RELEASED'    # 已释放
