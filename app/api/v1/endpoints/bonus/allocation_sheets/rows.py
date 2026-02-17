# -*- coding: utf-8 -*-
"""
奖金分配明细表 - 行数据查看
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.bonus import BonusAllocationSheet
from app.models.user import User
from app.schemas.bonus import BonusAllocationRow
from app.schemas.common import ResponseModel
from app.utils.db_helpers import get_or_404, save_obj, delete_obj

from ..rules import paginate_items

router = APIRouter()


@router.get(
    "/allocation-sheets/{sheet_id}/rows",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK
)
def get_allocation_sheet_rows(
    *,
    db: Session = Depends(deps.get_db),
    sheet_id: int,
    row_type: str = Query("valid", description="数据类型：valid 或 error"),
    pagination: PaginationParams = Depends(get_pagination_query),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    查看已解析的分配明细表数据，支持分页查看有效行或错误行
    """
    sheet = get_or_404(db, BonusAllocationSheet, sheet_id, "分配明细表不存在")

    normalized_type = row_type.lower()
    if normalized_type not in {"valid", "error"}:
        raise HTTPException(status_code=400, detail="row_type 仅支持 valid 或 error")

    if normalized_type == "valid":
        valid_rows = []
        if sheet.parse_result and sheet.parse_result.get('valid_rows'):
            for row_data in sheet.parse_result['valid_rows']:
                distribution_date = row_data.get('distribution_date')
                if isinstance(distribution_date, str):
                    try:
                        distribution_date = date.fromisoformat(distribution_date)
                    except ValueError:
                        distribution_date = datetime.fromisoformat(distribution_date).date()
                elif isinstance(distribution_date, datetime):
                    distribution_date = distribution_date.date()
                elif not isinstance(distribution_date, date):
                    try:
                        distribution_date = datetime.fromisoformat(str(distribution_date)).date()
                    except ValueError:
                        distribution_date = datetime.strptime(str(distribution_date), '%Y-%m-%d').date()

                valid_rows.append(
                    BonusAllocationRow(
                        calculation_id=int(row_data['calculation_id']),
                        user_id=int(row_data['user_id']),
                        user_name=row_data.get('user_name'),
                        calculated_amount=Decimal(str(row_data['calculated_amount'])),
                        distributed_amount=Decimal(str(row_data['distributed_amount'])),
                        distribution_date=distribution_date,
                        payment_method=row_data.get('payment_method'),
                        voucher_no=row_data.get('voucher_no'),
                        payment_account=row_data.get('payment_account'),
                        payment_remark=row_data.get('payment_remark')
                    ).model_dump()
                )

        page_items, total, pages = paginate_items(valid_rows, pagination.page, pagination.page_size)
        data = {
            "sheet_id": sheet_id,
            "row_type": normalized_type,
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "pages": pages,
            "items": page_items
        }
    else:
        error_rows = []
        errors = sheet.parse_errors or {}
        for row_no, messages in errors.items():
            try:
                row_number = int(row_no)
            except (TypeError, ValueError):
                row_number = row_no
            if not isinstance(messages, list):
                messages = [str(messages)]
            error_rows.append({
                "row_number": row_number,
                "errors": [str(m) for m in messages]
            })

        error_rows.sort(key=lambda x: x["row_number"])
        page_items, total, pages = paginate_items(error_rows, pagination.page, pagination.page_size)
        data = {
            "sheet_id": sheet_id,
            "row_type": normalized_type,
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
            "pages": pages,
            "items": page_items
        }

    return ResponseModel(code=200, data=data)
