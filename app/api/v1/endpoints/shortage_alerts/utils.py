# -*- coding: utf-8 -*-
"""
缺料告警模块公共工具函数

用于在拆分后的 endpoints 之间复用编号生成逻辑。
"""

from sqlalchemy.orm import Session


def generate_shortage_report_no(db: Session) -> str:
    """生成缺料上报单号：SR-yymmdd-xxx"""
    from app.models.shortage import ShortageReport
    from app.utils.number_generator import generate_sequential_no

    return generate_sequential_no(
        db=db,
        model_class=ShortageReport,
        no_field="report_no",
        prefix="SR",
        date_format="%y%m%d",
        separator="-",
        seq_length=3,
    )


def generate_arrival_no(db: Session) -> str:
    """生成到货跟踪单号：ARR-yymmdd-xxx"""
    from app.models.shortage import MaterialArrival
    from app.utils.number_generator import generate_sequential_no

    return generate_sequential_no(
        db=db,
        model_class=MaterialArrival,
        no_field="arrival_no",
        prefix="ARR",
        date_format="%y%m%d",
        separator="-",
        seq_length=3,
    )


def generate_substitution_no(db: Session) -> str:
    """生成替代单号：SUB-yymmdd-xxx"""
    from app.models.shortage import MaterialSubstitution
    from app.utils.number_generator import generate_sequential_no

    return generate_sequential_no(
        db=db,
        model_class=MaterialSubstitution,
        no_field="substitution_no",
        prefix="SUB",
        date_format="%y%m%d",
        separator="-",
        seq_length=3,
    )


def generate_transfer_no(db: Session) -> str:
    """生成调拨单号：TRF-yymmdd-xxx"""
    from app.models.shortage import MaterialTransfer
    from app.utils.number_generator import generate_sequential_no

    return generate_sequential_no(
        db=db,
        model_class=MaterialTransfer,
        no_field="transfer_no",
        prefix="TRF",
        date_format="%y%m%d",
        separator="-",
        seq_length=3,
    )

