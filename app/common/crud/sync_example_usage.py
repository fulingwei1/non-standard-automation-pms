# -*- coding: utf-8 -*-
"""
同步版本CRUD基类使用示例
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Query, Path
from pydantic import BaseModel

from app.common.crud.sync_service import SyncBaseService
from app.models.project import Project, ProjectMilestone
from app.schemas.project import (
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneResponse
)
from app.schemas.common import PaginatedResponse
from app.api.dependencies import get_db, get_current_user

router = APIRouter()


# ========== 示例1: 最简单的Service实现 ==========

class MilestoneService(
    SyncBaseService[ProjectMilestone, MilestoneCreate, MilestoneUpdate, MilestoneResponse]
):
    """里程碑服务（只需实现_to_response方法！）"""
    
    def __init__(self, db: Session):
        super().__init__(
            model=ProjectMilestone,
            db=db,
            resource_name="里程碑"
        )
    
    def _to_response(self, obj: ProjectMilestone) -> MilestoneResponse:
        """将模型对象转换为响应对象"""
        return MilestoneResponse.model_validate(obj)


# ========== 示例2: 在API中使用 ==========

@router.get("/", response_model=PaginatedResponse[MilestoneResponse])
def list_milestones(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user = Depends(get_current_user),
):
    """获取里程碑列表"""
    service = MilestoneService(db)
    
    # 构建筛选条件
    filters = {"project_id": project_id}
    if status:
        filters["status"] = status
    
    # 调用Service的list方法
    result = service.list(
        skip=(page - 1) * page_size,
        limit=page_size,
        filters=filters,
        keyword=keyword,
        keyword_fields=["milestone_name", "description"],
        order_by="planned_date",
        order_direction="desc"
    )
    
    return PaginatedResponse(
        items=result["items"],
        total=result["total"],
        page=page,
        page_size=page_size,
        pages=(result["total"] + page_size - 1) // page_size
    )


@router.post("/", response_model=MilestoneResponse)
def create_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_in: MilestoneCreate = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """创建里程碑"""
    service = MilestoneService(db)
    
    # 确保使用项目ID
    milestone_data = milestone_in.model_dump()
    milestone_data["project_id"] = project_id
    milestone_create = MilestoneCreate(**milestone_data)
    
    # 调用Service的create方法
    return service.create(milestone_create)


@router.get("/{milestone_id}", response_model=MilestoneResponse)
def get_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_id: int = Path(..., description="里程碑ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取里程碑详情"""
    service = MilestoneService(db)
    
    # 调用Service的get方法
    milestone = service.get(milestone_id)
    
    # 验证里程碑属于该项目
    if milestone.project_id != project_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="里程碑不存在"
        )
    
    return milestone


@router.put("/{milestone_id}", response_model=MilestoneResponse)
def update_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_id: int = Path(..., description="里程碑ID"),
    milestone_in: MilestoneUpdate = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """更新里程碑"""
    service = MilestoneService(db)
    
    # 验证里程碑存在且属于该项目
    milestone = service.get(milestone_id)
    if milestone.project_id != project_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="里程碑不存在"
        )
    
    # 调用Service的update方法
    return service.update(milestone_id, milestone_in)


@router.delete("/{milestone_id}", status_code=204)
def delete_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_id: int = Path(..., description="里程碑ID"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """删除里程碑"""
    service = MilestoneService(db)
    
    # 验证里程碑存在且属于该项目
    milestone = service.get(milestone_id)
    if milestone.project_id != project_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="里程碑不存在"
        )
    
    # 调用Service的delete方法
    service.delete(milestone_id)
    return None


# ========== 示例3: 带业务逻辑的Service实现 ==========

class MilestoneServiceAdvanced(
    SyncBaseService[ProjectMilestone, MilestoneCreate, MilestoneUpdate, MilestoneResponse]
):
    """里程碑服务（带自定义业务逻辑）"""
    
    def __init__(self, db: Session):
        super().__init__(
            model=ProjectMilestone,
            db=db,
            resource_name="里程碑"
        )
    
    def _to_response(self, obj: ProjectMilestone) -> MilestoneResponse:
        """将模型对象转换为响应对象"""
        return MilestoneResponse.model_validate(obj)
    
    def list_by_project(
        self,
        project_id: int,
        *,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取项目的里程碑列表（自定义方法）"""
        filters = {"project_id": project_id}
        if status:
            filters["status"] = status
        
        return self.list(
            skip=skip,
            limit=limit,
            filters=filters,
            keyword=keyword,
            keyword_fields=["milestone_name", "description"],
            order_by="planned_date",
            order_direction="desc"
        )
    
    def create_for_project(
        self,
        project_id: int,
        milestone_in: MilestoneCreate
    ) -> MilestoneResponse:
        """为项目创建里程碑（自定义方法）"""
        # 确保使用项目ID
        milestone_data = milestone_in.model_dump()
        milestone_data["project_id"] = project_id
        
        milestone_create = MilestoneCreate(**milestone_data)
        
        return self.create(milestone_create)
    
    def _before_create(self, obj_in: MilestoneCreate) -> MilestoneCreate:
        """创建前钩子：自动设置默认值"""
        # 可以在这里添加业务逻辑
        # 例如：自动生成编码、设置默认状态等
        return obj_in
    
    def _after_create(self, db_obj: ProjectMilestone) -> ProjectMilestone:
        """创建后钩子：发送通知等"""
        # 可以在这里添加业务逻辑
        # 例如：发送通知、记录日志等
        return db_obj
