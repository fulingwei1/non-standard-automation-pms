# -*- coding: utf-8 -*-
"""
阶段实例模型 - 项目运行时

包含：
- ProjectStageInstance: 项目阶段实例表
- ProjectNodeInstance: 项目节点实例表
- NodeTask: 节点子任务表（负责人自行分解）
"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import (
    CompletionMethodEnum,
    NodeTypeEnum,
    StageStatusEnum,
)
from app.models.scheduler_config import JSONType


class ProjectStageInstance(Base, TimestampMixin):
    """项目阶段实例表"""

    __tablename__ = "project_stage_instances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属项目ID",
    )
    stage_definition_id = Column(
        Integer,
        ForeignKey("stage_definitions.id", ondelete="SET NULL"),
        comment="来源阶段定义ID",
    )
    stage_code = Column(String(20), nullable=False, comment="阶段编码")
    stage_name = Column(String(100), nullable=False, comment="阶段名称")
    sequence = Column(Integer, nullable=False, default=0, comment="排序序号")
    status = Column(
        String(20),
        default=StageStatusEnum.PENDING.value,
        nullable=False,
        comment="状态: PENDING/IN_PROGRESS/COMPLETED/DELAYED/BLOCKED/SKIPPED",
    )
    planned_start_date = Column(Date, comment="计划开始日期")
    planned_end_date = Column(Date, comment="计划结束日期")
    actual_start_date = Column(Date, comment="实际开始日期")
    actual_end_date = Column(Date, comment="实际结束日期")
    is_modified = Column(Boolean, default=False, comment="是否被调整过")
    remark = Column(Text, comment="备注")

    # 扩展字段（从模板复制）
    category = Column(String(20), default="execution", comment="阶段分类")
    is_milestone = Column(Boolean, default=False, comment="是否关键里程碑")
    is_parallel = Column(Boolean, default=False, comment="是否支持并行执行")
    progress = Column(Integer, default=0, comment="阶段进度百分比")

    # 门控检查
    entry_criteria = Column(Text, comment="入口条件")
    exit_criteria = Column(Text, comment="出口条件")
    entry_check_result = Column(Text, comment="入口检查结果")
    exit_check_result = Column(Text, comment="出口检查结果")

    # 阶段评审
    review_required = Column(Boolean, default=False, comment="是否需要评审")
    review_result = Column(String(20), comment="评审结果: PASSED/CONDITIONAL/FAILED")
    review_date = Column(DateTime, comment="评审日期")
    review_notes = Column(Text, comment="评审记录")

    # 关系
    project = relationship("Project", back_populates="stage_instances")
    stage_definition = relationship("StageDefinition")
    nodes = relationship(
        "ProjectNodeInstance",
        back_populates="stage_instance",
        cascade="all, delete-orphan",
        order_by="ProjectNodeInstance.sequence",
    )

    __table_args__ = {"comment": "项目阶段实例表"}


class ProjectNodeInstance(Base, TimestampMixin):
    """项目节点实例表"""

    __tablename__ = "project_node_instances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属项目ID",
    )
    stage_instance_id = Column(
        Integer,
        ForeignKey("project_stage_instances.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属阶段实例ID",
    )
    node_definition_id = Column(
        Integer,
        ForeignKey("node_definitions.id", ondelete="SET NULL"),
        comment="来源节点定义ID",
    )
    node_code = Column(String(20), nullable=False, comment="节点编码")
    node_name = Column(String(100), nullable=False, comment="节点名称")
    node_type = Column(
        String(20),
        default=NodeTypeEnum.TASK.value,
        nullable=False,
        comment="节点类型: TASK/APPROVAL/DELIVERABLE",
    )
    sequence = Column(Integer, nullable=False, default=0, comment="排序序号")
    status = Column(
        String(20),
        default=StageStatusEnum.PENDING.value,
        nullable=False,
        comment="状态: PENDING/IN_PROGRESS/COMPLETED/DELAYED/BLOCKED/SKIPPED",
    )
    progress = Column(Integer, default=0, comment="节点进度百分比")
    completion_method = Column(
        String(20),
        default=CompletionMethodEnum.MANUAL.value,
        nullable=False,
        comment="完成方式",
    )
    dependency_node_instance_ids = Column(JSONType, comment="前置依赖节点实例ID列表")
    is_required = Column(Boolean, default=True, comment="是否必需节点")
    planned_date = Column(Date, comment="计划完成日期")
    actual_date = Column(Date, comment="实际完成日期")
    completed_by = Column(Integer, ForeignKey("users.id"), comment="完成人ID")
    completed_at = Column(DateTime, comment="完成时间")
    attachments = Column(JSONType, comment="上传的附件列表(JSON)")
    approval_record_id = Column(Integer, comment="关联审批记录ID")
    remark = Column(Text, comment="备注")

    # 任务分解相关
    assignee_id = Column(Integer, ForeignKey("users.id"), comment="负责人ID")
    auto_complete_on_tasks = Column(
        Boolean,
        default=True,
        comment="子任务全部完成时是否自动完成节点"
    )

    # 责任分配与交付物（从模板复制，可修改）
    owner_role_code = Column(String(50), comment="负责角色编码")
    participant_role_codes = Column(JSONType, comment="参与角色编码列表(JSON数组)")
    deliverables = Column(JSONType, comment="交付物清单(JSON数组)")
    # 实际指派的人员
    owner_id = Column(Integer, ForeignKey("users.id"), comment="实际负责人ID")
    participant_ids = Column(JSONType, comment="实际参与人ID列表(JSON数组)")

    # 关系
    project = relationship("Project", back_populates="node_instances")
    stage_instance = relationship("ProjectStageInstance", back_populates="nodes")
    node_definition = relationship("NodeDefinition")
    completer = relationship("User", foreign_keys=[completed_by])
    assignee = relationship("User", foreign_keys=[assignee_id])
    owner = relationship("User", foreign_keys=[owner_id])
    tasks = relationship(
        "NodeTask",
        back_populates="node_instance",
        cascade="all, delete-orphan",
        order_by="NodeTask.sequence"
    )

    __table_args__ = {"comment": "项目节点实例表"}


class NodeTask(Base, TimestampMixin):
    """
    节点子任务表

    由节点负责人自行分解的执行任务，用于个人工作管理。
    当所有子任务完成时，可自动触发节点完成（根据配置）。
    """

    __tablename__ = "node_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_instance_id = Column(
        Integer,
        ForeignKey("project_node_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属节点实例ID",
    )
    task_code = Column(String(30), nullable=False, comment="任务编码")
    task_name = Column(String(200), nullable=False, comment="任务名称")
    description = Column(Text, comment="任务描述")
    sequence = Column(Integer, nullable=False, default=0, comment="排序序号")

    # 状态
    status = Column(
        String(20),
        default=StageStatusEnum.PENDING.value,
        nullable=False,
        comment="状态: PENDING/IN_PROGRESS/COMPLETED/SKIPPED",
    )

    # 时间
    estimated_hours = Column(Integer, comment="预计工时(小时)")
    actual_hours = Column(Integer, comment="实际工时(小时)")
    planned_start_date = Column(Date, comment="计划开始日期")
    planned_end_date = Column(Date, comment="计划结束日期")
    actual_start_date = Column(Date, comment="实际开始日期")
    actual_end_date = Column(Date, comment="实际结束日期")

    # 执行人（默认继承节点负责人，也可指定其他人）
    assignee_id = Column(Integer, ForeignKey("users.id"), comment="执行人ID")
    completed_by = Column(Integer, ForeignKey("users.id"), comment="完成人ID")
    completed_at = Column(DateTime, comment="完成时间")

    # 优先级和标签
    priority = Column(String(20), default="NORMAL", comment="优先级: LOW/NORMAL/HIGH/URGENT")
    tags = Column(String(200), comment="标签(逗号分隔)")

    # 附件和备注
    attachments = Column(JSONType, comment="附件列表(JSON)")
    remark = Column(Text, comment="备注")

    # 关系
    node_instance = relationship("ProjectNodeInstance", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_id])
    completer = relationship("User", foreign_keys=[completed_by])

    __table_args__ = {"comment": "节点子任务表"}

    def __repr__(self):
        return f"<NodeTask {self.task_code}: {self.task_name}>"
