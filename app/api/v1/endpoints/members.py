from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.project import ProjectMember, Project
from app.models.user import User
from app.schemas.project import ProjectMemberCreate, ProjectMemberResponse

router = APIRouter()


@router.get("/", response_model=List[ProjectMemberResponse])
def read_members(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    project_id: int = Query(None, description="Filter by project ID"),
) -> Any:
    """
    Retrieve project members.
    """
    query = db.query(ProjectMember)
    if project_id:
        query = query.filter(ProjectMember.project_id == project_id)

    members = query.offset(skip).limit(limit).all()

    # Map user info
    for m in members:
        m.username = m.user.username if m.user else "Unknown"
        m.real_name = m.user.real_name if m.user else "Unknown"

    return members


@router.post("/", response_model=ProjectMemberResponse)
def add_member(
    *,
    db: Session = Depends(deps.get_db),
    member_in: ProjectMemberCreate,
) -> Any:
    """
    Add member to project.
    """
    # Check project exists
    project = db.query(Project).filter(Project.id == member_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check user exists
    user = db.query(User).filter(User.id == member_in.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if already a member
    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == member_in.project_id,
            ProjectMember.user_id == member_in.user_id,
        )
        .first()
    )
    if member:
        raise HTTPException(
            status_code=400,
            detail="User is already a member of this project.",
        )

    member = ProjectMember(**member_in.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)

    member.username = user.username
    member.real_name = user.real_name
    return member


@router.delete("/{member_id}", response_model=ProjectMemberResponse)
def remove_member(
    *,
    db: Session = Depends(deps.get_db),
    member_id: int,
) -> Any:
    """
    Remove record from project members.
    """
    member = db.query(ProjectMember).filter(ProjectMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member record not found")

    # Pre-capture user info for response after deletion if needed,
    # but db.delete might affect lazy loading if not careful.
    res_data = {
        **member.__dict__,
        "username": member.user.username if member.user else "Unknown",
        "real_name": member.user.real_name if member.user else "Unknown",
    }

    db.delete(member)
    db.commit()
    return res_data
