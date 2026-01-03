from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import Role, Permission, RolePermission, User
from app.schemas.auth import RoleCreate, RoleUpdate, RoleResponse, PermissionResponse

router = APIRouter()


@router.get("/", response_model=List[RoleResponse])
def read_roles(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(security.require_permission("ROLE_VIEW")),
) -> Any:
    """
    Retrieve roles.
    """
    roles = db.query(Role).offset(skip).limit(limit).all()
    # Map permissions
    for r in roles:
        r.permissions_list = [rp.permission.permission_name for rp in r.permissions]
    return roles


@router.post("/", response_model=RoleResponse)
def create_role(
    *,
    db: Session = Depends(deps.get_db),
    role_in: RoleCreate,
    current_user: User = Depends(security.require_permission("ROLE_CREATE")),
) -> Any:
    """
    Create new role.
    """
    role = db.query(Role).filter(Role.role_code == role_in.role_code).first()
    if role:
        raise HTTPException(
            status_code=400,
            detail="The role with this code already exists in the system.",
        )

    role = Role(
        role_code=role_in.role_code,
        role_name=role_in.role_name,
        description=role_in.description,
        data_scope=role_in.data_scope,
    )
    db.add(role)
    db.commit()
    db.refresh(role)

    if role_in.permission_ids:
        for p_id in role_in.permission_ids:
            db.add(RolePermission(role_id=role.id, permission_id=p_id))
        db.commit()
        db.refresh(role)

    return role


@router.get("/permissions", response_model=List[PermissionResponse])
def read_permissions(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    List all available permissions.
    """
    return db.query(Permission).all()
