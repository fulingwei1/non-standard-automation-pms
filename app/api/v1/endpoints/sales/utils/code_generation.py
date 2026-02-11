# -*- coding: utf-8 -*-
"""
销售模块公共工具函数 - 编码生成函数
"""
from sqlalchemy.orm import Session

from app.common.query_filters import apply_like_filter
from app.models.sales import (
    Contract,
    ContractAmendment,
    Invoice,
    Lead,
    Opportunity,
    Quote,
)


def generate_lead_code(db: Session) -> str:
    """生成线索编码：L2507-001"""
    from app.utils.number_generator import generate_monthly_no

    return generate_monthly_no(
        db=db,
        model_class=Lead,
        no_field='lead_code',
        prefix='L',
        separator='-',
        seq_length=3
    )


def generate_opportunity_code(db: Session) -> str:
    """生成商机编码：O2507-001"""
    from app.utils.number_generator import generate_monthly_no

    return generate_monthly_no(
        db=db,
        model_class=Opportunity,
        no_field='opp_code',
        prefix='O',
        separator='-',
        seq_length=3
    )


def generate_quote_code(db: Session) -> str:
    """生成报价编码：Q2507-001"""
    from app.utils.number_generator import generate_monthly_no

    return generate_monthly_no(
        db=db,
        model_class=Quote,
        no_field='quote_code',
        prefix='Q',
        separator='-',
        seq_length=3
    )


def generate_contract_code(db: Session) -> str:
    """生成合同编码：HT2507-001"""
    from app.utils.number_generator import generate_monthly_no

    return generate_monthly_no(
        db=db,
        model_class=Contract,
        no_field='contract_code',
        prefix='HT',
        separator='-',
        seq_length=3
    )


def generate_amendment_no(db: Session, contract_code: str) -> str:
    """生成合同变更编号：{合同编码}-BG{序号}"""
    prefix = f"{contract_code}-BG"
    count_query = db.query(ContractAmendment)
    count_query = apply_like_filter(
        count_query,
        ContractAmendment,
        f"{prefix}%",
        "amendment_no",
        use_ilike=False,
    )
    count = count_query.count()
    seq = count + 1
    return f"{prefix}{seq:03d}"


def generate_invoice_code(db: Session) -> str:
    """生成发票编码：INV-yymmdd-xxx"""
    from app.utils.number_generator import generate_sequential_no

    return generate_sequential_no(
        db=db,
        model_class=Invoice,
        no_field='invoice_code',
        prefix='INV',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )
