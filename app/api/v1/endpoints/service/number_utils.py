# -*- coding: utf-8 -*-
"""
客服模块编号生成工具
"""

from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session


def generate_ticket_no(db: Session) -> str:
    """生成服务工单号：SRV-yymmdd-xxx"""
    from app.models.service import ServiceTicket
    from app.utils.number_generator import generate_sequential_no

    return generate_sequential_no(
        db=db,
        model_class=ServiceTicket,
        no_field='ticket_no',
        prefix='SRV',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )


def generate_record_no(db: Session) -> str:
    """生成服务记录号：REC-yymmdd-xxx"""
    from app.models.service import ServiceRecord
    from app.utils.number_generator import generate_sequential_no

    return generate_sequential_no(
        db=db,
        model_class=ServiceRecord,
        no_field='record_no',
        prefix='REC',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )


def generate_communication_no(db: Session) -> str:
    """生成沟通记录号：COM-yymmdd-xxx"""
    from app.models.service import CustomerCommunication

    today = datetime.now().strftime("%y%m%d")
    max_comm = (
        db.query(CustomerCommunication)
        .filter(CustomerCommunication.communication_no.like(f"COM-{today}-%"))
        .order_by(desc(CustomerCommunication.communication_no))
        .first()
    )
    if max_comm:
        seq = int(max_comm.communication_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"COM-{today}-{seq:03d}"


def generate_survey_no(db: Session) -> str:
    """生成调查号：SUR-yymmdd-xxx"""
    from app.models.service import CustomerSatisfaction

    today = datetime.now().strftime("%y%m%d")
    max_survey = (
        db.query(CustomerSatisfaction)
        .filter(CustomerSatisfaction.survey_no.like(f"SUR-{today}-%"))
        .order_by(desc(CustomerSatisfaction.survey_no))
        .first()
    )
    if max_survey:
        seq = int(max_survey.survey_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"SUR-{today}-{seq:03d}"


def generate_article_no(db: Session) -> str:
    """生成文章编号：KB-yymmdd-xxx"""
    from app.models.service import KnowledgeBase

    today = datetime.now().strftime("%y%m%d")
    max_article = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.article_no.like(f"KB-{today}-%"))
        .order_by(desc(KnowledgeBase.article_no))
        .first()
    )
    if max_article:
        seq = int(max_article.article_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"KB-{today}-{seq:03d}"
