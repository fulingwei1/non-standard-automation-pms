# -*- coding: utf-8 -*-
"""
同步版本的Repository基类
适配当前项目使用的同步Session
"""

from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel

from app.common.crud.sync_filters import SyncQueryBuilder
from app.common.crud.exceptions import NotFoundError, AlreadyExistsError

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class SyncBaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """同步版本的Repository基类"""
    
    def __init__(
        self,
        model: Type[ModelType],
        db: Session,
        resource_name: str = None
    ):
        """
        Args:
            model: SQLAlchemy模型类
            db: 数据库会话（同步Session）
            resource_name: 资源名称（用于错误消息）
        """
        self.model = model
        self.db = db
        self.resource_name = resource_name or model.__name__
    
    def get(
        self,
        id: int,
        *,
        load_relationships: Optional[List[str]] = None
    ) -> Optional[ModelType]:
        """
        根据ID获取单个对象
        
        Args:
            id: 对象ID
            load_relationships: 需要预加载的关系字段列表
        
        Returns:
            模型对象或None
        """
        query = self.db.query(self.model).filter(self.model.id == id)
        
        # 预加载关系（使用joinedload）
        if load_relationships:
            for rel in load_relationships:
                query = query.options(joinedload(getattr(self.model, rel)))
        
        return query.first()
    
    def get_by_field(
        self,
        field_name: str,
        value: Any,
        *,
        load_relationships: Optional[List[str]] = None
    ) -> Optional[ModelType]:
        """
        根据字段值获取单个对象
        
        Args:
            field_name: 字段名
            value: 字段值
            load_relationships: 需要预加载的关系字段列表
        
        Returns:
            模型对象或None
        """
        field = getattr(self.model, field_name, None)
        if not field:
            raise ValueError(f"字段 {field_name} 不存在")
        
        query = self.db.query(self.model).filter(field == value)
        
        # 预加载关系
        if load_relationships:
            for rel in load_relationships:
                query = query.options(joinedload(getattr(self.model, rel)))
        
        return query.first()
    
    def list(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        keyword: Optional[str] = None,
        keyword_fields: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        order_direction: str = "asc",
        load_relationships: Optional[List[str]] = None
    ) -> tuple[List[ModelType], int]:
        """
        列表查询（支持筛选、搜索、排序、分页）
        
        Returns:
            (结果列表, 总数)
        """
        # 构建查询
        query, count_query = SyncQueryBuilder.build_list_query(
            model=self.model,
            db=self.db,
            skip=skip,
            limit=limit,
            filters=filters,
            keyword=keyword,
            keyword_fields=keyword_fields,
            order_by=order_by,
            order_direction=order_direction
        )
        
        # 预加载关系
        if load_relationships:
            for rel in load_relationships:
                query = query.options(joinedload(getattr(self.model, rel)))
        
        # 执行查询
        return SyncQueryBuilder.execute_list_query(query, count_query)
    
    def create(
        self,
        obj_in: CreateSchemaType,
        *,
        commit: bool = True
    ) -> ModelType:
        """
        创建对象
        
        Args:
            obj_in: 创建数据
            commit: 是否立即提交
        
        Returns:
            创建的模型对象
        """
        obj_data = obj_in.model_dump(exclude_unset=True)
        db_obj = self.model(**obj_data)
        
        self.db.add(db_obj)
        
        if commit:
            self.db.commit()
            self.db.refresh(db_obj)
        
        return db_obj
    
    def create_many(
        self,
        objs_in: List[CreateSchemaType],
        *,
        commit: bool = True
    ) -> List[ModelType]:
        """
        批量创建对象
        
        Args:
            objs_in: 创建数据列表
            commit: 是否立即提交
        
        Returns:
            创建的模型对象列表
        """
        db_objs = []
        
        for obj_in in objs_in:
            obj_data = obj_in.model_dump(exclude_unset=True)
            db_obj = self.model(**obj_data)
            db_objs.append(db_obj)
            self.db.add(db_obj)
        
        if commit:
            self.db.commit()
            for db_obj in db_objs:
                self.db.refresh(db_obj)
        
        return db_objs
    
    def update(
        self,
        id: int,
        obj_in: UpdateSchemaType,
        *,
        commit: bool = True
    ) -> Optional[ModelType]:
        """
        更新对象
        
        Args:
            id: 对象ID
            obj_in: 更新数据
            commit: 是否立即提交
        
        Returns:
            更新后的模型对象或None
        """
        db_obj = self.get(id)
        if not db_obj:
            return None
        
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        if commit:
            self.db.commit()
            self.db.refresh(db_obj)
        
        return db_obj
    
    def update_by_field(
        self,
        field_name: str,
        field_value: Any,
        obj_in: UpdateSchemaType,
        *,
        commit: bool = True
    ) -> Optional[ModelType]:
        """
        根据字段值更新对象
        
        Args:
            field_name: 字段名
            field_value: 字段值
            obj_in: 更新数据
            commit: 是否立即提交
        
        Returns:
            更新后的模型对象或None
        """
        db_obj = self.get_by_field(field_name, field_value)
        if not db_obj:
            return None
        
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        if commit:
            self.db.commit()
            self.db.refresh(db_obj)
        
        return db_obj
    
    def delete(
        self,
        id: int,
        *,
        commit: bool = True,
        soft_delete: bool = False
    ) -> bool:
        """
        删除对象
        
        Args:
            id: 对象ID
            commit: 是否立即提交
            soft_delete: 是否软删除（设置deleted_at字段）
        
        Returns:
            是否删除成功
        """
        db_obj = self.get(id)
        if not db_obj:
            return False
        
        if soft_delete:
            # 软删除：设置deleted_at字段
            if hasattr(db_obj, 'deleted_at'):
                from datetime import datetime
                db_obj.deleted_at = datetime.utcnow()
            else:
                raise ValueError("模型不支持软删除（缺少deleted_at字段）")
        else:
            # 硬删除
            self.db.delete(db_obj)
        
        if commit:
            self.db.commit()
        
        return True
    
    def exists(self, id: int) -> bool:
        """检查对象是否存在"""
        obj = self.get(id)
        return obj is not None
    
    def exists_by_field(
        self,
        field_name: str,
        value: Any
    ) -> bool:
        """检查字段值是否存在"""
        obj = self.get_by_field(field_name, value)
        return obj is not None
    
    def count(
        self,
        *,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """统计数量"""
        query, count_query = SyncQueryBuilder.build_list_query(
            model=self.model,
            db=self.db,
            filters=filters
        )
        
        return count_query.scalar() or 0
