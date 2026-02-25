# -*- coding: utf-8 -*-
"""
移动端AI销售助手 - 数据库模型
"""


from sqlalchemy import (
    JSON,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class PresaleMobileAssistantChat(Base, TimestampMixin):
    """移动助手对话记录表"""

    __tablename__ = "presale_mobile_assistant_chat"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    presale_ticket_id = Column(
        Integer, ForeignKey("presale_support_ticket.id"), nullable=True, comment="售前工单ID"
    )
    question = Column(Text, comment="提问内容")
    answer = Column(Text, comment="AI回答")
    question_type = Column(
        Enum("technical", "competitor", "case", "pricing", "other", name="question_type_enum"),
        default="other",
        comment="问题类型：技术/竞品/案例/报价/其他",
    )
    context = Column(JSON, comment="对话上下文")
    response_time = Column(Integer, comment="响应时间（毫秒）")

    # 关系
    user = relationship("User", foreign_keys=[user_id])


class PresaleVisitRecord(Base, TimestampMixin):
    """拜访记录表"""

    __tablename__ = "presale_visit_record"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    presale_ticket_id = Column(
        Integer, ForeignKey("presale_support_ticket.id"), nullable=False, comment="售前工单ID"
    )
    customer_id = Column(
        Integer, ForeignKey("customers.id"), nullable=False, comment="客户ID"
    )
    visit_date = Column(Date, nullable=False, comment="拜访日期")
    visit_type = Column(
        Enum(
            "first_contact",
            "follow_up",
            "demo",
            "negotiation",
            "closing",
            name="visit_type_enum",
        ),
        nullable=False,
        comment="拜访类型：初次接触/跟进/演示/谈判/签约",
    )
    attendees = Column(JSON, comment="参会人员")
    discussion_points = Column(Text, comment="讨论要点")
    customer_feedback = Column(Text, comment="客户反馈")
    next_steps = Column(Text, comment="下一步行动")
    audio_recording_url = Column(String(255), comment="录音文件URL")
    ai_generated_summary = Column(Text, comment="AI生成的摘要")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")

    # 关系
    presale_ticket = relationship("PresaleSupportTicket", foreign_keys=[presale_ticket_id])
    created_by_user = relationship("User", foreign_keys=[created_by])


class PresaleMobileQuickEstimate(Base, TimestampMixin):
    """移动端快速估价记录表"""

    __tablename__ = "presale_mobile_quick_estimate"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    presale_ticket_id = Column(
        Integer, ForeignKey("presale_support_ticket.id"), nullable=True, comment="售前工单ID"
    )
    customer_id = Column(
        Integer, ForeignKey("customers.id"), nullable=True, comment="客户ID"
    )
    equipment_photo_url = Column(String(255), comment="设备照片URL")
    recognized_equipment = Column(String(200), comment="识别的设备名称")
    equipment_description = Column(Text, comment="设备描述")
    estimated_cost = Column(Integer, comment="预估成本（元）")
    price_range_min = Column(Integer, comment="报价范围最小值（元）")
    price_range_max = Column(Integer, comment="报价范围最大值（元）")
    bom_items = Column(JSON, comment="BOM物料清单")
    confidence_score = Column(Integer, comment="识别置信度（0-100）")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")

    # 关系
    created_by_user = relationship("User", foreign_keys=[created_by])


class PresaleMobileOfflineData(Base, TimestampMixin):
    """移动端离线数据同步表"""

    __tablename__ = "presale_mobile_offline_data"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    data_type = Column(
        String(50), nullable=False, comment="数据类型：chat/visit/estimate"
    )
    local_id = Column(String(100), comment="本地临时ID")
    data_payload = Column(JSON, comment="数据内容")
    sync_status = Column(
        String(20), default="pending", comment="同步状态：pending/synced/failed"
    )
    synced_at = Column(DateTime, comment="同步时间")
    error_message = Column(Text, comment="错误信息")

    # 关系
    user = relationship("User", foreign_keys=[user_id])
