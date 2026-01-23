# 通用CRUD基类完整实现

> 用于完全重写系统的通用CRUD基础设施  
> 版本：v1.0  
> 日期：2026-01-23

---

## 一、架构设计

```
app/common/crud/
├── base.py              # 基础CRUD接口
├── repository.py        # Repository模式实现
├── service.py           # Service层基类
├── filters.py           # 查询构建器
└── exceptions.py        # CRUD相关异常
```

---

## 二、完整实现代码

### 2.1 异常定义

```python
# app/common/crud/exceptions.py
# -*- coding: utf-8 -*-
"""
CRUD相关异常定义
"""

from fastapi import HTTPException, status


class CRUDException(Exception):
    """CRUD基础异常"""
    pass


class NotFoundError(CRUDException):
    """资源不存在异常"""
    
    def __init__(self, resource_name: str, resource_id: int):
        self.resource_name = resource_name
        self.resource_id = resource_id
        super().__init__(f"{resource_name} (ID: {resource_id}) 不存在")


class AlreadyExistsError(CRUDException):
    """资源已存在异常"""
    
    def __init__(self, resource_name: str, field: str, value: str):
        self.resource_name = resource_name
        self.field = field
        self.value = value
        super().__init__(f"{resource_name} 的 {field}={value} 已存在")


class ValidationError(CRUDException):
    """验证错误"""
    
    def __init__(self, message: str, errors: dict = None):
        self.message = message
        self.errors = errors or {}
        super().__init__(message)


def raise_not_found(resource_name: str, resource_id: int):
    """抛出404异常"""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource_name} (ID: {resource_id}) 不存在"
    )


def raise_already_exists(resource_name: str, field: str, value: str):
    """抛出409冲突异常"""
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"{resource_name} 的 {field}={value} 已存在"
    )
```

### 2.2 查询构建器（筛选、排序、分页）

```python
# app/common/crud/filters.py
# -*- coding: utf-8 -*-
"""
通用查询构建器
支持筛选、排序、分页、关键词搜索
"""

from typing import Any, Dict, List, Optional, Type, TypeVar
from sqlalchemy import Select, and_, or_, func, asc, desc
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class QueryBuilder:
    """统一查询构建器"""
    
    @staticmethod
    def build_list_query(
        model: Type[ModelType],
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        keyword: Optional[str] = None,
        keyword_fields: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        order_direction: str = "asc"
    ) -> tuple[Select, Select]:
        """
        构建列表查询
        
        Args:
            model: SQLAlchemy模型类
            db: 数据库会话
            skip: 跳过记录数
            limit: 返回记录数
            filters: 筛选条件字典，支持多种格式：
                - 精确匹配: {"status": "ACTIVE"}
                - 列表匹配: {"status": ["ACTIVE", "PENDING"]}
                - 范围查询: {"price": {"min": 100, "max": 1000}}
                - 模糊匹配: {"name": {"like": "test"}}
                - 空值查询: {"deleted_at": None}
            keyword: 关键词搜索
            keyword_fields: 关键词搜索的字段列表
            order_by: 排序字段
            order_direction: 排序方向 (asc/desc)
        
        Returns:
            (查询对象, 计数查询对象)
        """
        from sqlalchemy import select
        
        # 基础查询
        query = select(model)
        count_query = select(func.count()).select_from(model)
        
        conditions = []
        
        # 应用筛选条件
        if filters:
            filter_conditions = QueryBuilder._build_filter_conditions(
                model, filters
            )
            if filter_conditions:
                conditions.extend(filter_conditions)
        
        # 应用关键词搜索
        if keyword and keyword_fields:
            keyword_conditions = QueryBuilder._build_keyword_conditions(
                model, keyword, keyword_fields
            )
            if keyword_conditions:
                conditions.append(or_(*keyword_conditions))
        
        # 应用所有条件
        if conditions:
            where_clause = and_(*conditions)
            query = query.where(where_clause)
            count_query = count_query.where(where_clause)
        
        # 应用排序
        if order_by:
            order_field = getattr(model, order_by, None)
            if order_field:
                if order_direction.lower() == "desc":
                    query = query.order_by(desc(order_field))
                else:
                    query = query.order_by(asc(order_field))
        
        # 应用分页
        if skip > 0:
            query = query.offset(skip)
        if limit > 0:
            query = query.limit(limit)
        
        return query, count_query
    
    @staticmethod
    def _build_filter_conditions(
        model: Type[ModelType],
        filters: Dict[str, Any]
    ) -> List:
        """构建筛选条件"""
        conditions = []
        
        for field_name, value in filters.items():
            if value is None:
                continue
            
            # 获取模型字段
            field = getattr(model, field_name, None)
            if not field:
                continue
            
            # 处理不同类型的筛选
            if isinstance(value, list):
                # 列表匹配：{"status": ["ACTIVE", "PENDING"]}
                conditions.append(field.in_(value))
            
            elif isinstance(value, dict):
                # 字典格式的复杂查询
                if "min" in value or "max" in value:
                    # 范围查询：{"price": {"min": 100, "max": 1000}}
                    if "min" in value:
                        conditions.append(field >= value["min"])
                    if "max" in value:
                        conditions.append(field <= value["max"])
                
                elif "like" in value:
                    # 模糊匹配：{"name": {"like": "test"}}
                    conditions.append(field.ilike(f"%{value['like']}%"))
                
                elif "in" in value:
                    # IN查询：{"id": {"in": [1, 2, 3]}}
                    conditions.append(field.in_(value["in"]))
                
                elif "not_in" in value:
                    # NOT IN查询
                    conditions.append(~field.in_(value["not_in"]))
                
                elif "is_null" in value:
                    # NULL查询：{"deleted_at": {"is_null": True}}
                    if value["is_null"]:
                        conditions.append(field.is_(None))
                    else:
                        conditions.append(field.isnot(None))
            
            else:
                # 精确匹配
                conditions.append(field == value)
        
        return conditions
    
    @staticmethod
    def _build_keyword_conditions(
        model: Type[ModelType],
        keyword: str,
        fields: List[str]
    ) -> List:
        """构建关键词搜索条件"""
        conditions = []
        
        for field_name in fields:
            field = getattr(model, field_name, None)
            if field:
                conditions.append(field.ilike(f"%{keyword}%"))
        
        return conditions
    
    @staticmethod
    async def execute_list_query(
        query: Select,
        count_query: Select,
        db: AsyncSession
    ) -> tuple[List[ModelType], int]:
        """
        执行列表查询
        
        Returns:
            (结果列表, 总数)
        """
        # 执行计数查询
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 执行数据查询
        result = await db.execute(query)
        items = result.scalars().all()
        
        return list(items), total
```

### 2.3 Repository基类

```python
# app/common/crud/repository.py
# -*- coding: utf-8 -*-
"""
Repository模式实现
数据访问层抽象
"""

from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload, joinedload
from pydantic import BaseModel

from app.common.crud.filters import QueryBuilder
from app.common.crud.exceptions import NotFoundError, AlreadyExistsError

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Repository基类"""
    
    def __init__(
        self,
        model: Type[ModelType],
        db: AsyncSession,
        resource_name: str = None
    ):
        """
        Args:
            model: SQLAlchemy模型类
            db: 数据库会话
            resource_name: 资源名称（用于错误消息）
        """
        self.model = model
        self.db = db
        self.resource_name = resource_name or model.__name__
    
    async def get(
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
        query = select(self.model).where(self.model.id == id)
        
        # 预加载关系
        if load_relationships:
            for rel in load_relationships:
                query = query.options(selectinload(getattr(self.model, rel)))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_field(
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
        
        query = select(self.model).where(field == value)
        
        # 预加载关系
        if load_relationships:
            for rel in load_relationships:
                query = query.options(selectinload(getattr(self.model, rel)))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def list(
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
        query, count_query = QueryBuilder.build_list_query(
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
                query = query.options(selectinload(getattr(self.model, rel)))
        
        # 执行查询
        return await QueryBuilder.execute_list_query(query, count_query, self.db)
    
    async def create(
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
            await self.db.commit()
            await self.db.refresh(db_obj)
        
        return db_obj
    
    async def create_many(
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
            await self.db.commit()
            for db_obj in db_objs:
                await self.db.refresh(db_obj)
        
        return db_objs
    
    async def update(
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
        db_obj = await self.get(id)
        if not db_obj:
            return None
        
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        if commit:
            await self.db.commit()
            await self.db.refresh(db_obj)
        
        return db_obj
    
    async def update_by_field(
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
        db_obj = await self.get_by_field(field_name, field_value)
        if not db_obj:
            return None
        
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        if commit:
            await self.db.commit()
            await self.db.refresh(db_obj)
        
        return db_obj
    
    async def delete(
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
        db_obj = await self.get(id)
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
            await self.db.delete(db_obj)
        
        if commit:
            await self.db.commit()
        
        return True
    
    async def exists(self, id: int) -> bool:
        """检查对象是否存在"""
        obj = await self.get(id)
        return obj is not None
    
    async def exists_by_field(
        self,
        field_name: str,
        value: Any
    ) -> bool:
        """检查字段值是否存在"""
        obj = await self.get_by_field(field_name, value)
        return obj is not None
    
    async def count(
        self,
        *,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """统计数量"""
        query, count_query = QueryBuilder.build_list_query(
            model=self.model,
            db=self.db,
            filters=filters
        )
        
        result = await self.db.execute(count_query)
        return result.scalar() or 0
```

### 2.4 Service层基类

```python
# app/common/crud/service.py
# -*- coding: utf-8 -*-
"""
Service层基类
业务逻辑层抽象
"""

from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.common.crud.repository import BaseRepository
from app.common.crud.exceptions import (
    NotFoundError,
    AlreadyExistsError,
    raise_not_found,
    raise_already_exists
)

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]):
    """Service基类"""
    
    def __init__(
        self,
        model: Type[ModelType],
        db: AsyncSession,
        resource_name: str = None
    ):
        """
        Args:
            model: SQLAlchemy模型类
            db: 数据库会话
            resource_name: 资源名称（用于错误消息）
        """
        self.model = model
        self.db = db
        self.resource_name = resource_name or model.__name__
        self.repository = BaseRepository(model, db, resource_name)
    
    async def get(
        self,
        id: int,
        *,
        load_relationships: Optional[List[str]] = None
    ) -> ResponseSchemaType:
        """
        获取单个对象
        
        Raises:
            HTTPException: 404 if not found
        """
        obj = await self.repository.get(id, load_relationships=load_relationships)
        if not obj:
            raise_not_found(self.resource_name, id)
        
        return self._to_response(obj)
    
    async def get_by_field(
        self,
        field_name: str,
        value: Any,
        *,
        load_relationships: Optional[List[str]] = None
    ) -> Optional[ResponseSchemaType]:
        """
        根据字段值获取单个对象
        
        Returns:
            响应对象或None
        """
        obj = await self.repository.get_by_field(
            field_name, value, load_relationships=load_relationships
        )
        if not obj:
            return None
        
        return self._to_response(obj)
    
    async def list(
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
    ) -> Dict[str, Any]:
        """
        列表查询
        
        Returns:
            {
                "items": List[ResponseSchemaType],
                "total": int,
                "skip": int,
                "limit": int
            }
        """
        items, total = await self.repository.list(
            skip=skip,
            limit=limit,
            filters=filters,
            keyword=keyword,
            keyword_fields=keyword_fields,
            order_by=order_by,
            order_direction=order_direction,
            load_relationships=load_relationships
        )
        
        return {
            "items": [self._to_response(item) for item in items],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    async def create(
        self,
        obj_in: CreateSchemaType,
        *,
        check_unique: Optional[Dict[str, Any]] = None
    ) -> ResponseSchemaType:
        """
        创建对象
        
        Args:
            obj_in: 创建数据
            check_unique: 唯一性检查字段，如 {"code": obj_in.code}
        
        Raises:
            HTTPException: 409 if already exists
        """
        # 唯一性检查
        if check_unique:
            for field, value in check_unique.items():
                exists = await self.repository.exists_by_field(field, value)
                if exists:
                    raise_already_exists(self.resource_name, field, str(value))
        
        # 创建前钩子（可扩展）
        obj_in = await self._before_create(obj_in)
        
        # 创建对象
        db_obj = await self.repository.create(obj_in)
        
        # 创建后钩子（可扩展）
        db_obj = await self._after_create(db_obj)
        
        return self._to_response(db_obj)
    
    async def update(
        self,
        id: int,
        obj_in: UpdateSchemaType,
        *,
        check_unique: Optional[Dict[str, Any]] = None
    ) -> ResponseSchemaType:
        """
        更新对象
        
        Args:
            id: 对象ID
            obj_in: 更新数据
            check_unique: 唯一性检查字段（排除当前对象）
        
        Raises:
            HTTPException: 404 if not found, 409 if conflict
        """
        # 检查存在性
        db_obj = await self.repository.get(id)
        if not db_obj:
            raise_not_found(self.resource_name, id)
        
        # 唯一性检查（排除当前对象）
        if check_unique:
            for field, value in check_unique.items():
                existing = await self.repository.get_by_field(field, value)
                if existing and existing.id != id:
                    raise_already_exists(self.resource_name, field, str(value))
        
        # 更新前钩子（可扩展）
        obj_in = await self._before_update(id, obj_in, db_obj)
        
        # 更新对象
        db_obj = await self.repository.update(id, obj_in)
        
        # 更新后钩子（可扩展）
        db_obj = await self._after_update(db_obj)
        
        return self._to_response(db_obj)
    
    async def delete(
        self,
        id: int,
        *,
        soft_delete: bool = False
    ) -> bool:
        """
        删除对象
        
        Args:
            id: 对象ID
            soft_delete: 是否软删除
        
        Raises:
            HTTPException: 404 if not found
        """
        # 检查存在性
        exists = await self.repository.exists(id)
        if not exists:
            raise_not_found(self.resource_name, id)
        
        # 删除前钩子（可扩展）
        await self._before_delete(id)
        
        # 删除对象
        success = await self.repository.delete(id, soft_delete=soft_delete)
        
        # 删除后钩子（可扩展）
        if success:
            await self._after_delete(id)
        
        return success
    
    async def count(
        self,
        *,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """统计数量"""
        return await self.repository.count(filters=filters)
    
    # ========== 可扩展的钩子方法 ==========
    
    def _to_response(self, obj: ModelType) -> ResponseSchemaType:
        """
        将模型对象转换为响应对象
        
        子类可以重写此方法以实现自定义转换逻辑
        """
        # 默认实现：假设ResponseSchemaType可以直接从模型创建
        # 实际使用时需要根据具体情况实现
        return ResponseSchemaType.model_validate(obj)
    
    async def _before_create(self, obj_in: CreateSchemaType) -> CreateSchemaType:
        """创建前钩子（可扩展）"""
        return obj_in
    
    async def _after_create(self, db_obj: ModelType) -> ModelType:
        """创建后钩子（可扩展）"""
        return db_obj
    
    async def _before_update(
        self,
        id: int,
        obj_in: UpdateSchemaType,
        db_obj: ModelType
    ) -> UpdateSchemaType:
        """更新前钩子（可扩展）"""
        return obj_in
    
    async def _after_update(self, db_obj: ModelType) -> ModelType:
        """更新后钩子（可扩展）"""
        return db_obj
    
    async def _before_delete(self, id: int) -> None:
        """删除前钩子（可扩展）"""
        pass
    
    async def _after_delete(self, id: int) -> None:
        """删除后钩子（可扩展）"""
        pass
```

### 2.5 使用示例

```python
# app/services/projects/project_service.py
# -*- coding: utf-8 -*-
"""
项目服务实现示例
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.crud.service import BaseService
from app.models.projects import Project
from app.schemas.projects import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse
)


class ProjectService(
    BaseService[Project, ProjectCreate, ProjectUpdate, ProjectResponse]
):
    """项目服务"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(
            model=Project,
            db=db,
            resource_name="项目"
        )
    
    async def get_by_code(self, code: str) -> Optional[ProjectResponse]:
        """根据项目编码获取项目"""
        return await self.get_by_field("code", code)
    
    async def create(
        self,
        obj_in: ProjectCreate,
        *,
        check_unique: Optional[Dict[str, Any]] = None
    ) -> ProjectResponse:
        """创建项目（自动检查编码唯一性）"""
        # 自动添加编码唯一性检查
        if check_unique is None:
            check_unique = {}
        check_unique["code"] = obj_in.code
        
        return await super().create(obj_in, check_unique=check_unique)
    
    async def _before_create(self, obj_in: ProjectCreate) -> ProjectCreate:
        """创建前处理：自动生成项目编码"""
        if not obj_in.code:
            # 生成项目编码逻辑
            obj_in.code = await self._generate_project_code()
        return obj_in
    
    async def _generate_project_code(self) -> str:
        """生成项目编码"""
        # 实现编码生成逻辑
        from datetime import datetime
        date_str = datetime.now().strftime("%y%m%d")
        # 查询当天已有项目数
        count = await self.count(filters={"code": {"like": f"PJ{date_str}"}})
        return f"PJ{date_str}{count + 1:03d}"
    
    def _to_response(self, obj: Project) -> ProjectResponse:
        """自定义响应转换（包含关联数据）"""
        # 可以在这里添加额外的数据转换逻辑
        return ProjectResponse.model_validate(obj)
```

### 2.6 API路由使用示例

```python
# app/api/v1/routers/projects.py
# -*- coding: utf-8 -*-
"""
项目API路由
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.services.projects.project_service import ProjectService
from app.schemas.projects import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse
)
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取项目列表"""
    service = ProjectService(db)
    
    # 构建筛选条件
    filters = {}
    if status:
        filters["status"] = status
    if customer_id:
        filters["customer_id"] = customer_id
    
    # 关键词搜索字段
    keyword_fields = ["code", "name", "contract_no"]
    
    # 调用服务
    result = await service.list(
        skip=(page - 1) * page_size,
        limit=page_size,
        filters=filters,
        keyword=keyword,
        keyword_fields=keyword_fields,
        order_by="created_at",
        order_direction="desc"
    )
    
    return PaginatedResponse(
        items=result["items"],
        total=result["total"],
        page=page,
        page_size=page_size,
        pages=(result["total"] + page_size - 1) // page_size
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int = Path(..., description="项目ID"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取项目详情"""
    service = ProjectService(db)
    return await service.get(project_id)


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建项目"""
    service = ProjectService(db)
    return await service.create(project_in)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int = Path(..., description="项目ID"),
    project_in: ProjectUpdate = ...,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新项目"""
    service = ProjectService(db)
    return await service.update(project_id, project_in)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int = Path(..., description="项目ID"),
    soft_delete: bool = Query(False, description="是否软删除"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除项目"""
    service = ProjectService(db)
    await service.delete(project_id, soft_delete=soft_delete)
    return None
```

---

## 三、高级功能

### 3.1 支持复杂查询

```python
# 使用示例：复杂筛选
filters = {
    # 精确匹配
    "status": "ACTIVE",
    
    # 列表匹配
    "type": ["TYPE_A", "TYPE_B"],
    
    # 范围查询
    "price": {"min": 100, "max": 1000},
    
    # 模糊匹配
    "name": {"like": "test"},
    
    # NULL查询
    "deleted_at": {"is_null": True},
    
    # IN查询
    "id": {"in": [1, 2, 3]},
    
    # NOT IN查询
    "category_id": {"not_in": [5, 6]}
}

result = await service.list(filters=filters)
```

### 3.2 支持关系预加载

```python
# 预加载关联数据
project = await service.get(
    project_id,
    load_relationships=["customer", "members", "machines"]
)
```

### 3.3 支持批量操作

```python
# 批量创建
projects = await service.repository.create_many([
    ProjectCreate(code="PJ001", name="项目1"),
    ProjectCreate(code="PJ002", name="项目2"),
])
```

---

## 四、优势总结

### 4.1 代码复用

- **减少重复代码**：所有CRUD操作只需几行代码
- **统一接口**：所有模块使用相同的API模式
- **易于维护**：修改基类，所有模块受益

### 4.2 功能强大

- **灵活筛选**：支持多种筛选方式
- **关键词搜索**：自动支持多字段搜索
- **关系预加载**：避免N+1查询问题
- **软删除支持**：可选的软删除功能

### 4.3 易于扩展

- **钩子方法**：可以在创建/更新/删除前后执行自定义逻辑
- **自定义转换**：可以自定义响应对象转换
- **业务逻辑**：可以在Service层添加业务特定方法

### 4.4 类型安全

- **完整类型提示**：所有方法都有类型提示
- **Pydantic验证**：自动数据验证
- **IDE支持**：更好的代码补全和错误检查

---

## 五、使用建议

### 5.1 何时使用基类

✅ **应该使用**：
- 标准的CRUD操作
- 列表查询（筛选、搜索、排序、分页）
- 简单的业务逻辑

❌ **不应该使用**：
- 复杂的业务逻辑（应该在Service层实现）
- 跨表事务（应该在Service层处理）
- 特殊的查询需求（可以扩展Repository）

### 5.2 扩展方式

1. **在Service层添加业务方法**
   ```python
   class ProjectService(BaseService):
       async def start_project(self, project_id: int):
           # 业务特定逻辑
           pass
   ```

2. **重写钩子方法**
   ```python
   async def _before_create(self, obj_in):
       # 自定义创建前逻辑
       return obj_in
   ```

3. **扩展Repository**
   ```python
   class ProjectRepository(BaseRepository):
       async def get_active_projects(self):
           # 自定义查询
           pass
   ```

---

## 六、测试示例

```python
# tests/services/test_project_service.py
import pytest
from app.services.projects.project_service import ProjectService
from app.schemas.projects import ProjectCreate

@pytest.mark.asyncio
async def test_create_project(db_session):
    """测试创建项目"""
    service = ProjectService(db_session)
    
    project_in = ProjectCreate(
        code="PJ001",
        name="测试项目",
        customer_id=1
    )
    
    project = await service.create(project_in)
    
    assert project.code == "PJ001"
    assert project.name == "测试项目"

@pytest.mark.asyncio
async def test_list_projects_with_filters(db_session):
    """测试带筛选的列表查询"""
    service = ProjectService(db_session)
    
    result = await service.list(
        filters={"status": "ACTIVE"},
        keyword="测试",
        keyword_fields=["name", "code"]
    )
    
    assert result["total"] > 0
    assert all(item.status == "ACTIVE" for item in result["items"])
```

---

**文档版本**：v1.0  
**最后更新**：2026-01-23
