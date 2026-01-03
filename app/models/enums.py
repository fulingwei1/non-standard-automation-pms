# -*- coding: utf-8 -*-
"""
系统枚举值定义
"""

from enum import Enum


# ==================== 项目管理相关 ====================

class ProjectStageEnum(str, Enum):
    """项目阶段"""
    S1 = 'S1'  # 需求进入
    S2 = 'S2'  # 方案设计
    S3 = 'S3'  # 采购备料
    S4 = 'S4'  # 加工制造
    S5 = 'S5'  # 装配调试
    S6 = 'S6'  # 出厂验收(FAT)
    S7 = 'S7'  # 包装发运
    S8 = 'S8'  # 现场安装(SAT)
    S9 = 'S9'  # 质保结项


class ProjectHealthEnum(str, Enum):
    """项目健康度"""
    H1 = 'H1'  # 正常(绿色)
    H2 = 'H2'  # 有风险(黄色)
    H3 = 'H3'  # 阻塞(红色)
    H4 = 'H4'  # 已完结(灰色)


class MachineStatusEnum(str, Enum):
    """设备状态"""
    PLANNING = 'PLANNING'          # 规划中
    IN_PRODUCTION = 'IN_PRODUCTION'  # 生产中
    TESTING = 'TESTING'            # 测试中
    SHIPPED = 'SHIPPED'            # 已发运
    INSTALLED = 'INSTALLED'        # 已安装
    ACCEPTED = 'ACCEPTED'          # 已验收
    IN_WARRANTY = 'IN_WARRANTY'    # 质保中


class MilestoneTypeEnum(str, Enum):
    """里程碑类型"""
    CONTRACT = 'CONTRACT'              # 合同签订
    DESIGN_COMPLETE = 'DESIGN_COMPLETE'  # 设计完成
    PURCHASE_COMPLETE = 'PURCHASE_COMPLETE'  # 采购完成
    ASSEMBLY_COMPLETE = 'ASSEMBLY_COMPLETE'  # 装配完成
    FAT_PASS = 'FAT_PASS'              # FAT通过
    SHIPMENT = 'SHIPMENT'              # 发运
    SAT_PASS = 'SAT_PASS'              # SAT通过
    FINAL_ACCEPTANCE = 'FINAL_ACCEPTANCE'  # 终验
    WARRANTY_END = 'WARRANTY_END'      # 质保结束


# ==================== 采购与物料相关 ====================

class MaterialTypeEnum(str, Enum):
    """物料类型"""
    STANDARD = 'STANDARD'      # 标准件
    MECHANICAL = 'MECHANICAL'  # 机械件
    ELECTRICAL = 'ELECTRICAL'  # 电气件
    PNEUMATIC = 'PNEUMATIC'    # 气动件
    HYDRAULIC = 'HYDRAULIC'    # 液压件
    SENSOR = 'SENSOR'          # 传感器
    MOTOR = 'MOTOR'            # 电机
    PLC = 'PLC'                # PLC
    HMI = 'HMI'                # 触摸屏
    SAFETY = 'SAFETY'          # 安全器件
    CONSUMABLE = 'CONSUMABLE'  # 耗材
    OTHER = 'OTHER'            # 其他


class MaterialSourceEnum(str, Enum):
    """物料来源"""
    PURCHASE = 'PURCHASE'      # 采购
    OUTSOURCE = 'OUTSOURCE'    # 外协
    SELF_MADE = 'SELF_MADE'    # 自制
    CUSTOMER = 'CUSTOMER'      # 客供


class PurchaseOrderStatusEnum(str, Enum):
    """采购订单状态"""
    DRAFT = 'DRAFT'                    # 草稿
    PENDING_APPROVAL = 'PENDING_APPROVAL'  # 待审批
    APPROVED = 'APPROVED'              # 已审批
    REJECTED = 'REJECTED'              # 已驳回
    ORDERED = 'ORDERED'                # 已下单
    PARTIAL_RECEIVED = 'PARTIAL_RECEIVED'  # 部分到货
    RECEIVED = 'RECEIVED'              # 已到货
    COMPLETED = 'COMPLETED'            # 已完成
    CANCELLED = 'CANCELLED'            # 已取消


class SupplierLevelEnum(str, Enum):
    """供应商等级"""
    A = 'A'  # 优选供应商
    B = 'B'  # 合格供应商
    C = 'C'  # 待改进供应商
    D = 'D'  # 淘汰供应商


class PaymentStatusEnum(str, Enum):
    """付款状态"""
    UNPAID = 'UNPAID'      # 未付款
    PARTIAL = 'PARTIAL'    # 部分付款
    PAID = 'PAID'          # 已付清


# ==================== 变更管理相关 ====================

class EcnTypeEnum(str, Enum):
    """ECN类型"""
    DESIGN = 'DESIGN'              # 设计变更
    MATERIAL = 'MATERIAL'          # 物料变更
    PROCESS = 'PROCESS'            # 工艺变更
    SPECIFICATION = 'SPECIFICATION'  # 规格变更
    SCHEDULE = 'SCHEDULE'          # 计划变更
    OTHER = 'OTHER'                # 其他变更


class EcnSourceTypeEnum(str, Enum):
    """ECN来源类型"""
    CUSTOMER = 'CUSTOMER'    # 客户要求
    INTERNAL = 'INTERNAL'    # 内部发起
    SUPPLIER = 'SUPPLIER'    # 供应商
    QUALITY = 'QUALITY'      # 质量问题
    COST = 'COST'            # 成本优化


class EcnStatusEnum(str, Enum):
    """ECN状态"""
    DRAFT = 'DRAFT'                    # 草稿
    SUBMITTED = 'SUBMITTED'            # 已提交
    EVALUATING = 'EVALUATING'          # 评估中
    PENDING_APPROVAL = 'PENDING_APPROVAL'  # 待审批
    APPROVED = 'APPROVED'              # 已批准
    REJECTED = 'REJECTED'              # 已驳回
    EXECUTING = 'EXECUTING'            # 执行中
    COMPLETED = 'COMPLETED'            # 已完成
    CLOSED = 'CLOSED'                  # 已关闭
    CANCELLED = 'CANCELLED'            # 已取消


class PriorityEnum(str, Enum):
    """优先级"""
    LOW = 'LOW'          # 低
    NORMAL = 'NORMAL'    # 普通
    HIGH = 'HIGH'        # 高
    URGENT = 'URGENT'    # 紧急


class ChangeScopeEnum(str, Enum):
    """变更范围"""
    PARTIAL = 'PARTIAL'              # 局部
    SINGLE_MACHINE = 'SINGLE_MACHINE'  # 单台设备
    ALL_MACHINES = 'ALL_MACHINES'    # 所有设备
    MULTI_PROJECT = 'MULTI_PROJECT'  # 跨项目


# ==================== 验收管理相关 ====================

class AcceptanceTypeEnum(str, Enum):
    """验收类型"""
    FAT = 'FAT'      # 工厂验收
    SAT = 'SAT'      # 现场验收
    FINAL = 'FINAL'  # 终验


class AcceptanceOrderStatusEnum(str, Enum):
    """验收单状态"""
    DRAFT = 'DRAFT'              # 草稿
    READY = 'READY'              # 待验收
    IN_PROGRESS = 'IN_PROGRESS'  # 验收中
    PENDING_SIGN = 'PENDING_SIGN'  # 待签字
    COMPLETED = 'COMPLETED'      # 已完成
    CANCELLED = 'CANCELLED'      # 已取消


class AcceptanceResultEnum(str, Enum):
    """验收结果"""
    PASSED = 'PASSED'          # 通过
    FAILED = 'FAILED'          # 不通过
    CONDITIONAL = 'CONDITIONAL'  # 有条件通过


class CheckItemResultEnum(str, Enum):
    """检查项结果"""
    PENDING = 'PENDING'          # 待检
    PASSED = 'PASSED'            # 通过
    FAILED = 'FAILED'            # 不通过
    NA = 'NA'                    # 不适用
    CONDITIONAL = 'CONDITIONAL'  # 有条件通过


class IssueTypeEnum(str, Enum):
    """验收问题类型"""
    DEFECT = 'DEFECT'          # 缺陷
    DEVIATION = 'DEVIATION'    # 偏差
    SUGGESTION = 'SUGGESTION'  # 建议


class SeverityEnum(str, Enum):
    """严重程度"""
    CRITICAL = 'CRITICAL'  # 严重
    MAJOR = 'MAJOR'        # 主要
    MINOR = 'MINOR'        # 次要


class IssueStatusEnum(str, Enum):
    """问题状态"""
    OPEN = 'OPEN'              # 开放
    PROCESSING = 'PROCESSING'  # 处理中
    RESOLVED = 'RESOLVED'      # 已解决
    CLOSED = 'CLOSED'          # 已关闭
    DEFERRED = 'DEFERRED'      # 已延期


# ==================== 外协管理相关 ====================

class VendorTypeEnum(str, Enum):
    """外协商类型"""
    MACHINING = 'MACHINING'    # 机加工
    ASSEMBLY = 'ASSEMBLY'      # 装配
    SURFACE = 'SURFACE'        # 表面处理
    ELECTRICAL = 'ELECTRICAL'  # 电气
    OTHER = 'OTHER'            # 其他


class OutsourcingOrderStatusEnum(str, Enum):
    """外协订单状态"""
    DRAFT = 'DRAFT'              # 草稿
    CONFIRMED = 'CONFIRMED'      # 已确认
    IN_PROGRESS = 'IN_PROGRESS'  # 加工中
    DELIVERED = 'DELIVERED'      # 已交付
    INSPECTED = 'INSPECTED'      # 已检验
    COMPLETED = 'COMPLETED'      # 已完成
    CANCELLED = 'CANCELLED'      # 已取消


class InspectionResultEnum(str, Enum):
    """质检结果"""
    PASSED = 'PASSED'          # 合格
    REJECTED = 'REJECTED'      # 不合格
    CONDITIONAL = 'CONDITIONAL'  # 让步接收


class DispositionEnum(str, Enum):
    """不合格品处置"""
    ACCEPT = 'ACCEPT'    # 接收
    REWORK = 'REWORK'    # 返工
    RETURN = 'RETURN'    # 退货
    SCRAP = 'SCRAP'      # 报废


# ==================== 预警与异常相关 ====================

class AlertLevelEnum(str, Enum):
    """预警级别"""
    INFO = 'INFO'          # 提示(蓝色)
    WARNING = 'WARNING'    # 警告(黄色)
    CRITICAL = 'CRITICAL'  # 严重(橙色)
    URGENT = 'URGENT'      # 紧急(红色)


class AlertRuleTypeEnum(str, Enum):
    """预警规则类型"""
    SCHEDULE_DELAY = 'SCHEDULE_DELAY'      # 进度延期
    COST_OVERRUN = 'COST_OVERRUN'          # 成本超支
    MILESTONE_DUE = 'MILESTONE_DUE'        # 里程碑到期
    DELIVERY_DUE = 'DELIVERY_DUE'          # 交期预警
    MATERIAL_SHORTAGE = 'MATERIAL_SHORTAGE'  # 物料短缺
    QUALITY_ISSUE = 'QUALITY_ISSUE'        # 质量问题
    PAYMENT_DUE = 'PAYMENT_DUE'            # 付款到期
    CUSTOM = 'CUSTOM'                      # 自定义


class AlertStatusEnum(str, Enum):
    """预警状态"""
    PENDING = 'PENDING'          # 待处理
    ACKNOWLEDGED = 'ACKNOWLEDGED'  # 已确认
    PROCESSING = 'PROCESSING'    # 处理中
    RESOLVED = 'RESOLVED'        # 已解决
    IGNORED = 'IGNORED'          # 已忽略
    EXPIRED = 'EXPIRED'          # 已过期


class ExceptionTypeEnum(str, Enum):
    """异常事件类型"""
    SCHEDULE = 'SCHEDULE'    # 进度异常
    QUALITY = 'QUALITY'      # 质量异常
    COST = 'COST'            # 成本异常
    RESOURCE = 'RESOURCE'    # 资源异常
    SAFETY = 'SAFETY'        # 安全异常
    OTHER = 'OTHER'          # 其他


class ExceptionSeverityEnum(str, Enum):
    """异常严重程度"""
    MINOR = 'MINOR'        # 轻微
    MAJOR = 'MAJOR'        # 重大
    CRITICAL = 'CRITICAL'  # 严重
    BLOCKER = 'BLOCKER'    # 阻塞


class ExceptionStatusEnum(str, Enum):
    """异常状态"""
    OPEN = 'OPEN'            # 开放
    ANALYZING = 'ANALYZING'  # 分析中
    RESOLVING = 'RESOLVING'  # 解决中
    RESOLVED = 'RESOLVED'    # 已解决
    CLOSED = 'CLOSED'        # 已关闭
    DEFERRED = 'DEFERRED'    # 已延期


# ==================== 通用枚举 ====================

class StatusEnum(str, Enum):
    """通用状态"""
    DRAFT = 'DRAFT'              # 草稿
    PENDING = 'PENDING'          # 待处理
    IN_PROGRESS = 'IN_PROGRESS'  # 进行中
    COMPLETED = 'COMPLETED'      # 已完成
    CANCELLED = 'CANCELLED'      # 已取消
    ON_HOLD = 'ON_HOLD'          # 暂停


class ActiveStatusEnum(str, Enum):
    """启用状态"""
    ACTIVE = 'ACTIVE'      # 启用
    INACTIVE = 'INACTIVE'  # 停用


class ApprovalResultEnum(str, Enum):
    """审批结果"""
    APPROVED = 'APPROVED'    # 批准
    REJECTED = 'REJECTED'    # 驳回
    RETURNED = 'RETURNED'    # 退回


class NotifyChannelEnum(str, Enum):
    """通知渠道"""
    SYSTEM = 'SYSTEM'    # 系统消息
    EMAIL = 'EMAIL'      # 邮件
    SMS = 'SMS'          # 短信
    WECHAT = 'WECHAT'    # 微信


class DataScopeEnum(str, Enum):
    """数据权限范围"""
    ALL = 'ALL'            # 全部
    DEPT = 'DEPT'          # 部门
    PROJECT = 'PROJECT'    # 项目
    OWN = 'OWN'            # 个人
    CUSTOMER = 'CUSTOMER'  # 客户
