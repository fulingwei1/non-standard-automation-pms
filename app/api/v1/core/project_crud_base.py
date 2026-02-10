# -*- coding: utf-8 -*-
"""
项目中心CRUD路由基类
用于快速创建项目子模块的CRUD端点

使用示例:
    from app.api.v1.core.project_crud_base import create_project_crud_router
    
    router = create_project_crud_router(
        model=ProjectMilestone,
        create_schema=MilestoneCreate,
        update_schema=MilestoneUpdate,
        response_schema=MilestoneResponse,
        permission_prefix="milestone",
        project_id_field="project_id"
    )
"""

from typing import Type, TypeVar, List, Optional, Any, Dict, Callable
from fastapi import APIRouter, Path, Depends, Query, HTTPException, status, Body, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.common.pagination import PaginationParams, get_pagination_query
from app.utils.permission_helpers import check_project_access_or_raise

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)


def create_project_crud_router(
    model: Type[ModelType],
    create_schema: Type[CreateSchemaType],
    update_schema: Type[UpdateSchemaType],
    response_schema: Type[ResponseSchemaType],
    permission_prefix: str,
    project_id_field: str = "project_id",
    keyword_fields: Optional[List[str]] = None,
    default_order_by: Optional[str] = None,
    default_order_direction: str = "desc",
    custom_filters: Optional[Dict[str, Callable]] = None,
    before_create: Optional[Callable] = None,
    after_create: Optional[Callable] = None,
    before_update: Optional[Callable] = None,
    after_update: Optional[Callable] = None,
    before_delete: Optional[Callable] = None,
    after_delete: Optional[Callable] = None,
) -> APIRouter:
    """
    创建项目中心CRUD路由
    
    Args:
        model: SQLAlchemy模型类
        create_schema: 创建请求Schema
        update_schema: 更新请求Schema
        response_schema: 响应Schema
        permission_prefix: 权限前缀，如 "milestone" 会生成 "milestone:read", "milestone:create" 等
        project_id_field: 项目ID字段名，默认为 "project_id"
        keyword_fields: 关键词搜索的字段列表，默认为 ["name", "code"]
        default_order_by: 默认排序字段，默认为 "created_at"
        default_order_direction: 默认排序方向，默认为 "desc"
        custom_filters: 自定义筛选器字典，格式为 {field_name: filter_function}
        before_create: 创建前钩子函数
        after_create: 创建后钩子函数
        before_update: 更新前钩子函数
        after_update: 更新后钩子函数
        before_delete: 删除前钩子函数
        after_delete: 删除后钩子函数
    
    Returns:
        APIRouter实例
    """
    router = APIRouter()
    
    # 默认关键词搜索字段
    if keyword_fields is None:
        keyword_fields = ["name", "code"]
    
    # 默认排序字段
    if default_order_by is None:
        default_order_by = "created_at"
    
    # 获取项目ID字段
    project_id_attr = getattr(model, project_id_field, None)
    if not project_id_attr:
        raise ValueError(f"模型 {model.__name__} 没有字段 {project_id_field}")
    
    @router.get("/", response_model=PaginatedResponse[response_schema])
    def list_items(
        request: Request,  # FastAPI自动注入，必须放在最前面
        project_id: int = Path(..., description="项目ID"),
        db: Session = Depends(deps.get_db),
        pagination: PaginationParams = Depends(get_pagination_query),
        keyword: Optional[str] = Query(None, description="关键词搜索"),
        order_by: Optional[str] = Query(None, description="排序字段"),
        order_direction: Optional[str] = Query("desc", description="排序方向 (asc/desc)"),
        current_user: User = Depends(security.require_permission(f"{permission_prefix}:read")),
    ) -> Any:
        """获取项目子资源列表"""

        # 检查项目访问权限
        check_project_access_or_raise(db, current_user, project_id)

        # 构建基础查询
        query = db.query(model).filter(project_id_attr == project_id)

        # 应用自定义筛选（从request.query_params获取）
        if custom_filters:
            for field_name, filter_func in custom_filters.items():
                filter_value = request.query_params.get(field_name)
                if filter_value is not None:
                    query = filter_func(query, filter_value)

        # 关键词搜索
        if keyword:
            from sqlalchemy import or_
            conditions = []
            for field_name in keyword_fields:
                field = getattr(model, field_name, None)
                if field:
                    conditions.append(field.ilike(f"%{keyword}%"))
            if conditions:
                query = query.filter(or_(*conditions))

        # 排序
        order_field_name = order_by or default_order_by
        order_field = getattr(model, order_field_name, None)
        if order_field:
            order_dir = order_direction or default_order_direction
            if order_dir.lower() == "asc":
                query = query.order_by(order_field.asc())
            else:
                query = query.order_by(order_field.desc())
        else:
            # 如果没有找到排序字段，使用默认排序
            if hasattr(model, "created_at"):
                query = query.order_by(model.created_at.desc())

        # 总数
        total = query.count()

        # 分页
        items = query.offset(pagination.offset).limit(pagination.limit).all()

        # 转换为响应Schema
        response_items = [response_schema.model_validate(item) for item in items]

        return PaginatedResponse(
            items=response_items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pagination.pages_for_total(total)
        )
    
    @router.post("/", response_model=response_schema, status_code=status.HTTP_201_CREATED)
    def create_item(
        project_id: int = Path(..., description="项目ID"),
        item_in: create_schema = Body(..., description="创建数据"),
        db: Session = Depends(deps.get_db),
        current_user: User = Depends(security.require_permission(f"{permission_prefix}:create")),
    ) -> Any:
        """创建项目子资源"""
        # 检查项目访问权限
        check_project_access_or_raise(
            db, current_user, project_id, f"您没有权限在该项目中创建{permission_prefix}"
        )
        
        # 验证项目存在
        from app.models.project import Project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在"
            )
        
        # 准备创建数据
        item_data = item_in.model_dump(exclude_unset=True)
        item_data[project_id_field] = project_id  # 确保使用路径中的项目ID
        
        # 创建前钩子
        if before_create:
            item_data = before_create(item_data, project_id, current_user)
        
        # 创建对象
        db_item = model(**item_data)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        
        # 创建后钩子
        if after_create:
            db_item = after_create(db_item, project_id, current_user)
            if db_item:
                db.commit()
                db.refresh(db_item)
        
        return response_schema.model_validate(db_item)
    
    @router.get("/{item_id}", response_model=response_schema)
    def get_item(
        project_id: int = Path(..., description="项目ID"),
        item_id: int = Path(..., description="资源ID"),
        db: Session = Depends(deps.get_db),
        current_user: User = Depends(security.require_permission(f"{permission_prefix}:read")),
    ) -> Any:
        """获取项目子资源详情"""
        # 检查项目访问权限
        check_project_access_or_raise(db, current_user, project_id)
        
        # 查询对象（必须属于该项目）
        item = db.query(model).filter(
            model.id == item_id,
            project_id_attr == project_id
        ).first()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__} not found"
            )
        
        return response_schema.model_validate(item)
    
    @router.put("/{item_id}", response_model=response_schema)
    def update_item(
        project_id: int = Path(..., description="项目ID"),
        item_id: int = Path(..., description="资源ID"),
        item_in: update_schema = Body(..., description="更新数据"),
        db: Session = Depends(deps.get_db),
        current_user: User = Depends(security.require_permission(f"{permission_prefix}:update")),
    ) -> Any:
        """更新项目子资源"""
        # 检查项目访问权限
        check_project_access_or_raise(db, current_user, project_id)
        
        # 查询对象（必须属于该项目）
        item = db.query(model).filter(
            model.id == item_id,
            project_id_attr == project_id
        ).first()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__} not found"
            )
        
        # 更新前钩子
        if before_update:
            item_in = before_update(item, item_in, project_id, current_user)
            if item_in is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="更新被取消"
                )
        
        # 更新数据（排除项目ID，防止修改）
        update_data = item_in.model_dump(exclude_unset=True)
        if project_id_field in update_data:
            del update_data[project_id_field]  # 不允许修改项目ID
        
        # 应用更新
        for field, value in update_data.items():
            if hasattr(item, field):
                setattr(item, field, value)
        
        db.commit()
        db.refresh(item)
        
        # 更新后钩子
        if after_update:
            item = after_update(item, project_id, current_user)
            if item:
                db.commit()
                db.refresh(item)
        
        return response_schema.model_validate(item)
    
    @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
    def delete_item(
        project_id: int = Path(..., description="项目ID"),
        item_id: int = Path(..., description="资源ID"),
        db: Session = Depends(deps.get_db),
        current_user: User = Depends(security.require_permission(f"{permission_prefix}:delete")),
    ):
        """删除项目子资源"""
        # 检查项目访问权限
        check_project_access_or_raise(db, current_user, project_id)
        
        # 查询对象（必须属于该项目）
        item = db.query(model).filter(
            model.id == item_id,
            project_id_attr == project_id
        ).first()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__} not found"
            )
        
        # 删除前钩子
        if before_delete:
            if not before_delete(item, project_id, current_user):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="删除被取消"
                )
        
        # 删除对象
        db.delete(item)
        db.commit()
        
        # 删除后钩子
        if after_delete:
            after_delete(item_id, project_id, current_user)
    
    return router


class ProjectCRUDRouter:
    """
    项目中心CRUD路由类（面向对象方式）
    
    使用示例:
        router = ProjectCRUDRouter(
            model=ProjectMilestone,
            create_schema=MilestoneCreate,
            update_schema=MilestoneUpdate,
            response_schema=MilestoneResponse,
            permission_prefix="milestone"
        )
        router.register_routes()
    """
    
    def __init__(
        self,
        model: Type[ModelType],
        create_schema: Type[CreateSchemaType],
        update_schema: Type[UpdateSchemaType],
        response_schema: Type[ResponseSchemaType],
        permission_prefix: str,
        project_id_field: str = "project_id",
        keyword_fields: Optional[List[str]] = None,
        default_order_by: Optional[str] = None,
        default_order_direction: str = "desc",
    ):
        self.model = model
        self.create_schema = create_schema
        self.update_schema = update_schema
        self.response_schema = response_schema
        self.permission_prefix = permission_prefix
        self.project_id_field = project_id_field
        self.keyword_fields = keyword_fields or ["name", "code"]
        self.default_order_by = default_order_by or "created_at"
        self.default_order_direction = default_order_direction
        self.router = APIRouter()
    
    def register_routes(self) -> APIRouter:
        """注册所有CRUD路由"""
        return create_project_crud_router(
            model=self.model,
            create_schema=self.create_schema,
            update_schema=self.update_schema,
            response_schema=self.response_schema,
            permission_prefix=self.permission_prefix,
            project_id_field=self.project_id_field,
            keyword_fields=self.keyword_fields,
            default_order_by=self.default_order_by,
            default_order_direction=self.default_order_direction,
        )
