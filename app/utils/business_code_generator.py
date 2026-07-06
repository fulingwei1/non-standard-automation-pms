# -*- coding: utf-8 -*-
"""
业务编号统一生成器

集中处理“按日期前缀查询当前最大序号，再生成下一个编号”的逻辑，并在当前
进程内预约已生成序号，避免并发请求看到同一数据库快照时产生重复编号。
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Any, Callable, Optional, Type

from sqlalchemy.orm import Session

from app.common.query_filters import apply_like_filter as default_apply_like_filter

_reservation_lock = threading.Lock()
_reserved_sequences: dict[tuple[str, str, str], int] = {}


def reset_business_code_reservations() -> None:
    """清空本进程编号预约状态，供测试隔离使用。"""
    with _reservation_lock:
        _reserved_sequences.clear()


def _model_key(model_class: Type[Any]) -> str:
    return str(getattr(model_class, "__tablename__", None) or model_class.__name__)


def _build_prefix(
    *,
    prefix: str,
    now: datetime,
    date_format: str,
    date_separator: str,
    sequence_separator: str,
    use_date: bool,
) -> str:
    if not use_date:
        return f"{prefix}{sequence_separator}" if sequence_separator else prefix

    date_str = now.strftime(date_format)
    return f"{prefix}{date_separator}{date_str}{sequence_separator}"


def _extract_sequence(
    record: Any,
    field_name: str,
    *,
    sequence_separator: str,
    seq_length: int,
) -> int:
    try:
        value = str(getattr(record, field_name))
        if sequence_separator:
            seq_text = value.rsplit(sequence_separator, 1)[-1]
        else:
            seq_text = value[-seq_length:]
        return int(seq_text)
    except (AttributeError, TypeError, ValueError, IndexError):
        return 0


def _apply_like_filter_safely(
    query: Any,
    model_class: Type[Any],
    pattern: str,
    field_name: str,
    like_filter: Optional[Callable[..., Any]],
) -> Any:
    filter_func = like_filter or default_apply_like_filter
    try:
        return filter_func(
            query,
            model_class,
            pattern,
            field_name,
            use_ilike=False,
        )
    except Exception:
        return query


def generate_business_code(
    db: Session,
    model_class: Type[Any],
    field_name: str,
    *,
    prefix: str,
    now: Optional[datetime] = None,
    date_format: str = "%y%m%d",
    date_separator: str = "",
    sequence_separator: str = "-",
    seq_length: int = 3,
    use_date: bool = True,
    like_filter: Optional[Callable[..., Any]] = None,
) -> str:
    """
    生成业务编号。

    支持 `SO250101-001`、`INV-250101-001` 等格式；同一进程内对同一
    模型、字段、前缀加锁预约序号，避免并发请求重复返回同一个编号。
    """
    current_time = now or datetime.now()
    pattern_prefix = _build_prefix(
        prefix=prefix,
        now=current_time,
        date_format=date_format,
        date_separator=date_separator,
        sequence_separator=sequence_separator,
        use_date=use_date,
    )
    reservation_key = (_model_key(model_class), field_name, pattern_prefix)

    with _reservation_lock:
        query = db.query(model_class)
        query = _apply_like_filter_safely(
            query,
            model_class,
            f"{pattern_prefix}%",
            field_name,
            like_filter,
        )
        latest = query.order_by(getattr(model_class, field_name).desc()).first()

        latest_sequence = _extract_sequence(
            latest,
            field_name,
            sequence_separator=sequence_separator,
            seq_length=seq_length,
        ) if latest else 0
        reserved_sequence = _reserved_sequences.get(reservation_key, 0)
        next_sequence = max(latest_sequence, reserved_sequence) + 1
        _reserved_sequences[reservation_key] = next_sequence

    return f"{pattern_prefix}{next_sequence:0{seq_length}d}"
