# -*- coding: utf-8 -*-
"""
项目中心CRUD路由基类使用示例
"""

from fastapi import APIRouter, Query
from sqlalchemy.orm import Session

from app.api.v1.core.project_crud_base import create_project_crud_router
from app.models.project import ProjectMilestone
from app.schemas.project import (
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneResponse
)


# ========== 示例1: 最简单的使用方式 ==========

# 直接创建路由
milestone_router = create_project_crud_router(
    model=ProjectMilestone,
    create_schema=MilestoneCreate,
    update_schema=MilestoneUpdate,
    response_schema=MilestoneResponse,
    permission_prefix="milestone",
    project_id_field="project_id"
)

# 在主路由中注册
# router.include_router(
#     milestone_router,
#     prefix="/{project_id}/milestones",
#     tags=["projects-milestones"]
# )


# ========== 示例2: 带自定义筛选 ==========

def filter_by_status(query, status: str):
    """自定义状态筛选器"""
    return query.filter(ProjectMilestone.status == status)


milestone_router_with_filters = create_project_crud_router(
    model=ProjectMilestone,
    create_schema=MilestoneCreate,
    update_schema=MilestoneUpdate,
    response_schema=MilestoneResponse,
    permission_prefix="milestone",
    project_id_field="project_id",
    keyword_fields=["milestone_name", "description"],
    default_order_by="planned_date",
    custom_filters={
        "status": filter_by_status  # 在列表接口中可以通过 ?status=ACTIVE 筛选
    }
)


# ========== 示例3: 带钩子函数 ==========

def before_create_milestone(item_data: dict, project_id: int, current_user):
    """创建前钩子：自动设置默认值"""
    # 例如：自动生成编码
    if "code" not in item_data or not item_data["code"]:
        item_data["code"] = f"MIL-{project_id}-{len(item_data)}"
    
    # 例如：设置创建人
    if "created_by" not in item_data:
        item_data["created_by"] = current_user.id
    
    return item_data


def after_create_milestone(db_item, project_id: int, current_user):
    """创建后钩子：发送通知等"""
    # 例如：发送通知
    # send_notification(f"创建了里程碑: {db_item.milestone_name}")
    
    # 例如：记录日志
    # log_action("milestone_created", db_item.id, current_user.id)
    
    return db_item


def before_update_milestone(item, item_in, project_id: int, current_user):
    """更新前钩子：验证业务规则"""
    # 例如：检查是否可以更新
    if item.status == "COMPLETED":
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已完成的里程碑不能修改"
        )
    
    return item_in


def after_update_milestone(item, project_id: int, current_user):
    """更新后钩子：记录变更历史"""
    # 例如：记录变更历史
    # log_change("milestone_updated", item.id, current_user.id)
    
    return item


def before_delete_milestone(item, project_id: int, current_user):
    """删除前钩子：检查是否可以删除"""
    # 例如：检查是否可以删除
    if item.status == "COMPLETED":
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已完成的里程碑不能删除"
        )
    
    return True  # 返回True允许删除，False取消删除


def after_delete_milestone(item_id: int, project_id: int, current_user):
    """删除后钩子：清理关联数据"""
    # 例如：清理关联数据
    # cleanup_related_data(item_id)
    pass


milestone_router_with_hooks = create_project_crud_router(
    model=ProjectMilestone,
    create_schema=MilestoneCreate,
    update_schema=MilestoneUpdate,
    response_schema=MilestoneResponse,
    permission_prefix="milestone",
    project_id_field="project_id",
    keyword_fields=["milestone_name", "description"],
    default_order_by="planned_date",
    before_create=before_create_milestone,
    after_create=after_create_milestone,
    before_update=before_update_milestone,
    after_update=after_update_milestone,
    before_delete=before_delete_milestone,
    after_delete=after_delete_milestone,
)


# ========== 示例4: 添加自定义端点 ==========

# 创建基础路由
base_router = create_project_crud_router(
    model=ProjectMilestone,
    create_schema=MilestoneCreate,
    update_schema=MilestoneUpdate,
    response_schema=MilestoneResponse,
    permission_prefix="milestone",
    project_id_field="project_id"
)

# 添加自定义端点
@base_router.put("/{item_id}/complete", response_model=MilestoneResponse)
def complete_milestone(
    project_id: int,
    item_id: int,
    db: Session,
    current_user,
):
    """完成里程碑（自定义端点）"""
    from app.api import deps
    from app.core import security
    from app.utils.permission_helpers import check_project_access_or_raise
    from fastapi import Path, Depends, HTTPException, status
    
    check_project_access_or_raise(db, current_user, project_id)
    
    milestone = db.query(ProjectMilestone).filter(
        ProjectMilestone.id == item_id,
        ProjectMilestone.project_id == project_id
    ).first()
    
    if not milestone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="里程碑不存在"
        )
    
    milestone.status = "COMPLETED"
    db.commit()
    db.refresh(milestone)
    
    return MilestoneResponse.model_validate(milestone)


# ========== 示例5: 使用面向对象方式 ==========

from app.api.v1.core.project_crud_base import ProjectCRUDRouter

class MilestoneRouter(ProjectCRUDRouter):
    """里程碑路由（面向对象方式）"""
    
    def __init__(self):
        super().__init__(
            model=ProjectMilestone,
            create_schema=MilestoneCreate,
            update_schema=MilestoneUpdate,
            response_schema=MilestoneResponse,
            permission_prefix="milestone",
            project_id_field="project_id",
            keyword_fields=["milestone_name", "description"],
            default_order_by="planned_date"
        )
    
    def register_routes(self):
        """注册路由并添加自定义端点"""
        router = super().register_routes()
        
        # 添加自定义端点
        @router.put("/{item_id}/complete", response_model=MilestoneResponse)
        def complete_milestone(...):
            # 自定义逻辑
            pass
        
        return router
