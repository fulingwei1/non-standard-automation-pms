# -*- coding: utf-8 -*-
"""
统一响应格式和验证器
"""

from app.core.schemas.response import (
    BaseResponse,
    ErrorResponse,
    ListResponse,
    PaginatedResponse,
    SuccessResponse,
    error_response,
    list_response,
    paginated_response,
    success_response,
)
from app.core.schemas.validators import (
    validate_bank_card,
    validate_date_range,
    validate_email,
    validate_id_card,
    validate_non_empty_string,
    validate_phone,
    validate_positive_number,
    validate_project_code,
)

__all__ = [
    # 响应格式
    "BaseResponse",
    "SuccessResponse",
    "ErrorResponse",
    "PaginatedResponse",
    "ListResponse",
    # 响应辅助函数
    "success_response",
    "error_response",
    "paginated_response",
    "list_response",
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
