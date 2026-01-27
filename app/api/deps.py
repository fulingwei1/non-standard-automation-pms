from typing import Optional

from fastapi import Depends, HTTPException, Request, status

from app.core import security
from app.models.base import get_db
from app.models.user import User

# Re-export get_db from models.base for API endpoint dependencies
# This is the single source of truth for database session injection

def get_current_user_from_state(request: Request) -> User:
    """
    从 request.state 获取已验证的用户

    此函数用于从全局认证中间件已验证的用户信息中获取当前用户。
    中间件会将验证通过的用户存储在 request.state.user 中。

    Args:
        request: FastAPI Request对象

    Returns:
        User: 当前已认证的用户

    Raises:
        HTTPException: 如果用户未认证（401）

    使用示例：
        @router.get("/my-data")
        async def get_my_data(
            request: Request,
            current_user: User = Depends(get_current_user_from_state)
        ):
            # current_user已经被中间件验证过了
            pass
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户未认证，请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return request.state.user


def get_tenant_id(
    current_user: User = Depends(security.get_current_active_user),
) -> Optional[int]:
    """
    获取当前用户的租户ID

    用于数据隔离，确保用户只能访问自己租户的数据。
    超级管理员可以访问所有租户的数据（返回 None）。

    Args:
        current_user: 当前已认证的用户

    Returns:
        Optional[int]: 租户ID，超级管理员返回 None
    """
    if current_user.is_superuser:
        # 超级管理员可以访问所有租户数据
        return None
    return current_user.tenant_id


def require_tenant_id(
    current_user: User = Depends(security.get_current_active_user),
) -> int:
    """
    要求必须有租户ID

    用于需要严格租户隔离的场景，超级管理员也必须指定租户。

    Args:
        current_user: 当前已认证的用户

    Returns:
        int: 租户ID

    Raises:
        HTTPException: 如果用户没有关联租户
    """
    if current_user.tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户未关联租户，无法执行此操作",
        )
    return current_user.tenant_id


def require_tenant_admin(
    current_user: User = Depends(security.get_current_active_user),
) -> User:
    """
    要求租户管理员权限

    Args:
        current_user: 当前已认证的用户

    Returns:
        User: 当前用户

    Raises:
        HTTPException: 如果用户不是租户管理员或超级管理员
    """
    if not current_user.is_superuser and not current_user.is_tenant_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要租户管理员权限",
        )
    return current_user


def require_super_admin(
    current_user: User = Depends(security.get_current_active_user),
) -> User:
    """
    要求超级管理员权限

    Args:
        current_user: 当前已认证的用户

    Returns:
        User: 当前用户

    Raises:
        HTTPException: 如果用户不是超级管理员
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限",
        )
    return current_user


# Re-export authentication dependencies
get_current_user = security.get_current_user
get_current_active_user = security.get_current_active_user
get_current_active_superuser = security.get_current_active_superuser
