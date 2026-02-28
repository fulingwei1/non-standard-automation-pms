# -*- coding: utf-8 -*-
"""供应商价格趋势分析 API."""

import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _safe_identifier(identifier: str) -> str:
    if not _IDENTIFIER_RE.match(identifier):
        raise HTTPException(status_code=500, detail=f"Invalid SQL identifier: {identifier}")
    return identifier


def _get_table_columns(db: Session, table_name: str) -> set[str]:
    table = _safe_identifier(table_name)
    rows = db.execute(text(f"PRAGMA table_info({table})")).fetchall()
    columns: set[str] = set()
    for row in rows:
        mapping = row._mapping
        name = mapping.get("name", row[1] if len(row) > 1 else None)
        if name:
            columns.add(str(name))
    return columns


def _pick_column(columns: set[str], candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def _resolve_query_schema(db: Session) -> dict[str, str]:
    # 按需求先检查 purchase_orders 与 suppliers 的实际字段
    po_columns = _get_table_columns(db, "purchase_orders")
    supplier_columns = _get_table_columns(db, "suppliers")
    supplier_table = "suppliers"

    if not po_columns:
        raise HTTPException(status_code=500, detail="Table purchase_orders not found")

    # 当前系统已逐步迁移到 vendors，兼容旧 suppliers 表
    if not supplier_columns:
        supplier_table = "vendors"
        supplier_columns = _get_table_columns(db, supplier_table)

    if not supplier_columns:
        raise HTTPException(status_code=500, detail="Table suppliers/vendors not found")

    amount_column = _pick_column(
        po_columns, ["total_amount", "amount_with_tax", "tax_amount", "paid_amount"]
    )
    date_column = _pick_column(po_columns, ["order_date", "created_at", "updated_at"])
    supplier_id_column = _pick_column(supplier_columns, ["id", "supplier_id"])
    supplier_name_column = _pick_column(
        supplier_columns, ["supplier_name", "name", "supplier_short_name", "code"]
    )

    if not amount_column:
        raise HTTPException(
            status_code=500,
            detail="No amount column found in purchase_orders",
        )
    if not date_column:
        raise HTTPException(
            status_code=500,
            detail="No date column found in purchase_orders",
        )
    if not supplier_id_column:
        raise HTTPException(
            status_code=500,
            detail="No supplier id column found in suppliers/vendors",
        )
    if not supplier_name_column:
        raise HTTPException(
            status_code=500,
            detail="No supplier name column found in suppliers/vendors",
        )

    return {
        "supplier_table": _safe_identifier(supplier_table),
        "amount_column": _safe_identifier(amount_column),
        "date_column": _safe_identifier(date_column),
        "supplier_id_column": _safe_identifier(supplier_id_column),
        "supplier_name_column": _safe_identifier(supplier_name_column),
        "vendor_filter_clause": (
            " AND s.vendor_type = 'MATERIAL'"
            if supplier_table == "vendors" and "vendor_type" in supplier_columns
            else ""
        ),
    }


@router.get("/trends", response_model=ResponseModel)
def get_supplier_price_trends(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("purchase:read")),
) -> Any:
    """供应商价格趋势：按供应商+月份聚合采购金额."""
    schema = _resolve_query_schema(db)
    amount_expr = f"CAST(COALESCE(po.{schema['amount_column']}, 0) AS REAL)"
    sql = text(
        f"""
        SELECT
            po.supplier_id AS supplier_id,
            COALESCE(s.{schema['supplier_name_column']}, '供应商#' || po.supplier_id) AS supplier_name,
            strftime('%Y-%m', po.{schema['date_column']}) AS period,
            ROUND(SUM({amount_expr}), 2) AS total_amount,
            COUNT(*) AS order_count
        FROM purchase_orders po
        LEFT JOIN {schema['supplier_table']} s
            ON po.supplier_id = s.{schema['supplier_id_column']}
            {schema['vendor_filter_clause']}
        WHERE po.supplier_id IS NOT NULL
          AND po.{schema['date_column']} IS NOT NULL
          AND strftime('%Y-%m', po.{schema['date_column']}) IS NOT NULL
        GROUP BY po.supplier_id, supplier_name, period
        ORDER BY period ASC, total_amount DESC
        """
    )

    rows = db.execute(sql).fetchall()
    points: list[dict[str, Any]] = []
    supplier_map: dict[int, dict[str, Any]] = {}
    periods: set[str] = set()

    for row in rows:
        payload = row._mapping
        supplier_id = int(payload["supplier_id"])
        period = payload["period"]
        amount = float(payload["total_amount"] or 0)
        order_count = int(payload["order_count"] or 0)
        periods.add(period)

        point = {
            "supplier_id": supplier_id,
            "supplier_name": payload["supplier_name"],
            "period": period,
            "total_amount": amount,
            "order_count": order_count,
        }
        points.append(point)

        if supplier_id not in supplier_map:
            supplier_map[supplier_id] = {
                "supplier_id": supplier_id,
                "supplier_name": payload["supplier_name"],
                "total_amount": 0.0,
                "total_orders": 0,
                "trend": [],
            }
        supplier_map[supplier_id]["trend"].append(
            {
                "period": period,
                "total_amount": amount,
                "order_count": order_count,
            }
        )
        supplier_map[supplier_id]["total_amount"] += amount
        supplier_map[supplier_id]["total_orders"] += order_count

    series = sorted(
        supplier_map.values(),
        key=lambda item: item["total_amount"],
        reverse=True,
    )

    return ResponseModel(
        code=200,
        message="success",
        data={
            "periods": sorted(periods),
            "series": series,
            "points": points,
        },
    )


@router.get("/comparison", response_model=ResponseModel)
def get_supplier_price_comparison(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("purchase:read")),
) -> Any:
    """供应商价格对比：每个供应商的平均订单金额."""
    schema = _resolve_query_schema(db)
    amount_expr = f"CAST(COALESCE(po.{schema['amount_column']}, 0) AS REAL)"
    sql = text(
        f"""
        SELECT
            po.supplier_id AS supplier_id,
            COALESCE(s.{schema['supplier_name_column']}, '供应商#' || po.supplier_id) AS supplier_name,
            ROUND(AVG({amount_expr}), 2) AS avg_order_amount,
            ROUND(SUM({amount_expr}), 2) AS total_amount,
            COUNT(*) AS order_count,
            ROUND(MIN({amount_expr}), 2) AS min_order_amount,
            ROUND(MAX({amount_expr}), 2) AS max_order_amount
        FROM purchase_orders po
        LEFT JOIN {schema['supplier_table']} s
            ON po.supplier_id = s.{schema['supplier_id_column']}
            {schema['vendor_filter_clause']}
        WHERE po.supplier_id IS NOT NULL
        GROUP BY po.supplier_id, supplier_name
        ORDER BY avg_order_amount DESC
        """
    )

    rows = db.execute(sql).fetchall()
    data = [
        {
            "supplier_id": int(row.supplier_id),
            "supplier_name": row.supplier_name,
            "avg_order_amount": float(row.avg_order_amount or 0),
            "total_amount": float(row.total_amount or 0),
            "order_count": int(row.order_count or 0),
            "min_order_amount": float(row.min_order_amount or 0),
            "max_order_amount": float(row.max_order_amount or 0),
        }
        for row in rows
    ]

    return ResponseModel(code=200, message="success", data=data)


@router.get("/volatility", response_model=ResponseModel)
def get_supplier_price_volatility(
    *,
    db: Session = Depends(deps.get_db),
    limit: int = Query(10, ge=1, le=100, description="返回记录数"),
    current_user: User = Depends(security.require_permission("purchase:read")),
) -> Any:
    """供应商价格波动：按订单金额标准差降序返回."""
    schema = _resolve_query_schema(db)
    amount_expr = f"CAST(COALESCE(po.{schema['amount_column']}, 0) AS REAL)"
    variance_expr = (
        f"(AVG(({amount_expr}) * ({amount_expr})) - AVG({amount_expr}) * AVG({amount_expr}))"
    )
    stddev_expr = (
        f"ROUND(SQRT(CASE WHEN {variance_expr} > 0 THEN {variance_expr} ELSE 0 END), 2)"
    )

    sql = text(
        f"""
        SELECT
            po.supplier_id AS supplier_id,
            COALESCE(s.{schema['supplier_name_column']}, '供应商#' || po.supplier_id) AS supplier_name,
            COUNT(*) AS order_count,
            ROUND(AVG({amount_expr}), 2) AS avg_order_amount,
            {stddev_expr} AS stddev_amount,
            ROUND(MAX({amount_expr}) - MIN({amount_expr}), 2) AS range_amount
        FROM purchase_orders po
        LEFT JOIN {schema['supplier_table']} s
            ON po.supplier_id = s.{schema['supplier_id_column']}
            {schema['vendor_filter_clause']}
        WHERE po.supplier_id IS NOT NULL
        GROUP BY po.supplier_id, supplier_name
        HAVING COUNT(*) >= 2
        ORDER BY stddev_amount DESC
        LIMIT :limit
        """
    )

    rows = db.execute(sql, {"limit": limit}).fetchall()
    data = [
        {
            "supplier_id": int(row.supplier_id),
            "supplier_name": row.supplier_name,
            "order_count": int(row.order_count or 0),
            "avg_order_amount": float(row.avg_order_amount or 0),
            "stddev_amount": float(row.stddev_amount or 0),
            "range_amount": float(row.range_amount or 0),
        }
        for row in rows
    ]

    return ResponseModel(code=200, message="success", data=data)
