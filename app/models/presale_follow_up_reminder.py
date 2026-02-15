"""
跟进提醒模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base
import enum


class ReminderPriority(str, enum.Enum):
    """提醒优先级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReminderStatus(str, enum.Enum):
    """提醒状态"""
    PENDING = "pending"
    COMPLETED = "completed"
    DISMISSED = "dismissed"


class PresaleFollowUpReminder(Base):
    """跟进提醒表"""
    __tablename__ = "presale_follow_up_reminder"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    presale_ticket_id = Column(Integer, ForeignKey("presale_tickets.id"), nullable=False, index=True, comment="售前工单ID")
    recommended_time = Column(DateTime, comment="推荐跟进时间")
    priority = Column(Enum(ReminderPriority), comment="优先级")
    follow_up_content = Column(Text, comment="跟进内容建议")
    reason = Column(Text, comment="最佳时机理由")
    status = Column(Enum(ReminderStatus), default=ReminderStatus.PENDING, comment="状态")
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<PresaleFollowUpReminder(id={self.id}, ticket_id={self.presale_ticket_id}, priority={self.priority})>"
