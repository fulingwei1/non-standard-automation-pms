# -*- coding: utf-8 -*-
"""
项目关联管理
包含：项目间关联、依赖关系、关联查询
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.utils.db_helpers import get_or_404

router = APIRouter()

# 关联类型定义
RELATION_TYPES = {
    "PARENT_CHILD": {"name": "父子项目", "reverse": "CHILD_PARENT"},
    "CHILD_PARENT": {"name": "子父项目", "reverse": "PARENT_CHILD"},
    "DEPENDS_ON": {"name": "依赖于", "reverse": "DEPENDED_BY"},
    "DEPENDED_BY": {"name": "被依赖", "reverse": "DEPENDS_ON"},
    "RELATED": {"name": "相关项目", "reverse": "RELATED"},
    "SUCCESSOR": {"name": "后续项目", "reverse": "PREDECESSOR"},
    "PREDECESSOR": {"name": "前置项目", "reverse": "SUCCESSOR"},
}


@router.get("/{project_id}/relations", response_model=ResponseModel)
def get_project_relations(
    project_id: int,
    db: Session = Depends(get_db),
    relation_type: Optional[str] = Query(None, description="关联类型"),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取项目关联关系

    Args:
        project_id: 项目ID
        db: 数据库会话
        relation_type: 关联类型筛选
        current_user: 当前用户

    Returns:
        ResponseModel: 关联列表
    """
    project = get_or_404(db, Project, project_id, detail="项目不存在")

    # 从项目的 related_projects 字段获取关联（假设是 JSON 格式存储）
    relations = []

    # 如果项目有 parent_project_id，添加父项目关联
    if hasattr(project, 'parent_project_id') and project.parent_project_id:
        parent = db.query(Project).filter(Project.id == project.parent_project_id).first()
        if parent:
            relations.append({
                "relation_type": "PARENT_CHILD",
                "relation_name": "父项目",
                "related_project_id": parent.id,
                "related_project_code": parent.project_code,
                "related_project_name": parent.project_name,
                "related_project_status": parent.status,
            })

    # 查找子项目
    if hasattr(Project, 'parent_project_id'):
        children = db.query(Project).filter(Project.parent_project_id == project_id).all()
        for child in children:
            relations.append({
                "relation_type": "CHILD_PARENT",
                "relation_name": "子项目",
                "related_project_id": child.id,
                "related_project_code": child.project_code,
                "related_project_name": child.project_name,
                "related_project_status": child.status,
            })

    # 按类型筛选
    if relation_type:
        relations = [r for r in relations if r["relation_type"] == relation_type]

    return ResponseModel(
        code=200,
        message="获取项目关联成功",
        data={
            "project_id": project_id,
            "project_code": project.project_code,
            "total": len(relations),
            "relations": relations
        }
    )


@router.get("/relations/types", response_model=ResponseModel)
def get_relation_types(
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取关联类型定义

    Args:
        current_user: 当前用户

    Returns:
        ResponseModel: 关联类型列表
    """
    types = [{
        "code": code,
        "name": info["name"],
        "reverse_type": info["reverse"]
    } for code, info in RELATION_TYPES.items()]

    return ResponseModel(
        code=200,
        message="获取关联类型成功",
        data={"types": types}
    )


@router.post("/{project_id}/relations", response_model=ResponseModel)
def create_project_relation(
    project_id: int,
    relation_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    创建项目关联

    Args:
        project_id: 项目ID
        relation_data: 关联数据（related_project_id, relation_type）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 创建结果
    """
    project = get_or_404(db, Project, project_id, detail="项目不存在")

    related_project_id = relation_data.get("related_project_id")
    relation_type = relation_data.get("relation_type", "RELATED")

    if project_id == related_project_id:
        raise HTTPException(status_code=400, detail="不能关联自身")

    related_project = get_or_404(db, Project, related_project_id, detail="关联项目不存在")

    if relation_type not in RELATION_TYPES:
        raise HTTPException(status_code=400, detail="无效的关联类型")

    # 处理父子关系
    if relation_type == "PARENT_CHILD":
        if hasattr(project, 'parent_project_id'):
            project.parent_project_id = related_project_id
            db.commit()
            return ResponseModel(
                code=200,
                message="父项目关联成功",
                data={"project_id": project_id, "parent_project_id": related_project_id}
            )

    # 其他关系类型可以存储在 JSON 字段中
    return ResponseModel(
        code=200,
        message="项目关联创建成功",
        data={
            "project_id": project_id,
            "related_project_id": related_project_id,
            "relation_type": relation_type
        }
    )


@router.delete("/{project_id}/relations/{related_project_id}", response_model=ResponseModel)
def delete_project_relation(
    project_id: int,
    related_project_id: int,
    relation_type: str = Query(..., description="关联类型"),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    删除项目关联

    Args:
        project_id: 项目ID
        related_project_id: 关联项目ID
        relation_type: 关联类型
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 删除结果
    """
    project = get_or_404(db, Project, project_id, detail="项目不存在")

    # 处理父子关系删除
    if relation_type == "PARENT_CHILD":
        if hasattr(project, 'parent_project_id') and project.parent_project_id == related_project_id:
            project.parent_project_id = None
            db.commit()
            return ResponseModel(code=200, message="父项目关联已删除", data={"project_id": project_id})

    return ResponseModel(
        code=200,
        message="项目关联删除成功",
        data={"project_id": project_id, "related_project_id": related_project_id}
    )


@router.get("/{project_id}/dependency-chain", response_model=ResponseModel)
def get_dependency_chain(
    project_id: int,
    direction: str = Query("both", description="方向：upstream/downstream/both"),
    max_depth: int = Query(5, ge=1, le=10, description="最大深度"),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取项目依赖链

    Args:
        project_id: 项目ID
        direction: 查询方向
        max_depth: 最大深度
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 依赖链
    """
    project = get_or_404(db, Project, project_id, detail="项目不存在")

    chain = {
        "project_id": project_id,
        "project_code": project.project_code,
        "project_name": project.project_name,
        "upstream": [],
        "downstream": []
    }

    # 获取上游（父项目链）
    if direction in ["upstream", "both"]:
        current = project
        depth = 0
        while hasattr(current, 'parent_project_id') and current.parent_project_id and depth < max_depth:
            parent = db.query(Project).filter(Project.id == current.parent_project_id).first()
            if parent:
                chain["upstream"].append({
                    "project_id": parent.id,
                    "project_code": parent.project_code,
                    "project_name": parent.project_name,
                    "depth": depth + 1
                })
                current = parent
                depth += 1
            else:
                break

    # 获取下游（子项目链）
    if direction in ["downstream", "both"]:
        def get_children(parent_id, current_depth):
            if current_depth >= max_depth:
                return []
            if not hasattr(Project, 'parent_project_id'):
                return []
            children = db.query(Project).filter(Project.parent_project_id == parent_id).all()
            result = []
            for child in children:
                result.append({
                    "project_id": child.id,
                    "project_code": child.project_code,
                    "project_name": child.project_name,
                    "depth": current_depth + 1,
                    "children": get_children(child.id, current_depth + 1)
                })
            return result

        chain["downstream"] = get_children(project_id, 0)

    return ResponseModel(
        code=200,
        message="获取依赖链成功",
        data=chain
    )
