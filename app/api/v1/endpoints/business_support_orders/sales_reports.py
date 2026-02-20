# -*- coding: utf-8 -*-
"""
商务支持模块 - 销售报表 API endpoints（日报、周报、月报）
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.business_support import SalesReportResponse
from app.schemas.common import ResponseModel
from app.services.business_support_reports import BusinessSupportReportsService

router = APIRouter()


@router.get(
    "/reports/sales-daily",
    response_model=ResponseModel[SalesReportResponse],
    summary="获取销售日报",
)
async def get_sales_daily_report(
    report_date: Optional[str] = Query(
        None, description="报表日期（YYYY-MM-DD格式），不提供则使用今天"
    ),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """获取销售日报"""
    try:
        # 验证日期格式
        if report_date:
            try:
                from datetime import datetime

                datetime.strptime(report_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="日期格式错误，应为YYYY-MM-DD"
                )

        # 调用服务层
        service = BusinessSupportReportsService(db)
        data = service.get_daily_report(report_date)

        return ResponseModel(
            code=200,
            message="获取销售日报成功",
            data=SalesReportResponse(**data),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取销售日报失败: {str(e)}")


@router.get(
    "/reports/sales-weekly",
    response_model=ResponseModel[SalesReportResponse],
    summary="获取销售周报",
)
async def get_sales_weekly_report(
    week: Optional[str] = Query(
        None, description="周（YYYY-WW格式），不提供则使用当前周"
    ),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """获取销售周报"""
    try:
        # 验证周格式
        if week:
            try:
                parts = week.split("-W")
                if len(parts) != 2:
                    raise ValueError
                int(parts[0])
                int(parts[1])
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail="周格式错误，应为YYYY-WW")

        # 调用服务层
        service = BusinessSupportReportsService(db)
        data = service.get_weekly_report(week)

        return ResponseModel(
            code=200,
            message="获取销售周报成功",
            data=SalesReportResponse(**data),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取销售周报失败: {str(e)}")


@router.get(
    "/reports/sales-monthly",
    response_model=ResponseModel[SalesReportResponse],
    summary="获取销售月报",
)
async def get_sales_monthly_report(
    month: Optional[str] = Query(
        None, description="月份（YYYY-MM格式），不提供则使用当前月份"
    ),
    format: str = Query("json", description="格式：json/pdf/excel"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """获取销售月报（使用统一报表框架）"""
    from app.services.report_framework import ConfigError
    from app.services.report_framework.engine import (
        ParameterError,
        PermissionError,
        ReportEngine,
    )

    try:
        engine = ReportEngine(db)
        result = engine.generate(
            report_code="SALES_MONTHLY",
            params={
                "month": month,
            },
            format=format,
            user=current_user,
            skip_cache=False,
        )

        if format == "excel":
            month_str = month or f"{date.today().year}-{date.today().month:02d}"
            filename = f"销售月报_{month_str}.xlsx"
            return StreamingResponse(
                result.data.get("file_stream"),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        elif format == "pdf":
            month_str = month or f"{date.today().year}-{date.today().month:02d}"
            filename = f"销售月报_{month_str}.pdf"
            return StreamingResponse(
                result.data.get("file_stream"),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        else:
            # JSON格式，转换为SalesReportResponse格式以保持向后兼容
            sales_data = result.data.get("sales_data", {})
            contract_stats = sales_data.get("contract_statistics", {})
            order_stats = sales_data.get("order_statistics", {})
            receipt_stats = sales_data.get("receipt_statistics", {})
            invoice_stats = sales_data.get("invoice_statistics", {})
            bidding_stats = sales_data.get("bidding_statistics", {})

            return ResponseModel(
                code=200,
                message="获取销售月报成功",
                data=SalesReportResponse(
                    report_date=sales_data.get("report_date", ""),
                    report_type="monthly",
                    new_contracts_count=contract_stats.get("new_contracts_count", 0),
                    new_contracts_amount=contract_stats.get("new_contracts_amount", 0),
                    active_contracts_count=contract_stats.get("active_contracts", 0),
                    completed_contracts_count=contract_stats.get(
                        "completed_contracts", 0
                    ),
                    new_orders_count=order_stats.get("new_orders_count", 0),
                    new_orders_amount=order_stats.get("new_orders_amount", 0),
                    planned_receipt_amount=receipt_stats.get(
                        "planned_receipt_amount", 0
                    ),
                    actual_receipt_amount=receipt_stats.get("actual_receipt_amount", 0),
                    receipt_completion_rate=receipt_stats.get(
                        "receipt_completion_rate", 0
                    ),
                    overdue_amount=receipt_stats.get("overdue_amount", 0),
                    invoices_count=invoice_stats.get("invoices_count", 0),
                    invoices_amount=invoice_stats.get("invoices_amount", 0),
                    invoice_rate=invoice_stats.get("invoice_rate", 0),
                    new_bidding_count=bidding_stats.get("new_bidding", 0),
                    won_bidding_count=bidding_stats.get("won_bidding", 0),
                    bidding_win_rate=bidding_stats.get("bidding_win_rate", 0),
                ),
            )
    except ConfigError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ParameterError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取销售月报失败: {str(e)}")
