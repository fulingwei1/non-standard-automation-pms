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


# ==================== 绩效管理相关 ====================

class PerformanceLevelEnum(str, Enum):
    """绩效等级"""
    EXCELLENT = 'EXCELLENT'              # 优秀 (A)
    GOOD = 'GOOD'                        # 良好 (B)
    QUALIFIED = 'QUALIFIED'              # 合格 (C)
    NEEDS_IMPROVEMENT = 'NEEDS_IMPROVEMENT'  # 待改进 (D)


# ==================== 奖金激励相关 ====================

class BonusTypeEnum(str, Enum):
    """奖金类型"""
    PERFORMANCE_BASED = 'PERFORMANCE_BASED'  # 绩效奖金
    PROJECT_BASED = 'PROJECT_BASED'          # 项目奖金
    MILESTONE_BASED = 'MILESTONE_BASED'      # 里程碑奖金
    TEAM_BASED = 'TEAM_BASED'                # 团队奖金
    SALES_BASED = 'SALES_BASED'              # 销售奖金
    SALES_DIRECTOR_BASED = 'SALES_DIRECTOR_BASED'  # 销售总监奖金
    PRESALE_BASED = 'PRESALE_BASED'          # 售前技术支持奖金


class BonusCalculationStatusEnum(str, Enum):
    """奖金计算状态"""
    CALCULATED = 'CALCULATED'    # 已计算
    APPROVED = 'APPROVED'        # 已审批
    DISTRIBUTED = 'DISTRIBUTED'  # 已发放
    CANCELLED = 'CANCELLED'      # 已取消


class BonusDistributionStatusEnum(str, Enum):
    """奖金发放状态"""
    PENDING = 'PENDING'    # 待发放
    PAID = 'PAID'          # 已发放
    CANCELLED = 'CANCELLED'  # 已取消


class PaymentMethodEnum(str, Enum):
    """发放方式"""
    CASH = 'CASH'                    # 现金
    BANK_TRANSFER = 'BANK_TRANSFER'  # 银行转账
    SALARY = 'SALARY'                # 工资合并


class TeamBonusAllocationMethodEnum(str, Enum):
    """团队奖金分配方式"""
    EQUAL = 'EQUAL'                  # 平均分配
    BY_CONTRIBUTION = 'BY_CONTRIBUTION'  # 按贡献分配
    BY_ROLE = 'BY_ROLE'              # 按角色分配
    CUSTOM = 'CUSTOM'                # 自定义


# ==================== 项目评价相关 ====================

class ProjectNoveltyLevelEnum(str, Enum):
    """项目新旧程度"""
    BRAND_NEW = 'BRAND_NEW'          # 全新项目（从未做过）
    SIMILAR = 'SIMILAR'              # 类似项目（做过类似）
    STANDARD = 'STANDARD'            # 标准项目（做过多次）
    FULLY_STANDARD = 'FULLY_STANDARD'  # 完全标准项目


class ProjectEvaluationLevelEnum(str, Enum):
    """项目评价等级"""
    S = 'S'  # S级：90-100分（战略项目/超高难度）
    A = 'A'  # A级：80-89分（重点项目/高难度）
    B = 'B'  # B级：70-79分（一般项目/中等难度）
    C = 'C'  # C级：60-69分（普通项目/低难度）
    D = 'D'  # D级：<60分（简单项目）


class ProjectEvaluationStatusEnum(str, Enum):
    """项目评价状态"""
    DRAFT = 'DRAFT'          # 草稿
    CONFIRMED = 'CONFIRMED'  # 已确认
    ARCHIVED = 'ARCHIVED'    # 已归档


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


class IssueRootCauseEnum(str, Enum):
    """问题原因"""
    DESIGN_ERROR = 'DESIGN_ERROR'        # 设计问题
    MATERIAL_DEFECT = 'MATERIAL_DEFECT'   # 物料缺陷
    PROCESS_ERROR = 'PROCESS_ERROR'       # 工艺问题
    EXTERNAL_FACTOR = 'EXTERNAL_FACTOR'   # 外部因素
    OTHER = 'OTHER'                       # 其他


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
    SPECIFICATION_MISMATCH = 'SPECIFICATION_MISMATCH'  # 规格不匹配
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


# ==================== 技术规格匹配相关 ====================

class SpecRequirementLevelEnum(str, Enum):
    """规格要求级别"""
    REQUIRED = 'REQUIRED'    # 必需
    OPTIONAL = 'OPTIONAL'    # 可选
    STRICT = 'STRICT'        # 严格


class SpecMatchTypeEnum(str, Enum):
    """规格匹配类型"""
    BOM = 'BOM'                    # BOM
    PURCHASE_ORDER = 'PURCHASE_ORDER'  # 采购订单


class SpecMatchStatusEnum(str, Enum):
    """规格匹配状态"""
    MATCHED = 'MATCHED'        # 匹配
    MISMATCHED = 'MISMATCHED'  # 不匹配
    UNKNOWN = 'UNKNOWN'        # 未知


# ==================== 销售管理相关 ====================

class LeadStatusEnum(str, Enum):
    """线索状态"""
    NEW = 'NEW'              # 待跟进
    QUALIFYING = 'QUALIFYING'  # 资格评估中
    INVALID = 'INVALID'      # 无效
    CONVERTED = 'CONVERTED'  # 已转商机


class OpportunityStageEnum(str, Enum):
    """商机阶段"""
    DISCOVERY = 'DISCOVERY'      # 需求澄清
    QUALIFIED = 'QUALIFIED'      # 商机合格
    PROPOSAL = 'PROPOSAL'        # 方案/报价中
    NEGOTIATION = 'NEGOTIATION'  # 商务谈判
    WON = 'WON'                  # 赢单
    LOST = 'LOST'                # 丢单
    ON_HOLD = 'ON_HOLD'          # 暂停


class GateStatusEnum(str, Enum):
    """阶段门状态"""
    PENDING = 'PENDING'  # 待审核
    PASS = 'PASS'        # 通过
    REJECT = 'REJECT'    # 拒绝


class QuoteStatusEnum(str, Enum):
    """报价状态"""
    DRAFT = 'DRAFT'          # 草稿
    IN_REVIEW = 'IN_REVIEW'  # 审批中
    APPROVED = 'APPROVED'    # 已批准
    SENT = 'SENT'            # 已发送
    EXPIRED = 'EXPIRED'      # 过期
    REJECTED = 'REJECTED'    # 被拒


class ContractStatusEnum(str, Enum):
    """合同状态"""
    DRAFT = 'DRAFT'          # 草拟中
    IN_REVIEW = 'IN_REVIEW'  # 审批中
    SIGNED = 'SIGNED'        # 已签订
    ACTIVE = 'ACTIVE'        # 执行中
    CLOSED = 'CLOSED'        # 已结案
    CANCELLED = 'CANCELLED'  # 取消


class InvoiceStatusEnum(str, Enum):
    """发票状态"""
    DRAFT = 'DRAFT'          # 草稿
    APPLIED = 'APPLIED'      # 已申请
    APPROVED = 'APPROVED'    # 已批准
    ISSUED = 'ISSUED'        # 已开票
    VOID = 'VOID'            # 作废


class InvoiceTypeEnum(str, Enum):
    """发票类型"""
    SPECIAL = 'SPECIAL'      # 专票
    NORMAL = 'NORMAL'        # 普票


class QuoteItemTypeEnum(str, Enum):
    """报价明细类型"""
    MODULE = 'MODULE'        # 模块
    LABOR = 'LABOR'          # 工时
    SOFTWARE = 'SOFTWARE'    # 软件
    OUTSOURCE = 'OUTSOURCE'  # 外协
    OTHER = 'OTHER'          # 其他


class DisputeStatusEnum(str, Enum):
    """回款争议状态"""
    OPEN = 'OPEN'            # 开放
    PROCESSING = 'PROCESSING'  # 处理中
    RESOLVED = 'RESOLVED'    # 已解决
    CLOSED = 'CLOSED'        # 已关闭


class DisputeReasonCodeEnum(str, Enum):
    """回款争议原因代码"""
    NO_ACCEPTANCE = 'NO_ACCEPTANCE'      # 未验收
    MISSING_DOCS = 'MISSING_DOCS'        # 资料缺失
    ACCOUNT_MISMATCH = 'ACCOUNT_MISMATCH'  # 对账问题
    PERFORMANCE_DISPUTE = 'PERFORMANCE_DISPUTE'  # 性能争议
    SCOPE_DISPUTE = 'SCOPE_DISPUTE'      # 范围争议
    OTHER = 'OTHER'                      # 其他


# ==================== 技术评审相关 ====================

class ReviewTypeEnum(str, Enum):
    """评审类型"""
    PDR = 'PDR'  # 方案设计评审 (Preliminary Design Review)
    DDR = 'DDR'  # 详细设计评审 (Detailed Design Review)
    PRR = 'PRR'  # 生产准备评审 (Production Readiness Review)
    FRR = 'FRR'  # 出厂评审 (Factory Review)
    ARR = 'ARR'  # 现场评审 (Acceptance Review)


class ReviewStatusEnum(str, Enum):
    """评审状态"""
    DRAFT = 'DRAFT'              # 草稿
    PENDING = 'PENDING'          # 待评审
    IN_PROGRESS = 'IN_PROGRESS'  # 评审中
    COMPLETED = 'COMPLETED'      # 已完成
    CANCELLED = 'CANCELLED'      # 已取消


class MeetingTypeEnum(str, Enum):
    """会议形式"""
    ONSITE = 'ONSITE'    # 现场
    ONLINE = 'ONLINE'    # 线上
    HYBRID = 'HYBRID'    # 混合


class ReviewConclusionEnum(str, Enum):
    """评审结论"""
    PASS = 'PASS'                    # 通过
    PASS_WITH_CONDITION = 'PASS_WITH_CONDITION'  # 有条件通过
    REJECT = 'REJECT'                # 不通过
    ABORT = 'ABORT'                  # 中止


class ParticipantRoleEnum(str, Enum):
    """评审参与人角色"""
    HOST = 'HOST'          # 主持人
    EXPERT = 'EXPERT'      # 评审专家
    PRESENTER = 'PRESENTER'  # 汇报人
    RECORDER = 'RECORDER'  # 记录人
    OBSERVER = 'OBSERVER'  # 观察者


class AttendanceStatusEnum(str, Enum):
    """出席状态"""
    PENDING = 'PENDING'      # 待确认
    CONFIRMED = 'CONFIRMED'  # 已确认
    ABSENT = 'ABSENT'        # 缺席
    DELEGATED = 'DELEGATED'  # 已委派


class MaterialTypeEnumReview(str, Enum):
    """评审材料类型"""
    DRAWING = 'DRAWING'    # 图纸
    BOM = 'BOM'            # BOM清单
    REPORT = 'REPORT'      # 报告
    DOCUMENT = 'DOCUMENT'  # 文档
    OTHER = 'OTHER'        # 其他


class ChecklistResultEnum(str, Enum):
    """检查项结果"""
    PASS = 'PASS'    # 通过
    FAIL = 'FAIL'    # 不通过
    NA = 'NA'        # 不适用


class IssueLevelEnum(str, Enum):
    """问题等级"""
    A = 'A'  # A类问题（严重）
    B = 'B'  # B类问题（重要）
    C = 'C'  # C类问题（一般）
    D = 'D'  # D类问题（轻微）


class ReviewIssueStatusEnum(str, Enum):
    """评审问题状态"""
    OPEN = 'OPEN'              # 开放
    PROCESSING = 'PROCESSING'  # 处理中
    RESOLVED = 'RESOLVED'      # 已解决
    VERIFIED = 'VERIFIED'      # 已验证
    CLOSED = 'CLOSED'          # 已关闭


class VerifyResultEnum(str, Enum):
    """验证结果"""
    PASS = 'PASS'    # 通过
    FAIL = 'FAIL'    # 不通过


# ==================== 技术评估相关 ====================

class AssessmentSourceTypeEnum(str, Enum):
    """技术评估来源类型"""
    LEAD = 'LEAD'              # 线索
    OPPORTUNITY = 'OPPORTUNITY'  # 商机


class AssessmentStatusEnum(str, Enum):
    """技术评估状态"""
    PENDING = 'PENDING'        # 待评估
    IN_PROGRESS = 'IN_PROGRESS'  # 评估中
    COMPLETED = 'COMPLETED'    # 已完成
    CANCELLED = 'CANCELLED'    # 已取消


class AssessmentDecisionEnum(str, Enum):
    """技术评估决策建议"""
    RECOMMEND = 'RECOMMEND'              # 推荐立项
    CONDITIONAL = 'CONDITIONAL'         # 有条件立项
    DEFER = 'DEFER'                     # 暂缓
    NOT_RECOMMEND = 'NOT_RECOMMEND'     # 不建议立项


class FreezeTypeEnum(str, Enum):
    """需求冻结类型"""
    SOLUTION = 'SOLUTION'           # 方案冻结
    INTERFACE = 'INTERFACE'         # 接口冻结
    ACCEPTANCE = 'ACCEPTANCE'       # 验收冻结
    KEY_SELECTION = 'KEY_SELECTION'  # 关键选型冻结


class OpenItemTypeEnum(str, Enum):
    """未决事项类型"""
    INTERFACE = 'INTERFACE'         # 接口
    TAKT = 'TAKT'                   # 节拍
    ACCEPTANCE = 'ACCEPTANCE'       # 验收
    SAMPLE = 'SAMPLE'               # 样品
    SITE = 'SITE'                   # 现场
    REGULATION = 'REGULATION'       # 法规
    BUSINESS = 'BUSINESS'           # 商务
    OTHER = 'OTHER'                 # 其他


class OpenItemStatusEnum(str, Enum):
    """未决事项状态"""
    PENDING = 'PENDING'             # 待确认
    REPLIED = 'REPLIED'             # 已回复
    VERIFIED = 'VERIFIED'           # 已验证
    CLOSED = 'CLOSED'               # 关闭


class ResponsiblePartyEnum(str, Enum):
    """责任方"""
    CUSTOMER = 'CUSTOMER'           # 客户
    SALES = 'SALES'                 # 销售
    PRESALES = 'PRESALES'           # 售前
    ENGINEERING = 'ENGINEERING'     # 工程
    PROCUREMENT = 'PROCUREMENT'     # 采购
    OTHER = 'OTHER'                 # 其他


# ==================== 装配齐套分析相关 ====================

class AssemblyStageEnum(str, Enum):
    """装配阶段"""
    FRAME = 'FRAME'        # 框架装配
    MECH = 'MECH'          # 机械模组
    ELECTRIC = 'ELECTRIC'  # 电气安装
    WIRING = 'WIRING'      # 线路整理
    DEBUG = 'DEBUG'        # 调试准备
    COSMETIC = 'COSMETIC'  # 外观完善


class ImportanceLevelEnum(str, Enum):
    """物料重要程度"""
    CRITICAL = 'CRITICAL'  # 关键(缺失必停工)
    HIGH = 'HIGH'          # 高(影响进度)
    NORMAL = 'NORMAL'      # 普通
    LOW = 'LOW'            # 低(可后补)


class ShortageAlertLevelEnum(str, Enum):
    """缺料预警级别"""
    L1 = 'L1'  # 停工预警(已到开工日期仍缺料)
    L2 = 'L2'  # 紧急预警(3天内需要)
    L3 = 'L3'  # 提前预警(7天内需要)
    L4 = 'L4'  # 常规预警(14天内需要)


class ShortageStatusEnum(str, Enum):
    """缺料状态"""
    OPEN = 'OPEN'              # 开放
    ORDERING = 'ORDERING'      # 采购中
    IN_TRANSIT = 'IN_TRANSIT'  # 在途
    RESOLVED = 'RESOLVED'      # 已解决
    CANCELLED = 'CANCELLED'    # 已取消


class ReadinessStatusEnum(str, Enum):
    """齐套分析状态"""
    DRAFT = 'DRAFT'          # 草稿
    CONFIRMED = 'CONFIRMED'  # 已确认
    EXPIRED = 'EXPIRED'      # 已过期


class ReadinessAnalysisTypeEnum(str, Enum):
    """齐套分析类型"""
    AUTO = 'AUTO'          # 自动分析
    MANUAL = 'MANUAL'      # 手动分析
    SCHEDULED = 'SCHEDULED'  # 定时分析


class SuggestionTypeEnum(str, Enum):
    """排产建议类型"""
    START = 'START'          # 建议开工
    DELAY = 'DELAY'          # 建议延期
    EXPEDITE = 'EXPEDITE'    # 建议加急采购
    SUBSTITUTE = 'SUBSTITUTE'  # 建议替代料
    PARTIAL = 'PARTIAL'      # 建议部分开工


class SuggestionStatusEnum(str, Enum):
    """排产建议状态"""
    PENDING = 'PENDING'      # 待处理
    ACCEPTED = 'ACCEPTED'    # 已接受
    REJECTED = 'REJECTED'    # 已拒绝
    EXPIRED = 'EXPIRED'      # 已过期


class EquipmentTypeEnum(str, Enum):
    """设备类型(用于装配模板)"""
    ICT = 'ICT'              # ICT测试设备
    FCT = 'FCT'              # FCT测试设备
    EOL = 'EOL'              # EOL测试设备
    AGING = 'AGING'          # 老化设备
    VISION = 'VISION'        # 视觉检测设备
    ASSEMBLY = 'ASSEMBLY'    # 自动化组装线
    BURN_IN = 'BURN_IN'      # 烧录设备
    TEST = 'TEST'            # 通用测试设备
    OTHER = 'OTHER'          # 其他
