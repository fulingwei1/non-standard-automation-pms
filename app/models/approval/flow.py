# -*- coding: utf-8 -*-
"""
审批流程定义模型

定义审批流程、节点和路由规则
"""

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


class ApprovalFlowDefinition(Base, TimestampMixin):
    """审批流程定义 - 关联模板，定义具体流程"""

    __tablename__ = "approval_flow_definitions"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    template_id = Column(Integer, ForeignKey("approval_templates.id"), nullable=False, comment="模板ID")
    flow_name = Column(String(100), nullable=False, comment="流程名称")
    description = Column(Text, comment="流程描述")

    # 是否为默认流程（当没有匹配的路由规则时使用）
    is_default = Column(Boolean, default=False, comment="是否为默认流程")

    # 版本
    version = Column(Integer, default=1, comment="版本号")
    is_active = Column(Boolean, default=True, comment="是否启用")

    # 创建人
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")

    # 关系
    template = relationship("ApprovalTemplate", back_populates="flows")
    nodes = relationship("ApprovalNodeDefinition", back_populates="flow",
                        cascade="all, delete-orphan", order_by="ApprovalNodeDefinition.node_order")
    routing_rules = relationship("ApprovalRoutingRule", back_populates="flow")
    instances = relationship("ApprovalInstance", back_populates="flow")

    __table_args__ = (
        Index("idx_approval_flow_template", "template_id"),
        Index("idx_approval_flow_active", "is_active"),
        Index("idx_approval_flow_default", "template_id", "is_default"),
    )

    def __repr__(self):
        return f"<ApprovalFlowDefinition {self.flow_name}>"


class ApprovalNodeDefinition(Base, TimestampMixin):
    """审批节点定义 - 支持多种节点类型"""

    __tablename__ = "approval_node_definitions"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    flow_id = Column(Integer, ForeignKey("approval_flow_definitions.id"), nullable=False, comment="流程ID")

    # 节点基础信息
    node_code = Column(String(50), comment="节点编码")
    node_name = Column(String(100), nullable=False, comment="节点名称")
    node_order = Column(Integer, nullable=False, comment="节点顺序")

    # 节点类型
    node_type = Column(String(20), nullable=False, default="APPROVAL", comment="""
        节点类型：
        APPROVAL: 审批节点
        CC: 抄送节点
        CONDITION: 条件分支节点
        PARALLEL: 并行网关（分支）
        JOIN: 合并网关（汇聚）
    """)

    # 审批模式（仅APPROVAL类型有效）
    approval_mode = Column(String(20), default="SINGLE", comment="""
        审批模式：
        SINGLE: 单人审批
        OR_SIGN: 或签（任一人通过即通过）
        AND_SIGN: 会签（全部通过才通过）
        SEQUENTIAL: 依次审批（按顺序逐个审批）
    """)
    is_active = Column(Boolean, default=True, comment="节点是否启用")

    # 审批人配置
    approver_type = Column(String(30), comment="""
        审批人确定方式：
        FIXED_USER: 指定用户
        ROLE: 指定角色
        DEPARTMENT_HEAD: 部门主管
        DIRECT_MANAGER: 直属上级
        FORM_FIELD: 表单字段（动态从表单取值）
        INITIATOR_DEPT_HEAD: 发起人部门主管
        MULTI_DEPT: 多部门会签（如ECN评估）
        DYNAMIC: 动态计算
    """)
    approver_config = Column(JSON, comment="""
        审批人配置详情，示例：
        - FIXED_USER: {"user_ids": [1, 2, 3]}
        - ROLE: {"role_codes": ["SALES_MANAGER", "DEPT_HEAD"]}
        - DEPARTMENT_HEAD: {"level": 1}  // 向上几级
        - FORM_FIELD: {"field_name": "approver_id"}
        - MULTI_DEPT: {"departments": ["工程部", "采购部"], "eval_form": {...}}
    """)

    # 条件配置（仅CONDITION类型有效）
    condition_expression = Column(Text, comment="""
        条件表达式，示例：
        {"operator": "AND", "items": [
            {"field": "form.amount", "op": ">", "value": 10000}
        ]}
    """)

    # 分支配置（仅CONDITION类型有效）
    branches = Column(JSON, comment="""
        分支配置，示例：
        [
            {"condition": {...}, "next_node_id": 5},
            {"condition": null, "next_node_id": 6}  // 默认分支
        ]
    """)

    # 行为配置
    can_add_approver = Column(Boolean, default=False, comment="允许加签")
    can_transfer = Column(Boolean, default=True, comment="允许转审")
    can_delegate = Column(Boolean, default=True, comment="允许委托")
    can_reject_to = Column(String(20), default="START", comment="""
        驳回目标：
        START: 退回到发起人
        PREV: 退回到上一节点
        SPECIFIC: 可选择退回到任意之前的节点
        NONE: 不允许驳回（直接终止）
    """)

    # 超时配置
    timeout_hours = Column(Integer, comment="超时时间（小时），空表示不限时")
    timeout_action = Column(String(20), comment="""
        超时操作：
        REMIND: 仅提醒
        AUTO_PASS: 自动通过
        AUTO_REJECT: 自动驳回
        ESCALATE: 上报上级
    """)
    timeout_remind_hours = Column(Integer, comment="超时提醒时间（提前几小时提醒）")

    # 通知配置
    notify_config = Column(JSON, comment="""
        通知配置，示例：
        {
            "on_pending": true,       // 待审批时通知
            "on_approved": true,      // 审批通过时通知发起人
            "on_rejected": true,      // 审批驳回时通知发起人
            "channels": ["SYSTEM", "EMAIL", "WECHAT"]
        }
    """)

    # 评估表单配置（用于ECN等需要填写评估内容的场景）
    eval_form_schema = Column(JSON, comment="""
        评估表单定义（会签时各审批人需要填写的内容），示例：
        {
            "fields": [
                {"name": "impact_analysis", "type": "textarea", "label": "影响分析"},
                {"name": "cost_estimate", "type": "number", "label": "成本估算"}
            ]
        }
    """)

    # 关系
    flow = relationship("ApprovalFlowDefinition", back_populates="nodes")
    tasks = relationship("ApprovalTask", foreign_keys="[ApprovalTask.node_id]", back_populates="node")

    __table_args__ = (
        Index("idx_approval_node_flow", "flow_id"),
        Index("idx_approval_node_order", "flow_id", "node_order"),
        Index("idx_approval_node_type", "node_type"),
    )

    def __repr__(self):
        return f"<ApprovalNodeDefinition {self.node_name} ({self.node_type})>"


class ApprovalRoutingRule(Base, TimestampMixin):
    """审批路由规则 - 条件分流配置"""

    __tablename__ = "approval_routing_rules"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    template_id = Column(Integer, ForeignKey("approval_templates.id"), nullable=False, comment="模板ID")
    flow_id = Column(Integer, ForeignKey("approval_flow_definitions.id"), nullable=False, comment="匹配的流程ID")

    # 规则基础信息
    rule_name = Column(String(100), nullable=False, comment="规则名称")
    rule_order = Column(Integer, nullable=False, comment="规则优先级（数字越小优先级越高）")
    description = Column(Text, comment="规则描述")

    # 条件配置（支持多条件组合）
    conditions = Column(JSON, nullable=False, comment="""
        条件配置示例：
        {
            "operator": "AND",  // AND/OR
            "items": [
                {"field": "form.leave_days", "op": "<=", "value": 3},
                {"field": "form.leave_type", "op": "in", "value": ["年假", "事假"]},
                {"field": "entity.gross_margin", "op": "<", "value": 0.2},
                {"field": "initiator.dept_id", "op": "==", "value": 10}
            ]
        }

        支持的操作符：
        ==, !=, >, >=, <, <=, in, not_in, between, contains, is_null

        支持的字段来源：
        form.xxx - 表单字段
        entity.xxx - 业务实体属性
        initiator.xxx - 发起人属性
        sys.xxx - 系统变量
    """)

    is_active = Column(Boolean, default=True, comment="是否启用")

    # 创建人
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")

    # 关系
    template = relationship("ApprovalTemplate", back_populates="routing_rules")
    flow = relationship("ApprovalFlowDefinition", back_populates="routing_rules")

    __table_args__ = (
        Index("idx_routing_rule_template", "template_id"),
        Index("idx_routing_rule_order", "template_id", "rule_order"),
        Index("idx_routing_rule_active", "is_active"),
    )

    def __repr__(self):
        return f"<ApprovalRoutingRule {self.rule_name}>"
