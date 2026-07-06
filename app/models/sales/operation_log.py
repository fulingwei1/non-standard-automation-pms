# -*- coding: utf-8 -*-
"""
销售业务操作日志模型

记录线索、商机、报价、合同等业务实体的操作历史，
支持变更追溯和审计。
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship

from app.models.base import Base


class SalesOperationLog(Base):
    """销售业务操作日志表

    统一记录销售模块（线索、商机、报价、合同）的业务操作，
    包括创建、更新、状态变更、审批等操作的完整记录。
    """

    __tablename__ = "sales_operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, comment="租户ID")

    # 业务实体标识
    entity_type = Column(
        String(50),
        nullable=False,
        comment="实体类型：LEAD/OPPORTUNITY/QUOTE/CONTRACT",
    )
    entity_id = Column(Integer, nullable=False, comment="实体ID")
    entity_code = Column(String(100), comment="实体编码（如合同编号）")

    # 操作信息
    operation_type = Column(
        String(50),
        nullable=False,
        comment="操作类型：CREATE/UPDATE/DELETE/STATUS_CHANGE/SUBMIT/APPROVE/REJECT/CONVERT",
    )
    operation_desc = Column(String(500), comment="操作描述")

    # 变更详情
    old_value = Column(JSON, comment="变更前值（JSON格式）")
    new_value = Column(JSON, comment="变更后值（JSON格式）")
    changed_fields = Column(JSON, comment="变更字段列表")

    # 操作人信息
    operator_id = Column(Integer, ForeignKey("users.id"), comment="操作人ID")
    operator_name = Column(String(100), comment="操作人姓名")
    operator_dept = Column(String(100), comment="操作人部门")

    # 操作上下文
    operation_time = Column(DateTime, default=datetime.now, nullable=False, comment="操作时间")
    ip_address = Column(String(50), comment="操作IP地址")
    user_agent = Column(String(500), comment="浏览器UA")
    request_id = Column(String(100), comment="请求ID（用于追踪）")

    # 备注
    remark = Column(Text, comment="备注说明")

    # 关系
    operator = relationship("User", foreign_keys=[operator_id])

    __table_args__ = (
        Index("idx_sales_log_entity", "entity_type", "entity_id"),
        Index("idx_sales_log_operator", "operator_id"),
        Index("idx_sales_log_time", "operation_time"),
        Index("idx_sales_log_type", "operation_type"),
        {"comment": "销售业务操作日志表"},
    )

    def __repr__(self):
        return (
            f"<SalesOperationLog {self.entity_type}:{self.entity_id} "
            f"{self.operation_type} by {self.operator_name}>"
        )


# 操作类型常量
class SalesOperationType:
    """销售操作类型枚举"""

    CREATE = "CREATE"  # 创建
    UPDATE = "UPDATE"  # 更新
    DELETE = "DELETE"  # 删除
    STATUS_CHANGE = "STATUS_CHANGE"  # 状态变更
    SUBMIT = "SUBMIT"  # 提交审批
    APPROVE = "APPROVE"  # 审批通过
    REJECT = "REJECT"  # 审批驳回
    CONVERT = "CONVERT"  # 转化（如线索转商机）
    ASSIGN = "ASSIGN"  # 分配
    TRANSFER = "TRANSFER"  # 转移
    ARCHIVE = "ARCHIVE"  # 归档
    RESTORE = "RESTORE"  # 恢复
    COMMENT = "COMMENT"  # 添加备注
    ATTACH = "ATTACH"  # 添加附件


# 实体类型常量
class SalesEntityType:
    """销售实体类型枚举"""

    LEAD = "LEAD"  # 线索
    OPPORTUNITY = "OPPORTUNITY"  # 商机
    QUOTE = "QUOTE"  # 报价
    QUOTE_VERSION = "QUOTE_VERSION"  # 报价版本
    CONTRACT = "CONTRACT"  # 合同
    INVOICE = "INVOICE"  # 发票
    RECEIVABLE_DISPUTE = "RECEIVABLE_DISPUTE"  # 回款争议
    CUSTOMER = "CUSTOMER"  # 客户
    CONTACT = "CONTACT"  # 联系人
    TARGET = "TARGET"  # 销售目标
    TEAM = "TEAM"  # 销售团队
    TEAM_PK = "TEAM_PK"  # 销售团队PK
    APPROVAL_WORKFLOW = "APPROVAL_WORKFLOW"  # 销售审批流程配置
    QUOTE_TEMPLATE = "QUOTE_TEMPLATE"  # 报价模板
    QUOTE_TEMPLATE_VERSION = "QUOTE_TEMPLATE_VERSION"  # 报价模板版本
    QUOTE_COST_TEMPLATE = "QUOTE_COST_TEMPLATE"  # 报价成本模板
    PURCHASE_MATERIAL_COST = "PURCHASE_MATERIAL_COST"  # 采购物料成本
    MATERIAL_COST_REMINDER = "MATERIAL_COST_REMINDER"  # 物料成本更新提醒
    CONTRACT_TEMPLATE = "CONTRACT_TEMPLATE"  # 合同模板
    CONTRACT_TEMPLATE_VERSION = "CONTRACT_TEMPLATE_VERSION"  # 合同模板版本
    CPQ_RULE_SET = "CPQ_RULE_SET"  # CPQ规则集
    PRESALE_EXPENSE = "PRESALE_EXPENSE"  # 售前费用
    MARGIN_ALERT_CONFIG = "MARGIN_ALERT_CONFIG"  # 毛利率预警配置
    SCORING_RULE = "SCORING_RULE"  # 评分规则
    FAILURE_CASE = "FAILURE_CASE"  # 失败案例
    ASSESSMENT_TEMPLATE = "ASSESSMENT_TEMPLATE"  # 技术评估模板
    ASSESSMENT_ITEM = "ASSESSMENT_ITEM"  # 技术评估项
    ASSESSMENT_RISK = "ASSESSMENT_RISK"  # 技术评估风险
    ASSESSMENT_VERSION = "ASSESSMENT_VERSION"  # 技术评估版本
