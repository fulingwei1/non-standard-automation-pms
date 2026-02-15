"""
售前AI系统集成 - 数据模型
Team 10: 售前AI系统集成与前端UI
"""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, JSON,
    Date, TIMESTAMP, ForeignKey, Enum, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class AIFunctionEnum(str, enum.Enum):
    """AI功能枚举"""
    REQUIREMENT = "requirement"  # 需求理解AI
    SOLUTION = "solution"  # 方案生成AI
    COST = "cost"  # 成本估算AI
    WINRATE = "winrate"  # 赢率预测AI
    QUOTATION = "quotation"  # 报价生成AI
    KNOWLEDGE = "knowledge"  # 知识库AI
    SCRIPT = "script"  # 话术推荐AI
    EMOTION = "emotion"  # 情绪分析AI
    MOBILE = "mobile"  # 移动助手


class WorkflowStepEnum(str, enum.Enum):
    """工作流步骤枚举"""
    REQUIREMENT = "requirement"
    SOLUTION = "solution"
    COST = "cost"
    WINRATE = "winrate"
    QUOTATION = "quotation"


class WorkflowStatusEnum(str, enum.Enum):
    """工作流状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class PresaleAIUsageStats(Base):
    """AI功能使用统计表"""
    __tablename__ = "presale_ai_usage_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ai_function = Column(Enum(AIFunctionEnum), nullable=False)
    usage_count = Column(Integer, default=0, comment="使用次数")
    success_count = Column(Integer, default=0, comment="成功次数")
    avg_response_time = Column(Integer, comment="平均响应时间(毫秒)")
    date = Column(Date, nullable=False, comment="统计日期")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    # 关系
    user = relationship("User", backref="ai_usage_stats")

    __table_args__ = (
        Index('idx_user_function_date', 'user_id', 'ai_function', 'date'),
        Index('idx_date', 'date'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )


class PresaleAIFeedback(Base):
    """AI反馈表"""
    __tablename__ = "presale_ai_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ai_function = Column(String(50), nullable=False, comment="AI功能名称")
    presale_ticket_id = Column(Integer, nullable=True, comment="关联售前工单ID")
    rating = Column(Integer, nullable=False, comment="评分1-5星")
    feedback_text = Column(Text, nullable=True, comment="反馈内容")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    # 关系
    user = relationship("User", backref="ai_feedbacks")

    __table_args__ = (
        Index('idx_user_function', 'user_id', 'ai_function'),
        Index('idx_rating', 'rating'),
        Index('idx_created_at', 'created_at'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )


class PresaleAIConfig(Base):
    """AI配置表"""
    __tablename__ = "presale_ai_config"

    id = Column(Integer, primary_key=True, index=True)
    ai_function = Column(String(50), nullable=False, unique=True, comment="AI功能名称")
    enabled = Column(Boolean, default=True, comment="是否启用")
    model_name = Column(String(100), nullable=True, comment="模型名称")
    temperature = Column(Float, default=0.7, comment="温度参数")
    max_tokens = Column(Integer, default=2000, comment="最大token数")
    timeout_seconds = Column(Integer, default=30, comment="超时时间(秒)")
    config_json = Column(JSON, nullable=True, comment="其他配置参数")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'},
    )


class PresaleAIWorkflowLog(Base):
    """AI工作流日志表"""
    __tablename__ = "presale_ai_workflow_log"

    id = Column(Integer, primary_key=True, index=True)
    presale_ticket_id = Column(Integer, nullable=False, comment="售前工单ID")
    workflow_step = Column(Enum(WorkflowStepEnum), nullable=False, comment="工作流步骤")
    status = Column(Enum(WorkflowStatusEnum), default=WorkflowStatusEnum.PENDING, comment="状态")
    input_data = Column(JSON, nullable=True, comment="输入数据")
    output_data = Column(JSON, nullable=True, comment="输出数据")
    error_message = Column(Text, nullable=True, comment="错误信息")
    started_at = Column(TIMESTAMP, nullable=True, comment="开始时间")
    completed_at = Column(TIMESTAMP, nullable=True, comment="完成时间")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    __table_args__ = (
        Index('idx_ticket_step', 'presale_ticket_id', 'workflow_step'),
        Index('idx_status', 'status'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )


class PresaleAIAuditLog(Base):
    """AI审计日志表"""
    __tablename__ = "presale_ai_audit_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(100), nullable=False, comment="操作类型")
    ai_function = Column(String(50), nullable=True, comment="AI功能")
    resource_type = Column(String(50), nullable=True, comment="资源类型")
    resource_id = Column(Integer, nullable=True, comment="资源ID")
    details = Column(JSON, nullable=True, comment="详细信息")
    ip_address = Column(String(45), nullable=True, comment="IP地址")
    user_agent = Column(String(255), nullable=True, comment="用户代理")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    # 关系
    user = relationship("User", backref="ai_audit_logs")

    __table_args__ = (
        Index('idx_user_action', 'user_id', 'action'),
        Index('idx_created_at', 'created_at'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'}
    )
