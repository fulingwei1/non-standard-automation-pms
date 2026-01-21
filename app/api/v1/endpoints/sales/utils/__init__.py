# -*- coding: utf-8 -*-
"""
销售模块公共工具函数

统一导出所有工具函数
"""
from .code_generation import (
    generate_amendment_no,
    generate_contract_code,
    generate_invoice_code,
    generate_lead_code,
    generate_opportunity_code,
    generate_quote_code,
)
from .common import (
    build_department_name_map,
    calculate_growth,
    get_entity_creator_id,
    get_previous_range,
    get_user_role_code,
    get_user_role_name,
    get_visible_sales_users,
    generate_trend_buckets,
    normalize_date_range,
    shift_month,
)
from .gate_validation import (
    validate_g1_lead_to_opportunity,
    validate_g2_opportunity_to_quote,
    validate_g3_quote_to_contract,
    validate_g4_contract_to_project,
)

__all__ = [
    # 通用函数
    "get_entity_creator_id",
    "normalize_date_range",
    "get_user_role_code",
    "get_user_role_name",
    "get_visible_sales_users",
    "build_department_name_map",
    "shift_month",
    "generate_trend_buckets",
    "calculate_growth",
    "get_previous_range",
    # 阶段门验证函数
    "validate_g1_lead_to_opportunity",
    "validate_g2_opportunity_to_quote",
    "validate_g3_quote_to_contract",
    "validate_g4_contract_to_project",
    # 编码生成函数
    "generate_lead_code",
    "generate_opportunity_code",
    "generate_quote_code",
    "generate_contract_code",
    "generate_amendment_no",
    "generate_invoice_code",
]
