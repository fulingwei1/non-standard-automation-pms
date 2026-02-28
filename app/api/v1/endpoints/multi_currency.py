# -*- coding: utf-8 -*-
"""
多币种支持 API
- 汇率管理（获取、更新、历史记录）
- 汇率转换
- 项目多币种汇总
"""

import sqlite3
from datetime import datetime, date
from typing import Any, List, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field

from app.api import deps
from app.models.user import User

router = APIRouter()

# ============================================================================
# Configuration
# ============================================================================

DB_PATH = Path(__file__).parent.parent.parent.parent.parent / "data" / "app.db"

SUPPORTED_CURRENCIES = ["CNY", "USD", "EUR", "JPY", "GBP", "KRW", "TWD"]

DEFAULT_RATES = {
    "USD": 7.24,
    "EUR": 7.85,
    "JPY": 0.048,
    "GBP": 9.15,
    "KRW": 0.0053,
    "TWD": 0.22,
    "CNY": 1.0,
}

# ============================================================================
# Database Initialization (Lazy)
# ============================================================================

def init_tables():
    """Lazy init: 创建汇率相关表（如果不存在）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 汇率表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS currency_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            currency TEXT NOT NULL UNIQUE,
            rate REAL NOT NULL,
            updated_at TEXT NOT NULL,
            updated_by TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    # 汇率历史表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS currency_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            currency TEXT NOT NULL,
            rate REAL NOT NULL,
            recorded_at TEXT NOT NULL,
            note TEXT
        )
    """)
    
    # 初始化默认汇率
    now = datetime.now().isoformat()
    for currency, rate in DEFAULT_RATES.items():
        cursor.execute("""
            INSERT OR IGNORE INTO currency_rates (currency, rate, updated_at)
            VALUES (?, ?, ?)
        """, (currency, rate, now))
    
    conn.commit()
    conn.close()


def get_db_connection():
    """获取数据库连接"""
    init_tables()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============================================================================
# Schemas
# ============================================================================

class CurrencyRate(BaseModel):
    currency: str
    rate: float
    updated_at: Optional[str] = None
    change_24h: Optional[float] = None  # 24 小时涨跌幅 %


class RateUpdateInput(BaseModel):
    currency: str
    rate: float
    note: Optional[str] = None


class ConvertRequest(BaseModel):
    from_currency: str
    to_currency: str
    amount: float


class ConvertResponse(BaseModel):
    from_currency: str
    to_currency: str
    amount: float
    converted_amount: float
    rate: float
    rate_date: str


class HistoryRecord(BaseModel):
    currency: str
    rate: float
    recorded_at: str
    note: Optional[str] = None


class ProjectCurrencySummary(BaseModel):
    project_id: int
    project_name: str
    project_code: str
    original_currency: str
    original_amount: float
    rate_to_cny: float
    amount_cny: float
    fx_gain_loss: Optional[float] = None  # 汇兑损益


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/rates", summary="获取汇率列表")
def get_currency_rates(
    db: User = Depends(deps.get_current_active_user),
) -> List[CurrencyRate]:
    """
    获取所有支持币种的当前汇率
    - 返回 CNY/USD/EUR/JPY/GBP/KRW/TWD 的汇率
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT currency, rate, updated_at
        FROM currency_rates
        WHERE is_active = 1
        ORDER BY currency
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    rates = []
    for row in rows:
        rates.append(CurrencyRate(
            currency=row["currency"],
            rate=row["rate"],
            updated_at=row["updated_at"],
            change_24h=0.0  # 预留字段，后续可计算实际涨跌
        ))
    
    return rates


@router.post("/rates", summary="更新汇率")
def update_currency_rate(
    input: RateUpdateInput,
    current_user: User = Depends(deps.get_current_active_user),
) -> dict:
    """
    手动更新某个币种的汇率
    - 同时记录到历史表
    """
    if input.currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的币种：{input.currency}。支持的币种：{', '.join(SUPPORTED_CURRENCIES)}"
        )
    
    if input.rate <= 0:
        raise HTTPException(status_code=400, detail="汇率必须大于 0")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # 获取旧汇率（用于历史记录）
    cursor.execute("SELECT rate FROM currency_rates WHERE currency = ?", (input.currency,))
    old_row = cursor.fetchone()
    old_rate = old_row["rate"] if old_row else None
    
    # 更新汇率表
    cursor.execute("""
        UPDATE currency_rates
        SET rate = ?, updated_at = ?, updated_by = ?
        WHERE currency = ?
    """, (input.rate, now, current_user.username, input.currency))
    
    # 如果之前没有该币种，插入新记录
    if cursor.rowcount == 0:
        cursor.execute("""
            INSERT INTO currency_rates (currency, rate, updated_at, updated_by)
            VALUES (?, ?, ?, ?)
        """, (input.currency, input.rate, now, current_user.username))
    
    # 记录到历史表
    note = input.note or f"手动更新 by {current_user.username}"
    cursor.execute("""
        INSERT INTO currency_history (currency, rate, recorded_at, note)
        VALUES (?, ?, ?, ?)
    """, (input.currency, input.rate, now, note))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "currency": input.currency,
        "old_rate": old_rate,
        "new_rate": input.rate,
        "updated_at": now
    }


@router.get("/convert", summary="汇率转换")
def convert_currency(
    from_currency: str = Query(..., description="源币种"),
    to_currency: str = Query(..., description="目标币种"),
    amount: float = Query(..., description="金额"),
    current_user: User = Depends(deps.get_current_active_user),
) -> ConvertResponse:
    """
    汇率转换
    - 支持任意两个币种之间的转换
    - 通过 CNY 作为中间货币进行换算
    """
    if from_currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(status_code=400, detail=f"不支持的币种：{from_currency}")
    if to_currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(status_code=400, detail=f"不支持的币种：{to_currency}")
    if amount < 0:
        raise HTTPException(status_code=400, detail="金额不能为负数")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取两个币种的汇率
    cursor.execute("SELECT rate FROM currency_rates WHERE currency = ?", (from_currency,))
    from_row = cursor.fetchone()
    cursor.execute("SELECT rate FROM currency_rates WHERE currency = ?", (to_currency,))
    to_row = cursor.fetchone()
    conn.close()
    
    if not from_row or not to_row:
        raise HTTPException(status_code=404, detail="汇率数据不存在")
    
    from_rate = from_row["rate"]
    to_rate = to_row["rate"]
    
    # 通过 CNY 作为中间货币：from -> CNY -> to
    # amount_in_cny = amount * from_rate
    # converted = amount_in_cny / to_rate
    if from_currency == "CNY":
        rate = 1.0 / to_rate
    elif to_currency == "CNY":
        rate = from_rate
    else:
        rate = from_rate / to_rate
    
    converted_amount = amount * rate
    
    return ConvertResponse(
        from_currency=from_currency,
        to_currency=to_currency,
        amount=amount,
        converted_amount=round(converted_amount, 2),
        rate=round(rate, 6),
        rate_date=datetime.now().isoformat()
    )


@router.get("/history", summary="汇率历史记录")
def get_currency_history(
    currency: Optional[str] = Query(None, description="币种，不传则返回所有"),
    limit: int = Query(50, ge=1, le=500, description="返回记录数"),
    current_user: User = Depends(deps.get_current_active_user),
) -> List[HistoryRecord]:
    """
    获取汇率历史记录
    - 可按币种筛选
    - 默认返回最近 50 条记录
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if currency:
        if currency not in SUPPORTED_CURRENCIES:
            raise HTTPException(status_code=400, detail=f"不支持的币种：{currency}")
        cursor.execute("""
            SELECT currency, rate, recorded_at, note
            FROM currency_history
            WHERE currency = ?
            ORDER BY recorded_at DESC
            LIMIT ?
        """, (currency, limit))
    else:
        cursor.execute("""
            SELECT currency, rate, recorded_at, note
            FROM currency_history
            ORDER BY recorded_at DESC
            LIMIT ?
        """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        HistoryRecord(
            currency=row["currency"],
            rate=row["rate"],
            recorded_at=row["recorded_at"],
            note=row["note"]
        )
        for row in rows
    ]


@router.get("/project-summary/{project_id}", summary="项目多币种汇总")
def get_project_currency_summary(
    project_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> List[ProjectCurrencySummary]:
    """
    获取项目的多币种汇总
    - 原币金额、折合人民币、汇兑损益
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取项目基本信息
    cursor.execute("""
        SELECT id, project_name, project_code, currency as original_currency,
               contract_amount as original_amount
        FROM projects
        WHERE id = ? AND is_active = 1
    """, (project_id,))
    project = cursor.fetchone()
    
    if not project:
        conn.close()
        raise HTTPException(status_code=404, detail="项目不存在")
    
    original_currency = project["original_currency"] or "CNY"
    original_amount = project["original_amount"] or 0
    
    # 获取当前汇率
    cursor.execute("SELECT rate FROM currency_rates WHERE currency = ?", (original_currency,))
    rate_row = cursor.fetchone()
    conn.close()
    
    rate_to_cny = rate_row["rate"] if rate_row else 1.0
    amount_cny = original_amount * rate_to_cny
    
    # 汇兑损益 = 当前折算 - 原始折算（简化计算，实际应基于历史汇率）
    # 这里简化为 0，实际业务中需要记录签约时的汇率
    fx_gain_loss = None
    
    return [
        ProjectCurrencySummary(
            project_id=project["id"],
            project_name=project["project_name"],
            project_code=project["project_code"],
            original_currency=original_currency,
            original_amount=original_amount,
            rate_to_cny=rate_to_cny,
            amount_cny=round(amount_cny, 2),
            fx_gain_loss=fx_gain_loss
        )
    ]
