# -*- coding: utf-8 -*-
"""
数据范围过滤实际使用示例

这个文件包含了各种真实场景下的数据范围过滤使用案例
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced
from app.services.data_scope.generic_filter import GenericFilterService
from app.services.data_scope.config import DataScopeConfig, DATA_SCOPE_CONFIGS


# ============================================================================
# 示例 1: 项目管理 API
# ============================================================================

router = APIRouter(prefix="/api/v1", tags=["projects"])


class ProjectListResponse(BaseModel):
    """项目列表响应"""
    total: int
    page: int
    size: int
    data: List[dict]


@router.get("/projects", response_model=ProjectListResponse)
def list_projects(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目列表
    
    根据用户的数据权限范围返回可见的项目：
    - 超级管理员：看到所有项目
    - 部门经理：看到本部门及子部门的项目
    - 项目经理：看到参与的项目
    - 普通员工：看到自己创建的项目
    """
    from app.models.project import Project
    
    # 创建基础查询
    query = db.query(Project)
    
    # 应用业务过滤条件
    if status:
        query = query.filter(Project.status == status)
    
    # 应用数据权限过滤 ⭐ 核心功能
    query = DataScopeServiceEnhanced.apply_data_scope(
        query=query,
        db=db,
        user=current_user,
        resource_type="project",
        org_field="dept_id",        # 组织字段
        owner_field="created_by",   # 创建者字段
        pm_field="pm_id"            # 项目经理字段
    )
    
    # 分页查询
    total = query.count()
    projects = query.offset((page - 1) * size).limit(size).all()
    
    return {
        "total": total,
        "page": page,
        "size": size,
        "data": [p.to_dict() for p in projects]
    }


@router.get("/projects/{project_id}")
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目详情（带权限检查）
    
    两层权限验证：
    1. 查询时过滤
    2. 返回前再次检查
    """
    from app.models.project import Project
    
    # 先查询项目
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查访问权限 ⭐ 核心功能
    if not DataScopeServiceEnhanced.can_access_data(
        db=db,
        user=current_user,
        resource_type="project",
        data=project,
        org_field="dept_id",
        owner_field="created_by"
    ):
        raise HTTPException(status_code=403, detail="无权访问此项目")
    
    return project.to_dict()


@router.put("/projects/{project_id}")
def update_project(
    project_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新项目（带权限检查）
    
    只有项目所有者或PM可以更新项目
    """
    from app.models.project import Project
    
    # 通过数据范围过滤查询
    query = db.query(Project).filter(Project.id == project_id)
    query = DataScopeServiceEnhanced.apply_data_scope(
        query, db, current_user, "project", org_field="dept_id"
    )
    
    project = query.first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在或无权访问")
    
    # 额外检查：只有创建者或PM可以编辑
    if not (project.created_by == current_user.id or project.pm_id == current_user.id):
        raise HTTPException(status_code=403, detail="只有项目创建者或PM可以编辑")
    
    # 更新项目
    for key, value in data.items():
        if hasattr(project, key):
            setattr(project, key, value)
    
    db.commit()
    db.refresh(project)
    
    return project.to_dict()


# ============================================================================
# 示例 2: 采购订单管理
# ============================================================================

purchase_router = APIRouter(prefix="/api/v1", tags=["purchase"])


@purchase_router.get("/purchase-orders")
def list_purchase_orders(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取采购订单列表（使用通用过滤器）
    
    使用预定义的配置简化代码
    """
    from app.models.purchase import PurchaseOrder
    
    query = db.query(PurchaseOrder)
    
    # 使用通用过滤器 + 预定义配置 ⭐ 推荐方式
    config = DATA_SCOPE_CONFIGS.get("purchase_order")
    query = GenericFilterService.filter_by_scope(
        db=db,
        query=query,
        model=PurchaseOrder,
        user=current_user,
        config=config
    )
    
    # 分页
    total = query.count()
    orders = query.offset((page - 1) * size).limit(size).all()
    
    return {
        "total": total,
        "page": page,
        "size": size,
        "data": [order.to_dict() for order in orders]
    }


# ============================================================================
# 示例 3: 任务管理（自定义配置）
# ============================================================================

task_router = APIRouter(prefix="/api/v1", tags=["tasks"])


@task_router.get("/tasks")
def list_tasks(
    assignee_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取任务列表（自定义配置）
    
    任务的特殊性：
    - 所有者可能是assignee（分配人）或creator（创建者）
    - 需要通过project_id关联项目
    """
    from app.models.task import Task
    
    query = db.query(Task)
    
    # 应用业务过滤
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
    if status:
        query = query.filter(Task.status == status)
    
    # 自定义数据范围配置 ⭐ 核心功能
    config = DataScopeConfig(
        owner_field="assignee_id",              # 主要所有者：分配人
        additional_owner_fields=["created_by"], # 额外所有者：创建者
        project_field="project_id",             # 项目关联
        dept_through_project=True               # 通过项目获取部门
    )
    
    query = GenericFilterService.filter_by_scope(
        db=db,
        query=query,
        model=Task,
        user=current_user,
        config=config
    )
    
    tasks = query.all()
    return [task.to_dict() for task in tasks]


# ============================================================================
# 示例 4: 文档管理（自定义过滤函数）
# ============================================================================

doc_router = APIRouter(prefix="/api/v1", tags=["documents"])


def custom_document_filter(query, user, data_scope, db):
    """
    自定义文档过滤函数
    
    规则：
    - 公开文档：所有人可见
    - 私有文档：只有上传者可见
    - 项目文档：项目成员可见
    """
    from sqlalchemy import or_
    from app.models.document import Document
    from app.models.enums import DataScopeEnum
    
    if data_scope == DataScopeEnum.ALL.value:
        return query
    
    # 基本条件：公开文档 或 自己上传的
    conditions = [
        Document.is_public == True,
        Document.uploaded_by == user.id
    ]
    
    # 如果有项目权限，加上项目文档
    if data_scope in [DataScopeEnum.PROJECT.value, DataScopeEnum.DEPT.value]:
        from app.services.data_scope.user_scope import UserScopeService
        user_project_ids = UserScopeService.get_user_project_ids(db, user.id)
        if user_project_ids:
            conditions.append(Document.project_id.in_(list(user_project_ids)))
    
    return query.filter(or_(*conditions))


@doc_router.get("/documents")
def list_documents(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取文档列表（自定义过滤逻辑）
    """
    from app.models.document import Document
    
    query = db.query(Document)
    
    if project_id:
        query = query.filter(Document.project_id == project_id)
    
    # 使用自定义过滤函数 ⭐ 高级用法
    config = DataScopeConfig(
        owner_field="uploaded_by",
        project_field="project_id",
        custom_filter=custom_document_filter  # 自定义逻辑
    )
    
    query = GenericFilterService.filter_by_scope(
        db=db,
        query=query,
        model=Document,
        user=current_user,
        config=config
    )
    
    documents = query.all()
    return [doc.to_dict() for doc in documents]


# ============================================================================
# 示例 5: 批量操作权限检查
# ============================================================================

batch_router = APIRouter(prefix="/api/v1", tags=["batch"])


@batch_router.post("/tasks/batch-delete")
def batch_delete_tasks(
    task_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    批量删除任务（带权限检查）
    
    只能删除有权限的任务
    """
    from app.models.task import Task
    
    # 查询任务
    tasks = db.query(Task).filter(Task.id.in_(task_ids)).all()
    
    if not tasks:
        raise HTTPException(status_code=404, detail="未找到任务")
    
    # 逐个检查权限 ⭐ 批量操作的权限验证
    deleted_count = 0
    failed_ids = []
    
    for task in tasks:
        # 检查访问权限
        if DataScopeServiceEnhanced.can_access_data(
            db=db,
            user=current_user,
            resource_type="task",
            data=task,
            owner_field="assignee_id"
        ):
            db.delete(task)
            deleted_count += 1
        else:
            failed_ids.append(task.id)
    
    db.commit()
    
    return {
        "deleted_count": deleted_count,
        "failed_ids": failed_ids,
        "message": f"成功删除 {deleted_count} 个任务"
    }


# ============================================================================
# 示例 6: 统计报表（聚合查询）
# ============================================================================

stats_router = APIRouter(prefix="/api/v1", tags=["statistics"])


@stats_router.get("/stats/project-count")
def get_project_count_by_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    按状态统计项目数量
    
    只统计用户有权限看到的项目
    """
    from sqlalchemy import func
    from app.models.project import Project
    
    # 创建基础查询
    query = db.query(
        Project.status,
        func.count(Project.id).label("count")
    )
    
    # 应用数据权限过滤 ⭐ 统计也要考虑权限
    query = DataScopeServiceEnhanced.apply_data_scope(
        query=query,
        db=db,
        user=current_user,
        resource_type="project",
        org_field="dept_id",
        owner_field="created_by",
        pm_field="pm_id"
    )
    
    # 分组统计
    results = query.group_by(Project.status).all()
    
    return {
        status: count for status, count in results
    }


# ============================================================================
# 示例 7: 导出功能（权限过滤）
# ============================================================================

export_router = APIRouter(prefix="/api/v1", tags=["export"])


@export_router.get("/export/projects")
def export_projects(
    format: str = Query("excel", regex="^(excel|csv|pdf)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出项目列表
    
    只导出用户有权限看到的项目
    """
    from app.models.project import Project
    import pandas as pd
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    
    # 创建查询（应用权限过滤）⭐ 导出也要过滤
    query = db.query(Project)
    query = DataScopeServiceEnhanced.apply_data_scope(
        query, db, current_user, "project", org_field="dept_id"
    )
    
    projects = query.all()
    
    # 转换为DataFrame
    data = [p.to_dict() for p in projects]
    df = pd.DataFrame(data)
    
    # 根据格式导出
    if format == "excel":
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=projects.xlsx"}
        )
    
    elif format == "csv":
        output = StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=projects.csv"}
        )


# ============================================================================
# 示例 8: 调试工具
# ============================================================================

debug_router = APIRouter(prefix="/api/v1/debug", tags=["debug"])


@debug_router.get("/my-scope-info")
def get_my_scope_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    调试工具：查看当前用户的数据范围信息
    
    用于排查权限问题
    """
    from app.services.permission_service import PermissionService
    
    # 获取用户组织单元
    user_orgs = DataScopeServiceEnhanced.get_user_org_units(db, current_user.id)
    
    # 获取数据权限配置
    scopes = PermissionService.get_user_data_scopes(db, current_user.id)
    
    # 获取各范围类型的可访问组织
    accessible_orgs = {}
    for scope_type in ["DEPARTMENT", "BUSINESS_UNIT", "TEAM"]:
        accessible_orgs[scope_type] = DataScopeServiceEnhanced.get_accessible_org_units(
            db, current_user.id, scope_type
        )
    
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "is_superuser": current_user.is_superuser,
        "user_organizations": user_orgs,
        "data_scopes": scopes,
        "accessible_organizations": accessible_orgs
    }


# ============================================================================
# 示例 9: Service 层使用
# ============================================================================

class ProjectService:
    """项目服务类示例"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_projects(self, user: User, status: Optional[str] = None) -> List:
        """
        获取用户可见的项目列表
        
        在 Service 层使用数据范围过滤
        """
        from app.models.project import Project
        
        query = self.db.query(Project)
        
        if status:
            query = query.filter(Project.status == status)
        
        # Service 层应用权限过滤 ⭐ 服务层封装
        query = DataScopeServiceEnhanced.apply_data_scope(
            query=query,
            db=self.db,
            user=user,
            resource_type="project",
            org_field="dept_id",
            owner_field="created_by",
            pm_field="pm_id"
        )
        
        return query.all()
    
    def can_user_edit_project(self, user: User, project_id: int) -> bool:
        """
        检查用户是否可以编辑项目
        """
        from app.models.project import Project
        
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False
        
        # 检查基本访问权限
        if not DataScopeServiceEnhanced.can_access_data(
            db=self.db,
            user=user,
            resource_type="project",
            data=project,
            org_field="dept_id"
        ):
            return False
        
        # 检查编辑权限（创建者或PM）
        return project.created_by == user.id or project.pm_id == user.id


# ============================================================================
# 示例 10: 复杂查询场景
# ============================================================================

@router.get("/projects/advanced-search")
def advanced_project_search(
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    高级项目搜索
    
    结合多种过滤条件 + 数据权限过滤
    """
    from app.models.project import Project
    from sqlalchemy import and_, or_
    from datetime import datetime
    
    # 基础查询
    query = db.query(Project)
    
    # 业务过滤条件
    filters = []
    
    if keyword:
        filters.append(
            or_(
                Project.name.ilike(f"%{keyword}%"),
                Project.description.ilike(f"%{keyword}%")
            )
        )
    
    if status:
        filters.append(Project.status == status)
    
    if start_date:
        start = datetime.fromisoformat(start_date)
        filters.append(Project.start_date >= start)
    
    if end_date:
        end = datetime.fromisoformat(end_date)
        filters.append(Project.end_date <= end)
    
    if filters:
        query = query.filter(and_(*filters))
    
    # 最后应用数据权限过滤 ⭐ 权限过滤放在最后
    query = DataScopeServiceEnhanced.apply_data_scope(
        query=query,
        db=db,
        user=current_user,
        resource_type="project",
        org_field="dept_id",
        owner_field="created_by",
        pm_field="pm_id"
    )
    
    # 执行查询
    projects = query.all()
    
    return [p.to_dict() for p in projects]


# ============================================================================
# 使用说明
# ============================================================================

"""
如何在你的项目中使用这些示例：

1. **简单场景**：
   - 直接使用 DataScopeServiceEnhanced.apply_data_scope()
   - 参考示例 1（项目管理）

2. **标准模型**：
   - 使用 DATA_SCOPE_CONFIGS 中的预定义配置
   - 参考示例 2（采购订单）

3. **自定义配置**：
   - 创建 DataScopeConfig 对象
   - 参考示例 3（任务管理）

4. **复杂逻辑**：
   - 实现自定义过滤函数
   - 参考示例 4（文档管理）

5. **Service 层**：
   - 在服务类中封装权限逻辑
   - 参考示例 9（ProjectService）

6. **调试问题**：
   - 使用调试接口查看权限信息
   - 参考示例 8（调试工具）

记住：
✅ 总是在 API 层应用数据权限过滤
✅ 敏感操作要二次检查权限
✅ 批量操作要逐个验证
✅ 导出和统计也要考虑权限
"""
