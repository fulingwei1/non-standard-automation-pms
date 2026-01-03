from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User, UserRole
from app.schemas.auth import UserCreate, UserUpdate, UserResponse

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(security.require_permission("USER_VIEW")),
) -> Any:
    """
    Retrieve users.
    """
    users = db.query(User).offset(skip).limit(limit).all()
    # Map roles for response
    for u in users:
        u.roles_list = [ur.role.role_name for ur in u.roles]
    return users


@router.post("/", response_model=UserResponse)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
    current_user: User = Depends(security.require_permission("USER_CREATE")),
) -> Any:
    """
    Create new user.
    """
    user = db.query(User).filter(User.username == user_in.username).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )

    user = User(
        username=user_in.username,
        password_hash=security.get_password_hash(user_in.password),
        email=user_in.email,
        phone=user_in.phone,
        real_name=user_in.real_name,
        employee_no=user_in.employee_no,
        department=user_in.department,
        position=user_in.position,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if user_in.role_ids:
        for role_id in user_in.role_ids:
            user_role = UserRole(user_id=user.id, role_id=role_id)
            db.add(user_role)
        db.commit()
        db.refresh(user)

    return user


@router.get("/{user_id}", response_model=UserResponse)
def read_user_by_id(
    user_id: int,
    current_user: User = Depends(security.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id != current_user.id and not security.check_permission(
        current_user, "USER_VIEW"
    ):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(security.require_permission("USER_UPDATE")),
) -> Any:
    """
    Update a user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_in.model_dump(exclude_unset=True)
    if "role_ids" in update_data:
        role_ids = update_data.pop("role_ids")
        # Update user roles
        db.query(UserRole).filter(UserRole.user_id == user.id).delete()
        for r_id in role_ids:
            db.add(UserRole(user_id=user.id, role_id=r_id))

    for field, value in update_data.items():
        setattr(user, field, value)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user
