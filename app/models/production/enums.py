# -*- coding: utf-8 -*-
"""
生产管理枚举定义
"""
from enum import Enum


class WorkshopTypeEnum(str, Enum):
    """车间类型"""
    MACHINING = 'MACHINING'      # 机加车间
    ASSEMBLY = 'ASSEMBLY'        # 装配车间
    DEBUGGING = 'DEBUGGING'      # 调试车间
    WELDING = 'WELDING'          # 焊接车间
    SURFACE = 'SURFACE'          # 表面处理车间
    WAREHOUSE = 'WAREHOUSE'      # 仓库
    OTHER = 'OTHER'              # 其他


class WorkstationStatusEnum(str, Enum):
    """工位状态"""
    IDLE = 'IDLE'                # 空闲
    WORKING = 'WORKING'          # 工作中
    MAINTENANCE = 'MAINTENANCE'  # 维护中
    DISABLED = 'DISABLED'        # 停用


class WorkerStatusEnum(str, Enum):
    """工人状态"""
    ACTIVE = 'ACTIVE'      # 在岗
    LEAVE = 'LEAVE'        # 请假
    RESIGNED = 'RESIGNED'  # 离职


class SkillLevelEnum(str, Enum):
    """技能等级"""
    JUNIOR = 'JUNIOR'          # 初级
    INTERMEDIATE = 'INTERMEDIATE'  # 中级
    SENIOR = 'SENIOR'          # 高级
    EXPERT = 'EXPERT'          # 专家


class ProductionPlanTypeEnum(str, Enum):
    """生产计划类型"""
    MASTER = 'MASTER'        # 主生产计划(MPS)
    WORKSHOP = 'WORKSHOP'    # 车间作业计划


class ProductionPlanStatusEnum(str, Enum):
    """生产计划状态"""
    DRAFT = 'DRAFT'              # 草稿
    SUBMITTED = 'SUBMITTED'      # 已提交
    APPROVED = 'APPROVED'        # 已审批
    PUBLISHED = 'PUBLISHED'      # 已发布
    EXECUTING = 'EXECUTING'      # 执行中
    COMPLETED = 'COMPLETED'      # 已完成
    CANCELLED = 'CANCELLED'      # 已取消


class WorkOrderTypeEnum(str, Enum):
    """工单类型"""
    MACHINING = 'MACHINING'    # 机加
    ASSEMBLY = 'ASSEMBLY'      # 装配
    DEBUGGING = 'DEBUGGING'    # 调试
    WELDING = 'WELDING'        # 焊接
    INSPECTION = 'INSPECTION'  # 检验
    OTHER = 'OTHER'            # 其他


class WorkOrderStatusEnum(str, Enum):
    """工单状态"""
    PENDING = 'PENDING'          # 待派工
    ASSIGNED = 'ASSIGNED'        # 已派工
    STARTED = 'STARTED'          # 已开工
    PAUSED = 'PAUSED'            # 已暂停
    COMPLETED = 'COMPLETED'      # 已完工
    APPROVED = 'APPROVED'        # 已审核
    CANCELLED = 'CANCELLED'      # 已取消


class WorkOrderPriorityEnum(str, Enum):
    """工单优先级"""
    LOW = 'LOW'          # 低
    NORMAL = 'NORMAL'    # 普通
    HIGH = 'HIGH'        # 高
    URGENT = 'URGENT'    # 紧急


class WorkReportTypeEnum(str, Enum):
    """报工类型"""
    START = 'START'          # 开工
    PROGRESS = 'PROGRESS'    # 进度
    PAUSE = 'PAUSE'          # 暂停
    RESUME = 'RESUME'        # 恢复
    COMPLETE = 'COMPLETE'    # 完工


class WorkReportStatusEnum(str, Enum):
    """报工状态"""
    PENDING = 'PENDING'      # 待审核
    APPROVED = 'APPROVED'    # 已通过
    REJECTED = 'REJECTED'    # 已驳回


class ProductionExceptionTypeEnum(str, Enum):
    """生产异常类型"""
    MATERIAL = 'MATERIAL'      # 物料异常
    EQUIPMENT = 'EQUIPMENT'    # 设备异常
    QUALITY = 'QUALITY'        # 质量异常
    PROCESS = 'PROCESS'        # 工艺异常
    SAFETY = 'SAFETY'          # 安全异常
    OTHER = 'OTHER'            # 其他


class ProductionExceptionLevelEnum(str, Enum):
    """生产异常级别"""
    MINOR = 'MINOR'        # 轻微
    MAJOR = 'MAJOR'        # 一般
    CRITICAL = 'CRITICAL'  # 严重


class ProductionExceptionStatusEnum(str, Enum):
    """生产异常状态"""
    REPORTED = 'REPORTED'    # 已上报
    HANDLING = 'HANDLING'    # 处理中
    RESOLVED = 'RESOLVED'    # 已解决
    CLOSED = 'CLOSED'        # 已关闭


class MaterialRequisitionStatusEnum(str, Enum):
    """领料单状态"""
    DRAFT = 'DRAFT'          # 草稿
    SUBMITTED = 'SUBMITTED'  # 已提交
    APPROVED = 'APPROVED'    # 已审批
    REJECTED = 'REJECTED'    # 已驳回
    ISSUED = 'ISSUED'        # 已发料
    COMPLETED = 'COMPLETED'  # 已完成
    CANCELLED = 'CANCELLED'  # 已取消


class EquipmentStatusEnum(str, Enum):
    """设备状态"""
    IDLE = 'IDLE'                # 空闲
    RUNNING = 'RUNNING'          # 运行中
    MAINTENANCE = 'MAINTENANCE'  # 保养中
    REPAIR = 'REPAIR'            # 维修中
    DISABLED = 'DISABLED'        # 停用


class ProcessTypeEnum(str, Enum):
    """工序类型"""
    MACHINING = 'MACHINING'    # 机加
    ASSEMBLY = 'ASSEMBLY'      # 装配
    DEBUGGING = 'DEBUGGING'    # 调试
    WELDING = 'WELDING'        # 焊接
    SURFACE = 'SURFACE'        # 表面处理
    INSPECTION = 'INSPECTION'  # 检验
    OTHER = 'OTHER'            # 其他
