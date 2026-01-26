# -*- coding: utf-8 -*-
"""
服务模型模块

聚合所有客服服务相关的模型，保持向后兼容
"""
from .communication_satisfaction import (
    CustomerCommunication,
    CustomerSatisfaction,
    SatisfactionSurveyTemplate,
)
from .enums import (
    CommunicationTypeEnum,
    ServiceRecordStatusEnum,
    ServiceRecordTypeEnum,
    ServiceTicketProblemTypeEnum,
    ServiceTicketStatusEnum,
    ServiceTicketUrgencyEnum,
    SurveyStatusEnum,
    SurveyTypeEnum,
)
from .knowledge import KnowledgeBase
from .record import ServiceRecord
from .ticket import ServiceTicket, ServiceTicketCcUser, ServiceTicketProject

__all__ = [
    # Enums
    "ServiceTicketStatusEnum",
    "ServiceTicketUrgencyEnum",
    "ServiceTicketProblemTypeEnum",
    "ServiceRecordTypeEnum",
    "ServiceRecordStatusEnum",
    "CommunicationTypeEnum",
    "SurveyStatusEnum",
    "SurveyTypeEnum",
    # Ticket
    "ServiceTicket",
    "ServiceTicketProject",
    "ServiceTicketCcUser",
    # Record
    "ServiceRecord",
    # Communication and Satisfaction
    "CustomerCommunication",
    "CustomerSatisfaction",
    "SatisfactionSurveyTemplate",
    # Knowledge
    "KnowledgeBase",
]
