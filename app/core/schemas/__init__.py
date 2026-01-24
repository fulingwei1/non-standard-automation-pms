# -*- coding: utf-8 -*-
"""
统一响应格式和验证器
"""

from app.core.schemas.response import (
    BaseResponse,
    SuccessResponse,
    ErrorResponse,
    PaginatedResponse,
    ListResponse,
)
from app.core.schemas.validators import (
    validate_project_code,
    validate_phone,
    validate_email,
    validate_id_card,
    validate_bank_card,
    validate_date_range,
    validate_positive_number,
    validate_non_empty_string,
)

__all__ = [
    # 响应格式
    "BaseResponse",
    "SuccessResponse",
    "ErrorResponse",
    "PaginatedResponse",
    "ListResponse",
    # 验证器
    "validate_project_code",
    "validate_phone",
    "validate_email",
    "validate_id_card",
    "validate_bank_card",
    "validate_date_range",
    "validate_positive_number",
    "validate_non_empty_string",
]
