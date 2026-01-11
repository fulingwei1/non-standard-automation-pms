# -*- coding: utf-8 -*-
"""
生产管理模块 - 公共工具函数

包含：编号生成、通用查询等工具函数
"""
from sqlalchemy.orm import Session


def generate_plan_no(db: Session) -> str:
    """生成生产计划编号：PP-yymmdd-xxx"""
    from app.utils.number_generator import generate_sequential_no
    from app.models.production import ProductionPlan

    return generate_sequential_no(
        db=db,
        model_class=ProductionPlan,
        no_field='plan_no',
        prefix='PP',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )


def generate_work_order_no(db: Session) -> str:
    """生成工单编号：WO-yymmdd-xxx"""
    from app.utils.number_generator import generate_sequential_no
    from app.models.production import WorkOrder

    return generate_sequential_no(
        db=db,
        model_class=WorkOrder,
        no_field='work_order_no',
        prefix='WO',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )


def generate_report_no(db: Session) -> str:
    """生成报工单号：WR-yymmdd-xxx"""
    from app.utils.number_generator import generate_sequential_no
    from app.models.production import WorkReport

    return generate_sequential_no(
        db=db,
        model_class=WorkReport,
        no_field='report_no',
        prefix='WR',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )
