# -*- coding: utf-8 -*-
"""
通用CRUD基类

提供基础的CRUD操作，消除35处CRUD重复。
"""

from typing import Any, Dict, Generic, List, Optional, Type, Union
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import inspect

T = TypeVar("T")


class CRUDBase(Generic[T]):
    """
    通用CRUD基类

    提供基本的增删改查操作，所有ORM模型都可以继承此类。
    """

    def __init__(self, model: Type[T]):
        """
        初始化CRUD基类

        Args:
            model: ORM模型类
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[T]:
        """
        根据ID获取单条记录

        Args:
            db: 数据库会话
            id: 记录ID

        Returns:
            模型实例或None
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[T]:
        """
        获取多条记录（分页）

        Args:
            db: 数据库会话
            skip: 跳过记录数
            limit: 返回记录数

        Returns:
            模型实例列表
        """
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: Dict[str, Any]) -> T:
        """
        创建新记录

        Args:
            db: 数据库会话
            obj_in: 创建数据的字典

        Returns:
            创建后的模型实例
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: T, obj_in: Union[Dict[str, Any], T]) -> T:
        """
        更新记录

        Args:
            db: 数据库会话
            db_obj: 要更新的数据库对象
            obj_in: 更新数据的字典或模型实例

        Returns:
            更新后的模型实例
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = {
                column.key: getattr(obj_in, column.key)
                for column in inspect(obj_in).mapper.column_attrs
            }

        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, id: int) -> T:
        """
        删除记录

        Args:
            db: 数据库会话
            id: 记录ID

        Returns:
            被删除的模型实例
        """
        obj = self.get(db, id=id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def get_by_field(
        self, db: Session, *, field_name: str, field_value: Any
    ) -> Optional[T]:
        """
        根据指定字段值获取记录

        Args:
            db: 数据库会话
            field_name: 字段名
            field_value: 字段值

        Returns:
            模型实例或None
        """
        if not hasattr(self.model, field_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"模型 {self.model.__name__} 不存在字段 {field_name}",
            )

        field = getattr(self.model, field_name)
        return db.query(self.model).filter(field == field_value).first()

    def exists(self, db: Session, *, id: int) -> bool:
        """
        检查记录是否存在

        Args:
            db: 数据库会话
            id: 记录ID

        Returns:
            是否存在
        """
        return self.get(db, id=id) is not None

    def count(self, db: Session) -> int:
        """
        统计记录总数

        Args:
            db: 数据库会话

        Returns:
            总记录数
        """
        return db.query(self.model).count()

    def get_or_404(self, db: Session, *, id: int) -> T:
        """
        根据ID获取记录，不存在则抛出404异常

        Args:
            db: 数据库会话
            id: 记录ID

        Returns:
            模型实例

        Raises:
            HTTPException: 记录不存在
        """
        obj = self.get(db, id=id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} (id={id}) 不存在",
            )
        return obj


def jsonable_encoder(obj: Any) -> Dict[str, Any]:
    """
    将对象转换为可序列化的字典

    处理datetime等特殊类型
    """
    if isinstance(obj, dict):
        return obj
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj
