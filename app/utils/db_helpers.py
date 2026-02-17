# -*- coding: utf-8 -*-
"""
数据库操作辅助函数

消除重复的 CRUD 模板代码，统一错误处理。

使用示例：

    # 替代：
    #   obj = db.query(Model).filter(Model.id == id).first()
    #   if not obj: raise HTTPException(status_code=404, detail="...")
    obj = get_or_404(db, Model, id)

    # 替代：
    #   db.add(obj); db.commit(); db.refresh(obj)
    save_obj(db, obj)

    # 替代：
    #   db.delete(obj); db.commit()
    delete_obj(db, obj)
"""

from typing import Any, Optional, Type, TypeVar
from fastapi import HTTPException
from sqlalchemy.orm import Session

T = TypeVar("T")


def get_or_404(
    db: Session,
    model: Type[T],
    obj_id: Any,
    detail: Optional[str] = None,
    id_field: str = "id",
) -> T:
    """
    查询对象，不存在则抛出 404。

    Args:
        db: 数据库会话
        model: SQLAlchemy 模型类
        obj_id: 对象 ID
        detail: 404 错误消息（默认为 "{ModelName} not found"）
        id_field: ID 字段名（默认 "id"）

    Returns:
        找到的对象

    Raises:
        HTTPException(404): 对象不存在时
    """
    field = getattr(model, id_field)
    obj = db.query(model).filter(field == obj_id).first()
    if obj is None:
        raise HTTPException(
            status_code=404,
            detail=detail or f"{model.__name__} with {id_field}={obj_id} not found",
        )
    return obj


def save_obj(db: Session, obj: T, refresh: bool = True) -> T:
    """
    保存对象到数据库（add + commit + refresh）。

    Args:
        db: 数据库会话
        obj: 要保存的对象
        refresh: 是否在 commit 后 refresh（默认 True）

    Returns:
        保存后的对象
    """
    db.add(obj)
    db.commit()
    if refresh:
        db.refresh(obj)
    return obj


def delete_obj(db: Session, obj: Any) -> None:
    """
    从数据库删除对象（delete + commit）。

    Args:
        db: 数据库会话
        obj: 要删除的对象
    """
    db.delete(obj)
    db.commit()


def update_obj(db: Session, obj: T, data: dict, refresh: bool = True) -> T:
    """
    批量更新对象字段并保存。

    Args:
        db: 数据库会话
        obj: 要更新的对象
        data: 字段更新字典
        refresh: 是否刷新（默认 True）

    Returns:
        更新后的对象
    """
    for field, value in data.items():
        if hasattr(obj, field):
            setattr(obj, field, value)
    return save_obj(db, obj, refresh=refresh)


def safe_commit(db: Session) -> bool:
    """
    安全提交，失败时自动回滚。

    Returns:
        True 表示成功，False 表示失败并已回滚
    """
    try:
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False
